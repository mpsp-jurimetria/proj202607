"""Transformações puras da camada silver do BNMP: recebem os JSON do bronze
(dict/list) e devolvem list[dict] prontos para INSERT. Sem rede, sem banco.

A API devolve o mesmo campo ora como null, ora como {} vazio, ora como objeto
preenchido — os helpers defensivos (_id, _descricao, _sigla...) normalizam.
"""

import json
from collections.abc import Callable

# -- Helpers defensivos -------------------------------------------------------


def _id(valor: object) -> int | None:
    if isinstance(valor, dict):
        valor = valor.get("id")
    if isinstance(valor, bool) or not isinstance(valor, (int, str)):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _descricao(valor: object) -> str | None:
    if isinstance(valor, dict):
        valor = valor.get("descricao") or valor.get("nome")
    return valor if isinstance(valor, str) and valor else None


def _sigla(valor: object) -> str | None:
    if isinstance(valor, dict):
        valor = valor.get("sigla")
    return valor if isinstance(valor, str) and valor else None


def _data(valor: object) -> str | None:
    """Reduz um timestamp ISO ("2020-06-05T00:00:00-03:00") à data ("2020-06-05")."""
    if not isinstance(valor, str) or len(valor) < 10:
        return None
    return valor[:10]


def _bit(valor: object) -> int | None:
    if valor is None:
        return None
    return 1 if valor else 0


def _texto(valor: object, tamanho: int) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto[:tamanho] if texto else None


def _obj(valor: object) -> dict:
    return valor if isinstance(valor, dict) else {}


# -- Domínios -----------------------------------------------------------------

COLUNAS_BNMP_DOMINIO = ["dominio", "item_id", "descricao", "ativo", "extras_json", "coletado_em"]

_CHAVES_BASICAS_DOMINIO = {"id", "descricao", "ativo"}


def linhas_bnmp_dominio(dominios: dict, coletado_em: str | None = None) -> list[dict]:
    """Achata as ~90 listas de /dominios em linhas (dominio, item_id, descricao...).

    Chaves nulas são ignoradas; campos além de id/descricao/ativo (sigla,
    paisId, ddi, familiaLinguistica...) vão serializados em extras_json.
    """
    linhas: list[dict] = []
    for dominio, itens in dominios.items():
        if not isinstance(itens, list):
            continue
        for item in itens:
            if not isinstance(item, dict):
                continue
            extras = {
                chave: valor
                for chave, valor in item.items()
                if chave not in _CHAVES_BASICAS_DOMINIO and valor is not None
            }
            linhas.append(
                {
                    "dominio": dominio,
                    "item_id": _id(item),
                    "descricao": _texto(item.get("descricao") or item.get("nome"), 500),
                    "ativo": _bit(item.get("ativo")),
                    "extras_json": json.dumps(extras, ensure_ascii=False) if extras else None,
                    "coletado_em": coletado_em,
                }
            )
    return linhas


# -- Pessoas ------------------------------------------------------------------

COLUNAS_BNMP_PESSOA = [
    "pessoa_id_api",
    "consulta",
    "pagina",
    "coletado_em",
    "ativo",
    "numero_individuo",
    "numero_cpf",
    "status_pessoa_id",
    "status_pessoa_descricao",
    "uf_custodia_sigla",
    "id_estabelecimento",
    "pessoa_tem_peca",
    "possui_dependentes",
    "unificada",
    "dados_gerais_id",
    "nome",
    "nome_social",
    "alcunha",
    "nome_pai",
    "nome_mae",
    "sexo_id",
    "sexo_descricao",
    "data_nascimento",
    "estado_civil_id",
    "estado_civil_descricao",
    "cor_raca_id",
    "cor_raca_descricao",
    "escolaridade_id",
    "escolaridade_descricao",
    "identificacao_biometria_id",
    "identificacao_biometria_descricao",
    "profissao",
    "gravidez",
    "lactante",
    "deficiente_fisico",
    "dependente_quimico",
    "possui_doenca_grave",
    "naturalidade_municipio_nome",
    "naturalidade_uf_sigla",
    "pais_nascimento_id",
    "id_tribunal",
    "orgao_judiciario_id",
    "orgao_judiciario_nome",
    "orgao_judiciario_ativo",
    "orgao_judiciario_externo",
    "orgao_judiciario_tipo_id",
    "orgao_judiciario_pai_nome",
    "municipio_id",
    "municipio_nome",
    "municipio_cod_ibge",
    "uf_id",
    "uf_sigla",
    "uf_nome",
    "tribunal_id",
    "tribunal_sigla",
    "tribunal_nome",
]


