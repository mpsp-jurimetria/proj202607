import pytest

from src.modulos.cnmp.etl.aliases_campos import ALIASES
from src.modulos.cnmp.etl.load_gold import (
    _ALIAS_VALIDO,
    _COLUNAS_BASE,
    DDL_GOLD,
    _construir_pivot,
    _construir_tabela_campos,
    _erro_linha_grande,
    _nome_coluna,
    _slug,
    _sql_dim_unidade,
    _validar_nomes_colunas,
)


def test_slug_remove_numeracao_e_normaliza():
    assert _slug("13.11.2 Cocaína:") == "cocaina"
    assert _slug("1.1 Data da visita:") == "data_da_visita"


def test_slug_label_vazio_cai_no_fallback():
    assert _slug("12.3") == "campo"


def test_nome_coluna_sem_alias_prefixa_com_campo_id():
    campo = {"campo_id_api": 30133, "label": "1.1 Data da visita:"}
    assert _nome_coluna(campo) == "c30133_data_da_visita"


def test_nome_coluna_usa_alias_quando_presente():
    campo = {"campo_id_api": 30133, "label": "1.1 Data da visita:", "alias": "data_visita"}
    assert _nome_coluna(campo) == "data_visita"


def test_validar_nomes_colunas_rejeita_alias_invalido():
    campos = [{"campo_id_api": 1, "label": "x", "tipo_campo": "TEXTO", "alias": "1_comeca_com_digito"}]
    with pytest.raises(ValueError, match="identificador válido"):
        _validar_nomes_colunas(1322, campos)


def test_validar_nomes_colunas_rejeita_colisao_com_coluna_base():
    campos = [{"campo_id_api": 1, "label": "Ano:", "tipo_campo": "TEXTO", "alias": "ano"}]
    with pytest.raises(ValueError, match="coluna base"):
        _validar_nomes_colunas(1322, campos)


def test_validar_nomes_colunas_rejeita_alias_duplicado():
    campos = [
        {"campo_id_api": 1, "label": "a", "tipo_campo": "TEXTO", "alias": "capacidade"},
        {"campo_id_api": 2, "label": "b", "tipo_campo": "TEXTO", "alias": "capacidade"},
    ]
    with pytest.raises(ValueError, match="mesma coluna"):
        _validar_nomes_colunas(1322, campos)


def test_validar_nomes_colunas_aceita_mistura_de_alias_e_fallback():
    campos = [
        {"campo_id_api": 1, "label": "1.1 Data da visita:", "tipo_campo": "DATA", "alias": "data_visita"},
        {"campo_id_api": 2, "label": "1.2 Período:", "tipo_campo": "RADIO", "alias": None},
    ]
    _validar_nomes_colunas(1322, campos)  # não levanta


def test_aliases_curados_sao_validos_e_unicos_por_formulario():
    """Garante que edições manuais em aliases_campos.py não introduzam
    aliases inválidos, duplicados ou colidindo com colunas base."""
    for formulario_id, aliases in ALIASES.items():
        campos = [
            {"campo_id_api": campo_id, "label": "", "tipo_campo": "TEXTO", "alias": alias}
            for campo_id, alias in aliases.items()
        ]
        _validar_nomes_colunas(formulario_id, campos)
        for alias in aliases.values():
            assert _ALIAS_VALIDO.match(alias)
            assert alias not in _COLUNAS_BASE


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


def test_construir_tabela_campos_parte_nao_inclui_colunas_base():
    """Tabela 'parte' (fato_visita_{id}_p2, _p3...) só tem instancia_id_api
    como chave de junção — entidade_id_api/ano/periodo/status já estão na
    tabela principal, repeti-los não ajudaria."""
    campos = [{"campo_id_api": 30133, "label": "1.1 Data:", "tipo_campo": "DATA"}]
    ddl, insert_base, _ = _construir_tabela_campos(
        "fato_visita_1462_p2", 1462, campos, incluir_base=False, colunas_por_lote=40
    )

    assert "instancia_id_api INT NOT NULL" in ddl
    assert "entidade_id_api" not in ddl
    assert "INSERT INTO fato_visita_1462_p2 (instancia_id_api)" in insert_base


def test_ddl_dim_unidade_tem_colunas_sap():
    for coluna in ("municipio", "cod_ibge", "regional", "raj", "comarca"):
        assert coluna in DDL_GOLD
    assert "dim_unidade_sap" in DDL_GOLD


def test_sql_dim_unidade_com_sap_faz_left_join():
    sql = _sql_dim_unidade("mp_silver", com_sap=True)
    assert "LEFT JOIN dim_unidade_sap" in sql
    assert "LEFT JOIN mp_silver.dbo.sap_unidade" in sql
    assert "SELECT DISTINCT" in sql
    assert "s.municipio" in sql


def test_sql_dim_unidade_sem_sap_carrega_so_colunas_cnmp():
    sql = _sql_dim_unidade("mp_silver", com_sap=False)
    assert "sap_unidade" not in sql
    assert "SELECT DISTINCT entidade_id_api" in sql


def test_depara_tem_entidades_unicas_e_nomes_nao_vazios():
    from src.modulos.sap.depara_unidades import DEPARA

    assert DEPARA, "de-para vazio"
    for entidade_id, nome in DEPARA.items():
        assert isinstance(entidade_id, int)
        assert isinstance(nome, str) and nome.strip()


def test_erro_linha_grande_detecta_mensagem_do_sql_server():
    erro = Exception(
        "Cannot create a row of size 8080 which is greater than the allowable maximum row size of 8060."
    )
    assert _erro_linha_grande(erro) is True


def test_erro_linha_grande_nao_confunde_com_outros_erros():
    assert _erro_linha_grande(Exception("query processor ran out of stack space")) is False
