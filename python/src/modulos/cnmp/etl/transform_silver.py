"""Camada silver: funções puras que transformam o JSON bruto da API do CNMP
(camada bronze) nas linhas das tabelas normalizadas descritas em
python/downloads/cnmp/schema_lakehouse_resolucao_277.md.

Nenhuma função aqui acessa rede ou banco — recebem dict/list já carregados
(do bronze) e devolvem listas de dicts prontas para INSERT.
"""

from typing import Any


def linhas_dim_ambiente(ambientes: list[dict]) -> list[dict]:
    return [{"ambiente_id_api": a["id"], "descricao": a["descricao"]} for a in ambientes]


def linha_dim_formulario(formulario_detalhe: dict, ambiente_id_api: int) -> dict:
    return {
        "formulario_id_api": formulario_detalhe["id"],
        "ambiente_id_api": ambiente_id_api,
        "nome": formulario_detalhe["nome"],
        "periodicidade": formulario_detalhe.get("periodicidade"),
        "versao": formulario_detalhe.get("versao"),
        "ano_inicio": formulario_detalhe.get("anoInicio"),
        "periodo_inicio": formulario_detalhe.get("periodoInicio"),
        "ano_termino": formulario_detalhe.get("anoTermino"),
        "periodo_termino": formulario_detalhe.get("periodoTermino"),
    }


def linhas_dim_formulario_tipo_entidade(formulario_detalhe: dict) -> list[dict]:
    formulario_id_api = formulario_detalhe["id"]
    return [
        {
            "formulario_id_api": formulario_id_api,
            "tipo_entidade_id_api": tipo["id"],
            "descricao": tipo["descricao"],
        }
        for tipo in formulario_detalhe.get("tiposEntidadeAceitos", [])
    ]


def linhas_secao_campo(
    formulario_detalhe: dict,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Explode seções e campos do formulário, incluindo colunas de TABELA_DINAMICA.

    Returns:
        (secoes, campos, campo_opcoes, campo_dependencias)
    """
    formulario_id_api = formulario_detalhe["id"]
    secoes: list[dict] = []
    campos: list[dict] = []
    opcoes: list[dict] = []
    dependencias: list[dict] = []

    def _processar_campo(campo: dict, secao_id_api: int, parent_campo_id_api: int | None) -> None:
        tipo = campo["tipoCampo"]["tipo"]
        campos.append(
            {
                "campo_id_api": campo["id"],
                "secao_id_api": secao_id_api,
                "formulario_id_api": formulario_id_api,
                "parent_campo_id_api": parent_campo_id_api,
                "label": campo.get("label"),
                "indice": campo.get("indice"),
                "tabulacao": campo.get("tabulacao"),
                "obrigatorio": bool(campo.get("obrigatorio", False)),
                "tamanho_maximo": campo.get("tamanhoMaximo"),
                "tipo_campo": tipo,
                "is_tabela_dinamica": tipo == "TABELA_DINAMICA",
            }
        )

        for resposta in campo.get("respostas") or []:
            opcoes.append(
                {
                    "campo_id_api": campo["id"],
                    "valor_api": str(resposta["valor"]),
                    "descricao": resposta["descricao"],
                }
            )

        for dependencia in campo.get("dependencias") or []:
            dependencias.append(
                {
                    "campo_id_api": campo["id"],
                    "campo_id_condicao_api": dependencia["idCampo"],
                    "valor_resposta_esperado": str(dependencia["valorResposta"]),
                }
            )

        for coluna in campo.get("colunas") or []:
            _processar_campo(coluna["campo"], secao_id_api, campo["id"])

    for secao in formulario_detalhe.get("secoes", []):
        secoes.append(
            {
                "secao_id_api": secao["id"],
                "formulario_id_api": formulario_id_api,
                "indice": secao.get("indice"),
                "nome": secao.get("nome"),
            }
        )
        for campo in secao.get("campos", []):
            _processar_campo(campo, secao["id"], None)

    return secoes, campos, opcoes, dependencias


def linhas_dim_entidade(entidades: list[dict], ambiente_id_api: int) -> list[dict]:
    return [
        {
            "entidade_id_api": entidade["id"],
            "ambiente_id_api": ambiente_id_api,
            "descricao": entidade.get("descricao") or entidade.get("nome"),
        }
        for entidade in entidades
    ]


def linha_fato_instancia(
    instancia_resumo: dict, formulario_id_api: int, entidade_id_api: int
) -> dict:
    return {
        "instancia_id_api": instancia_resumo["id"],
        "formulario_id_api": formulario_id_api,
        "entidade_id_api": entidade_id_api,
        "ano": instancia_resumo.get("ano"),
        "periodo": instancia_resumo.get("periodo"),
        "status_atual": instancia_resumo.get("statusAtual"),
    }


def linhas_fato_resposta(instancia_id_api: int, conteudo: list[dict]) -> list[dict]:
    """Explode o conteúdo (EAV) de uma instância.

    Campos comuns geram 1 linha com `linha = 1`. Campos TABELA_DINAMICA não geram
    linha própria; cada repetição em `campoTabela.linhas[]` gera 1 linha por coluna,
    com `linha` igual ao número da repetição — todas as colunas de uma mesma
    repetição compartilham esse número, permitindo reagrupá-las depois.
    """
    linhas: list[dict] = []

    def _processar(item: dict[str, Any], linha: int) -> None:
        campo_tabela = item.get("campoTabela")
        if campo_tabela:
            for linha_tabela in campo_tabela.get("linhas", []):
                numero_linha = linha_tabela["linha"]
                for coluna in linha_tabela.get("colunas", []):
                    _processar(coluna, numero_linha)
        else:
            linhas.append(
                {
                    "instancia_id_api": instancia_id_api,
                    "campo_id_api": item["idCampo"],
                    "linha": linha,
                    "valor_resposta": item.get("valorResposta"),
                }
            )

    for item in conteudo:
        _processar(item, 1)

    return linhas
