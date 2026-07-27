from src.modulos.bnmp.etl.transform_silver import linhas_bnmp_dominio, linhas_bnmp_pessoa
from src.modulos.bnmp.filtros import filtro_pecas, filtro_pessoas, rotulo_consulta

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


def test_rotulo_consulta_gera_slug_seguro():
    rotulo = rotulo_consulta("pessoas", uf=26, ativo=True, status=None)

    assert rotulo == "pessoas_ativo-1_uf-26"
    assert "/" not in rotulo

    assert rotulo_consulta("peças", órgão="São Paulo") == "pecas_orgao-sao-paulo"
