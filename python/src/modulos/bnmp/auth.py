"""Autenticação no SSO do PJe (Keycloak) para o BNMP 2.0, sem navegador.

Fluxo authorization_code do Keycloak (sem PKCE, conforme observado no HAR do
frontend bnmp-frontend): abre a página de login, envia usuário/senha, envia o
código TOTP quando exigido, captura o `code` do redirect e troca por tokens.

O access_token e o refresh_token expiram juntos em ~8h; coletas mais longas
refazem o login completo (ver BnmpClient._garantir_token).
"""

import html
import logging
import re
import time
import uuid
from dataclasses import dataclass

import httpx
import pyotp

logger = logging.getLogger(__name__)

_SSO_BASE = "https://sso.cloud.pje.jus.br/auth/realms/pje/protocol/openid-connect"
_CLIENT_ID = "bnmp-frontend"
_REDIRECT_URI = "https://bnmp.pdpj.jus.br/pagina-inicial"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)
_MAX_REDIRECTS = 10

# Margem de segurança antes da expiração real do token, em segundos.
_MARGEM_EXPIRACAO = 300


@dataclass
class Token:
    access_token: str
    refresh_token: str
    expira_em: float  # time.monotonic() em que o access_token deixa de valer

    @property
    def expirado(self) -> bool:
        return time.monotonic() >= self.expira_em


# -- Parsers do HTML do Keycloak (funções puras, testáveis sem rede) ----------


def extrair_action_formulario(html_pagina: str) -> str:
    """Extrai a URL de action do formulário de login do Keycloak."""
    match = re.search(r'<form[^>]*\baction="([^"]+)"', html_pagina)
    if not match:
        raise RuntimeError("Formulário de login não encontrado na página do SSO")
    return html.unescape(match.group(1))


def detectar_campo_otp(html_pagina: str) -> str | None:
    """Devolve o nome do campo de OTP ("otp" ou "totp") se a página o exigir."""
    match = re.search(r'<input[^>]*\bname="(t?otp)"', html_pagina)
    return match.group(1) if match else None


def extrair_erro_login(html_pagina: str) -> str | None:
    """Extrai a mensagem de erro exibida pelo Keycloak, se houver."""
    match = re.search(
        r'(?:id="input-error"[^>]*>|class="[^"]*kc-feedback-text[^"]*"[^>]*>)\s*([^<]+)',
        html_pagina,
    )
    if not match:
        return None
    texto = html.unescape(match.group(1)).strip()
    return texto or None


def extrair_code(url_redirect: str) -> str:
    """Extrai o parâmetro code da URL de redirect final."""
    match = re.search(r"[?&#]code=([^&]+)", url_redirect)
    if not match:
        raise RuntimeError("Redirect do SSO não contém o parâmetro code")
    return match.group(1)


# -- Fluxo com rede -----------------------------------------------------------


def _novo_http_client() -> httpx.Client:
    return httpx.Client(
        follow_redirects=False,
        timeout=30.0,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        },
    )


def _montar_token(resposta_token: dict) -> Token:
    return Token(
        access_token=resposta_token["access_token"],
        refresh_token=resposta_token["refresh_token"],
        expira_em=time.monotonic() + resposta_token["expires_in"] - _MARGEM_EXPIRACAO,
    )


def _trocar_code_por_token(http: httpx.Client, code: str) -> Token:
    resposta = http.post(
        f"{_SSO_BASE}/token",
        data={
            "code": code,
            "grant_type": "authorization_code",
            "client_id": _CLIENT_ID,
            "redirect_uri": _REDIRECT_URI,
        },
        headers={"Origin": "https://bnmp.pdpj.jus.br", "Referer": "https://bnmp.pdpj.jus.br/"},
    )
    resposta.raise_for_status()
    return _montar_token(resposta.json())


