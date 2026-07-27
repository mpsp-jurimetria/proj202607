import pytest

from src.modulos.bnmp.auth import (
    detectar_campo_otp,
    extrair_action_formulario,
    extrair_code,
    extrair_erro_login,
)

HTML_LOGIN = """
<html><body>
  <form id="kc-form-login" onsubmit="login.disabled = true; return true;"
        action="https://sso.cloud.pje.jus.br/auth/realms/pje/login-actions/authenticate?session_code=abc&amp;execution=xyz&amp;client_id=bnmp-frontend"
        method="post">
    <input id="username" name="username" type="text" autofocus />
    <input id="password" name="password" type="password" />
  </form>
</body></html>
"""

HTML_OTP = """
<html><body>
  <form id="kc-otp-login-form" action="https://sso.cloud.pje.jus.br/auth/realms/pje/login-actions/authenticate?session_code=def"
        method="post">
    <input id="otp" name="otp" autocomplete="off" type="text" autofocus />
  </form>
</body></html>
"""

HTML_OTP_ANTIGO = '<form action="/x"><input name="totp" type="text" /></form>'

HTML_ERRO = """
<html><body>
  <span id="input-error" class="pf-c-form__helper-text pf-m-error">Usuário ou senha inválidos.</span>
  <form action="/x"><input name="username" /></form>
</body></html>
"""


def test_extrair_action_formulario_desescapa_entidades():
    acao = extrair_action_formulario(HTML_LOGIN)

    assert acao.startswith("https://sso.cloud.pje.jus.br/auth/realms/pje/login-actions/authenticate")
    assert "&execution=xyz" in acao
    assert "&amp;" not in acao


def test_extrair_action_formulario_sem_form_falha():
    with pytest.raises(RuntimeError):
        extrair_action_formulario("<html><body>sem formulário</body></html>")


def test_detectar_campo_otp():
    assert detectar_campo_otp(HTML_OTP) == "otp"
    assert detectar_campo_otp(HTML_OTP_ANTIGO) == "totp"
    assert detectar_campo_otp(HTML_LOGIN) is None


def test_extrair_erro_login():
    assert extrair_erro_login(HTML_ERRO) == "Usuário ou senha inválidos."
    assert extrair_erro_login(HTML_LOGIN) is None


def test_extrair_code_do_redirect():
    url = (
        "https://bnmp.pdpj.jus.br/pagina-inicial?state=1a2b&session_state=3c4d"
        "&code=586f1de8-635a-4ea1-babc-4506ca387e30.a7bf364b&iss=https%3A%2F%2Fsso"
    )

    assert extrair_code(url) == "586f1de8-635a-4ea1-babc-4506ca387e30.a7bf364b"


def test_extrair_code_ausente_falha():
    with pytest.raises(RuntimeError):
        extrair_code("https://bnmp.pdpj.jus.br/pagina-inicial?error=access_denied")
