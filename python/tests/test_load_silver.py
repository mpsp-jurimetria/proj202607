from src.modulos.cnmp.etl.load_silver import csv_valor


def testcsv_valor_none_vira_campo_vazio_sem_aspas():
    assert csv_valor(None) == ""


def testcsv_valor_string_vazia_vira_aspas_vazias():
    assert csv_valor("") == '""'


def testcsv_valor_numero_sem_aspas():
    assert csv_valor(123) == "123"


def testcsv_valor_string_comum_entre_aspas():
    assert csv_valor("Sim") == '"Sim"'


def testcsv_valor_escapa_aspas_internas():
    assert csv_valor('Texto "citado"') == '"Texto ""citado"""'


def testcsv_valor_preserva_virgula_e_quebra_de_linha_dentro_das_aspas():
    assert csv_valor("a, b\nc") == '"a, b\nc"'
