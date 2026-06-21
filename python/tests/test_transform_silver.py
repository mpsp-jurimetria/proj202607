from src.modulos.cnmp.etl.transform_silver import (
    linha_dim_formulario,
    linha_fato_instancia,
    linhas_dim_ambiente,
    linhas_dim_entidade,
    linhas_dim_formulario_tipo_entidade,
    linhas_fato_resposta,
    linhas_secao_campo,
)

FORMULARIO_DETALHE = {
    "id": 1322,
    "nome": "Formulário de Visita Semestral à Estabelecimentos Prisionais",
    "ambiente": "Resolução 277",
    "versao": 2,
    "periodicidade": "Semestral",
    "anoInicio": 2024,
    "periodoInicio": 1,
    "anoTermino": 2024,
    "periodoTermino": 1,
    "tiposEntidadeAceitos": [
        {"id": 542, "descricao": "Penitenciária Resolução 277"},
        {"id": 543, "descricao": "Cadeia pública Resolução 277"},
    ],
    "secoes": [
        {
            "id": 2067,
            "indice": 1,
            "nome": "SEÇÃO I - IDENTIFICAÇÃO",
            "campos": [
                {
                    "id": 30133,
                    "label": "1.1 Data da visita:",
                    "indice": 1,
                    "tabulacao": 0,
                    "obrigatorio": True,
                    "tipoCampo": {"tipo": "DATA", "descricao": "Campo data"},
                },
                {
                    "id": 30134,
                    "label": "1.2 Período de referência:",
                    "indice": 2,
                    "obrigatorio": True,
                    "tipoCampo": {"tipo": "RADIO", "descricao": "Lista de Seleção (Radio)"},
                    "respostas": [
                        {"valor": 30493, "descricao": "Julho a dezembro do ano anterior"},
                        {"valor": 30494, "descricao": "Janeiro a junho do ano corrente"},
                    ],
                },
            ],
        },
        {
            "id": 2070,
            "indice": 2,
            "nome": "SEÇÃO XIII - DROGAS",
            "campos": [
                {
                    "id": 30446,
                    "label": "13.10 Houve apreensão de drogas?",
                    "indice": 1,
                    "obrigatorio": True,
                    "tipoCampo": {"tipo": "SIM_NAO", "descricao": "Sim/Não"},
                },
                {
                    "id": 30447,
                    "label": "Tipo e Quantidade em gramas:",
                    "indice": 2,
                    "tabulacao": 1,
                    "obrigatorio": True,
                    "tipoCampo": {"tipo": "TABELA_DINAMICA", "descricao": "Tabela dinâmica"},
                    "dependencias": [{"idCampo": 30446, "valorResposta": "Sim"}],
                    "colunas": [
                        {
                            "campo": {
                                "id": 30513,
                                "label": "13.11.1 Maconha:",
                                "indice": 1,
                                "obrigatorio": True,
                                "tipoCampo": {
                                    "tipo": "SOMENTE_NUMERO",
                                    "descricao": "Campo somente números",
                                },
                            }
                        },
                        {
                            "campo": {
                                "id": 30514,
                                "label": "13.11.2 Cocaína:",
                                "indice": 2,
                                "obrigatorio": True,
                                "tipoCampo": {
                                    "tipo": "SOMENTE_NUMERO",
                                    "descricao": "Campo somente números",
                                },
                            }
                        },
                    ],
                },
            ],
        },
    ],
}

# Estrutura real observada na inspeção (entidade 71532, formulário 1322): campo
# SIM_NAO comum + TABELA_DINAMICA com 1 repetição preenchida.
CONTEUDO_INSTANCIA = [
    {"idCampo": 30133, "valorResposta": "01/03/2024", "campoTabela": None},
    {"idCampo": 30446, "valorResposta": "true", "campoTabela": None},
    {
        "idCampo": 30447,
        "valorResposta": None,
        "campoTabela": {
            "idCampo": 30447,
            "linhas": [
                {
                    "linha": 1,
                    "colunas": [
                        {"idCampo": 30513, "valorResposta": "327", "campoTabela": None},
                        {"idCampo": 30514, "valorResposta": "6", "campoTabela": None},
                    ],
                }
            ],
        },
    },
]


def test_linhas_dim_ambiente():
    ambientes = [{"id": 282, "descricao": "Resolução 277 (militar)"}]
    assert linhas_dim_ambiente(ambientes) == [
        {"ambiente_id_api": 282, "descricao": "Resolução 277 (militar)"}
    ]


