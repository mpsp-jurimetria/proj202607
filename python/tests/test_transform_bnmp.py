from src.modulos.bnmp.etl.transform_silver import (
    COLUNAS_BNMP_EVENTO,
    COLUNAS_BNMP_PECA,
    linhas_bnmp_dominio,
    linhas_bnmp_evento,
    linhas_bnmp_peca,
    linhas_bnmp_pessoa,
)
from src.modulos.bnmp.filtros import filtro_pecas, filtro_pessoas, rotulo_consulta

# Item real de /pecas/light-filter (DTO plano, sem objetos aninhados).
ITEM_PECA = {
    "id": 207204272,
    "numeroPeca": "0003697212025826007725000316",
    "descricaoTipoPeca": "Mandado de Medidas Diversas da Prisão em Execução",
    "dataExpedicao": "2026-08-15T03:00:00.000+0000",
    "dataAssinaturaMagistrado": "2026-06-16T11:29:00",
    "descricaoStatus": "Ativo",
    "nomePessoa": "RICARDO DOS SANTOS LUIZ",
    "numeroCpf": "21429396865",
    "numeroProcesso": "00036972120258260077",
    "dataNascimento": "1978-07-28T00:00:00.000+0000",
    "idTipoPeca": 25,
    "idOrgaoJudiciario": 9404,
    "nomeOrgao": "1 VARA CRIMINAL DA COMARCA DE BIRIGUI",
    "numeroPecaAnterior": None,
    "sigiloso": False,
    "agenteExterno": False,
    "siglaTribunal": "TJSP",
    "comarca": "Birigui",
    "medidaCautelares": None,
}

# Item real de /eventos/light-filter.
ITEM_EVENTO = {
    "id": 132116,
    "numeroEvento": "2024130004425402",
    "idTipoEvento": 13,
    "descricaoTipoEvento": "Audiência de Custódia e Análise de Prisão",
    "descricaoStatusEvento": "Encerrado",
    "dataCriacao": "2024-09-09T10:00:00.000+0000",
    "dataEncerramento": None,
    "nomePessoa": "FULANO DE TAL",
    "idOrgaoJudiciario": 9404,
    "agenteExterno": False,
}

# Item real capturado do endpoint /pessoas/filter, reduzido aos campos usados.
ITEM_PESSOA = {
    "id": 195244766,
    "ativo": True,
    "numeroIndividuo": "26734692897",
    "numeroCpf": "41052440860",
    "statusPessoa": {"id": 20, "descricao": "Em acompanhamento de medidas diversas da prisão"},
    "ufCustodia": None,
    "idEstabelecimento": None,
    "pessoaTemPeca": False,
    "possuiDependentes": False,
    "unificada": False,
    "dadosGeraisPessoa": {
        "id": 195709472,
        "nome": "MAYCON WALBER FERREIRA",
        "alcunha": "Não Informado",
        "nomePai": "NÃO INFORMADO",
        "nomeMae": "EFIGENIA LINA DE SOUZA FERREIRA",
        "sexo": {"id": 1, "descricao": "Masculino"},
        "idTribunal": 33,
        "dataNascimento": None,
        "nomeSocial": None,
        "profissao": None,
        "natural": {"id": None, "nome": None, "uf": None},
        "gravidez": False,
        "lactante": False,
        "deficienteFisico": False,
        "dependenteQuimico": False,
        "possuiDoencaGrave": False,
        "escolaridade": None,
        "estadoCivil": {"id": 1, "descricao": "Solteiro"},
        "corRaca": None,
        "paisNascimento": {"nome": None, "id": 1},
        "identificacaoBiometria": {"id": 2, "descricao": "Biometria não coletada"},
    },
    "orgaoJudiciario": {
        "id": 12717,
        "externo": False,
        "nome": "1 VARA JUDICIAL DA COMARCA DE EMBU DAS ARTES",
        "ativo": True,
        "tipo": {"id": 12500, "unidadeJurisdicional": True},
        "municipio": {
            "id": 8868,
            "nome": "EMBU DAS ARTES",
            "uf": {"id": 26, "nome": "São Paulo", "sigla": "SP", "paisId": 1},
            "codIbge": 3515004,
        },
        "orgaoPaiNome": "EMBU DAS ARTES",
        "orgaoTribunal": {
            "id": 33,
            "nome": "Tribunal de Justiça do Estado de São Paulo",
            "sigla": "TJSP",
        },
    },
}


def test_linhas_bnmp_pessoa_item_completo():
    (linha,) = linhas_bnmp_pessoa([ITEM_PESSOA], "teste_sp", 0, "2026-07-27T18:00:00+00:00")

    assert linha["pessoa_id_api"] == 195244766
    assert linha["consulta"] == "teste_sp"
    assert linha["pagina"] == 0
    assert linha["nome"] == "MAYCON WALBER FERREIRA"
    assert linha["sexo_id"] == 1
    assert linha["sexo_descricao"] == "Masculino"
    assert linha["estado_civil_descricao"] == "Solteiro"
    assert linha["status_pessoa_id"] == 20
    assert linha["municipio_cod_ibge"] == 3515004
    assert linha["uf_sigla"] == "SP"
    assert linha["tribunal_sigla"] == "TJSP"
    assert linha["orgao_judiciario_id"] == 12717
    assert linha["orgao_judiciario_tipo_id"] == 12500
    assert linha["pessoa_tem_peca"] == 0
    assert linha["ativo"] == 1


def test_linhas_bnmp_pessoa_tolera_campos_nulos():
    (linha,) = linhas_bnmp_pessoa([ITEM_PESSOA], "teste_sp", 0, "2026-07-27T18:00:00+00:00")

    assert linha["escolaridade_id"] is None
    assert linha["escolaridade_descricao"] is None
    assert linha["cor_raca_descricao"] is None
    assert linha["data_nascimento"] is None
    assert linha["uf_custodia_sigla"] is None
    assert linha["naturalidade_municipio_nome"] is None