def _linhas_planas(
    itens: list[dict],
    mapa: dict[str, tuple[str, Callable[[object], object]]],
    consulta: str,
    pagina: int,
    coletado_em: str,
    chave: str,
) -> list[dict]:
    """Converte itens de DTO plano (peças e eventos) em linhas da silver."""
    linhas: list[dict] = []
    for item in itens:
        linha: dict[str, object] = {
            chave: item.get("id"),
            "consulta": consulta,
            "pagina": pagina,
            "coletado_em": coletado_em,
        }
        for campo_api, (coluna, conversor) in mapa.items():
            linha[coluna] = conversor(item.get(campo_api))
        linhas.append(linha)
    return linhas


# Os endpoints light-filter devolvem DTOs planos, sem objetos aninhados.
_MAPA_PECA: dict[str, tuple[str, Callable[[object], object]]] = {
    "numeroPeca": ("numero_peca", lambda v: _texto(v, 60)),
    "numeroPecaAnterior": ("numero_peca_anterior", lambda v: _texto(v, 60)),
    "idTipoPeca": ("tipo_peca_id", _id),
    "descricaoTipoPeca": ("tipo_peca_descricao", lambda v: _texto(v, 200)),
    "descricaoStatus": ("status_descricao", lambda v: _texto(v, 100)),
    "dataExpedicao": ("data_expedicao", _data),
    "dataAssinaturaMagistrado": ("data_assinatura_magistrado", _data),
    "dataAssinaturaServidor": ("data_assinatura_servidor", _data),
    "dataFimMedida": ("data_fim_medida", _data),
    "nomeCriador": ("nome_criador", lambda v: _texto(v, 200)),
    "nomePessoa": ("nome_pessoa", lambda v: _texto(v, 300)),
    "nomeMae": ("nome_mae", lambda v: _texto(v, 300)),
    "numeroIndividuo": ("numero_individuo", lambda v: _texto(v, 30)),
    "numeroCpf": ("numero_cpf", lambda v: _texto(v, 20)),
    "dataNascimento": ("data_nascimento", _data),
    "numeroProcesso": ("numero_processo", lambda v: _texto(v, 40)),
    "idOrgaoJudiciario": ("orgao_judiciario_id", _id),
    "nomeOrgao": ("orgao_judiciario_nome", lambda v: _texto(v, 300)),
    "siglaTribunal": ("tribunal_sigla", lambda v: _texto(v, 20)),
    "comarca": ("comarca", lambda v: _texto(v, 200)),
    "motivoExpedicao": ("motivo_expedicao", lambda v: _texto(v, 300)),
    "especiePrisao": ("especie_prisao", lambda v: _texto(v, 200)),
    "tipoMedidaRestritiva": ("tipo_medida_restritiva", lambda v: _texto(v, 200)),
    "medidaCautelares": ("medidas_cautelares", lambda v: _texto(v, 1000)),
    "tipoGuia": ("tipo_guia", lambda v: _texto(v, 100)),
    "sigiloso": ("sigiloso", _bit),
    "idSigilo": ("sigilo_id", _id),
    "sigilo": ("sigilo_descricao", lambda v: _texto(v, 200)),
    "agenteExterno": ("agente_externo", _bit),
    "assinadoAgenteExterno": ("assinado_agente_externo", _bit),
    "torcidaOrganizada": ("torcida_organizada", lambda v: _texto(v, 200)),
    "torcidaOrganizadaUf": ("torcida_organizada_uf", lambda v: _texto(v, 5)),
    "torcidaOrganizadaNomeTime": ("torcida_organizada_time", lambda v: _texto(v, 200)),
    "torcidaOrganizadaNomeTorcida": ("torcida_organizada_nome", lambda v: _texto(v, 200)),
}

