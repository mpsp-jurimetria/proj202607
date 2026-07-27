"""Camada bronze: extrai dados brutos da API do BNMP 2.0 e grava como JSON no
Lakehouse mp_bronze, sem nenhuma transformação.

Hierarquia de caminhos em Files/ do Lakehouse:
    bnmp/json/dominios.json
    bnmp/json/status_pessoas.json
    bnmp/json/contexto_sessao.json
    bnmp/json/{recurso}/{consulta}/_manifesto.json
    bnmp/json/{recurso}/{consulta}/pagina_000000.json

Cada arquivo de página é um envelope {"consulta", "pagina", "coletado_em",
"resposta"} com a resposta Spring completa (content/totalElements/...) — o
totalElements pode derivar entre páginas (dados mudam durante a coleta); a
deduplicação é feita na carga silver.

Consultas interrompidas são retomáveis: reexecutar pula as páginas que já
existem no Lakehouse.

Execute:
    uv run python -m src.modulos.bnmp.etl.extract_bronze
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone

from src.infra.lakehouse import listar_arquivos, upload_bytes
from src.modulos.bnmp.client import BnmpClient
from src.modulos.bnmp.filtros import filtro_pessoas

logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.modulos.bnmp.etl").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

_PREFIXO = "bnmp/json"

# Tamanho de página padrão; ajustar após a sondagem de capacidade da API
# (scripts/explorar_api_bnmp.py) se ela aceitar páginas maiores.
_TAMANHO_PAGINA = 200

# A cada quantas páginas o manifesto é reescrito durante a coleta.
_PAGINAS_POR_MANIFESTO = 20


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _gravar(caminho: str, dados: object, indentado: bool = True) -> None:
    if indentado:
        corpo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
    else:
        corpo = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    upload_bytes(corpo, f"{_PREFIXO}/{caminho}")


def extrair_dominios(client: BnmpClient) -> dict:
    dominios = client.dominios()
    _gravar("dominios.json", dominios)
    logger.info("dominios: %d chaves", len(dominios))
    return dominios


def extrair_status_pessoas(client: BnmpClient) -> list[dict]:
    status = client.status_pessoas()
    _gravar("status_pessoas.json", status)
    logger.info("status_pessoas: %d itens", len(status))
    return status


def extrair_contexto_sessao(client: BnmpClient) -> dict:
    contexto = client.contexto_sessao()
    _gravar("contexto_sessao.json", contexto)
    logger.info("contexto_sessao: orgao ativo %s", contexto.get("bnmp-orgaoAtivoNome"))
    return contexto


def _paginas_existentes(recurso: str, consulta: str) -> set[int]:
    existentes: set[int] = set()
    for caminho in listar_arquivos(f"{_PREFIXO}/{recurso}/{consulta}/"):
        nome = caminho.rsplit("/", 1)[-1]
        if nome.startswith("pagina_") and nome.endswith(".json"):
            existentes.add(int(nome[len("pagina_") : -len(".json")]))
    return existentes


def extrair_paginado(
    client: BnmpClient,
    recurso: str,
    consulta: str,
    filtros: dict,
    metodo: Callable[..., dict],
    tamanho: int = _TAMANHO_PAGINA,
    retomar: bool = True,
    max_paginas: int | None = None,
    ordenacao: str | None = None,
) -> dict:
    """Percorre todas as páginas de uma consulta gravando uma página por arquivo.

    Devolve o manifesto final. Com retomar=True, páginas já gravadas no
    Lakehouse são puladas (retomada de coleta interrompida).
    """
    existentes = _paginas_existentes(recurso, consulta) if retomar else set()
    if existentes:
        logger.info("%s/%s: %d páginas já gravadas — retomando", recurso, consulta, len(existentes))

    manifesto = {
        "consulta": consulta,
        "recurso": recurso,
        "filtros": filtros,
        "tamanho_pagina": tamanho,
        "total_elementos": None,
        "total_paginas": None,
        "paginas_gravadas": len(existentes),
        "ultima_pagina": max(existentes) if existentes else None,
        "iniciado_em": _agora(),
        "atualizado_em": None,
        "status": "em_andamento",
    }

    def _gravar_manifesto() -> None:
        manifesto["atualizado_em"] = _agora()
        _gravar(f"{recurso}/{consulta}/_manifesto.json", manifesto)

    pagina = 0
    total_paginas: int | None = None
    gravadas_nesta_execucao = 0
    while total_paginas is None or pagina < total_paginas:
        if pagina in existentes:
            pagina += 1
            continue
        resposta = metodo(filtros, pagina=pagina, tamanho=tamanho, ordenacao=ordenacao)
        total_paginas = resposta.get("totalPages", 0)
        manifesto["total_elementos"] = resposta.get("totalElements")
        manifesto["total_paginas"] = total_paginas

        envelope = {
            "consulta": consulta,
            "pagina": pagina,
            "coletado_em": _agora(),
            "resposta": resposta,
        }
        _gravar(f"{recurso}/{consulta}/pagina_{pagina:06d}.json", envelope, indentado=False)
        manifesto["paginas_gravadas"] += 1
        manifesto["ultima_pagina"] = pagina
        gravadas_nesta_execucao += 1

        if gravadas_nesta_execucao % _PAGINAS_POR_MANIFESTO == 0:
            _gravar_manifesto()
            logger.info(
                "%s/%s: página %d/%s gravada (%d elementos no total)",
                recurso, consulta, pagina, total_paginas, manifesto["total_elementos"],
            )
        if max_paginas is not None and gravadas_nesta_execucao >= max_paginas:
            _gravar_manifesto()
            logger.info("%s/%s: limite de %d páginas atingido", recurso, consulta, max_paginas)
            return manifesto
        if resposta.get("last", True) or not resposta.get("content"):
            break
        pagina += 1

    manifesto["status"] = "concluido"
    _gravar_manifesto()
    logger.info(
        "%s/%s: coleta concluída — %s páginas, %s elementos",
        recurso, consulta, manifesto["total_paginas"], manifesto["total_elementos"],
    )
    return manifesto


def extrair_pessoas(client: BnmpClient, consulta: str, filtros: dict, **kw: object) -> dict:
    return extrair_paginado(client, "pessoas", consulta, filtros, client.filtrar_pessoas, **kw)


def extrair_pecas(client: BnmpClient, consulta: str, filtros: dict, **kw: object) -> dict:
    return extrair_paginado(client, "pecas", consulta, filtros, client.filtrar_pecas, **kw)


def extrair_eventos(client: BnmpClient, consulta: str, filtros: dict, **kw: object) -> dict:
    return extrair_paginado(client, "eventos", consulta, filtros, client.filtrar_eventos, **kw)


def executar(
    consultas_pessoas: list[tuple[str, dict]] | None = None,
    consultas_pecas: list[tuple[str, dict]] | None = None,
    consultas_eventos: list[tuple[str, dict]] | None = None,
    tamanho_pagina: int = _TAMANHO_PAGINA,
) -> None:
    """Roda a extração bronze completa: domínios + consultas paginadas."""
    with BnmpClient() as client:
        extrair_contexto_sessao(client)
        extrair_dominios(client)
        extrair_status_pessoas(client)

        for consulta, filtros in consultas_pessoas or []:
            extrair_pessoas(client, consulta, filtros, tamanho=tamanho_pagina)
        for consulta, filtros in consultas_pecas or []:
            extrair_pecas(client, consulta, filtros, tamanho=tamanho_pagina)
        for consulta, filtros in consultas_eventos or []:
            extrair_eventos(client, consulta, filtros, tamanho=tamanho_pagina)

    logger.info("Extração bronze do BNMP concluída")


if __name__ == "__main__":
    # Recorte padrão: pessoas ativas com custódia/registro em São Paulo (uf 26).
    executar(consultas_pessoas=[("pessoas_uf-26_ativo-1", filtro_pessoas(uf_id=26))])
