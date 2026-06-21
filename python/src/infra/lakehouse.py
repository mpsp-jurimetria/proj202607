"""Conexão com o Lakehouse (OneLake) para armazenamento de arquivos brutos."""

import os
from pathlib import Path

from azure.identity import AzureCliCredential, ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient


def _get_credential() -> AzureCliCredential | ClientSecretCredential:
    client_secret = os.getenv("CLIENT_SECRET")
    if client_secret:
        return ClientSecretCredential(
            tenant_id=os.getenv("TENANT_ID"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret=client_secret,
        )
    return AzureCliCredential()


def get_client() -> DataLakeServiceClient:
    return DataLakeServiceClient(
        account_url="https://onelake.dfs.fabric.microsoft.com",
        credential=_get_credential(),
    )


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

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
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

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
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

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
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

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
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

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
    base = f"{lakehouse_id}/Files/{prefixo}"
    prefix_len = len(f"{lakehouse_id}/Files/")
    return [
        path.name[prefix_len:]
        for path in fs.get_paths(path=base)
        if not path.is_directory
    ]
