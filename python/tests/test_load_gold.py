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
    ddl, insert_base, updates = _construir_pivot(1322, campos)

    assert "DROP TABLE IF EXISTS fato_visita_1322;" in ddl
    assert "c30133_data_da_visita DATE NULL" in ddl
    assert "c30170_capacidade_total DECIMAL(18, 2) NULL" in ddl

    assert "WHERE formulario_id_api = 1322;" in insert_base
    assert "c30133_data_da_visita" not in insert_base  # insert base não inclui colunas de campo

    assert len(updates) == 1
    assert "t.c30133_data_da_visita = r30133.valor_data" in updates[0]
    assert "t.c30170_capacidade_total = r30170.valor_numero" in updates[0]
    assert f"FROM fato_visita_1322 t" in updates[0]


def test_construir_pivot_radio_resolve_via_dim_campo_opcao():
    campos = [{"campo_id_api": 30134, "label": "1.2 Período:", "tipo_campo": "RADIO"}]
    _, _, updates = _construir_pivot(1322, campos)

    assert "LEFT JOIN dim_campo_opcao o30134" in updates[0]
    assert "t.c30134_periodo = COALESCE(o30134.descricao, r30134.valor_texto)" in updates[0]


def test_construir_pivot_sem_campos_gera_tabela_so_com_colunas_base():
    ddl, insert_base, updates = _construir_pivot(999, [])

    assert "status_atual VARCHAR(100) NULL\n);" in ddl
    assert "SELECT instancia_id_api, entidade_id_api, ano, periodo, status_atual\n" in insert_base
    assert updates == []


def test_construir_pivot_nao_declara_primary_key():
    """Fabric Warehouse rejeita PRIMARY KEY mesmo como NONCLUSTERED NOT ENFORCED."""
    campos = [{"campo_id_api": 30133, "label": "1.1 Data:", "tipo_campo": "DATA"}]
    ddl, _, _ = _construir_pivot(1322, campos)

    assert "instancia_id_api INT NOT NULL" in ddl
    assert "PRIMARY KEY" not in ddl


def test_construir_pivot_divide_em_lotes_para_evitar_erro_8621():
    """Query com muitos LEFT JOINs numa query só deu erro 8621 (stack space)
    em produção para formulários grandes — confirma que campos são divididos
    em múltiplos UPDATEs em vez de 1 INSERT com centenas de JOINs."""
    campos = [
        {"campo_id_api": 30000 + i, "label": f"Campo {i}:", "tipo_campo": "TEXTO"}
        for i in range(95)
    ]
    _, _, updates = _construir_pivot(1322, campos, colunas_por_lote=40)

    assert len(updates) == 3
    assert updates[0].count("LEFT JOIN fato_resposta_tipada") == 40
    assert updates[1].count("LEFT JOIN fato_resposta_tipada") == 40
    assert updates[2].count("LEFT JOIN fato_resposta_tipada") == 15