def test_linha_dim_formulario():
    linha = linha_dim_formulario(FORMULARIO_DETALHE, ambiente_id_api=462)
    assert linha == {
        "formulario_id_api": 1322,
        "ambiente_id_api": 462,
        "nome": "Formulário de Visita Semestral à Estabelecimentos Prisionais",
        "periodicidade": "Semestral",
        "versao": 2,
        "ano_inicio": 2024,
        "periodo_inicio": 1,
        "ano_termino": 2024,
        "periodo_termino": 1,
    }


def test_linhas_dim_formulario_tipo_entidade():
    linhas = linhas_dim_formulario_tipo_entidade(FORMULARIO_DETALHE)
    assert linhas == [
        {
            "formulario_id_api": 1322,
            "tipo_entidade_id_api": 542,
            "descricao": "Penitenciária Resolução 277",
        },
        {
            "formulario_id_api": 1322,
            "tipo_entidade_id_api": 543,
            "descricao": "Cadeia pública Resolução 277",
        },
    ]


def test_linhas_secao_campo_explode_tabela_dinamica():
    secoes, campos, opcoes, dependencias = linhas_secao_campo(FORMULARIO_DETALHE)

    assert len(secoes) == 2
    assert {c["campo_id_api"] for c in campos} == {30133, 30134, 30446, 30447, 30513, 30514}

    campo_pai = next(c for c in campos if c["campo_id_api"] == 30447)
    assert campo_pai["is_tabela_dinamica"] is True
    assert campo_pai["parent_campo_id_api"] is None

    coluna = next(c for c in campos if c["campo_id_api"] == 30513)
    assert coluna["parent_campo_id_api"] == 30447
    assert coluna["is_tabela_dinamica"] is False

    assert opcoes == [
        {
            "campo_id_api": 30134,
            "valor_api": "30493",
            "descricao": "Julho a dezembro do ano anterior",
        },
        {
            "campo_id_api": 30134,
            "valor_api": "30494",
            "descricao": "Janeiro a junho do ano corrente",
        },
    ]

    assert dependencias == [
        {
            "campo_id_api": 30447,
            "campo_id_condicao_api": 30446,
            "valor_resposta_esperado": "Sim",
        }
    ]


def test_linhas_dim_entidade():
    entidades = [{"id": 71744, "descricao": 'PENITENCIÁRIA FEMININA "OSCAR GARCIA MACHADO"'}]
    assert linhas_dim_entidade(entidades, ambiente_id_api=462) == [
        {
            "entidade_id_api": 71744,
            "ambiente_id_api": 462,
            "descricao": 'PENITENCIÁRIA FEMININA "OSCAR GARCIA MACHADO"',
        }
    ]


def test_linha_fato_instancia():
    resumo = {"id": 363822, "ano": 2024, "periodo": 1, "statusAtual": "FINALIZADA"}
    assert linha_fato_instancia(resumo, formulario_id_api=1322, entidade_id_api=71532) == {
        "instancia_id_api": 363822,
        "formulario_id_api": 1322,
        "entidade_id_api": 71532,
        "ano": 2024,
        "periodo": 1,
        "status_atual": "FINALIZADA",
    }


def test_linhas_fato_resposta_campo_comum():
    linhas = linhas_fato_resposta(363822, CONTEUDO_INSTANCIA)
    comuns = [linha for linha in linhas if linha["campo_id_api"] in (30133, 30446)]
    assert comuns == [
        {"instancia_id_api": 363822, "campo_id_api": 30133, "linha": 1, "valor_resposta": "01/03/2024"},
        {"instancia_id_api": 363822, "campo_id_api": 30446, "linha": 1, "valor_resposta": "true"},
    ]


def test_linhas_fato_resposta_explode_tabela_dinamica():
    linhas = linhas_fato_resposta(363822, CONTEUDO_INSTANCIA)
    colunas_tabela = [linha for linha in linhas if linha["campo_id_api"] in (30513, 30514)]
    assert colunas_tabela == [
        {"instancia_id_api": 363822, "campo_id_api": 30513, "linha": 1, "valor_resposta": "327"},
        {"instancia_id_api": 363822, "campo_id_api": 30514, "linha": 1, "valor_resposta": "6"},
    ]
    # o campo pai (30447) não gera linha própria, só os filhos
    assert not any(linha["campo_id_api"] == 30447 for linha in linhas)
