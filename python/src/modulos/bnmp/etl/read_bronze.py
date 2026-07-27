"""Leitura da camada bronze (JSON brutos no Lakehouse mp_bronze) gravados por
extract_bronze.py. Os caminhos aqui espelham exatamente os usados na escrita.
"""

import json
from collections.abc import Iterator

from src.infra.lakehouse import download_bytes, listar_arquivos

_PREFIXO = "bnmp/json"


def _ler(caminho: str) -> object:
    return json.loads(download_bytes(f"{_PREFIXO}/{caminho}"))


def ler_dominios() -> dict:
    return _ler("dominios.json")


def ler_status_pessoas() -> list[dict]:
    return _ler("status_pessoas.json")


def ler_contexto_sessao() -> dict:
    return _ler("contexto_sessao.json")


def ler_manifesto(recurso: str, consulta: str) -> dict:
    return _ler(f"{recurso}/{consulta}/_manifesto.json")


def listar_paginas(recurso: str, consulta: str) -> list[int]:
    paginas: list[int] = []
    for caminho in listar_arquivos(f"{_PREFIXO}/{recurso}/{consulta}/"):
        nome = caminho.rsplit("/", 1)[-1]
        if nome.startswith("pagina_") and nome.endswith(".json"):
            paginas.append(int(nome[len("pagina_") : -len(".json")]))
    return sorted(paginas)


def ler_pagina(recurso: str, consulta: str, pagina: int) -> dict:
    return _ler(f"{recurso}/{consulta}/pagina_{pagina:06d}.json")


def iterar_paginas(recurso: str, consulta: str) -> Iterator[dict]:
    """Gera os envelopes de página em ordem, sem carregar tudo em memória."""
    for pagina in listar_paginas(recurso, consulta):
        yield ler_pagina(recurso, consulta, pagina)
