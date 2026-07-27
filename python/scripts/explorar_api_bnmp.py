"""Explora a API do BNMP 2.0 para subsidiar o desenho do schema silver.

O HAR do frontend só trouxe respostas vazias para /pecas/light-filter e
/eventos/light-filter (os filtros usados não bateram), então a estrutura dos
itens desses dois recursos é desconhecida. Este script sonda combinações de
filtros até achar as que retornam dados, baixa amostras e resume os campos.

Também mede a capacidade de paginação de /pessoas/filter (tamanho de página
aceito, ordenação, páginas profundas), o que define o particionamento da
coleta bronze.

Saída: JSON em python/downloads/bnmp/ (gitignored).

Uso:
    uv run python scripts/explorar_api_bnmp.py
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

from src.modulos.bnmp.client import BnmpClient
from src.modulos.bnmp.filtros import filtro_eventos, filtro_pecas, filtro_pessoas

logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.modulos.bnmp").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

SAIDA = Path(__file__).resolve().parent.parent / "downloads" / "bnmp"

# Órgãos candidatos a expeditor/judiciário nas sondagens: MPSP (o da sessão),
# TJSP e uma vara de exemplo vista no HAR.
ORGAOS_CANDIDATOS = [39, 33, 12717, None]


def gravar(nome: str, dados: object) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("gravado: %s", caminho)


def resumir_campos(itens: list[dict]) -> dict:
    """Mapeia recursivamente os campos dos itens: tipos, preenchimento e exemplos."""
    resumo: dict[str, dict[str, Any]] = {}

    def visitar(valor: object, caminho: str) -> None:
        entrada = resumo.setdefault(caminho, {"tipos": [], "preenchidos": 0, "exemplos": []})
        tipo = type(valor).__name__
        if tipo not in entrada["tipos"]:
            entrada["tipos"].append(tipo)
        if valor is not None and valor != {} and valor != []:
            entrada["preenchidos"] += 1
        if isinstance(valor, dict):
            for chave, subvalor in valor.items():
                visitar(subvalor, f"{caminho}.{chave}" if caminho else chave)
        elif isinstance(valor, list):
            for subvalor in valor[:3]:
                visitar(subvalor, f"{caminho}[]")
        elif valor is not None and len(entrada["exemplos"]) < 3:
            if valor not in entrada["exemplos"]:
                entrada["exemplos"].append(valor)

    for item in itens:
        visitar(item, "")
    resumo.pop("", None)
    return dict(sorted(resumo.items()))


def sondar(client: BnmpClient, metodo, combinacoes: list[tuple[str, dict]]) -> list[dict]:
    """Roda cada combinação de filtros com size=1 e registra o totalElements."""
    resultados = []
    for rotulo, filtros in combinacoes:
        try:
            resposta = metodo(filtros, pagina=0, tamanho=1)
            total = resposta.get("totalElements", 0)
            resultados.append({"rotulo": rotulo, "filtros": filtros, "total_elementos": total})
            logger.info("sondagem %s: %s elementos", rotulo, total)
        except Exception as erro:  # noqa: BLE001 — sondagem exploratória
            resultados.append({"rotulo": rotulo, "filtros": filtros, "erro": str(erro)})
            logger.info("sondagem %s: erro %s", rotulo, erro)
    return sorted(resultados, key=lambda r: r.get("total_elementos") or -1, reverse=True)


def explorar_dominios(client: BnmpClient) -> dict:
    dominios = client.dominios()
    gravar("dominios.json", dominios)
    gravar("status_pessoas.json", client.status_pessoas())

    resumo = {}
    for chave, valor in dominios.items():
        if isinstance(valor, list) and valor:
            chaves_item = sorted(valor[0].keys()) if isinstance(valor[0], dict) else None
            resumo[chave] = {"n_itens": len(valor), "chaves_do_item": chaves_item}
        else:
            resumo[chave] = {"n_itens": 0, "chaves_do_item": None}
    gravar("dominios_resumo.json", resumo)
    return dominios


def explorar_pecas(client: BnmpClient, dominios: dict) -> None:
    status_ids = [item["id"] for item in dominios.get("status") or []]
    combinacoes: list[tuple[str, dict]] = []
    for orgao in ORGAOS_CANDIDATOS:
        for perfil, judiciario, agente_externo in (
            ("judiciario", True, False),
            ("externo", False, True),
            ("sem-perfil", None, None),
        ):
            combinacoes.append(
                (
                    f"orgao-{orgao}_{perfil}",
                    filtro_pecas(
                        orgao_expeditor_id=orgao, judiciario=judiciario, agente_externo=agente_externo
                    ),
                )
            )
    for status_id in status_ids[:15]:
        combinacoes.append(
            (f"status-{status_id}", filtro_pecas(status_id=status_id, orgao_expeditor_id=None))
        )

    resultados = sondar(client, client.filtrar_pecas, combinacoes)
    gravar("sondagem_pecas.json", resultados)

    itens: list[dict] = []
    for resultado in resultados[:3]:
        if not resultado.get("total_elementos"):
            continue
        resposta = client.filtrar_pecas(resultado["filtros"], pagina=0, tamanho=40)
        gravar(f"amostra_pecas_{resultado['rotulo']}.json", resposta)
        itens.extend(resposta.get("content", []))
    if itens:
        gravar("mapa_campos_pecas.json", resumir_campos(itens))
    else:
        logger.warning("nenhuma combinação de filtros de peças retornou dados")


def explorar_eventos(client: BnmpClient, dominios: dict) -> None:
    status_ids = [item["id"] for item in dominios.get("statusEventos") or []]
    tipos_ids = [item["id"] for item in dominios.get("tiposEventos") or []]
    combinacoes: list[tuple[str, dict]] = []
    for orgao in ORGAOS_CANDIDATOS:
        combinacoes.append((f"orgao-{orgao}", filtro_eventos(orgao_judiciario_id=orgao)))
        combinacoes.append(
            (f"orgao-{orgao}_externo", filtro_eventos(orgao_judiciario_id=orgao, agente_externo=True))
        )
    for status_id in status_ids[:7]:
        combinacoes.append((f"status-{status_id}", filtro_eventos(status_evento_id=status_id)))
    for tipo_id in tipos_ids[:15]:
        combinacoes.append((f"tipo-{tipo_id}", filtro_eventos(tipo_evento_id=tipo_id)))

    resultados = sondar(client, client.filtrar_eventos, combinacoes)
    gravar("sondagem_eventos.json", resultados)

    itens: list[dict] = []
    for resultado in resultados[:3]:
        if not resultado.get("total_elementos"):
            continue
        resposta = client.filtrar_eventos(resultado["filtros"], pagina=0, tamanho=40)
        gravar(f"amostra_eventos_{resultado['rotulo']}.json", resposta)
        itens.extend(resposta.get("content", []))
    if itens:
        gravar("mapa_campos_eventos.json", resumir_campos(itens))
    else:
        logger.warning("nenhuma combinação de filtros de eventos retornou dados")


def explorar_capacidade_paginacao(client: BnmpClient) -> None:
    """Mede o tamanho de página realmente aceito, o efeito de sort e o limite
    de paginação profunda — define o particionamento da coleta."""
    filtros = filtro_pessoas(uf_id=26)
    medidas: dict[str, Any] = {"tamanhos": [], "ordenacao": None, "paginas_profundas": []}

    for tamanho in (40, 100, 200, 500, 1000):
        inicio = time.monotonic()
        try:
            resposta = client.filtrar_pessoas(filtros, pagina=0, tamanho=tamanho)
            medidas["tamanhos"].append(
                {
                    "solicitado": tamanho,
                    "size_devolvido": resposta.get("size"),
                    "itens_devolvidos": resposta.get("numberOfElements"),
                    "segundos": round(time.monotonic() - inicio, 2),
                }
            )
        except Exception as erro:  # noqa: BLE001
            medidas["tamanhos"].append({"solicitado": tamanho, "erro": str(erro)})

    try:
        resposta = client.filtrar_pessoas(filtros, pagina=0, tamanho=40, ordenacao="id,asc")
        medidas["ordenacao"] = {
            "aceito": True,
            "sort_devolvido": resposta.get("sort"),
            "primeiro_id": (resposta.get("content") or [{}])[0].get("id"),
        }
    except Exception as erro:  # noqa: BLE001
        medidas["ordenacao"] = {"aceito": False, "erro": str(erro)}

    for pagina in (100, 1_000, 10_000, 50_000):
        inicio = time.monotonic()
        try:
            resposta = client.filtrar_pessoas(filtros, pagina=pagina, tamanho=40)
            medidas["paginas_profundas"].append(
                {
                    "pagina": pagina,
                    "itens_devolvidos": resposta.get("numberOfElements"),
                    "segundos": round(time.monotonic() - inicio, 2),
                }
            )
        except Exception as erro:  # noqa: BLE001
            medidas["paginas_profundas"].append({"pagina": pagina, "erro": str(erro)})

    gravar("capacidade_paginacao.json", medidas)


def explorar_pessoas(client: BnmpClient) -> None:
    itens: list[dict] = []
    for pagina in range(5):
        resposta = client.filtrar_pessoas(filtro_pessoas(uf_id=26), pagina=pagina, tamanho=40)
        if pagina == 0:
            gravar("amostra_pessoas.json", resposta)
        itens.extend(resposta.get("content", []))
    gravar("mapa_campos_pessoas.json", resumir_campos(itens))


def main() -> None:
    with BnmpClient() as client:
        contexto = client.contexto_sessao()
        gravar("contexto_sessao.json", contexto)
        logger.info("sessão: %s", contexto.get("bnmp-orgaoAtivoNome"))

        dominios = explorar_dominios(client)
        explorar_pessoas(client)
        explorar_capacidade_paginacao(client)
        explorar_pecas(client, dominios)
        explorar_eventos(client, dominios)

    logger.info("Exploração concluída — arquivos em %s", SAIDA)


if __name__ == "__main__":
    main()
