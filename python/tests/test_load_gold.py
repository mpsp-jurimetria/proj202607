from src.modulos.cnmp.etl.load_gold import _construir_pivot, _nome_coluna, _slug


def test_slug_remove_numeracao_e_normaliza():
    assert _slug("13.11.2 Cocaína:") == "cocaina"
    assert _slug("1.1 Data da visita:") == "data_da_visita"


def test_slug_label_vazio_cai_no_fallback():
    assert _slug("12.3") == "campo"


def test_nome_coluna_prefixa_com_campo_id():
    assert _nome_coluna(30133, "1.1 Data da visita:") == "c30133_data_da_visita"


def test_construir_pivot_gera_ddl_com_uma_coluna_por_campo():
    campos = [
        {"campo_id_api": 30133, "label": "1.1 Data da visita:", "tipo_campo": "DATA"},
        {"campo_id_api": 30170, "label": "2.1 Capacidade total:", "tipo_campo": "SOMENTE_NUMERO"},
    ]
    ddl, insert = _construir_pivot(1322, campos)

    assert "DROP TABLE IF EXISTS fato_visita_1322;" in ddl
    assert "c30133_data_da_visita DATE NULL" in ddl
    assert "c30170_capacidade_total DECIMAL(18, 2) NULL" in ddl

    assert "r30133.valor_data AS c30133_data_da_visita" in insert
    assert "r30170.valor_numero AS c30170_capacidade_total" in insert
    assert "WHERE v.formulario_id_api = 1322;" in insert


def test_construir_pivot_radio_resolve_via_dim_campo_opcao():
    campos = [{"campo_id_api": 30134, "label": "1.2 Período:", "tipo_campo": "RADIO"}]
    ddl, insert = _construir_pivot(1322, campos)

    assert "LEFT JOIN dim_campo_opcao o30134" in insert
    assert "COALESCE(o30134.descricao, r30134.valor_texto) AS c30134_periodo" in insert


def test_construir_pivot_sem_campos_gera_tabela_so_com_colunas_base():
    ddl, insert = _construir_pivot(999, [])

    assert "status_atual VARCHAR(100) NULL\n);" in ddl
    assert "SELECT v.instancia_id_api, v.entidade_id_api, v.ano, v.periodo, v.status_atual\n" in insert


def test_construir_pivot_nao_declara_primary_key():
    """Fabric Warehouse rejeita PRIMARY KEY mesmo como NONCLUSTERED NOT ENFORCED."""
    campos = [{"campo_id_api": 30133, "label": "1.1 Data:", "tipo_campo": "DATA"}]
    ddl, _ = _construir_pivot(1322, campos)

    assert "instancia_id_api INT NOT NULL" in ddl
    assert "PRIMARY KEY" not in ddl
