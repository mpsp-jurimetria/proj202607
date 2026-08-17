"""Automação da sincronização git <-> workspace do Fabric via Service Principal.

Uso típico após um `git push` no repositório do Fabric:

    from infra.fabric_git import atualizar_workspace_do_git
    atualizar_workspace_do_git(workspace_id)

Pré-requisito único (feito uma vez, fora deste módulo): o Service Principal
precisa ter papel de Contributor (ou superior) no workspace do Fabric, e uma
credencial git configurada — ver `configurar_credencial_git()`.
"""

import logging
import os
import time
from typing import Any

import httpx
from azure.identity import ClientSecretCredential

logger = logging.getLogger(__name__)

_FABRIC_API = "https://api.fabric.microsoft.com/v1"
_SCOPE = "https://api.fabric.microsoft.com/.default"


def _credential() -> ClientSecretCredential:
    return ClientSecretCredential(
        tenant_id=os.environ["TENANT_ID"],
        client_id=os.environ["CLIENT_ID"],
        client_secret=os.environ["CLIENT_SECRET"],
    )


def _headers() -> dict[str, str]:
    token = _credential().get_token(_SCOPE).token
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _aguardar_operacao(operation_id: str, intervalo_s: int = 5, timeout_s: int = 300) -> None:
    """Espera uma long running operation do Fabric terminar (Succeeded/Failed)."""
    url = f"{_FABRIC_API}/operations/{operation_id}"
    decorridos = 0
    while decorridos < timeout_s:
        resp = httpx.get(url, headers=_headers(), timeout=30)
        resp.raise_for_status()
        estado = resp.json()
        if estado["status"] == "Succeeded":
            return
        if estado["status"] == "Failed":
            raise RuntimeError(f"Operação {operation_id} falhou: {estado.get('error')}")
        time.sleep(intervalo_s)
        decorridos += intervalo_s
    raise TimeoutError(f"Operação {operation_id} não terminou em {timeout_s}s")


def criar_conexao_ado_service_principal(organizacao: str, projeto: str, repositorio: str) -> str:
    """Cria, no Fabric, uma conexão 'Azure DevOps – Source Control' autenticada
    com as próprias credenciais do Service Principal (sem PAT). Retorna o
    connectionId, usado depois em `configurar_credencial_git()`."""
    payload: dict[str, Any] = {
        "displayName": f"ADO SP - {projeto}/{repositorio}",
        "connectivityType": "ShareableCloud",
        "connectionDetails": {
            "creationMethod": "AzureDevOpsSourceControl.Contents",
            "type": "AzureDevOpsSourceControl",
            "parameters": [
                {
                    "dataType": "Text",
                    "name": "url",
                    "value": f"https://dev.azure.com/{organizacao}/{projeto}/_git/{repositorio}/",
                }
            ],
        },
        "credentialDetails": {
            "credentials": {
                "credentialType": "ServicePrincipal",
                "tenantId": os.environ["TENANT_ID"],
                "servicePrincipalClientId": os.environ["CLIENT_ID"],
                "servicePrincipalSecret": os.environ["CLIENT_SECRET"],
            }
        },
    }
    resp = httpx.post(f"{_FABRIC_API}/connections", headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    connection_id = resp.json()["id"]
    logger.info("Conexão ADO criada: %s", connection_id)
    return connection_id


def configurar_credencial_git(workspace_id: str, connection_id: str) -> None:
    """Aponta a credencial git do Service Principal (para este workspace) para
    a conexão ADO criada por `criar_conexao_ado_service_principal()`."""
    url = f"{_FABRIC_API}/workspaces/{workspace_id}/git/myGitCredentials"
    payload = {"source": "ConfiguredConnection", "connectionId": connection_id}
    resp = httpx.patch(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    logger.info("Credencial git do Service Principal configurada (conexão %s)", connection_id)


def status_git(workspace_id: str) -> dict[str, Any]:
    """Consulta o status git do workspace (workspaceHead, remoteCommitHash, changes)."""
    url = f"{_FABRIC_API}/workspaces/{workspace_id}/git/status"
    resp = httpx.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def atualizar_workspace_do_git(workspace_id: str, allow_override_items: bool = False) -> dict[str, Any]:
    """Aplica ao workspace os commits mais recentes do branch git conectado
    (equivalente ao botão 'Update all' do portal). Prefere sempre o conteúdo
    do git em caso de conflito, já que este workspace só deve ser editado por
    aqui, nunca diretamente no portal."""
    status = status_git(workspace_id)
    if status["workspaceHead"] == status["remoteCommitHash"] and not status["changes"]:
        logger.info("Workspace já está atualizado, nada a fazer.")
        return status

    payload = {
        "workspaceHead": status["workspaceHead"],
        "remoteCommitHash": status["remoteCommitHash"],
        "conflictResolution": {
            "conflictResolutionType": "Workspace",
            "conflictResolutionPolicy": "PreferRemote",
        },
        "options": {"allowOverrideItems": allow_override_items},
    }
    url = f"{_FABRIC_API}/workspaces/{workspace_id}/git/updateFromGit"
    resp = httpx.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    if resp.status_code == 202:
        operation_id = resp.headers["x-ms-operation-id"]
        logger.info("Atualização em andamento (operação %s)...", operation_id)
        _aguardar_operacao(operation_id)
    logger.info("Workspace atualizado a partir do git (commit %s).", status["remoteCommitHash"][:8])
    return status
