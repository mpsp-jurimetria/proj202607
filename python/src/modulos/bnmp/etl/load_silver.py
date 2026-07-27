"""Camada silver do BNMP: lê o bronze (Lakehouse mp_bronze), aplica as
transformações puras de transform_silver.py e recarrega as tabelas no
Warehouse mp_silver.

Estratégia de carga:
- bnmp_dominio: delete + insert em lote (poucos milhares de linhas).
- bnmp_pessoa_carga: streaming página a página do bronze para partes CSV no
  Lakehouse (staging) + COPY INTO com curinga — o volume (potencialmente
  milhões de linhas) não cabe em memória nem em INSERT via pyodbc.
- bnmp_pessoa: CTAS deduplicando por pessoa_id_api (a paginação por offset
  sobre dados vivos gera duplicatas entre páginas).

Execute:
    uv run python -m src.modulos.bnmp.etl.load_silver
"""

import io
import logging
import os
from collections.abc import Iterator

from sqlalchemy import Engine, text

from src.infra.lakehouse import excluir_diretorio, upload_bytes
from src.infra.warehouse import get_silver_engine
from src.modulos.bnmp.etl import read_bronze
from src.modulos.bnmp.etl.transform_silver import (
    COLUNAS_BNMP_DOMINIO,
    COLUNAS_BNMP_PESSOA,
    linhas_bnmp_dominio,
    linhas_bnmp_pessoa,
)
from src.modulos.cnmp.etl.load_silver import csv_valor, recarregar_tabela

logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.modulos.bnmp.etl").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

_LINHAS_POR_PARTE = 200_000

# Fabric Warehouse (esta edição) rejeita PRIMARY KEY e DEFAULT no CREATE TABLE
# — mesma restrição documentada no módulo cnmp.
DDL_SILVER = """
IF OBJECT_ID('bnmp_dominio', 'U') IS NULL
CREATE TABLE bnmp_dominio (
    dominio      VARCHAR(100) NOT NULL,
    item_id      INT NULL,
    descricao    VARCHAR(500) NULL,
    ativo        BIT NULL,
    extras_json  VARCHAR(MAX) NULL,
    coletado_em  VARCHAR(30) NULL
);

IF OBJECT_ID('bnmp_pessoa_carga', 'U') IS NULL
CREATE TABLE bnmp_pessoa_carga (
    pessoa_id_api                     INT NOT NULL,
    consulta                          VARCHAR(100) NOT NULL,
    pagina                            INT NULL,
    coletado_em                       VARCHAR(30) NULL,
    ativo                             BIT NULL,
    numero_individuo                  VARCHAR(30) NULL,
    numero_cpf                        VARCHAR(20) NULL,
    status_pessoa_id                  INT NULL,
    status_pessoa_descricao           VARCHAR(200) NULL,
    uf_custodia_sigla                 VARCHAR(5) NULL,
    id_estabelecimento                INT NULL,
    pessoa_tem_peca                   BIT NULL,
    possui_dependentes                BIT NULL,
    unificada                         BIT NULL,
    dados_gerais_id                   INT NULL,
    nome                              VARCHAR(300) NULL,
    nome_social                       VARCHAR(300) NULL,
    alcunha                           VARCHAR(300) NULL,
    nome_pai                          VARCHAR(300) NULL,
    nome_mae                          VARCHAR(300) NULL,
    sexo_id                           INT NULL,
    sexo_descricao                    VARCHAR(50) NULL,
    data_nascimento                   DATE NULL,
    estado_civil_id                   INT NULL,
    estado_civil_descricao            VARCHAR(100) NULL,
    cor_raca_id                       INT NULL,
    cor_raca_descricao                VARCHAR(100) NULL,
    escolaridade_id                   INT NULL,
    escolaridade_descricao            VARCHAR(150) NULL,
    identificacao_biometria_id        INT NULL,
    identificacao_biometria_descricao VARCHAR(150) NULL,
    profissao                         VARCHAR(200) NULL,
    gravidez                          BIT NULL,
    lactante                          BIT NULL,
    deficiente_fisico                 BIT NULL,
    dependente_quimico                BIT NULL,
    possui_doenca_grave               BIT NULL,
    naturalidade_municipio_nome       VARCHAR(200) NULL,
    naturalidade_uf_sigla             VARCHAR(5) NULL,
    pais_nascimento_id                INT NULL,
    id_tribunal                       INT NULL,
    orgao_judiciario_id               INT NULL,
    orgao_judiciario_nome             VARCHAR(300) NULL,
    orgao_judiciario_ativo            BIT NULL,
    orgao_judiciario_externo          BIT NULL,
    orgao_judiciario_tipo_id          INT NULL,
    orgao_judiciario_pai_nome         VARCHAR(300) NULL,
    municipio_id                      INT NULL,
    municipio_nome                    VARCHAR(200) NULL,
    municipio_cod_ibge                INT NULL,
    uf_id                             INT NULL,
    uf_sigla                          VARCHAR(5) NULL,
    uf_nome                           VARCHAR(100) NULL,
    tribunal_id                       INT NULL,
    tribunal_sigla                    VARCHAR(20) NULL,
    tribunal_nome                     VARCHAR(300) NULL
);
"""


