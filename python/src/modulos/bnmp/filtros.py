"""Construtores de filtros para as consultas da API do BNMP 2.0.

Os templates reproduzem literalmente os corpos enviados pelo frontend
(capturados no HAR): objeto vazio {} significa "sem filtro" para o backend,
e parâmetro preenchido vira {"id": valor}. Funções puras, sem rede.
"""

import copy
import re
import unicodedata

FILTRO_PESSOAS_BASE: dict = {
    "sexo": {},
    "pessoa": {},
    "documento": {"tipoDocumento": {}},
    "statusPessoa": None,
    "identificacaoBiometria": [],
    "estado": {},
    "municipio": {},
    "ufCustodia": {},
    "municipioCustodia": {},
    "tipoPesquisa": {"id": 1},
    "orgao": {},
    "buscaOrgaoRecursivo": False,
    "ativo": True,
    "unidadePrisional": None,
    "statusPessoaUnico": None,
    "statusPessoaIds": None,
    "multiploStatusBusca": False,
}

FILTRO_PECAS_BASE: dict = {
    "tipoPeca": {},
    "status": {},
    "orgaoExpeditor": {},
    "tipoDocumento": {},
    "sexo": {},
    "buscaOrgaoRecursivo": True,
    "motivosExpedicao": [],
    "especiesPrisao": [],
    "tipoMedidaRestritiva": {"id": None, "descricao": None},
    "medidaCautelares": [],
}

FILTRO_EVENTOS_BASE: dict = {
    "tipoEvento": {},
    "statusEvento": {},
    "tipoDocumento": {},
    "usuarioCriador": {},
    "orgaoJudiciario": {},
    "buscaOrgaoRecursivo": True,
    "pessoaAtiva": True,
}


def _com_id(valor: int | None) -> dict:
    return {"id": valor} if valor is not None else {}


def filtro_pessoas(
    ativo: bool = True,
    uf_id: int | None = None,
    municipio_id: int | None = None,
    uf_custodia_id: int | None = None,
    municipio_custodia_id: int | None = None,
    orgao_id: int | None = None,
    busca_orgao_recursivo: bool = False,
    status_pessoa_id: int | None = None,
    status_pessoa_ids: list[int] | None = None,
    unidade_prisional_id: int | None = None,
    sexo_id: int | None = None,
    tipo_pesquisa_id: int = 1,
) -> dict:
    filtros = copy.deepcopy(FILTRO_PESSOAS_BASE)
    filtros["ativo"] = ativo
    filtros["estado"] = _com_id(uf_id)
    filtros["municipio"] = _com_id(municipio_id)
    filtros["ufCustodia"] = _com_id(uf_custodia_id)
    filtros["municipioCustodia"] = _com_id(municipio_custodia_id)
    filtros["orgao"] = _com_id(orgao_id)
    filtros["buscaOrgaoRecursivo"] = busca_orgao_recursivo
    filtros["sexo"] = _com_id(sexo_id)
    filtros["tipoPesquisa"] = {"id": tipo_pesquisa_id}
    # statusPessoa é uma LISTA de objetos: {"id": n} é recusado com 400, e os
    # campos statusPessoaIds/statusPessoaUnico do payload do frontend são
    # ignorados pelo backend (retornam o total sem filtro).
    ids_status = list(status_pessoa_ids or [])
    if status_pessoa_id is not None:
        ids_status.append(status_pessoa_id)
    if ids_status:
        filtros["statusPessoa"] = [{"id": item} for item in ids_status]
        filtros["multiploStatusBusca"] = len(ids_status) > 1
    if unidade_prisional_id is not None:
        filtros["unidadePrisional"] = {"id": unidade_prisional_id}
    return filtros


def filtro_pecas(
    status_id: int | None = None,
    orgao_expeditor_id: int | None = None,
    busca_orgao_recursivo: bool = True,
    tipo_peca_id: int | None = None,
    tipos_peca_ids: list[int] | None = None,
    tipo_documento_id: int | None = None,
    sexo_id: int | None = None,
    motivos_expedicao: list[int] | None = None,
    especies_prisao: list[int] | None = None,
    tipo_medida_restritiva_id: int | None = None,
    medidas_cautelares: list[int] | None = None,
    judiciario: bool | None = None,
    agente_externo: bool | None = None,
) -> dict:
    filtros = copy.deepcopy(FILTRO_PECAS_BASE)
    filtros["status"] = _com_id(status_id)
    filtros["orgaoExpeditor"] = _com_id(orgao_expeditor_id)
    filtros["buscaOrgaoRecursivo"] = busca_orgao_recursivo
    filtros["tipoPeca"] = _com_id(tipo_peca_id)
    filtros["tipoDocumento"] = _com_id(tipo_documento_id)
    filtros["sexo"] = _com_id(sexo_id)
    if tipos_peca_ids:
        filtros["tiposPecaIds"] = tipos_peca_ids
    if motivos_expedicao:
        filtros["motivosExpedicao"] = motivos_expedicao
    if especies_prisao:
        filtros["especiesPrisao"] = especies_prisao
    if tipo_medida_restritiva_id is not None:
        filtros["tipoMedidaRestritiva"] = {"id": tipo_medida_restritiva_id, "descricao": None}
    if medidas_cautelares:
        filtros["medidaCautelares"] = medidas_cautelares
    if judiciario is not None:
        filtros["judiciario"] = judiciario
    if agente_externo is not None:
        filtros["agenteExterno"] = agente_externo
    return filtros


def filtro_eventos(
    tipo_evento_id: int | None = None,
    status_evento_id: int | None = None,
    tipo_documento_id: int | None = None,
    usuario_criador_id: int | None = None,
    orgao_judiciario_id: int | None = None,
    busca_orgao_recursivo: bool = True,
    pessoa_ativa: bool = True,
    agente_externo: bool | None = None,
) -> dict:
    filtros = copy.deepcopy(FILTRO_EVENTOS_BASE)
    filtros["tipoEvento"] = _com_id(tipo_evento_id)
    filtros["statusEvento"] = _com_id(status_evento_id)
    filtros["tipoDocumento"] = _com_id(tipo_documento_id)
    filtros["usuarioCriador"] = _com_id(usuario_criador_id)
    filtros["orgaoJudiciario"] = _com_id(orgao_judiciario_id)
    filtros["buscaOrgaoRecursivo"] = busca_orgao_recursivo
    filtros["pessoaAtiva"] = pessoa_ativa
    if agente_externo is not None:
        filtros["agenteExterno"] = agente_externo
    return filtros


def rotulo_consulta(recurso: str, **partes: object) -> str:
    """Gera um slug determinístico e seguro para caminho no Lakehouse.

    Exemplo: rotulo_consulta("pessoas", uf=26, ativo=True) -> "pessoas_uf-26_ativo-1".
    Só emite [a-z0-9_-]; ignora partes com valor None.
    """
    pedacos = [_slug(recurso)]
    for chave in sorted(partes):
        valor = partes[chave]
        if valor is None:
            continue
        if isinstance(valor, bool):
            valor = int(valor)
        if isinstance(valor, (list, tuple)):
            valor = "-".join(str(item) for item in valor)
        pedacos.append(f"{_slug(chave)}-{_slug(str(valor))}")
    return "_".join(pedacos)


def _slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9-]+", "-", sem_acento.lower()).strip("-")
