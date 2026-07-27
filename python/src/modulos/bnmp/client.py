"""Cliente HTTP para a API do BNMP 2.0 (https://bnmp.pdpj.jus.br/v2/api).

Autenticação: SSO do PJe (Keycloak) com usuário, senha e TOTP — ver auth.py.
Toda requisição leva Bearer token, o header x-orgao-ativo (39 = MPSP) e um
x-correlation-id novo, espelhando o comportamento do frontend.
"""

import logging
import os
import random
import time
import uuid
from collections.abc import Callable, Iterator
from typing import Any

import httpx
from dotenv import load_dotenv

from src.modulos.bnmp import auth

load_dotenv()

logger = logging.getLogger(__name__)

_BASE_API = "https://bnmp.pdpj.jus.br/v2/api"
_ORGAO_ATIVO_PADRAO = "39"  # Ministério Público do Estado de São Paulo
_MAX_TENTATIVAS = 5


class BnmpClient:
    """Cliente autenticado do BNMP 2.0, com renovação automática de sessão.

    O access_token e o refresh_token expiram juntos em ~8h; quando ambos
    expiram no meio de uma coleta longa, o cliente refaz o login completo
    (usuário + senha + TOTP) sem intervenção.
    """

    def __init__(
        self,
        orgao_ativo: str | None = None,
        timeout: float = 60.0,
        intervalo_minimo: float = 0.3,
    ) -> None:
        self._usuario = os.getenv("BNMP_USER")
        self._senha = os.getenv("BNMP_PASSWORD")
        self._segredo_otp = os.getenv("BNMP_OTP_SECRET")
        if not self._usuario or not self._senha:
            raise ValueError("BNMP_USER e BNMP_PASSWORD devem estar definidos no .env")

        self._orgao_ativo = orgao_ativo or os.getenv("BNMP_ORGAO_ATIVO", _ORGAO_ATIVO_PADRAO)
        self._intervalo_minimo = intervalo_minimo
        self._ultima_requisicao = 0.0
        self._token: auth.Token | None = None
        self._userid: str | None = None
        self._client = httpx.Client(
            base_url=_BASE_API,
            timeout=timeout,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://bnmp.pdpj.jus.br",
                "Referer": "https://bnmp.pdpj.jus.br/pagina-inicial",
                "User-Agent": auth._USER_AGENT,
                "x-orgao-ativo": self._orgao_ativo,
            },
        )
        logger.info("BnmpClient iniciado — orgao_ativo=%s", self._orgao_ativo)

    # -- Sessão ---------------------------------------------------------------

    def _garantir_token(self) -> str:
        if self._token is None or self._token.expirado:
            if self._token is not None:
                try:
                    self._token = auth.renovar(self._token)
                except httpx.HTTPStatusError:
                    logger.info("Refresh token expirado — refazendo o login completo")
                    self._token = None
            if self._token is None:
                self._token = auth.autenticar(self._usuario, self._senha, self._segredo_otp)
        return self._token.access_token

    def _relogar(self) -> str:
        self._token = None
        return self._garantir_token()

    # -- Requisições ----------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._garantir_token()}",
            "x-correlation-id": str(uuid.uuid4()),
        }
        if self._userid:
            headers["userid"] = self._userid
        return headers

    def _aguardar_intervalo(self) -> None:
        decorrido = time.monotonic() - self._ultima_requisicao
        if decorrido < self._intervalo_minimo:
            time.sleep(self._intervalo_minimo - decorrido)
        self._ultima_requisicao = time.monotonic()

    def _requisitar(
        self,
        metodo: str,
        path: str,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        relogou = False
        for tentativa in range(1, _MAX_TENTATIVAS + 1):
            self._aguardar_intervalo()
            try:
                resposta = self._client.request(
                    metodo, path, json=json_body, params=params, headers=self._headers()
                )
            except (httpx.TimeoutException, httpx.TransportError) as erro:
                if tentativa == _MAX_TENTATIVAS:
                    raise
                espera = 2**tentativa + random.uniform(0, 1)
                logger.info("%s %s: %s — retry em %.0fs", metodo, path, type(erro).__name__, espera)
                time.sleep(espera)
                continue

            if resposta.status_code in (401, 403) and not relogou:
                logger.info("%s %s: %d — renovando a sessão", metodo, path, resposta.status_code)
                self._relogar()
                relogou = True
                continue
            if resposta.status_code == 429 or resposta.status_code >= 500:
                if tentativa == _MAX_TENTATIVAS:
                    resposta.raise_for_status()
                espera = float(resposta.headers.get("retry-after", 2**tentativa))
                espera += random.uniform(0, 1)
                logger.info(
                    "%s %s: %d — retry em %.0fs", metodo, path, resposta.status_code, espera
                )
                time.sleep(espera)
                continue

            resposta.raise_for_status()
            return resposta.json()
        raise AssertionError("inalcançável")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._requisitar("GET", path, params=params)

    def _post(self, path: str, body: Any, params: dict[str, Any] | None = None) -> Any:
        return self._requisitar("POST", path, json_body=body, params=params)

    # -- Endpoints ------------------------------------------------------------

    def contexto_sessao(self) -> dict:
        contexto = self._get("/usuario-logado/contexto-sessao")
        user_details = contexto.get("userDetails") or {}
        if user_details.get("id") is not None:
            self._userid = str(user_details["id"])
        return contexto

    def dominios(self) -> dict:
        resposta = self._get("/dominios")
        # A API devolve uma lista com um único objeto de ~90 listas de domínio.
        return resposta[0] if isinstance(resposta, list) else resposta

    def status_pessoas(self) -> list[dict]:
        return self._get("/status-pessoas")

    def municipios(self, tamanho: int = 3000) -> list[dict]:
        """Lista todos os municípios do país (o endpoint não filtra por UF;
        o recorte é feito no cliente pelo campo uf.sigla)."""
        todos: list[dict] = []
        pagina = 0
        while True:
            lote = self._get("/municipios", {"size": tamanho, "page": pagina})
            todos.extend(lote)
            if len(lote) < tamanho:
                return todos
            pagina += 1

    def _params_pagina(
        self, pagina: int, tamanho: int, ordenacao: str | None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": pagina, "size": tamanho}
        if ordenacao:
            params["sort"] = ordenacao
        return params

    def filtrar_pessoas(
        self, filtros: dict, pagina: int = 0, tamanho: int = 40, ordenacao: str | None = None
    ) -> dict:
        return self._post(
            "/pessoas/filter", filtros, self._params_pagina(pagina, tamanho, ordenacao)
        )

    def filtrar_pecas(
        self, filtros: dict, pagina: int = 0, tamanho: int = 40, ordenacao: str | None = None
    ) -> dict:
        return self._post(
            "/pecas/light-filter", filtros, self._params_pagina(pagina, tamanho, ordenacao)
        )

    def filtrar_eventos(
        self, filtros: dict, pagina: int = 0, tamanho: int = 40, ordenacao: str | None = None
    ) -> dict:
        return self._post(
            "/eventos/light-filter", filtros, self._params_pagina(pagina, tamanho, ordenacao)
        )

    def paginar(
        self,
        metodo: Callable[..., dict],
        filtros: dict,
        tamanho: int = 40,
        pagina_inicial: int = 0,
        max_paginas: int | None = None,
        ordenacao: str | None = None,
    ) -> Iterator[tuple[int, dict]]:
        """Percorre as páginas de uma consulta, gerando (número, resposta completa)."""
        pagina = pagina_inicial
        percorridas = 0
        while True:
            resposta = metodo(filtros, pagina=pagina, tamanho=tamanho, ordenacao=ordenacao)
            yield pagina, resposta
            percorridas += 1
            if resposta.get("last", True) or not resposta.get("content"):
                return
            if max_paginas is not None and percorridas >= max_paginas:
                return
            pagina += 1

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BnmpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
