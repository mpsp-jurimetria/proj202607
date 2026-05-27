"""Scraper Playwright para o Sistema de Resoluções do CNMP — Resolução 277.

Fluxo navegado (confirmado por inspeção):
  1. GET /home.seam → redireciona para /login.seam
  2. POST /login.seam com email + senha (formulário JSF)
  3. POST /home.seam com select 'Corregedoria Resolução 277' (value=4)
  4. Home pós-perfil: <li class='formulario-item'> com jsfcljs onclick
  5. Click em cada formulário → /usuario/detalhar_acao_formulario.seam
  6. Selecionar 'Todas' no select de entidades → clicar 'Pesquisar'
  7. Tabela AJAX (RichFaces rich:dataTable) exibe instâncias com link 'Visualizar'
  8. Clicar 'Visualizar' em cada instância → página de formulário preenchido
  9. Para cada seção do sidebar, clicar e aguardar AJAX → extrair campos
  10. Extrair: divData/divText/divNumber → input[value]; divRadio → radio checked label;
      divSimNao → select option[selected]
  11. Salvar JSON + CSV; paginação na tabela de instâncias

Execute:
  uv run python -m src.modulos.cnmp.scraper [--headless]
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from playwright.async_api import Page, async_playwright

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_URL = "https://sistemaresolucoes.cnmp.mp.br"
DADOS_DIR = Path(__file__).parents[4] / "dados" / "cnmp"
SCREENSHOTS_DIR = DADOS_DIR / "screenshots"

PERFIL_TEXTO = "Corregedoria Resolução 277"
TIMEOUT = 60_000  # ms


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

async def _screenshot(page: Page, nome: str) -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(SCREENSHOTS_DIR / f"{nome}.png"), full_page=True)


async def _aguardar_rede(page: Page) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=TIMEOUT)
    except Exception:
        pass


async def _aguardar_ajax(page: Page, timeout: int = 20_000) -> None:
    """Aguarda o modal RichFaces 'Processando...' desaparecer e a tabela ter dados."""
    try:
        modal = page.locator("#modalProcessando, #modalProcessandoContainer")
        try:
            await modal.first.wait_for(state="visible", timeout=2_000)
        except Exception:
            pass
        await modal.first.wait_for(state="hidden", timeout=timeout)
    except Exception:
        pass
    try:
        await page.wait_for_selector(
            "table.rich-table tbody tr.rich-table-row, "
            "table.rich-table tr:nth-child(2)",
            timeout=timeout,
        )
    except Exception:
        pass


async def _aguardar_secao(page: Page, timeout: int = 20_000) -> None:
    """Aguarda o AJAX da seção terminar (modal desaparecer + fieldset aparecer)."""
    try:
        modal = page.locator("#modalProcessando, #modalProcessandoContainer")
        try:
            await modal.first.wait_for(state="visible", timeout=2_000)
        except Exception:
            pass
        await modal.first.wait_for(state="hidden", timeout=timeout)
    except Exception:
        pass
    try:
        await page.wait_for_selector("fieldset", timeout=timeout)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def login(page: Page) -> None:
    usuario = os.getenv("CNMP_USER", "")
    senha = os.getenv("CNMP_PASSWORD", "")
    if not usuario or not senha:
        raise ValueError("CNMP_USER e CNMP_PASSWORD devem estar definidos no .env")

    logger.info("Acessando página de login...")
    await page.goto(f"{BASE_URL}/home.seam", wait_until="load", timeout=TIMEOUT)
    await _screenshot(page, "00_login_page")

    campo_email = page.locator('input[name="login:emailCampo:email"]')
    await campo_email.wait_for(state="visible", timeout=TIMEOUT)

    await campo_email.fill(usuario)
    await page.locator('input[type="password"]').fill(senha)
    await page.locator('input[name="login:j_id87"]').click()
    await _aguardar_rede(page)

    if "login.seam" in page.url:
        msg = await page.locator("ul.message").inner_text()
        raise RuntimeError(f"Login falhou: {msg.strip()}")

    logger.info("Login OK — %s", page.url)


# ---------------------------------------------------------------------------
# Seleção de perfil
# ---------------------------------------------------------------------------

async def selecionar_perfil(page: Page) -> None:
    logger.info("Selecionando perfil '%s'...", PERFIL_TEXTO)
    select = page.locator("select[name='selecionarPerfil:perfil:j_id68']")
    await select.select_option(label=PERFIL_TEXTO)
    await page.click("input[name='selecionarPerfil:j_id75']")
    await _aguardar_rede(page)
    logger.info("Perfil selecionado — %s", page.url)


# ---------------------------------------------------------------------------
# Extração via BeautifulSoup (parse do HTML da página)
# ---------------------------------------------------------------------------

def _campo_bs4(div: Tag) -> tuple[str, str] | None:
    """Extrai (rótulo, valor) de um div de campo JSF identificado pelo sufixo do id."""
    did = div.get("id", "")

    if any(t in did for t in [":divData", ":divText", ":divNumber"]):
        label = div.find("label")
        inp = div.find("input", disabled=True)
        if not label or not inp:
            return None
        rotulo = label.get_text(strip=True).rstrip("*").strip()
        valor = (inp.get("value") or "").strip()
        return rotulo, valor

    if ":divRadio" in did:
        labels = div.find_all("label")
        radios = div.find_all("input", type="radio")
        if not labels:
            return None
        rotulo = labels[0].get_text(strip=True).rstrip("*").strip()
        for ri, radio in enumerate(radios):
            if radio.get("checked"):
                valor = labels[ri + 1].get_text(strip=True) if len(labels) > ri + 1 else radio.get("value", "")
                return rotulo, valor
        return rotulo, ""

    if ":divSimNao" in did:
        label = div.find("label")
        sel = div.find("select")
        if not label or not sel:
            return None
        rotulo = label.get_text(strip=True).rstrip("*").strip()
        opt = sel.find("option", selected=True)
        valor = opt.get_text(strip=True) if opt else ""
        return rotulo, valor

    return None


def _secao_do_html(html: str) -> tuple[str, list[dict[str, str]]]:
    """Parseia o HTML da página e extrai título + campos da seção visível."""
    soup = BeautifulSoup(html, "html.parser")
    fieldsets = soup.find_all("fieldset")

    secao_fs = None
    titulo = ""
    for fs in reversed(fieldsets):
        leg = fs.find("legend")
        if leg:
            t = leg.get_text(strip=True)
            if t and "Preenchimento" not in t:
                secao_fs = fs
                titulo = t
                break

    if not secao_fs:
        return "", []

    tipos = ["divData", "divText", "divNumber", "divRadio", "divSimNao"]
    selector = ", ".join(f'[id*=":{t}"]' for t in tipos)
    campos: list[dict[str, str]] = []
    for div in secao_fs.select(selector):
        result = _campo_bs4(div)
        if result:
            rotulo, valor = result
            if rotulo:
                campos.append({"campo": rotulo, "valor": valor})

    return titulo, campos


def _metadados_do_html(html: str) -> dict[str, str]:
    """Extrai metadados do cabeçalho da instância (div#preenchimentoAbas:cabecalho)."""
    soup = BeautifulSoup(html, "html.parser")
    meta: dict[str, str] = {}

    cab = soup.find(id="preenchimentoAbas:cabecalho")
    if not cab:
        return meta

    texto = cab.get_text(separator="|", strip=True)
    for part in texto.split("|"):
        part = part.strip()
        for chave, prefixo in [
            ("entidade", "Entidade:"),
            ("cnpj", "CNPJ:"),
            ("estado", "Estado:"),
            ("municipio", "Município:"),
            ("endereco", "Endereço:"),
            ("telefone", "Telefone:"),
            ("periodo", "Período:"),
        ]:
            if part.startswith(prefixo):
                meta[chave] = part[len(prefixo):].strip()

    # Formulário vem da legend do fieldset principal
    leg = soup.select_one("fieldset legend")
    if leg:
        txt = leg.get_text(strip=True)
        if " - " in txt:
            meta["formulario_titulo"] = txt.split(" - ", 1)[1].strip()

    return meta


# ---------------------------------------------------------------------------
# Coleta de todas as seções de uma instância
# ---------------------------------------------------------------------------

async def extrair_instancia(page: Page) -> dict[str, Any]:
    """Navega por todas as seções do formulário e extrai os campos."""
    await _aguardar_rede(page)

    html_inicial = await page.content()
    dados: dict[str, Any] = {"url": page.url, "secoes": []}
    dados.update(_metadados_do_html(html_inicial))

    # Lista links de seção no sidebar (texto contendo "SEÇÃO")
    links_secao = page.locator("a").filter(has_text="SEÇÃO")
    n_secoes = await links_secao.count()
    logger.info("      Seções encontradas: %d", n_secoes)

    if n_secoes == 0:
        titulo, campos = _secao_do_html(html_inicial)
        if campos:
            dados["secoes"].append({"titulo": titulo, "campos": campos})
        return dados

    for si in range(n_secoes):
        links = page.locator("a").filter(has_text="SEÇÃO")
        link = links.nth(si)
        titulo_link = (await link.inner_text()).strip()

        logger.info("      Seção %d/%d: %s", si + 1, n_secoes, titulo_link[:60])

        try:
            await link.click()
            await _aguardar_secao(page)

            titulo, campos = _secao_do_html(await page.content())
            if not titulo:
                titulo = titulo_link

            if campos:
                dados["secoes"].append({"titulo": titulo, "campos": campos})
                logger.info("        → %d campos", len(campos))
            else:
                logger.warning("        → 0 campos extraídos")

        except Exception as exc:
            logger.error("        Erro na seção %d: %s", si + 1, exc)

    return dados


# ---------------------------------------------------------------------------
# Re-carrega a lista de instâncias (após go_back)
# ---------------------------------------------------------------------------

async def _recarregar_lista(page: Page) -> None:
    """Após voltar da página de instância, re-seleciona 'Todas' para recarregar a tabela AJAX."""
    select = page.locator("select[name*='entidade']")
    if await select.count() > 0:
        try:
            await select.select_option(label="Todas")
            await _aguardar_ajax(page)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Coleta principal
# ---------------------------------------------------------------------------

class _LimiteAtingido(Exception):
    pass


async def coletar_todos(headless: bool = True, limite: int = 0) -> list[dict[str, Any]]:
    DADOS_DIR.mkdir(parents=True, exist_ok=True)
    todos: list[dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        try:
            await login(page)
            await selecionar_perfil(page)
            await _screenshot(page, "01_home_pos_perfil")

            formulario_links = page.locator("li.formulario-item a")
            n_forms = await formulario_links.count()
            logger.info("Formulários encontrados: %d", n_forms)

            for fi in range(n_forms):
                forms = page.locator("li.formulario-item a")
                form_texto = (await forms.nth(fi).inner_text()).strip()
                logger.info("Formulário %d/%d: %s", fi + 1, n_forms, form_texto[:70])

                await forms.nth(fi).click()
                await _aguardar_rede(page)
                await _screenshot(page, f"02_form{fi+1:02d}_busca")

                # Passo 1: pesquisar (sem filtro) para popular o select de entidades
                btn_pesquisar = page.locator("input[value='Pesquisar']")
                if await btn_pesquisar.count() > 0:
                    await btn_pesquisar.click()
                    await _aguardar_rede(page)

                # Passo 2: selecionar "Todas" → AJAX carrega a tabela
                select = page.locator("select[name*='entidade']")
                if await select.count() > 0:
                    await select.select_option(label="Todas")
                    await _aguardar_ajax(page)

                await _screenshot(page, f"03_form{fi+1:02d}_lista")

                pagina = 1
                while True:
                    links_viz = page.get_by_role("link", name="Visualizar")
                    n_viz = await links_viz.count()
                    logger.info("  Página %d: %d instâncias", pagina, n_viz)

                    if n_viz == 0:
                        break

                    for vi in range(n_viz):
                        try:
                            viz = page.get_by_role("link", name="Visualizar")
                            if await viz.count() == 0:
                                logger.warning("    Links 'Visualizar' sumiram — saindo do loop")
                                break

                            entidade = ""
                            try:
                                tr = viz.nth(vi).locator("xpath=ancestor::tr[1]")
                                entidade = (await tr.locator("td").first.inner_text()).strip()
                            except Exception:
                                pass

                            logger.info("    Instância %d/%d: %s", vi + 1, n_viz, entidade[:60])

                            await viz.nth(vi).click()
                            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT)

                            dados = await extrair_instancia(page)
                            dados["formulario"] = form_texto
                            dados["entidade"] = entidade or dados.get("entidade", "")
                            dados["indice"] = len(todos) + 1
                            todos.append(dados)
                            logger.info("      → %d seções", len(dados["secoes"]))

                            json_path = _salvar_instancia_json(dados)
                            logger.info("      JSON: %s", json_path.name)
                            await _screenshot(page, f"04_instancia_{len(todos):04d}")

                            if limite and len(todos) >= limite:
                                logger.info("Limite de %d instância(s) atingido.", limite)
                                raise _LimiteAtingido

                            # Volta para a lista e recarrega a tabela AJAX
                            await page.go_back()
                            await _aguardar_rede(page)
                            await _recarregar_lista(page)

                        except Exception as exc:
                            logger.error("    Erro na instância %d: %s", vi + 1, exc)
                            try:
                                await page.go_back()
                                await _aguardar_rede(page)
                                await _recarregar_lista(page)
                            except Exception:
                                pass

                    # Tenta avançar para próxima página
                    btn_prox = page.locator("a").filter(has_text="»")
                    if await btn_prox.count() > 0:
                        onclick = await btn_prox.first.get_attribute("onclick")
                        if onclick and "jsfcljs" in onclick:
                            await btn_prox.first.click()
                            await _aguardar_ajax(page)
                            pagina += 1
                        else:
                            break
                    else:
                        break

                # Volta para a home pós-perfil
                await page.goto(f"{BASE_URL}/home.seam", wait_until="domcontentloaded")
                await _aguardar_rede(page)

        except _LimiteAtingido:
            pass
        except Exception as exc:
            logger.error("Erro geral: %s", exc)
            await _screenshot(page, "erro_geral")
            raise
        finally:
            await browser.close()

    _salvar_csv(todos)
    logger.info("Concluído — %d registros em %s", len(todos), DADOS_DIR)
    return todos


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def _slug_formulario(nome: str) -> str:
    """Converte o nome do formulário em slug para usar como nome de diretório."""
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    nome = nome.lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    nome = nome.strip("_")
    return nome[:60]


def _salvar_instancia_json(reg: dict[str, Any]) -> Path:
    """Salva um registro individual como JSON com timestamp no nome."""
    formulario = reg.get("formulario", "desconhecido")
    subdir = DADOS_DIR / _slug_formulario(formulario)
    subdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = subdir / f"{ts}.json"
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _salvar_csv(dados: list[dict[str, Any]]) -> None:
    path = DADOS_DIR / "resolucao277.csv"
    escrever_cabecalho = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["indice", "formulario", "entidade", "municipio", "estado", "periodo", "secao", "campo", "valor"],
        )
        if escrever_cabecalho:
            writer.writeheader()
        for reg in dados:
            meta = {
                "indice": reg.get("indice", ""),
                "formulario": reg.get("formulario", ""),
                "entidade": reg.get("entidade", ""),
                "municipio": reg.get("municipio", ""),
                "estado": reg.get("estado", ""),
                "periodo": reg.get("periodo", ""),
            }
            for secao in reg.get("secoes", []):
                for campo in secao.get("campos", []):
                    writer.writerow({
                        **meta,
                        "secao": secao.get("titulo", ""),
                        "campo": campo.get("campo", ""),
                        "valor": campo.get("valor", ""),
                    })
    logger.info("CSV atualizado: %s", path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper CNMP — Resolução 277")
    parser.add_argument(
        "--headless", action="store_true", default=False,
        help="Rodar sem janela do browser (padrão: com janela)"
    )
    parser.add_argument(
        "--limite", type=int, default=0, metavar="N",
        help="Parar após coletar N instâncias (0 = sem limite)"
    )
    args = parser.parse_args()
    asyncio.run(coletar_todos(headless=args.headless, limite=args.limite))