def _seguir_redirects_ate_code(http: httpx.Client, resposta: httpx.Response) -> str:
    """Segue a cadeia de 302 do Keycloak até a Location apontar para o redirect_uri."""
    for _ in range(_MAX_REDIRECTS):
        if resposta.status_code not in (301, 302, 303):
            raise RuntimeError(
                f"Fluxo do SSO interrompido: status {resposta.status_code} sem redirect"
            )
        location = resposta.headers["location"]
        if location.startswith(_REDIRECT_URI):
            return extrair_code(location)
        resposta = http.get(location)
    raise RuntimeError("Fluxo do SSO excedeu o limite de redirects sem chegar ao code")


def _enviar_otp(http: httpx.Client, html_pagina: str, campo_otp: str, segredo_otp: str) -> httpx.Response:
    """Envia o código TOTP; em código inválido por virada de janela, tenta uma 2ª vez."""
    for tentativa in (1, 2):
        acao = extrair_action_formulario(html_pagina)
        codigo = pyotp.TOTP(segredo_otp).now()
        resposta = http.post(acao, data={campo_otp: codigo, "login": "Entrar"})
        if resposta.status_code in (301, 302, 303):
            return resposta
        html_pagina = resposta.text
        erro = extrair_erro_login(html_pagina)
        if erro is None:
            raise RuntimeError("Resposta inesperada do SSO após o envio do OTP")
        if tentativa == 1:
            logger.info("OTP recusado (%s) — aguardando a próxima janela TOTP", erro)
            time.sleep(31 - time.time() % 30)
        else:
            raise RuntimeError(f"Falha no OTP do BNMP: {erro}")
    raise AssertionError("inalcançável")


def autenticar(
    usuario: str, senha: str, segredo_otp: str | None, http: httpx.Client | None = None
) -> Token:
    """Faz o login completo no SSO do PJe e devolve os tokens da sessão."""
    proprio = http is None
    http = http or _novo_http_client()
    try:
        pagina_login = http.get(
            f"{_SSO_BASE}/auth",
            params={
                "response_type": "code",
                "client_id": _CLIENT_ID,
                "redirect_uri": _REDIRECT_URI,
                "scope": "openid",
                "state": str(uuid.uuid4()),
                "nonce": str(uuid.uuid4()),
            },
        )
        pagina_login.raise_for_status()

        acao = extrair_action_formulario(pagina_login.text)
        resposta = http.post(
            acao,
            data={"username": usuario, "password": senha, "credentialId": ""},
            headers={"Referer": str(pagina_login.url)},
        )

        if resposta.status_code == 200:
            campo_otp = detectar_campo_otp(resposta.text)
            if campo_otp:
                if not segredo_otp:
                    raise ValueError(
                        "O SSO exigiu OTP mas BNMP_OTP_SECRET não está definido no .env"
                    )
                resposta = _enviar_otp(http, resposta.text, campo_otp, segredo_otp)
            else:
                erro = extrair_erro_login(resposta.text) or "resposta inesperada do SSO"
                raise RuntimeError(f"Falha no login do BNMP: {erro}")

        code = _seguir_redirects_ate_code(http, resposta)
        token = _trocar_code_por_token(http, code)
        logger.info("Login no BNMP concluído — token válido por ~8h")
        return token
    finally:
        if proprio:
            http.close()


def renovar(token: Token, http: httpx.Client | None = None) -> Token:
    """Renova o access_token via refresh_token.

    Lança httpx.HTTPStatusError (400 invalid_grant) se o refresh_token também
    tiver expirado — nesse caso o chamador deve refazer o login completo.
    """
    proprio = http is None
    http = http or _novo_http_client()
    try:
        resposta = http.post(
            f"{_SSO_BASE}/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": _CLIENT_ID,
            },
            headers={"Origin": "https://bnmp.pdpj.jus.br", "Referer": "https://bnmp.pdpj.jus.br/"},
        )
        resposta.raise_for_status()
        logger.info("Token do BNMP renovado via refresh_token")
        return _montar_token(resposta.json())
    finally:
        if proprio:
            http.close()
