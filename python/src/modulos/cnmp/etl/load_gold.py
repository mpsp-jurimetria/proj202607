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


# Fabric Warehouse (esta edição) rejeita, no CREATE TABLE: PRIMARY KEY (erro
# 24584, mesmo como NONCLUSTERED ... NOT ENFORCED) e DEFAULT. Por isso as
# tabelas não declaram chave primária nem valor padrão.
DDL_GOLD = """
IF OBJECT_ID('dim_unidade', 'U') IS NULL
CREATE TABLE dim_unidade (
    entidade_id_api INT NOT NULL,
    ambiente_id_api INT NOT NULL,
    descricao       VARCHAR(300) NOT NULL
);

IF OBJECT_ID('dim_formulario', 'U') IS NULL
CREATE TABLE dim_formulario (
    formulario_id_api INT NOT NULL,
    ambiente_id_api   INT NOT NULL,
    nome              VARCHAR(300) NOT NULL,
    periodicidade     VARCHAR(50) NULL,
    versao            INT NULL
);

IF OBJECT_ID('dim_campo', 'U') IS NULL
CREATE TABLE dim_campo (
    campo_id_api        INT NOT NULL,
    formulario_id_api   INT NOT NULL,
    secao_id_api        INT NOT NULL,
    parent_campo_id_api INT NULL,
    label               VARCHAR(MAX) NOT NULL,
    indice              INT NULL,
    tipo_campo          VARCHAR(50) NOT NULL,
    is_tabela_dinamica  BIT NOT NULL
);

IF OBJECT_ID('dim_campo_opcao', 'U') IS NULL
CREATE TABLE dim_campo_opcao (
    campo_id_api INT NOT NULL,
    valor_api    VARCHAR(50) NOT NULL,
    descricao    VARCHAR(MAX) NOT NULL
);

IF OBJECT_ID('fato_visita', 'U') IS NULL
CREATE TABLE fato_visita (
    instancia_id_api  INT NOT NULL,
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
    linha            INT NOT NULL,
    valor_texto      VARCHAR(MAX) NULL,
    valor_numero     DECIMAL(18, 2) NULL,
    valor_data       DATE NULL,
    valor_booleano   BIT NULL
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


# Colunas por lote de UPDATE ao preencher a tabela larga. Uma query com
# muitos LEFT JOINs (um por coluna) pode passar do limite do otimizador do
# SQL Server ("query processor ran out of stack space", erro 8621) em
# formulários grandes (ex.: 900+ campos) — confirmado em produção: 350
# colunas numa query só funcionou, ~600+ não. Preencher em lotes menores
# evita isso, ao custo de várias passadas em vez de uma.
_COLUNAS_POR_LOTE = 40


def _campo_para_join(campo: dict) -> tuple[str, str, list[str]]:
    """Para um campo, devolve (nome_coluna, expressão de valor, joins extras)."""
    campo_id = campo["campo_id_api"]
    tipo_campo = campo["tipo_campo"]
    nome_coluna = _nome_coluna(campo_id, campo["label"])
    alias_resp = f"r{campo_id}"

    joins = [
        f"LEFT JOIN fato_resposta_tipada {alias_resp} "
        f"ON {alias_resp}.instancia_id_api = t.instancia_id_api "
        f"AND {alias_resp}.campo_id_api = {campo_id} AND {alias_resp}.linha = 1"
    ]

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

    return nome_coluna, valor_expr, joins


def _construir_pivot(
    formulario_id: int, campos: list[dict], colunas_por_lote: int = _COLUNAS_POR_LOTE
) -> tuple[str, str, list[str]]:
    """Monta o DDL, o INSERT (só colunas base) e os UPDATEs em lote da tabela
    larga de um formulário."""
    nome_tabela = f"fato_visita_{formulario_id}"

    colunas_ddl = [
        f"    {_nome_coluna(c['campo_id_api'], c['label'])} "
        f"{_TIPO_SQL_POR_CAMPO.get(c['tipo_campo'], 'VARCHAR(MAX)')} NULL"
        for c in campos
    ]

    ddl = (
        f"DROP TABLE IF EXISTS {nome_tabela};\n"
        f"CREATE TABLE {nome_tabela} (\n"
        "    instancia_id_api INT NOT NULL,\n"
        "    entidade_id_api INT NOT NULL,\n"
        "    ano INT NULL,\n"
        "    periodo INT NULL,\n"
        "    status_atual VARCHAR(100) NULL"
        + (",\n" + ",\n".join(colunas_ddl) if colunas_ddl else "")
        + "\n);"
    )

    insert_base = (
        f"INSERT INTO {nome_tabela} (instancia_id_api, entidade_id_api, ano, periodo, status_atual)\n"
        "SELECT instancia_id_api, entidade_id_api, ano, periodo, status_atual\n"
        f"FROM fato_visita\nWHERE formulario_id_api = {formulario_id};"
    )

    updates = []
    for inicio in range(0, len(campos), colunas_por_lote):
        lote = campos[inicio : inicio + colunas_por_lote]
        sets = []
        joins: list[str] = []
        for campo in lote:
            nome_coluna, valor_expr, joins_campo = _campo_para_join(campo)
            sets.append(f"    t.{nome_coluna} = {valor_expr}")
            joins.extend(joins_campo)

        update = (
            f"UPDATE t SET\n"
            + ",\n".join(sets)
            + f"\nFROM {nome_tabela} t\n"
            + "\n".join(joins)
            + ";"
        )
        updates.append(update)

    return ddl, insert_base, updates


def _recarregar_tabelas_pivotadas(engine: Engine) -> None:
    with engine.connect() as conn:
        formularios = [
            row[0]
            for row in conn.execute(text("SELECT formulario_id_api FROM dim_formulario")).all()
        ]

    # Uma transação por formulário, não uma só para todos — se um formulário
    # falhar (ex.: erro 8621 num form grande), os outros já recarregados não
    # são desfeitos numa nova tentativa.
    for formulario_id in formularios:
        with engine.begin() as conn:
            campos = _campos_pivotaveis(conn, formulario_id)
            ddl, insert_base, updates = _construir_pivot(formulario_id, campos)
            conn.execute(text(ddl))
            conn.execute(text(insert_base))
            for indice_lote, update in enumerate(updates, start=1):
                conn.execute(text(update))
                logger.info(
                    "fato_visita_%s: lote %d/%d de colunas preenchido",
                    formulario_id, indice_lote, len(updates),
                )
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