def test_linhas_bnmp_pessoa_sem_dados_gerais_nem_orgao():
    item = {"id": 1, "ativo": True}
    (linha,) = linhas_bnmp_pessoa([item], "c", 3, "2026-07-27T18:00:00+00:00")

    assert linha["pessoa_id_api"] == 1
    assert linha["nome"] is None
    assert linha["municipio_id"] is None
    assert linha["tribunal_sigla"] is None


def test_uf_custodia_aceita_string_e_objeto():
    (com_string,) = linhas_bnmp_pessoa([{"id": 1, "ufCustodia": "SP"}], "c", 0, "t")
    (com_objeto,) = linhas_bnmp_pessoa(
        [{"id": 2, "ufCustodia": {"id": 26, "sigla": "SP"}}], "c", 0, "t"
    )

    assert com_string["uf_custodia_sigla"] == "SP"
    assert com_objeto["uf_custodia_sigla"] == "SP"


def test_data_nascimento_iso_com_offset_vira_data():
    item = {"id": 1, "dadosGeraisPessoa": {"dataNascimento": "1985-03-12T00:00:00-03:00"}}
    (linha,) = linhas_bnmp_pessoa([item], "c", 0, "t")

    assert linha["data_nascimento"] == "1985-03-12"


def test_linhas_bnmp_dominio_ignora_chaves_nulas_e_guarda_extras():
    dominios = {
        "acaoHistorico": None,
        "sexos": [{"id": 1, "descricao": "Masculino"}],
        "unidadesFederativa": [{"id": 26, "nome": "São Paulo", "sigla": "SP", "paisId": 1}],
    }

    linhas = linhas_bnmp_dominio(dominios, coletado_em="2026-07-27")

    assert len(linhas) == 2
    sexo = next(linha for linha in linhas if linha["dominio"] == "sexos")
    assert sexo["item_id"] == 1
    assert sexo["descricao"] == "Masculino"
    assert sexo["extras_json"] is None

    uf = next(linha for linha in linhas if linha["dominio"] == "unidadesFederativa")
    assert uf["descricao"] == "São Paulo"
    assert '"sigla": "SP"' in uf["extras_json"]
    assert uf["coletado_em"] == "2026-07-27"


def test_filtro_pessoas_preserva_template_e_aplica_uf():
    filtros = filtro_pessoas(uf_id=26, status_pessoa_id=20)

    assert filtros["estado"] == {"id": 26}
    # a API recusa {"id": n} aqui com 400; o formato aceito é lista de objetos
    assert filtros["statusPessoa"] == [{"id": 20}]
    assert filtros["municipio"] == {}
    assert filtros["tipoPesquisa"] == {"id": 1}
    assert filtros["ativo"] is True
    # o template original não pode ser mutado entre chamadas
    assert filtro_pessoas()["estado"] == {}
    assert filtro_pessoas()["statusPessoa"] is None


def test_filtro_pessoas_multiplos_status_liga_flag():
    filtros = filtro_pessoas(status_pessoa_ids=[20, 21])

    assert filtros["statusPessoa"] == [{"id": 20}, {"id": 21}]
    assert filtros["multiploStatusBusca"] is True


def test_filtro_pecas_com_tipos_peca_ids():
    filtros = filtro_pecas(status_id=4, orgao_expeditor_id=39, tipos_peca_ids=[7, 28, 9, 29],
                           agente_externo=True, judiciario=False)

    assert filtros["status"] == {"id": 4}
    assert filtros["orgaoExpeditor"] == {"id": 39}
    assert filtros["tiposPecaIds"] == [7, 28, 9, 29]
    assert filtros["agenteExterno"] is True
    assert filtros["judiciario"] is False
    assert filtros["tipoMedidaRestritiva"] == {"id": None, "descricao": None}


def test_linhas_bnmp_peca():
    (linha,) = linhas_bnmp_peca([ITEM_PECA], "amostra", 2, "2026-07-27T00:00:00+00:00")

    assert set(linha) == set(COLUNAS_BNMP_PECA)
    assert linha["peca_id_api"] == 207204272
    assert linha["pagina"] == 2
    assert linha["tipo_peca_id"] == 25
    assert linha["data_expedicao"] == "2026-08-15"
    assert linha["data_assinatura_magistrado"] == "2026-06-16"
    assert linha["data_nascimento"] == "1978-07-28"
    assert linha["sigiloso"] == 0
    assert linha["comarca"] == "Birigui"
    assert linha["numero_peca_anterior"] is None
    # campos ausentes do DTO viram None, não KeyError
    assert linha["tipo_guia"] is None


def test_linhas_bnmp_evento():
    (linha,) = linhas_bnmp_evento([ITEM_EVENTO], "amostra", 0, "2026-07-27T00:00:00+00:00")

    assert set(linha) == set(COLUNAS_BNMP_EVENTO)
    assert linha["evento_id_api"] == 132116
    assert linha["tipo_evento_id"] == 13
    assert linha["status_evento_descricao"] == "Encerrado"
    assert linha["data_criacao"] == "2024-09-09"
    assert linha["data_encerramento"] is None
    assert linha["agente_externo"] == 0
    assert linha["observacao"] is None


def test_rotulo_consulta_gera_slug_seguro():
    rotulo = rotulo_consulta("pessoas", uf=26, ativo=True, status=None)

    assert rotulo == "pessoas_ativo-1_uf-26"
    assert "/" not in rotulo

    assert rotulo_consulta("peças", órgão="São Paulo") == "pecas_orgao-sao-paulo"
