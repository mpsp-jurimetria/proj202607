"""Gera sugestões de alias para as colunas das tabelas largas do gold.

Lê o dicionário de campos em downloads/cnmp/formularios_metadata.json e
imprime, para os formulários pedidos, o trecho do dict ALIASES no formato de
src/modulos/cnmp/etl/aliases_campos.py — uma linha por campo pivotável, com o
label original como comentário para facilitar a curadoria manual.

A sugestão é o slug do label sem a numeração ("1.1 Data da visita:" ->
"data_da_visita"). Quando o mesmo slug aparece mais de uma vez no formulário
(ex.: "Regime Fechado | Feminino" existe em capacidade e em ocupação), todas as
ocorrências ganham o número da pergunta como prefixo ("q3_1_1_regime_fechado_
feminino") — o número desambigua e preserva a ordem do questionário.

O resultado é ponto de partida, não produto final: revise os nomes dos campos
mais usados e cole o trecho em aliases_campos.py. O script não sobrescreve o
arquivo curado justamente para não perder edições manuais.

Execute (do diretório python/):
    uv run python scripts/gerar_aliases_cnmp.py 1322 1342
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

from src.modulos.cnmp.etl.load_gold import _COLUNAS_BASE, _slug

_METADATA = Path(__file__).resolve().parent.parent / "downloads/cnmp/formularios_metadata.json"

# Mesmos tipos excluídos das tabelas largas em load_gold (_TIPOS_SEM_COLUNA +
# o container TABELA_DINAMICA; as colunas dele não aparecem no nível de seção).
_TIPOS_EXCLUIDOS = {"LABEL", "CAMPO_ANEXO", "TABELA_DINAMICA"}


def _numero_pergunta(label: str) -> str | None:
    """Extrai a numeração hierárquica do label: '3.1.1 Regime...' -> '3_1_1'."""
    match = re.match(r"^([\d.]+)", label.strip())
    if not match:
        return None
    numero = match.group(1).strip(".").replace(".", "_")
    return numero or None


def _campos_pivotaveis(formulario: dict) -> list[dict]:
    campos = []
    for secao in formulario.get("secoes", []):
        for campo in secao.get("campos", []):
            if campo["tipoCampo"]["tipo"] not in _TIPOS_EXCLUIDOS:
                campos.append(campo)
    return campos


def sugerir_aliases(formulario: dict) -> list[tuple[int, str, str]]:
    """Devolve [(campo_id_api, alias, label)] com aliases únicos no formulário."""
    campos = _campos_pivotaveis(formulario)
    slugs = [_slug(campo.get("label") or "") for campo in campos]
    repetidos = {slug for slug, total in Counter(slugs).items() if total > 1}

    sugestoes: list[tuple[int, str, str]] = []
    usados: set[str] = set()
    for campo, slug in zip(campos, slugs):
        label = campo.get("label") or ""
        alias = slug
        if slug in repetidos or slug in _COLUNAS_BASE:
            numero = _numero_pergunta(label)
            alias = f"q{numero}_{slug}" if numero else f"c{campo['id']}_{slug}"
        while alias in usados:
            alias = f"c{campo['id']}_{slug}"
        usados.add(alias)
        sugestoes.append((campo["id"], alias, label))
    return sugestoes


def main() -> None:
    formulario_ids = sys.argv[1:]
    if not formulario_ids:
        print(__doc__)
        sys.exit(1)

    metadata = json.loads(_METADATA.read_text(encoding="utf-8"))

    for formulario_id in formulario_ids:
        formulario = metadata[str(formulario_id)]
        print(f"    # {formulario['id']} — {formulario['nome']} (versão {formulario['versao']})")
        print(f"    {formulario['id']}: {{")
        for campo_id, alias, label in sugerir_aliases(formulario):
            comentario = " ".join(label.split())
            print(f'        {campo_id}: "{alias}",  # {comentario}')
        print("    },")


if __name__ == "__main__":
    main()