def criar_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for statement in DDL_SILVER.strip().split(";\n\n"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Schema silver do BNMP criado/verificado")


def gravar_partes_csv(
    linhas: Iterator[dict], colunas: list[str], prefixo_staging: str
) -> int:
    """Consome o iterador de linhas gravando partes CSV no Lakehouse.

    Gera bnmp/staging/<tabela>/parte_000.csv, parte_001.csv... com até
    _LINHAS_POR_PARTE linhas cada. Devolve o total de linhas gravadas.
    """
    excluir_diretorio(prefixo_staging)
    total = 0
    parte = 0
    buffer = io.StringIO()
    linhas_na_parte = 0

    def _descarregar() -> None:
        nonlocal parte, linhas_na_parte
        if linhas_na_parte:
            upload_bytes(
                buffer.getvalue().encode("utf-8"), f"{prefixo_staging}/parte_{parte:03d}.csv"
            )
            logger.info(
                "%s: parte %03d gravada (%d linhas)", prefixo_staging, parte, linhas_na_parte
            )
            parte += 1
            linhas_na_parte = 0
            buffer.seek(0)
            buffer.truncate(0)

    for linha in linhas:
        buffer.write(",".join(csv_valor(linha[coluna]) for coluna in colunas))
        buffer.write("\n")
        total += 1
        linhas_na_parte += 1
        if linhas_na_parte >= _LINHAS_POR_PARTE:
            _descarregar()
    _descarregar()
    return total


def recarregar_tabela_copy_into_partes(
    engine: Engine, tabela: str, colunas: list[str], prefixo_staging: str
) -> None:
    """Substitui o conteúdo da tabela via COPY INTO lendo todas as partes CSV
    do staging (curinga *.csv), do lado do servidor."""
    workspace_id = os.environ["FABRIC_WORKSPACE_ID"]
    lakehouse_id = os.environ["FABRIC_LAKEHOUSE_ID"]
    url_staging = (
        f"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}"
        f"/Files/{prefixo_staging}/*.csv"
    )
    colunas_sql = ", ".join(colunas)

    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {tabela}"))
        conn.execute(
            text(
                f"""
                COPY INTO {tabela} ({colunas_sql})
                FROM '{url_staging}'
                WITH (
                    FILE_TYPE = 'CSV',
                    FIELDQUOTE = '"',
                    FIELDTERMINATOR = ',',
                    ROWTERMINATOR = '0x0A',
                    FIRSTROW = 1
                )
                """
            )
        )
    logger.info("%s: recarregada via COPY INTO de %s", tabela, prefixo_staging)


def deduplicar_pessoas(engine: Engine) -> None:
    """Materializa bnmp_pessoa a partir de bnmp_pessoa_carga, mantendo a
    ocorrência mais recente de cada pessoa_id_api."""
    colunas_sql = ", ".join(COLUNAS_BNMP_PESSOA)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bnmp_pessoa"))
        conn.execute(
            text(
                f"""
                CREATE TABLE bnmp_pessoa AS
                SELECT {colunas_sql}
                FROM (
                    SELECT c.*, ROW_NUMBER() OVER (
                        PARTITION BY pessoa_id_api
                        ORDER BY coletado_em DESC, pagina
                    ) AS rn
                    FROM bnmp_pessoa_carga c
                ) t
                WHERE rn = 1
                """
            )
        )
    logger.info("bnmp_pessoa materializada (deduplicada por pessoa_id_api)")


def _iterar_linhas_pessoas(consultas: list[str]) -> Iterator[dict]:
    for consulta in consultas:
        for envelope in read_bronze.iterar_paginas("pessoas", consulta):
            yield from linhas_bnmp_pessoa(
                envelope["resposta"].get("content", []),
                envelope["consulta"],
                envelope["pagina"],
                envelope["coletado_em"],
            )


def carregar_silver(engine: Engine, consultas_pessoas: list[str]) -> None:
    criar_schema(engine)

    dominios = read_bronze.ler_dominios()
    recarregar_tabela(
        engine, "bnmp_dominio", COLUNAS_BNMP_DOMINIO, linhas_bnmp_dominio(dominios)
    )

    total = gravar_partes_csv(
        _iterar_linhas_pessoas(consultas_pessoas),
        COLUNAS_BNMP_PESSOA,
        "bnmp/staging/bnmp_pessoa",
    )
    logger.info("bnmp_pessoa_carga: %d linhas em staging", total)
    if total:
        recarregar_tabela_copy_into_partes(
            engine, "bnmp_pessoa_carga", COLUNAS_BNMP_PESSOA, "bnmp/staging/bnmp_pessoa"
        )
    else:
        logger.warning("Nenhuma linha de pessoa no bronze — bnmp_pessoa_carga não foi alterada")
    deduplicar_pessoas(engine)

    logger.info("Carga silver do BNMP concluída — consultas %s", consultas_pessoas)


if __name__ == "__main__":
    carregar_silver(get_silver_engine(), consultas_pessoas=["pessoas_uf-26_ativo-1"])
