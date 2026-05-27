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


def upload_file(local_path: Path, remote_path: str) -> None:
    """Envia arquivo para a seção Files do Lakehouse.

    Args:
        local_path: caminho local do arquivo.
        remote_path: caminho relativo dentro de Files, ex: "cnmp/pdfs/arquivo.pdf".
    """
    workspace_id = os.getenv("FABRIC_WORKSPACE_ID")
    lakehouse_id = os.getenv("FABRIC_LAKEHOUSE_ID")

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
    full_path = f"{lakehouse_id}/Files/{remote_path}"
    file_client = fs.get_file_client(full_path)

    with open(local_path, "rb") as f:
        file_client.upload_data(f, overwrite=True)


def download_file(remote_path: str, local_path: Path) -> None:
    """Baixa arquivo do Lakehouse para o disco local."""
    workspace_id = os.getenv("FABRIC_WORKSPACE_ID")
    lakehouse_id = os.getenv("FABRIC_LAKEHOUSE_ID")

    client = get_client()
    fs = client.get_file_system_client(file_system=workspace_id)
    full_path = f"{lakehouse_id}/Files/{remote_path}"
    file_client = fs.get_file_client(full_path)

    local_path.parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file_client.download_file().readall())
