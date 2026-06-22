"""Camada gold: lê o silver (Warehouse mp_silver) via cross-database query e
recarrega um modelo dimensional simplificado no Warehouse mp_gold, pronto para
o modelo semântico do Power BI.

Pré-requisito: mp_silver e mp_gold precisam estar no mesmo workspace Fabric —
cross-database query (nome de três partes, ex.: mp_silver.dbo.dim_entidade)
só funciona dentro do mesmo workspace.

Diferente do silver, aqui a transformação inteira roda em SQL (sem reler os
dados em Python), já que tanto a leitura quanto a escrita são no Warehouse.

Tipagem de fato_resposta_tipada: valor_resposta (texto) é convertido para
número/data/booleano conforme dim_campo.tipo_campo; campos que não se encaixam
em nenhum desses tipos (TEXTO, RADIO, COMBO_BOX, CPF, CHECKBOX) ficam só em
valor_texto — resolver RADIO/COMBO_BOX para a descrição da opção é trabalho do
modelo semântico (join com dim_campo_opcao), não desta camada.

Execute:
    uv run python -m src.modulos.cnmp.etl.load_gold
"""

import logging
import os

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
    campo_id_api       INT PRIMARY KEY,
    formulario_id_api  INT NOT NULL,
    secao_id_api       INT NOT NULL,
    label              VARCHAR(MAX) NOT NULL,
    tipo_campo         VARCHAR(50) NOT NULL,
    is_tabela_dinamica BIT NOT NULL DEFAULT 0
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


def criar_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for statement in DDL_GOLD.strip().split(";\n\n"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Schema gold criado/verificado")


def carregar_gold(engine: Engine) -> None:
    """Recarrega o gold inteiro a partir do silver via cross-database query."""
    silver_db = os.environ["FABRIC_WAREHOUSE_SILVER_NAME"]
    criar_schema(engine)

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
            INSERT INTO dim_campo (campo_id_api, formulario_id_api, secao_id_api, label, tipo_campo, is_tabela_dinamica)
            SELECT campo_id_api, formulario_id_api, secao_id_api, label, tipo_campo, is_tabela_dinamica
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

    logger.info("Carga gold concluída")


if __name__ == "__main__":
    carregar_gold(get_gold_engine())
