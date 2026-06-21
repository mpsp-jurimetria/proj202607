"""Leitura da camada bronze (JSON brutos no Lakehouse mp_bronze) gravados por
extract_bronze.py. Os caminhos aqui espelham exatamente os usados na escrita.
"""

import json

from src.infra.lakehouse import download_bytes

_PREFIXO = "cnmp/json"


def _ler(caminho: str) -> object:
    return json.loads(download_bytes(f"{_PREFIXO}/{caminho}"))


def ler_ambientes() -> list[dict]:
    return _ler("ambientes.json")


def ler_formularios(ambiente_id: int) -> list[dict]:
    return _ler(f"formularios/{ambiente_id}.json")


def ler_detalhe_formulario(formulario_id: int) -> dict:
    return _ler(f"formularios_detalhe/{formulario_id}.json")


def ler_entidades(formulario_id: int) -> list[dict]:
    return _ler(f"entidades/{formulario_id}.json")


def ler_instancias(formulario_id: int, entidade_id: int) -> list[dict]:
    return _ler(f"instancias/{formulario_id}/{entidade_id}.json")


def ler_detalhe_instancia(formulario_id: int, entidade_id: int, instancia_id: int) -> dict:
    return _ler(f"instancias_detalhe/{formulario_id}/{entidade_id}/{instancia_id}.json")
