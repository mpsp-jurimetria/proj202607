"""Conexão com o Lakehouse (OneLake) para armazenamento de arquivos brutos."""

import os
import threading
from pathlib import Path

from azure.identity import AzureCliCredential, ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient, FileSystemClient


class _NotebookCredential:
    """Credencial baseada na identidade nativa de um notebook Fabric (storage)."""

    def get_token(self, *scopes: str, **kwargs: object) -> object:
        from notebookutils import credentials as nb_credentials  # type: ignore[import-not-found]

        token = nb_credentials.getToken("storage")
        return type("Token", (), {"token": token, "expires_on": 0})()


def _get_credential() -> "_NotebookCredential | AzureCliCredential | ClientSecretCredential":
    """Identidade nativa do notebook Fabric quando disponível, senão Service
    Principal/AzureCliCredential para uso local (scripts via uv run)."""
    try:
        import notebookutils  # noqa: F401

        return _NotebookCredential()
    except ImportError:
        pass

    client_secret = os.getenv("CLIENT_SECRET")
    if client_secret:
        return ClientSecretCredential(
            tenant_id=os.getenv("TENANT_ID"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret=client_secret,
        )
    return AzureCliCredential()


_client_cache: DataLakeServiceClient | None = None
_fs_cache: dict[str, FileSystemClient] = {}
# RLock (não Lock comum): _get_filesystem_client adquire o lock e chama
# get_client() por dentro, que adquire o mesmo lock de novo na mesma thread —
# com Lock comum (não reentrante) isso é deadlock.
_cache_lock = threading.RLock()


def get_client() -> DataLakeServiceClient:
    """Cliente do OneLake, reaproveitado entre chamadas (e entre threads).

    Criar um DataLakeServiceClient novo a cada chamada também descarta o cache
    de token do azure-core — em uma carga com milhares de leituras (uma por
    instância), isso significava buscar um token novo a cada arquivo. Reaproveitar
    o cliente deixa o SDK cachear o token normalmente (válido por ~1h).
    """
    global _client_cache
    with _cache_lock:
        if _client_cache is None:
            _client_cache = DataLakeServiceClient(
                account_url="https://onelake.dfs.fabric.microsoft.com",
                credential=_get_credential(),
            )
        return _client_cache


def _get_filesystem_client(workspace_id: str) -> FileSystemClient:
    with _cache_lock:
        if workspace_id not in _fs_cache:
            _fs_cache[workspace_id] = get_client().get_file_system_client(file_system=workspace_id)
        return _fs_cache[workspace_id]


def _bronze_ids() -> tuple[str, str]:
    """Resolve workspace_id/lakehouse_id do Lakehouse mp_bronze."""
    workspace_id = os.environ["FABRIC_WORKSPACE_ID"]
    lakehouse_id = os.environ["FABRIC_LAKEHOUSE_ID"]
    return workspace_id, lakehouse_id


def upload_file(
    local_path: Path,
    remote_path: str,
    workspace_id: str | None = None,
    lakehouse_id: str | None = None,
) -> None:
    """Envia arquivo para a seção Files do Lakehouse.

    Args:
        local_path: caminho local do arquivo.
        remote_path: caminho relativo dentro de Files, ex: "cnmp/pdfs/arquivo.pdf".
        workspace_id: id do workspace; se omitido, resolve a camada bronze via env.
        lakehouse_id: id do lakehouse; se omitido, resolve a camada bronze via env.
    """
    if workspace_id is None or lakehouse_id is None:
        workspace_id, lakehouse_id = _bronze_ids()

    fs = _get_filesystem_client(workspace_id)
    full_path = f"{lakehouse_id}/Files/{remote_path}"
    file_client = fs.get_file_client(full_path)

    with open(local_path, "rb") as f:
        file_client.upload_data(f, overwrite=True)


def upload_bytes(
    data: bytes,
    remote_path: str,
    workspace_id: str | None = None,
    lakehouse_id: str | None = None,
) -> None:
    """Envia bytes diretamente para a seção Files do Lakehouse, sem arquivo local intermediário."""
    if workspace_id is None or lakehouse_id is None:
        workspace_id, lakehouse_id = _bronze_ids()

    fs = _get_filesystem_client(workspace_id)
    full_path = f"{lakehouse_id}/Files/{remote_path}"
    file_client = fs.get_file_client(full_path)
    file_client.upload_data(data, overwrite=True)


def download_file(
    remote_path: str,
    local_path: Path,
    workspace_id: str | None = None,
    lakehouse_id: str | None = None,
) -> None:
    """Baixa arquivo do Lakehouse para o disco local."""
    if workspace_id is None or lakehouse_id is None:
        workspace_id, lakehouse_id = _bronze_ids()

    fs = _get_filesystem_client(workspace_id)
    full_path = f"{lakehouse_id}/Files/{remote_path}"
    file_client = fs.get_file_client(full_path)

    local_path.parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file_client.download_file().readall())


def download_bytes(
    remote_path: str,
    workspace_id: str | None = None,
    lakehouse_id: str | None = None,
) -> bytes:
    """Baixa o conteúdo de um arquivo do Lakehouse direto em memória."""
    if workspace_id is None or lakehouse_id is None:
        workspace_id, lakehouse_id = _bronze_ids()

    fs = _get_filesystem_client(workspace_id)
    full_path = f"{lakehouse_id}/Files/{remote_path}"
    file_client = fs.get_file_client(full_path)
    return file_client.download_file().readall()


def listar_arquivos(
    prefixo: str,
    workspace_id: str | None = None,
    lakehouse_id: str | None = None,
) -> list[str]:
    """Lista caminhos (relativos a Files/) de todos os arquivos sob um prefixo."""
    if workspace_id is None or lakehouse_id is None:
        workspace_id, lakehouse_id = _bronze_ids()

    fs = _get_filesystem_client(workspace_id)
    base = f"{lakehouse_id}/Files/{prefixo}"
    prefix_len = len(f"{lakehouse_id}/Files/")
    return [
        path.name[prefix_len:]
        for path in fs.get_paths(path=base)
        if not path.is_directory
    ]
