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
        # fast_executemany evita o erro "Cannot convert to text/ntext or
        # collate to ..._UTF8" do pyodbc em INSERTs grandes com VARCHAR(MAX) —
        # sem isso, o driver às vezes promove o bind de string para um tipo
        # legado (text/ntext) incompatível com a collation UTF-8 do Fabric.
        fast_executemany=True,
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


def _onelake_storage_options() -> dict[str, str]:
    return {
        "azure_storage_client_id": os.environ["CLIENT_ID"],
        "azure_storage_client_secret": os.environ["CLIENT_SECRET"],
        "azure_storage_tenant_id": os.environ["TENANT_ID"],
    }


def listar_tabelas_onelake(
    warehouse_id: str, schema: str = "dbo", workspace_id: str | None = None
) -> list[str]:
    """Lista as tabelas físicas de um Warehouse via OneLake (pasta Tables/<schema>).

    Alternativa à conexão SQL (pyodbc) quando não há rota de rede até a porta
    do SQL endpoint, mas há para HTTPS — caso de ambientes de desenvolvimento
    em sandbox. warehouse_id é o id do *item* no Fabric (guid), não o host de
    conexão SQL; para descobrir, ver .env.example.
    """
    from infra.lakehouse import _get_filesystem_client

    workspace_id = workspace_id or os.environ["FABRIC_WORKSPACE_ID"]
    fs = _get_filesystem_client(workspace_id)
    paths = fs.get_paths(path=f"{warehouse_id}/Tables/{schema}", recursive=False)
    return sorted(p.name.rsplit("/", 1)[-1] for p in paths if p.is_directory)


def ler_tabela_onelake(
    tabela: str,
    warehouse_id: str,
    schema: str = "dbo",
    workspace_id: str | None = None,
    colunas: list[str] | None = None,
) -> Any:
    """Lê uma tabela do Warehouse direto do Delta no OneLake (retorna DataFrame pandas).

    Mesma motivação de listar_tabelas_onelake: contorna a falta de rota até o
    SQL endpoint. Requer os pacotes deltalake e pyarrow (uv add deltalake pyarrow).

    Limitação conhecida: tabelas gravadas com os recursos de leitor Delta
    columnMapping ou deletionVectors ainda não são suportadas pelo pacote
    deltalake (erro DeltaProtocolError) — nesse caso não há solução por aqui
    até o pacote adicionar suporte; usar a conexão SQL (get_gold_engine /
    get_silver_engine) de um ambiente com rota de rede até o SQL endpoint.
    Ver docs/aprendizados-powerbi-fabric.md para mais contexto.
    """
    from deltalake import DeltaTable

    workspace_id = workspace_id or os.environ["FABRIC_WORKSPACE_ID"]
    path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{warehouse_id}/Tables/{schema}/{tabela}"
    dt = DeltaTable(path, storage_options=_onelake_storage_options())
    return dt.to_pandas(columns=colunas)


def ler_tabela_gold_onelake(tabela: str, colunas: list[str] | None = None) -> Any:
    """Atalho para ler_tabela_onelake usando FABRIC_WAREHOUSE_GOLD_ID do .env."""
    return ler_tabela_onelake(tabela, warehouse_id=os.environ["FABRIC_WAREHOUSE_GOLD_ID"], colunas=colunas)


def ler_tabela_silver_onelake(tabela: str, colunas: list[str] | None = None) -> Any:
    """Atalho para ler_tabela_onelake usando FABRIC_WAREHOUSE_SILVER_ID do .env."""
    return ler_tabela_onelake(tabela, warehouse_id=os.environ["FABRIC_WAREHOUSE_SILVER_ID"], colunas=colunas)
