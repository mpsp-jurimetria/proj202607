"""Funções puras que transformam as linhas da planilha da SAP-SP
(sap_nova_corrigida.xlsx) nas linhas da tabela sap_unidade do silver.

Nenhuma função aqui acessa rede ou banco — recebem o cabeçalho e as linhas já
lidas (via openpyxl) e devolvem listas de dicts prontas para INSERT.
"""

from typing import Any

# Coluna da planilha -> coluna da tabela sap_unidade. A leitura é feita pelo
# nome do cabeçalho, não pela posição, para tolerar reordenação de colunas em
# versões futuras da planilha.
_COLUNAS = {
    "Ano": "ano",
    "Unidade Prisional": "unidade_nome",
    "nome_mun": "municipio",
    "regional": "regional",
    "cod_muni": "cod_ibge",
    "custodia": "custodia",
    "comarca": "comarca",
    "nome_raj": "raj",
    "Destinação da unidade Prisional": "destinacao",
    "Facções existentes na unidade prisional (nomes)": "faccoes",
    "Número de Servidores": "servidores",
    "Número de Policiais Penais": "policiais_penais",
    "Número de Presos": "presos",
    "Capacidade da Unidade Prisional": "capacidade",
    "superlotacao_percentual": "superlotacao_percentual",
    "Mortes naturais no trimestre": "mortes_naturais",
    "Mortes por intervenção de terceiros": "mortes_intervencao",
    "Morte Indeterminada / Suicídio": "mortes_indeterminadas",
    "Providências tomadas": "providencias",
    "DEECRIM": "deecrim",
    "Médico": "medicos",
    "Dentista": "dentistas",
    "Psicólogo": "psicologos",
    "Assistente Social": "assistentes_sociais",
    "Psquiatra": "psiquiatras",
    "Número de Presos que estudam": "presos_estudam",
    "Número de presos que trabalham": "presos_trabalham",
    "genero": "genero",
}

_COLUNAS_INTEIRAS = {
    "ano", "cod_ibge", "servidores", "policiais_penais", "presos", "capacidade",
    "mortes_naturais", "mortes_intervencao", "mortes_indeterminadas",
    "medicos", "dentistas", "psicologos", "assistentes_sociais", "psiquiatras",
    "presos_estudam", "presos_trabalham",
}

_COLUNAS_DECIMAIS = {"superlotacao_percentual"}

COLUNAS_SAP_UNIDADE = list(_COLUNAS.values())


def _inteiro(valor: Any) -> int | None:
    """Converte tolerantemente para int; texto não numérico (ex.: 'Prejudicado')
    vira None — a planilha mistura números, strings numéricas e observações."""
    if valor is None:
        return None
    try:
        return int(float(str(valor).replace(",", ".").strip()))
    except ValueError:
        return None


def _decimal(valor: Any) -> float | None:
    if valor is None:
        return None
    try:
        return float(str(valor).replace(",", ".").strip())
    except ValueError:
        return None


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def linhas_sap_unidade(cabecalho: list, linhas: list[tuple]) -> list[dict]:
    """Converte as linhas da planilha em dicts tipados para a tabela sap_unidade.

    Args:
        cabecalho: primeira linha da planilha (nomes das colunas).
        linhas: demais linhas (values_only). Linhas sem nome de unidade são
            ignoradas (linhas vazias no fim da planilha).

    Raises:
        ValueError: coluna esperada ausente ou nome de unidade duplicado
            (unidade_nome é a chave natural usada pelo de-para do CNMP).
    """
    indices: dict[str, int] = {}
    nomes_cabecalho = [(_texto(c) or "") for c in cabecalho]
    for coluna_planilha, coluna_tabela in _COLUNAS.items():
        if coluna_planilha not in nomes_cabecalho:
            raise ValueError(f"coluna {coluna_planilha!r} não encontrada na planilha")
        indices[coluna_tabela] = nomes_cabecalho.index(coluna_planilha)

    resultado: list[dict] = []
    vistos: set[str] = set()
    for linha in linhas:
        nome = _texto(linha[indices["unidade_nome"]])
        if not nome:
            continue
        if nome in vistos:
            raise ValueError(f"unidade duplicada na planilha: {nome!r}")
        vistos.add(nome)

        registro: dict = {}
        for coluna_tabela, indice in indices.items():
            valor = linha[indice]
            if coluna_tabela in _COLUNAS_INTEIRAS:
                registro[coluna_tabela] = _inteiro(valor)
            elif coluna_tabela in _COLUNAS_DECIMAIS:
                registro[coluna_tabela] = _decimal(valor)
            else:
                registro[coluna_tabela] = _texto(valor)
        resultado.append(registro)

    return resultado
