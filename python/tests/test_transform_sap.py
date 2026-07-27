import pytest

from src.modulos.sap.transform import COLUNAS_SAP_UNIDADE, linhas_sap_unidade

_CABECALHO = [
    "Ano", "Unidade Prisional", "nome_mun", "regional", "cod_muni", "custodia",
    "comarca", "nome_raj", "Destinação da unidade Prisional",
    "Facções existentes na unidade prisional (nomes)", "Número de Servidores",
    "Número de Policiais Penais", "Número de Presos",
    "Capacidade da Unidade Prisional", "superlotacao_percentual",
    "Mortes naturais no trimestre", "Mortes por intervenção de terceiros",
    "Morte Indeterminada / Suicídio", "Providências tomadas", "DEECRIM",
    "Médico", "Dentista", "Psicólogo", "Assistente Social", "Psquiatra",
    "Número de Presos que estudam", "Número de presos que trabalham", "genero",
]


def _linha(**kwargs) -> tuple:
    base = {
        "Ano": 2026, "Unidade Prisional": "CDP de Aguaí", "nome_mun": "Aguaí",
        "regional": "Campinas", "cod_muni": "3500303", "custodia": "exclusiva",
        "comarca": "AGUAÍ", "nome_raj": "CAMPINAS",
        "Destinação da unidade Prisional": "CDP", "Facções existentes na unidade prisional (nomes)": "Comum",
        "Número de Servidores": 2, "Número de Policiais Penais": 169,
        "Número de Presos": "1727", "Capacidade da Unidade Prisional": "823",
        "superlotacao_percentual": None, "Mortes naturais no trimestre": 0,
        "Mortes por intervenção de terceiros": 0, "Morte Indeterminada / Suicídio": None,
        "Providências tomadas": "Prejudicado", "DEECRIM": "DEECRIM 4ª RAJ",
        "Médico": 1, "Dentista": "1", "Psicólogo": 0, "Assistente Social": 0,
        "Psquiatra": 0, "Número de Presos que estudam": "92",
        "Número de presos que trabalham": "96", "genero": "Masculino",
    }
    base.update(kwargs)
    return tuple(base[coluna] for coluna in _CABECALHO)


def test_linha_vira_dict_tipado():
    registros = linhas_sap_unidade(_CABECALHO, [_linha()])

    assert len(registros) == 1
    registro = registros[0]
    assert set(registro) == set(COLUNAS_SAP_UNIDADE)
    assert registro["unidade_nome"] == "CDP de Aguaí"
    assert registro["municipio"] == "Aguaí"
    assert registro["cod_ibge"] == 3500303  # string na planilha, int na tabela
    assert registro["presos"] == 1727
    assert registro["dentistas"] == 1
    assert registro["raj"] == "CAMPINAS"


def test_texto_nao_numerico_em_coluna_inteira_vira_none():
    registros = linhas_sap_unidade(_CABECALHO, [_linha(**{"Número de Presos": "Prejudicado"})])
    assert registros[0]["presos"] is None


def test_linhas_sem_nome_de_unidade_sao_ignoradas():
    registros = linhas_sap_unidade(_CABECALHO, [_linha(), tuple([None] * len(_CABECALHO))])
    assert len(registros) == 1


def test_unidade_duplicada_levanta_erro():
    with pytest.raises(ValueError, match="duplicada"):
        linhas_sap_unidade(_CABECALHO, [_linha(), _linha()])


def test_coluna_ausente_levanta_erro():
    cabecalho_incompleto = [c for c in _CABECALHO if c != "nome_mun"]
    with pytest.raises(ValueError, match="nome_mun"):
        linhas_sap_unidade(cabecalho_incompleto, [])


def test_cabecalho_fora_de_ordem_e_tolerado():
    invertido = list(reversed(_CABECALHO))
    linha_invertida = tuple(reversed(_linha()))
    registros = linhas_sap_unidade(invertido, [linha_invertida])
    assert registros[0]["unidade_nome"] == "CDP de Aguaí"


def test_depara_referencia_apenas_unidades_da_planilha():
    """O de-para curado deve apontar para nomes que existem na planilha local
    (quando presente); um nome errado geraria NULL silencioso no gold."""
    import openpyxl

    from pathlib import Path

    from src.modulos.sap.depara_unidades import DEPARA

    planilha = Path(__file__).resolve().parent.parent / "downloads/sap/sap_nova_corrigida.xlsx"
    if not planilha.exists():
        pytest.skip("planilha local ausente")

    ws = openpyxl.load_workbook(planilha, read_only=True)["Sheet1"]
    nomes = {linha[1] for linha in ws.iter_rows(min_row=2, values_only=True) if linha[1]}
    fora = {nome for nome in DEPARA.values() if nome not in nomes}
    assert not fora, f"nomes do de-para ausentes da planilha: {sorted(fora)[:5]}"
