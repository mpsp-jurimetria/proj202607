"""Conexão com o Fabric Warehouse para leitura e escrita de tabelas estruturadas."""

import os
import struct
from itertools import chain, repeat
from typing import Any

from azure.identity import AzureCliCredential, ClientSecretCredential
from sqlalchemy import Engine, create_engine, event, text


class _NotebookCredential:
    """Credencial baseada na identidade nativa de um notebook Fabric.

    Usa notebookutils (disponível apenas dentro do runtime do Fabric) em vez de
    Service Principal — não precisa de CLIENT_ID/CLIENT_SECRET.
    """

    def get_token(self, *scopes: str, **kwargs: Any) -> Any:
        from notebookutils import credentials as nb_credentials  # type: ignore[import-not-found]

        token = nb_credentials.getToken("https://database.windows.net/")
        return type("Token", (), {"token": token})()


def _get_credential() -> "_NotebookCredential | AzureCliCredential | ClientSecretCredential":
    """Resolve a credencial: identidade nativa do notebook Fabric quando disponível
    (notebookutils só existe dentro do runtime do Fabric), senão Service
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


def _token_struct(credential: Any) -> bytes:
    token = credential.get_token("https://database.windows.net//.default")
    token_bytes = token.token.encode("UTF-8")
    encoded = bytes(chain.from_iterable(zip(token_bytes, repeat(0))))
    return struct.pack("<i", len(encoded)) + encoded


def get_engine(host: str, database: str, credential: Any = None) -> Engine:
    """Cria um engine SQLAlchemy para um Warehouse Fabric específico.

    Args:
        host: host do Warehouse (ex.: "xxxx.datawarehouse.fabric.microsoft.com").
        database: nome do Warehouse (ex.: "mp_silver").
        credential: credencial com método get_token(); por padrão usa Service
            Principal/AzureCliCredential (_get_credential). Dentro de um notebook
            Fabric, passe _NotebookCredential() para usar a identidade nativa.
    """
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},1433;"
        f"DATABASE={database};"
        f"Encrypt=Yes;TrustServerCertificate=No"
    )

    credential = credential or _get_credential()
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={connection_string}",
        echo=False,
    )

    @event.listens_for(engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams):  # noqa: ANN001
        cparams["attrs_before"] = {1256: _token_struct(credential)}

    return engine


def get_silver_engine() -> Engine:
    """Engine para o Warehouse da camada silver (FABRIC_WAREHOUSE_SILVER_HOST/NAME)."""
    return get_engine(
        host=os.environ["FABRIC_WAREHOUSE_SILVER_HOST"],
        database=os.environ["FABRIC_WAREHOUSE_SILVER_NAME"],
    )


def get_gold_engine() -> Engine:
    """Engine para o Warehouse da camada gold (FABRIC_WAREHOUSE_GOLD_HOST/NAME)."""
    return get_engine(
        host=os.environ["FABRIC_WAREHOUSE_GOLD_HOST"],
        database=os.environ["FABRIC_WAREHOUSE_GOLD_NAME"],
    )


def check_connection(engine: Engine) -> bool:
    """Verifica se a conexão com o Warehouse está funcional."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
