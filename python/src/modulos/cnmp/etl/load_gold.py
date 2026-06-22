"""Camada gold: lê o silver (Warehouse mp_silver) via cross-database query e
recarrega um modelo dimensional + tabelas largas por formulário no Warehouse
mp_gold, prontas para o modelo semântico do Power BI.

Pré-requisito: mp_silver e mp_gold precisam estar no mesmo workspace Fabric —
cross-database query (nome de três partes, ex.: mp_silver.dbo.dim_entidade)
só funciona dentro do mesmo workspace.

Duas partes:
1. Tabelas base (dim_unidade, dim_formulario, dim_campo, dim_campo_opcao,
   fato_visita, fato_resposta_tipada) — cópia tipada do silver, em SQL puro,
   sem reler dados em Python. Útil para consultas ad hoc e para os campos de
   TABELA_DINAMICA, que não entram nas tabelas largas (linhas repetidas não
   cabem numa coluna fixa).
2. Uma tabela larga por formulário (`fato_visita_{formulario_id}`), uma coluna
   por campo escalar (exclui TABELA_DINAMICA e seus filhos, LABEL e
   CAMPO_ANEXO), com o valor já tipado e RADIO/COMBO_BOX resolvido para a
   descrição da opção — pronta para abrir no Power BI sem precisar conhecer
   idCampo. Construída dinamicamente em Python a partir de dim_campo, porque
   cada formulário tem um conjunto de campos diferente (92 a ~900).

Execute:
    uv run python -m src.modulos.cnmp.etl.load_gold
"""

import logging
import os
import re
import unicodedata

from sqlalchemy import Engine, text

from src.infra.warehouse import get_gold_engine

logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.modulos.cnmp.etl").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


DDL_GOLD = """
IF OBJECT_ID('dim_unidade', 'U') IS NULL
CREATE TABLE dim_unidade (
    entidade_id_api INT PRIMARY KEY,
    ambiente_id_api INT NOT NULL,
    descricao       VARCHAR(300) NOT NULL
);

IF OBJECT_ID('dim_formulario', 'U') IS NULL
CREATE TABLE dim_formulario (
    formulario_id_api INT PRIMARY KEY,
    ambiente_id_api   INT NOT NULL,
    nome              VARCHAR(300) NOT NULL,
    periodicidade     VARCHAR(50) NULL,
    versao            INT NULL
);

IF OBJECT_ID('dim_campo', 'U') IS NULL
CREATE TABLE dim_campo (
    campo_id_api        INT PRIMARY KEY,
    formulario_id_api   INT NOT NULL,
    secao_id_api        INT NOT NULL,
    parent_campo_id_api INT NULL,
    label               VARCHAR(MAX) NOT NULL,
    indice              INT NULL,
    tipo_campo          VARCHAR(50) NOT NULL,
    is_tabela_dinamica  BIT NOT NULL DEFAULT 0
);

IF OBJECT_ID('dim_campo_opcao', 'U') IS NULL
CREATE TABLE dim_campo_opcao (
    campo_id_api INT NOT NULL,
    valor_api    VARCHAR(50) NOT NULL,
    descricao    VARCHAR(MAX) NOT NULL,
    PRIMARY KEY (campo_id_api, valor_api)
);

IF OBJECT_ID('fato_visita', 'U') IS NULL
CREATE TABLE fato_visita (
    instancia_id_api  INT PRIMARY KEY,
    formulario_id_api INT NOT NULL,
    entidade_id_api   INT NOT NULL,
    ano               INT NULL,
    periodo           INT NULL,
    status_atual      VARCHAR(100) NULL
);

IF OBJECT_ID('fato_resposta_tipada', 'U') IS NULL
CREATE TABLE fato_resposta_tipada (
    instancia_id_api INT NOT NULL,
    campo_id_api     INT NOT NULL,
    linha            INT NOT NULL DEFAULT 1,
    valor_texto      VARCHAR(MAX) NULL,
    valor_numero     DECIMAL(18, 2) NULL,
    valor_data       DATE NULL,
    valor_booleano   BIT NULL,
    PRIMARY KEY (instancia_id_api, campo_id_api, linha)
);
"""

# Tipos de campo que não geram coluna nas tabelas largas: LABEL é texto
# estático do formulário (não é resposta) e CAMPO_ANEXO referencia um arquivo,
# não um valor escalar.
_TIPOS_SEM_COLUNA = {"LABEL", "CAMPO_ANEXO"}

_TIPO_SQL_POR_CAMPO = {
    "DATA": "DATE",
    "SOMENTE_NUMERO": "DECIMAL(18, 2)",
    "SIM_NAO": "BIT",
}


