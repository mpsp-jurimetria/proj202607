import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_BASE_PRODUCAO = "https://sistemaresolucoes.cnmp.mp.br/seam/resource/rest"
_BASE_HOMOLOGACAO = "https://homologacaoeapext.cnmp.mp.br/resolucoes/seam/resource/rest"


class CnmpClient:
    """Cliente HTTP para o webservice do Sistema de Resoluções (CNMP).

    Autenticação: HTTP Basic Auth com usuário de perfil "Web Service".
    Para solicitar credenciais: sistemasresolucoes@cnmp.mp.br
    """

    def __init__(self, homologacao: bool = False) -> None:
        usuario = os.getenv("CNMP_USER")
        senha = os.getenv("CNMP_PASSWORD")
        if not usuario or not senha:
            raise ValueError("CNMP_USER e CNMP_PASSWORD devem estar definidos no .env")

        base_url = _BASE_HOMOLOGACAO if homologacao else _BASE_PRODUCAO
        self._client = httpx.Client(
            base_url=base_url,
            auth=(usuario, senha),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )
        logger.info("CnmpClient iniciado — base_url=%s", base_url)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, body: Any) -> Any:
        response = self._client.post(path, json=body)
        response.raise_for_status()
        return response.json()

    # -- Formulários ----------------------------------------------------------

    def formularios(
        self,
        id_ambiente: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {}
        if id_ambiente is not None:
            params["ambiente"] = id_ambiente
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        return self._get("/formularios", params)

    def detalhe_formulario(self, id_formulario: int) -> dict:
        return self._get(f"/formularios/{id_formulario}")

    # -- Entidades ------------------------------------------------------------

    def entidades(
        self,
        id_formulario: int | None = None,
        id_ambiente: int | None = None,
        nome: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {}
        if id_formulario is not None:
            params["formulario"] = id_formulario
        if id_ambiente is not None:
            params["ambiente"] = id_ambiente
        if nome is not None:
            params["nome"] = nome
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        return self._get("/entidades", params)

    # -- Cadastradores --------------------------------------------------------

    def cadastradores(
        self,
        id_formulario: int | None = None,
        id_ambiente: int | None = None,
        cpf: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {}
        if id_formulario is not None:
            params["formulario"] = id_formulario
        if id_ambiente is not None:
            params["ambiente"] = id_ambiente
        if cpf is not None:
            params["cpf"] = cpf
        return self._get("/cadastradores", params)

    # -- Ambientes ------------------------------------------------------------

    def ambientes(self) -> list[dict]:
        return self._get("/ambientes")

    # -- Tipos de entidades ---------------------------------------------------

    def tipos_entidades(self, id_ambiente: int) -> list[dict]:
        return self._get("/tiposEntidades", {"ambiente": id_ambiente})

    # -- Instâncias -----------------------------------------------------------

    def instancias(self, id_formulario: int, id_entidade: int) -> list[dict]:
        return self._get("/instancias", {"formulario": id_formulario, "entidade": id_entidade})

    def detalhe_instancia(self, id_instancia: int) -> dict:
        return self._get(f"/instancias/{id_instancia}")

    def salvar_instancia(self, dados: dict) -> dict:
        return self._post("/instancias", dados)

    def solicitar_retificacao(self, id_instancia: int, dados: dict) -> dict:
        return self._post(f"/instancias/retificacao/{id_instancia}", dados)

    # -- Histórico ------------------------------------------------------------

    def historico(
        self,
        id_formulario: int | None = None,
        id_ambiente: int | None = None,
        id_maior_que: int | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        perfil_inicial: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {}
        if id_formulario is not None:
            params["formulario"] = id_formulario
        if id_ambiente is not None:
            params["ambiente"] = id_ambiente
        if id_maior_que is not None:
            params["idMaiorQue"] = id_maior_que
        if data_inicio is not None:
            params["dataInicio"] = data_inicio
        if data_fim is not None:
            params["dataFim"] = data_fim
        if perfil_inicial is not None:
            params["perfilInicial"] = perfil_inicial
        return self._get("/historico", params)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CnmpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
