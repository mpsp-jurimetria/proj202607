"""Camada silver: lê o bronze (Lakehouse mp_bronze), aplica as transformações
puras de transform_silver.py e recarrega as tabelas normalizadas no Warehouse
mp_silver.

Estratégia de carga: "delete + insert" completo por tabela a cada execução
(não incremental). Simples e correto para o volume atual; revisar se o volume
crescer a ponto de tornar a carga completa lenta.

Execute:
    uv run python -m src.modulos.cnmp.etl.load_silver
"""

import logging

from sqlalchemy import Engine, text

from src.infra.warehouse import get_silver_engine
from src.modulos.cnmp.etl import read_bronze
from src.modulos.cnmp.etl.transform_silver import (
    linha_dim_formulario,
    linha_fato_instancia,
    linhas_dim_ambiente,
    linhas_dim_entidade,
    linhas_dim_formulario_tipo_entidade,
    linhas_fato_resposta,
    linhas_secao_campo,
)

logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.modulos.cnmp.etl").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


DDL_SILVER = """
IF OBJECT_ID('dim_ambiente', 'U') IS NULL
CREATE TABLE dim_ambiente (
    ambiente_id_api INT PRIMARY KEY,
    descricao       VARCHAR(200) NOT NULL
);

IF OBJECT_ID('dim_formulario', 'U') IS NULL
CREATE TABLE dim_formulario (
    formulario_id_api INT PRIMARY KEY,
    ambiente_id_api   INT NOT NULL,
    nome              VARCHAR(300) NOT NULL,
    periodicidade     VARCHAR(50) NULL,
    versao            INT NULL,
    ano_inicio        INT NULL,
    periodo_inicio    INT NULL,
    ano_termino       INT NULL,
    periodo_termino   INT NULL
);

IF OBJECT_ID('dim_formulario_tipo_entidade', 'U') IS NULL
CREATE TABLE dim_formulario_tipo_entidade (
    formulario_id_api    INT NOT NULL,
    tipo_entidade_id_api INT NOT NULL,
    descricao            VARCHAR(200) NOT NULL,
    PRIMARY KEY (formulario_id_api, tipo_entidade_id_api)
);

IF OBJECT_ID('dim_secao', 'U') IS NULL
CREATE TABLE dim_secao (
    secao_id_api      INT PRIMARY KEY,
    formulario_id_api INT NOT NULL,
    indice            INT NULL,
    nome              VARCHAR(300) NOT NULL
);

IF OBJECT_ID('dim_campo', 'U') IS NULL
CREATE TABLE dim_campo (
    campo_id_api        INT PRIMARY KEY,
    secao_id_api        INT NOT NULL,
    formulario_id_api   INT NOT NULL,
    parent_campo_id_api INT NULL,
    label               VARCHAR(MAX) NOT NULL,
    indice              INT NULL,
    tabulacao           INT NULL,
    obrigatorio         BIT NOT NULL DEFAULT 0,
    tamanho_maximo      INT NULL,
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

IF OBJECT_ID('dim_campo_dependencia', 'U') IS NULL
CREATE TABLE dim_campo_dependencia (
    campo_id_api            INT NOT NULL,
    campo_id_condicao_api    INT NOT NULL,
    valor_resposta_esperado VARCHAR(MAX) NOT NULL,
    PRIMARY KEY (campo_id_api, campo_id_condicao_api)
);

IF OBJECT_ID('dim_entidade', 'U') IS NULL
CREATE TABLE dim_entidade (
    entidade_id_api INT PRIMARY KEY,
    ambiente_id_api INT NOT NULL,
    descricao       VARCHAR(300) NOT NULL
);

IF OBJECT_ID('fato_instancia', 'U') IS NULL
CREATE TABLE fato_instancia (
    instancia_id_api  INT PRIMARY KEY,
    formulario_id_api INT NOT NULL,
    entidade_id_api   INT NOT NULL,
    ano               INT NULL,
    periodo           INT NULL,
    status_atual      VARCHAR(100) NULL,
    data_carga        DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

IF OBJECT_ID('fato_resposta', 'U') IS NULL
CREATE TABLE fato_resposta (
    instancia_id_api INT NOT NULL,
    campo_id_api     INT NOT NULL,
    linha            INT NOT NULL DEFAULT 1,
    valor_resposta   VARCHAR(MAX) NULL,
    PRIMARY KEY (instancia_id_api, campo_id_api, linha)
);
"""


