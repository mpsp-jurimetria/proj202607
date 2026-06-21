"""Camada bronze: extrai dados brutos da API do CNMP (Resolução 277) e grava
como JSON no Lakehouse mp_bronze, sem nenhuma transformação.

Hierarquia de caminhos em Files/ do Lakehouse:
    cnmp/json/ambientes.json
    cnmp/json/formularios/{ambiente_id}.json
    cnmp/json/formularios_detalhe/{formulario_id}.json
    cnmp/json/entidades/{formulario_id}.json
    cnmp/json/instancias/{formulario_id}/{entidade_id}.json
    cnmp/json/instancias_detalhe/{formulario_id}/{entidade_id}/{instancia_id}.json

Execute:
    uv run python -m src.modulos.cnmp.etl.extract_bronze
"""

import json
import logging

from src.infra.lakehouse import upload_bytes
from src.modulos.cnmp.client import CnmpClient

logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.modulos.cnmp.etl").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

_PREFIXO = "cnmp/json"


def _gravar(caminho: str, dados: object) -> None:
    corpo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
    upload_bytes(corpo, f"{_PREFIXO}/{caminho}")


def extrair_ambientes(client: CnmpClient) -> list[dict]:
    ambientes = client.ambientes()
    _gravar("ambientes.json", ambientes)
    logger.info("ambientes: %d", len(ambientes))
    return ambientes


def extrair_formularios(client: CnmpClient, ambiente_id: int) -> list[dict]:
    formularios = client.formularios(id_ambiente=ambiente_id)
    _gravar(f"formularios/{ambiente_id}.json", formularios)
    logger.info("ambiente %s: %d formulários", ambiente_id, len(formularios))
    return formularios


def extrair_detalhe_formulario(client: CnmpClient, formulario_id: int) -> dict:
    detalhe = client.detalhe_formulario(formulario_id)
    _gravar(f"formularios_detalhe/{formulario_id}.json", detalhe)
    return detalhe


def extrair_entidades(client: CnmpClient, formulario_id: int) -> list[dict]:
    entidades = client.entidades(id_formulario=formulario_id)
    _gravar(f"entidades/{formulario_id}.json", entidades)
    logger.info("formulário %s: %d entidades", formulario_id, len(entidades))
    return entidades


def extrair_instancias(client: CnmpClient, formulario_id: int, entidade_id: int) -> list[dict]:
    instancias = client.instancias(id_formulario=formulario_id, id_entidade=entidade_id)
    _gravar(f"instancias/{formulario_id}/{entidade_id}.json", instancias)
    return instancias


def extrair_detalhe_instancia(client: CnmpClient, formulario_id: int, entidade_id: int, instancia_id: int) -> dict:
    detalhe = client.detalhe_instancia(instancia_id)
    _gravar(f"instancias_detalhe/{formulario_id}/{entidade_id}/{instancia_id}.json", detalhe)
    return detalhe


def executar(ambientes_ids: list[int]) -> None:
    """Roda a extração bronze completa para os ambientes informados."""
    with CnmpClient() as client:
        extrair_ambientes(client)

        for ambiente_id in ambientes_ids:
            formularios = extrair_formularios(client, ambiente_id)

            for formulario in formularios:
                formulario_id = formulario["id"]
                extrair_detalhe_formulario(client, formulario_id)
                entidades = extrair_entidades(client, formulario_id)

                for entidade in entidades:
                    entidade_id = entidade["id"]
                    instancias = extrair_instancias(client, formulario_id, entidade_id)

                    for instancia in instancias:
                        extrair_detalhe_instancia(
                            client, formulario_id, entidade_id, instancia["id"]
                        )

    logger.info("Extração bronze concluída para ambientes %s", ambientes_ids)


if __name__ == "__main__":
    executar(ambientes_ids=[282, 462])