_MAPA_EVENTO: dict[str, tuple[str, Callable[[object], object]]] = {
    "numeroEvento": ("numero_evento", lambda v: _texto(v, 60)),
    "idTipoEvento": ("tipo_evento_id", _id),
    "descricaoTipoEvento": ("tipo_evento_descricao", lambda v: _texto(v, 200)),
    "descricaoStatusEvento": ("status_evento_descricao", lambda v: _texto(v, 100)),
    "dataCriacao": ("data_criacao", _data),
    "dataAtualizacao": ("data_atualizacao", _data),
    "dataValidacao": ("data_validacao", _data),
    "dataEncerramento": ("data_encerramento", _data),
    "nomePessoa": ("nome_pessoa", lambda v: _texto(v, 300)),
    "nomeMae": ("nome_mae", lambda v: _texto(v, 300)),
    "numeroIndividuo": ("numero_individuo", lambda v: _texto(v, 30)),
    "numeroCpf": ("numero_cpf", lambda v: _texto(v, 20)),
    "numeroProcesso": ("numero_processo", lambda v: _texto(v, 40)),
    "idOrgaoJudiciario": ("orgao_judiciario_id", _id),
    "nomeOrgao": ("orgao_judiciario_nome", lambda v: _texto(v, 300)),
    "idUsuarioCriador": ("usuario_criador_id", _id),
    "nomeUsuarioCriador": ("usuario_criador_nome", lambda v: _texto(v, 200)),
    "idUsuarioValidacao": ("usuario_validacao_id", _id),
    "nomeUsuarioValidacao": ("usuario_validacao_nome", lambda v: _texto(v, 200)),
    "nomeUsuarioAtualizacao": ("usuario_atualizacao_nome", lambda v: _texto(v, 200)),
    "justificativaCancelamento": ("justificativa_cancelamento", lambda v: _texto(v, 2000)),
    "observacao": ("observacao", lambda v: _texto(v, 2000)),
    "agenteExterno": ("agente_externo", _bit),
}

_COLUNAS_COMUNS = ["consulta", "pagina", "coletado_em"]

COLUNAS_BNMP_PECA = ["peca_id_api", *_COLUNAS_COMUNS, *(c for c, _ in _MAPA_PECA.values())]
COLUNAS_BNMP_EVENTO = ["evento_id_api", *_COLUNAS_COMUNS, *(c for c, _ in _MAPA_EVENTO.values())]


def linhas_bnmp_peca(
    itens: list[dict], consulta: str, pagina: int, coletado_em: str
) -> list[dict]:
    """Converte os itens de uma página de /pecas/light-filter em linhas da silver."""
    return _linhas_planas(itens, _MAPA_PECA, consulta, pagina, coletado_em, "peca_id_api")


def linhas_bnmp_evento(
    itens: list[dict], consulta: str, pagina: int, coletado_em: str
) -> list[dict]:
    """Converte os itens de uma página de /eventos/light-filter em linhas da silver."""
    return _linhas_planas(itens, _MAPA_EVENTO, consulta, pagina, coletado_em, "evento_id_api")


