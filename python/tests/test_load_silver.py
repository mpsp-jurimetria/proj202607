from src.modulos.cnmp.etl.load_silver import _csv_valor


def test_csv_valor_none_vira_campo_vazio_sem_aspas():
    assert _csv_valor(None) == ""


def test_csv_valor_string_vazia_vira_aspas_vazias():
    assert _csv_valor("") == '""'


def test_csv_valor_numero_sem_aspas():
    assert _csv_valor(123) == "123"


def test_csv_valor_string_comum_entre_aspas():
    assert _csv_valor("Sim") == '"Sim"'


def test_csv_valor_escapa_aspas_internas():
    assert _csv_valor('Texto "citado"') == '"Texto ""citado"""'


def test_csv_valor_preserva_virgula_e_quebra_de_linha_dentro_das_aspas():
    assert _csv_valor("a, b\nc") == '"a, b\nc"'