def criar_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for statement in DDL_SILVER.strip().split(";\n\n"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Schema silver criado/verificado")


def recarregar_tabela(engine: Engine, tabela: str, colunas: list[str], linhas: list[dict]) -> None:
    """Substitui todo o conteúdo de uma tabela silver pelas linhas informadas."""
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {tabela}"))
        if linhas:
            placeholders = ", ".join(f":{coluna}" for coluna in colunas)
            colunas_sql = ", ".join(colunas)
            conn.execute(
                text(f"INSERT INTO {tabela} ({colunas_sql}) VALUES ({placeholders})"),
                linhas,
            )
    logger.info("%s: %d linhas recarregadas", tabela, len(linhas))


def carregar_silver(engine: Engine, ambientes_ids: list[int]) -> None:
    criar_schema(engine)

    ambientes_brutos = read_bronze.ler_ambientes()
    ambientes_brutos = [a for a in ambientes_brutos if a["id"] in ambientes_ids]
    recarregar_tabela(
        engine, "dim_ambiente", ["ambiente_id_api", "descricao"], linhas_dim_ambiente(ambientes_brutos)
    )

    formularios_rows: list[dict] = []
    tipo_entidade_rows: list[dict] = []
    secao_rows: list[dict] = []
    campo_rows: list[dict] = []
    opcao_rows: list[dict] = []
    dependencia_rows: list[dict] = []
    entidade_rows: list[dict] = []
    instancia_rows: list[dict] = []
    resposta_rows: list[dict] = []

    for ambiente_id in ambientes_ids:
        formularios = read_bronze.ler_formularios(ambiente_id)

        for formulario in formularios:
            formulario_id = formulario["id"]
            detalhe = read_bronze.ler_detalhe_formulario(formulario_id)

            formularios_rows.append(linha_dim_formulario(detalhe, ambiente_id))
            tipo_entidade_rows.extend(linhas_dim_formulario_tipo_entidade(detalhe))

            secoes, campos, opcoes, dependencias = linhas_secao_campo(detalhe)
            secao_rows.extend(secoes)
            campo_rows.extend(campos)
            opcao_rows.extend(opcoes)
            dependencia_rows.extend(dependencias)

            entidades = read_bronze.ler_entidades(formulario_id)
            entidade_rows.extend(linhas_dim_entidade(entidades, ambiente_id))

            for entidade in entidades:
                entidade_id = entidade["id"]
                instancias = read_bronze.ler_instancias(formulario_id, entidade_id)

                for instancia in instancias:
                    instancia_rows.append(
                        linha_fato_instancia(instancia, formulario_id, entidade_id)
                    )
                    detalhe_instancia = read_bronze.ler_detalhe_instancia(
                        formulario_id, entidade_id, instancia["id"]
                    )
                    resposta_rows.extend(
                        linhas_fato_resposta(instancia["id"], detalhe_instancia.get("conteudo", []))
                    )

    recarregar_tabela(
        engine,
        "dim_formulario",
        [
            "formulario_id_api", "ambiente_id_api", "nome", "periodicidade",
            "versao", "ano_inicio", "periodo_inicio", "ano_termino", "periodo_termino",
        ],
        formularios_rows,
    )
    recarregar_tabela(
        engine,
        "dim_formulario_tipo_entidade",
        ["formulario_id_api", "tipo_entidade_id_api", "descricao"],
        tipo_entidade_rows,
    )
    recarregar_tabela(
        engine, "dim_secao", ["secao_id_api", "formulario_id_api", "indice", "nome"], secao_rows
    )
    recarregar_tabela(
        engine,
        "dim_campo",
        [
            "campo_id_api", "secao_id_api", "formulario_id_api", "parent_campo_id_api",
            "label", "indice", "tabulacao", "obrigatorio", "tamanho_maximo",
            "tipo_campo", "is_tabela_dinamica",
        ],
        campo_rows,
    )
    recarregar_tabela(
        engine, "dim_campo_opcao", ["campo_id_api", "valor_api", "descricao"], opcao_rows
    )
    recarregar_tabela(
        engine,
        "dim_campo_dependencia",
        ["campo_id_api", "campo_id_condicao_api", "valor_resposta_esperado"],
        dependencia_rows,
    )
    recarregar_tabela(
        engine, "dim_entidade", ["entidade_id_api", "ambiente_id_api", "descricao"], entidade_rows
    )
    recarregar_tabela(
        engine,
        "fato_instancia",
        ["instancia_id_api", "formulario_id_api", "entidade_id_api", "ano", "periodo", "status_atual"],
        instancia_rows,
    )
    recarregar_tabela(
        engine,
        "fato_resposta",
        ["instancia_id_api", "campo_id_api", "linha", "valor_resposta"],
        resposta_rows,
    )

    logger.info("Carga silver concluída para ambientes %s", ambientes_ids)


if __name__ == "__main__":
    carregar_silver(get_silver_engine(), ambientes_ids=[282, 462])
