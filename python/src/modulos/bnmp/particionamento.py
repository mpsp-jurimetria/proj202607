"""Particionamento das consultas do BNMP para caber no limite da API.

A API rejeita paginação além do registro 10.000 (offset >= 10000 devolve 500 e
acima disso 400), independentemente do tamanho de página. Uma consulta com mais
de 10.000 resultados, portanto, nunca pode ser coletada por inteiro — só os
primeiros 10.000.

A saída é uma lista de partições cujas consultas cabem no limite: começa por
uma dimensão grossa (UF) e, enquanto uma partição estourar, subdivide pela
próxima dimensão (status, sexo, município). Cada sondagem custa uma requisição
com size=1, então planejar é barato perto de coletar.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from src.modulos.bnmp.client import BnmpClient
from src.modulos.bnmp.filtros import filtro_pessoas, rotulo_consulta

logger = logging.getLogger(__name__)

# Maior offset aceito pela API (medido: page*size = 9960 passa, 10000 devolve 500).
LIMITE_REGISTROS = 10_000


@dataclass
class Particao:
    """Uma consulta que se pretende coletar por inteiro."""

    rotulo: str
    filtros: dict
    total: int
    valores: dict = field(default_factory=dict)

    @property
    def cabe_no_limite(self) -> bool:
        return self.total <= LIMITE_REGISTROS


def contar(client: BnmpClient, metodo: Callable[..., dict], filtros: dict) -> int:
    """Total de registros de uma consulta, com uma única requisição."""
    return metodo(filtros, pagina=0, tamanho=1).get("totalElements", 0)


def planejar(
    client: BnmpClient,
    metodo: Callable[..., dict],
    construtor: Callable[..., dict],
    dimensoes: list[tuple[str, list]],
    recurso: str,
    valores_fixos: dict | None = None,
) -> list[Particao]:
    """Monta a lista de partições coletáveis para um recurso.

    dimensoes: pares (nome do parâmetro do construtor, valores possíveis), da
    mais grossa para a mais fina. Uma partição só é subdividida se estourar o
    limite; partições vazias são descartadas.
    """
    valores_fixos = valores_fixos or {}
    pendentes = [(valores_fixos, 0)]
    particoes: list[Particao] = []

    while pendentes:
        valores, nivel = pendentes.pop(0)
        filtros = construtor(**valores)
        total = contar(client, metodo, filtros)
        rotulo = rotulo_consulta(recurso, **valores)

        if total == 0:
            logger.info("%s: vazia, descartada", rotulo)
            continue

        if total <= LIMITE_REGISTROS or nivel >= len(dimensoes):
            particao = Particao(rotulo=rotulo, filtros=filtros, total=total, valores=dict(valores))
            particoes.append(particao)
            if not particao.cabe_no_limite:
                logger.warning(
                    "%s: %d registros acima do limite de %d e sem dimensão para "
                    "subdividir — só os primeiros %d serão coletados",
                    rotulo, total, LIMITE_REGISTROS, LIMITE_REGISTROS,
                )
            continue

        nome, opcoes = dimensoes[nivel]
        logger.info(
            "%s: %d registros — subdividindo por %s (%d valores)",
            rotulo, total, nome, len(opcoes),
        )
        for opcao in opcoes:
            pendentes.append(({**valores, nome: opcao}, nivel + 1))

    return particoes


def planejar_pessoas(
    client: BnmpClient,
    uf_ids: list[int] | None = None,
    incluir_municipios: bool = True,
) -> list[Particao]:
    """Planeja a coleta de pessoas: UF, depois status, sexo e município."""
    dominios = client.dominios()
    ufs = uf_ids or [item["id"] for item in dominios.get("unidadesFederativa") or []]
    status_ids = [item["id"] for item in client.status_pessoas()]
    sexo_ids = [item["id"] for item in dominios.get("sexos") or []]

    dimensoes: list[tuple[str, list]] = [
        ("status_pessoa_id", status_ids),
        ("sexo_id", sexo_ids),
    ]
    if incluir_municipios:
        municipios = client.municipios()
        por_uf: dict[int, list[int]] = {}
        for municipio in municipios:
            uf = (municipio.get("uf") or {}).get("id")
            if uf is not None:
                por_uf.setdefault(uf, []).append(municipio["id"])
        # a lista de municípios depende da UF da partição, então entra como
        # dimensão resolvida por UF na hora de subdividir
        dimensoes.append(("municipio_id", por_uf))

    particoes: list[Particao] = []
    for uf_id in ufs:
        dimensoes_uf = [
            (nome, opcoes.get(uf_id, []) if isinstance(opcoes, dict) else opcoes)
            for nome, opcoes in dimensoes
        ]
        particoes.extend(
            planejar(
                client,
                client.filtrar_pessoas,
                filtro_pessoas,
                dimensoes_uf,
                recurso="pessoas",
                valores_fixos={"uf_id": uf_id},
            )
        )
    return particoes


def resumir(particoes: list[Particao]) -> dict:
    """Resumo do plano, para log e para gravar junto do bronze."""
    estouradas = [p for p in particoes if not p.cabe_no_limite]
    return {
        "particoes": len(particoes),
        "registros_previstos": sum(p.total for p in particoes),
        "particoes_acima_do_limite": len(estouradas),
        "registros_inalcancaveis": sum(p.total - LIMITE_REGISTROS for p in estouradas),
    }
