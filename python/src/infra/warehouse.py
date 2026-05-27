"""Conexão com o Fabric Warehouse para leitura e escrita de tabelas estruturadas."""

import os
import struct
from itertools import chain, repeat
from typing import Any

import pyodbc
from azure.identity import AzureCliCredential, ClientSecretCredential
from sqlalchemy import Engine, create_engine, event, text


def _get_credential() -> AzureCliCredential | ClientSecretCredential:
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


def get_engine() -> Engine:
    host = os.getenv("FABRIC_WAREHOUSE_HOST")
    db = os.getenv("FABRIC_WAREHOUSE_NAME")

    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},1433;"
        f"DATABASE={db};"
        f"Encrypt=Yes;TrustServerCertificate=No"
    )

    credential = _get_credential()
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={connection_string}",
        echo=False,
    )

    @event.listens_for(engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams):  # noqa: ANN001
        cparams["attrs_before"] = {1256: _token_struct(credential)}

    return engine


def check_connection() -> bool:
    """Verifica se a conexão com o Warehouse está funcional."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