def linhas_bnmp_pessoa(
    itens: list[dict], consulta: str, pagina: int, coletado_em: str
) -> list[dict]:
    """Converte os itens de uma página de /pessoas/filter em linhas da silver."""
    linhas: list[dict] = []
    for item in itens:
        dados = _obj(item.get("dadosGeraisPessoa"))
        natural = _obj(dados.get("natural"))
        orgao = _obj(item.get("orgaoJudiciario"))
        municipio = _obj(orgao.get("municipio"))
        uf = _obj(municipio.get("uf"))
        tribunal = _obj(orgao.get("orgaoTribunal"))
        # ufCustodia já foi observada como string ("SP") e como objeto {"sigla": "SP"}
        uf_custodia = item.get("ufCustodia")
        if isinstance(uf_custodia, dict):
            uf_custodia = _sigla(uf_custodia)
        linhas.append(
            {
                "pessoa_id_api": item.get("id"),
                "consulta": consulta,
                "pagina": pagina,
                "coletado_em": coletado_em,
                "ativo": _bit(item.get("ativo")),
                "numero_individuo": _texto(item.get("numeroIndividuo"), 30),
                "numero_cpf": _texto(item.get("numeroCpf"), 20),
                "status_pessoa_id": _id(item.get("statusPessoa")),
                "status_pessoa_descricao": _texto(_descricao(item.get("statusPessoa")), 200),
                "uf_custodia_sigla": _texto(uf_custodia, 5),
                "id_estabelecimento": _id(item.get("idEstabelecimento")),
                "pessoa_tem_peca": _bit(item.get("pessoaTemPeca")),
                "possui_dependentes": _bit(item.get("possuiDependentes")),
                "unificada": _bit(item.get("unificada")),
                "dados_gerais_id": dados.get("id"),
                "nome": _texto(dados.get("nome"), 300),
                "nome_social": _texto(dados.get("nomeSocial"), 300),
                "alcunha": _texto(dados.get("alcunha"), 300),
                "nome_pai": _texto(dados.get("nomePai"), 300),
                "nome_mae": _texto(dados.get("nomeMae"), 300),
                "sexo_id": _id(dados.get("sexo")),
                "sexo_descricao": _texto(_descricao(dados.get("sexo")), 50),
                "data_nascimento": _data(dados.get("dataNascimento")),
                "estado_civil_id": _id(dados.get("estadoCivil")),
                "estado_civil_descricao": _texto(_descricao(dados.get("estadoCivil")), 100),
                "cor_raca_id": _id(dados.get("corRaca")),
                "cor_raca_descricao": _texto(_descricao(dados.get("corRaca")), 100),
                "escolaridade_id": _id(dados.get("escolaridade")),
                "escolaridade_descricao": _texto(_descricao(dados.get("escolaridade")), 150),
                "identificacao_biometria_id": _id(dados.get("identificacaoBiometria")),
                "identificacao_biometria_descricao": _texto(
                    _descricao(dados.get("identificacaoBiometria")), 150
                ),
                "profissao": _texto(dados.get("profissao"), 200),
                "gravidez": _bit(dados.get("gravidez")),
                "lactante": _bit(dados.get("lactante")),
                "deficiente_fisico": _bit(dados.get("deficienteFisico")),
                "dependente_quimico": _bit(dados.get("dependenteQuimico")),
                "possui_doenca_grave": _bit(dados.get("possuiDoencaGrave")),
                "naturalidade_municipio_nome": _texto(natural.get("nome"), 200),
                "naturalidade_uf_sigla": _texto(natural.get("uf"), 5),
                "pais_nascimento_id": _id(dados.get("paisNascimento")),
                "id_tribunal": _id(dados.get("idTribunal")),
                "orgao_judiciario_id": _id(orgao),
                "orgao_judiciario_nome": _texto(orgao.get("nome"), 300),
                "orgao_judiciario_ativo": _bit(orgao.get("ativo")),
                "orgao_judiciario_externo": _bit(orgao.get("externo")),
                "orgao_judiciario_tipo_id": _id(orgao.get("tipo")),
                "orgao_judiciario_pai_nome": _texto(orgao.get("orgaoPaiNome"), 300),
                "municipio_id": _id(municipio),
                "municipio_nome": _texto(municipio.get("nome"), 200),
                "municipio_cod_ibge": _id(municipio.get("codIbge")),
                "uf_id": _id(uf),
                "uf_sigla": _texto(uf.get("sigla"), 5),
                "uf_nome": _texto(uf.get("nome"), 100),
                "tribunal_id": _id(tribunal),
                "tribunal_sigla": _texto(tribunal.get("sigla"), 20),
                "tribunal_nome": _texto(tribunal.get("nome"), 300),
            }
        )
    return linhas