def _slug(label: str, max_len: int = 40) -> str:
    """Reduz o label do campo a um identificador SQL legível.

    Ex.: '13.11.2 Cocaína:' -> 'cocaina'. Não precisa ser único por si só —
    quem garante unicidade da coluna é o prefixo com campo_id_api.
    """
    texto = re.sub(r"^[\d.]+\s*", "", label)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto).strip("_").lower()
    return texto[:max_len].strip("_") or "campo"


def _nome_coluna(campo_id_api: int, label: str) -> str:
    return f"c{campo_id_api}_{_slug(label)}"


def criar_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for statement in DDL_GOLD.strip().split(";\n\n"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Schema gold (tabelas base) criado/verificado")


def _recarregar_tabelas_base(engine: Engine) -> None:
    silver_db = os.environ["FABRIC_WAREHOUSE_SILVER_NAME"]

    comandos = [
        ("dim_unidade", f"""
            DELETE FROM dim_unidade;
            INSERT INTO dim_unidade (entidade_id_api, ambiente_id_api, descricao)
            SELECT entidade_id_api, ambiente_id_api, descricao
            FROM {silver_db}.dbo.dim_entidade;
        """),
        ("dim_formulario", f"""
            DELETE FROM dim_formulario;
            INSERT INTO dim_formulario (formulario_id_api, ambiente_id_api, nome, periodicidade, versao)
            SELECT formulario_id_api, ambiente_id_api, nome, periodicidade, versao
            FROM {silver_db}.dbo.dim_formulario;
        """),
        ("dim_campo", f"""
            DELETE FROM dim_campo;
            INSERT INTO dim_campo
                (campo_id_api, formulario_id_api, secao_id_api, parent_campo_id_api, label, indice, tipo_campo, is_tabela_dinamica)
            SELECT campo_id_api, formulario_id_api, secao_id_api, parent_campo_id_api, label, indice, tipo_campo, is_tabela_dinamica
            FROM {silver_db}.dbo.dim_campo;
        """),
        ("dim_campo_opcao", f"""
            DELETE FROM dim_campo_opcao;
            INSERT INTO dim_campo_opcao (campo_id_api, valor_api, descricao)
            SELECT campo_id_api, valor_api, descricao
            FROM {silver_db}.dbo.dim_campo_opcao;
        """),
        ("fato_visita", f"""
            DELETE FROM fato_visita;
            INSERT INTO fato_visita (instancia_id_api, formulario_id_api, entidade_id_api, ano, periodo, status_atual)
            SELECT instancia_id_api, formulario_id_api, entidade_id_api, ano, periodo, status_atual
            FROM {silver_db}.dbo.fato_instancia;
        """),
        ("fato_resposta_tipada", f"""
            DELETE FROM fato_resposta_tipada;
            INSERT INTO fato_resposta_tipada
                (instancia_id_api, campo_id_api, linha, valor_texto, valor_numero, valor_data, valor_booleano)
            SELECT
                r.instancia_id_api,
                r.campo_id_api,
                r.linha,
                CASE WHEN c.tipo_campo IN ('SOMENTE_NUMERO', 'DATA', 'SIM_NAO') THEN NULL ELSE r.valor_resposta END,
                CASE WHEN c.tipo_campo = 'SOMENTE_NUMERO' THEN TRY_CAST(r.valor_resposta AS DECIMAL(18, 2)) END,
                CASE WHEN c.tipo_campo = 'DATA' THEN TRY_CONVERT(DATE, r.valor_resposta, 103) END,
                CASE
                    WHEN c.tipo_campo = 'SIM_NAO' AND r.valor_resposta IN ('true', 'Sim') THEN 1
                    WHEN c.tipo_campo = 'SIM_NAO' AND r.valor_resposta IN ('false', 'Não', 'Nao') THEN 0
                END
            FROM {silver_db}.dbo.fato_resposta r
            INNER JOIN {silver_db}.dbo.dim_campo c ON c.campo_id_api = r.campo_id_api;
        """),
    ]

    with engine.begin() as conn:
        for tabela, sql in comandos:
            for statement in sql.strip().split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
            logger.info("%s recarregada", tabela)


def _campos_pivotaveis(conn, formulario_id: int) -> list[dict]:
    """Campos escalares do formulário, na ordem do questionário.

    Exclui o container de TABELA_DINAMICA (is_tabela_dinamica=1), as colunas
    dele (parent_campo_id_api IS NOT NULL) e os tipos sem valor de resposta.
    """
    placeholders = ", ".join(f"'{tipo}'" for tipo in _TIPOS_SEM_COLUNA)
    linhas = conn.execute(
        text(f"""
            SELECT campo_id_api, label, tipo_campo
            FROM dim_campo
            WHERE formulario_id_api = :formulario_id
              AND is_tabela_dinamica = 0
              AND parent_campo_id_api IS NULL
              AND tipo_campo NOT IN ({placeholders})
            ORDER BY indice
        """),
        {"formulario_id": formulario_id},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def _construir_pivot(formulario_id: int, campos: list[dict]) -> tuple[str, str]:
    """Monta o DDL e o INSERT...SELECT da tabela larga de um formulário."""
    nome_tabela = f"fato_visita_{formulario_id}"

    colunas_ddl = []
    colunas_select = []
    joins = []

    for campo in campos:
        campo_id = campo["campo_id_api"]
        tipo_campo = campo["tipo_campo"]
        nome_coluna = _nome_coluna(campo_id, campo["label"])
        tipo_sql = _TIPO_SQL_POR_CAMPO.get(tipo_campo, "VARCHAR(MAX)")
        colunas_ddl.append(f"    {nome_coluna} {tipo_sql} NULL")

        alias_resp = f"r{campo_id}"
        joins.append(
            f"LEFT JOIN fato_resposta_tipada {alias_resp} "
            f"ON {alias_resp}.instancia_id_api = v.instancia_id_api "
            f"AND {alias_resp}.campo_id_api = {campo_id} AND {alias_resp}.linha = 1"
        )

        if tipo_campo in ("RADIO", "COMBO_BOX"):
            alias_opt = f"o{campo_id}"
            joins.append(
                f"LEFT JOIN dim_campo_opcao {alias_opt} "
                f"ON {alias_opt}.campo_id_api = {campo_id} "
                f"AND {alias_opt}.valor_api = {alias_resp}.valor_texto"
            )
            valor_expr = f"COALESCE({alias_opt}.descricao, {alias_resp}.valor_texto)"
        elif tipo_campo == "DATA":
            valor_expr = f"{alias_resp}.valor_data"
        elif tipo_campo == "SOMENTE_NUMERO":
            valor_expr = f"{alias_resp}.valor_numero"
        elif tipo_campo == "SIM_NAO":
            valor_expr = f"{alias_resp}.valor_booleano"
        else:
            valor_expr = f"{alias_resp}.valor_texto"

        colunas_select.append(f"    {valor_expr} AS {nome_coluna}")

    ddl = (
        f"DROP TABLE IF EXISTS {nome_tabela};\n"
        f"CREATE TABLE {nome_tabela} (\n"
        "    instancia_id_api INT PRIMARY KEY,\n"
        "    entidade_id_api INT NOT NULL,\n"
        "    ano INT NULL,\n"
        "    periodo INT NULL,\n"
        "    status_atual VARCHAR(100) NULL"
        + (",\n" + ",\n".join(colunas_ddl) if colunas_ddl else "")
        + "\n);"
    )

    nomes_colunas = ", ".join(_nome_coluna(c["campo_id_api"], c["label"]) for c in campos)
    insert = (
        f"INSERT INTO {nome_tabela} "
        f"(instancia_id_api, entidade_id_api, ano, periodo, status_atual"
        + (f", {nomes_colunas}" if campos else "")
        + ")\n"
        "SELECT v.instancia_id_api, v.entidade_id_api, v.ano, v.periodo, v.status_atual"
        + (",\n" + ",\n".join(colunas_select) if colunas_select else "")
        + "\nFROM fato_visita v\n"
        + "\n".join(joins)
        + f"\nWHERE v.formulario_id_api = {formulario_id};"
    )

    return ddl, insert


def _recarregar_tabelas_pivotadas(engine: Engine) -> None:
    with engine.begin() as conn:
        formularios = [
            row[0]
            for row in conn.execute(text("SELECT formulario_id_api FROM dim_formulario")).all()
        ]

        for formulario_id in formularios:
            campos = _campos_pivotaveis(conn, formulario_id)
            ddl, insert = _construir_pivot(formulario_id, campos)
            conn.execute(text(ddl))
            conn.execute(text(insert))
            logger.info(
                "fato_visita_%s recarregada (%d colunas de campo)", formulario_id, len(campos)
            )


def carregar_gold(engine: Engine) -> None:
    """Recarrega o gold inteiro: tabelas base a partir do silver, depois as
    tabelas largas por formulário a partir das tabelas base já recarregadas."""
    criar_schema(engine)
    _recarregar_tabelas_base(engine)
    _recarregar_tabelas_pivotadas(engine)
    logger.info("Carga gold concluída")


if __name__ == "__main__":
    carregar_gold(get_gold_engine())
