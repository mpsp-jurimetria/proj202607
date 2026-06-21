"""Inspeciona a API de resolucoes do CNMP em producao: para cada formulario dos
ambientes da Resolucao 277, lista entidades, uma amostra de instancias e o
detalhe (campos) de uma instancia, para subsidiar o desenho do schema do
Lakehouse.

Uso:
    CNMP_USUARIO=... CNMP_SENHA_PROD=... uv run python scripts/inspecionar_api_cnmp.py
"""
import json
import os
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

PROD_URL = "https://sistemaresolucoes.cnmp.mp.br/seam/resource/rest"
AMBIENTES_RES_277 = [282, 462]

usuario = os.environ["CNMP_USUARIO"]
senha_prod = os.environ["CNMP_SENHA_PROD"]
auth = HTTPBasicAuth(usuario, senha_prod)


def get(path: str, params: dict | None = None) -> list | dict:
    resp = requests.get(f"{PROD_URL}/{path}", params=params, auth=auth, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    resultado = {"ambientes": {}}

    for ambiente_id in AMBIENTES_RES_277:
        formularios = get("formularios", {"ambiente": ambiente_id})
        ambiente_info = {"formularios": {}}

        for form in formularios:
            form_id = form["id"]
            entry = {"descricao": form.get("descricao") or form.get("nome"), "entidades": []}

            try:
                entidades = get("entidades", {"formulario": form_id})
            except requests.HTTPError as exc:
                entry["erro_entidades"] = str(exc)
                ambiente_info["formularios"][form_id] = entry
                continue

            for ent in entidades:
                ent_id = ent["id"]
                ent_entry = {"descricao": ent.get("descricao") or ent.get("nome")}

                try:
                    instancias = get(
                        "instancias", {"formulario": form_id, "entidade": ent_id}
                    )
                except requests.HTTPError as exc:
                    ent_entry["erro_instancias"] = str(exc)
                    ent_entry["instancias"] = []
                    entry["entidades"].append({ent_id: ent_entry})
                    continue

                ent_entry["total_instancias"] = len(instancias)
                ent_entry["amostra_instancias"] = instancias[:3]

                if instancias:
                    primeiro_id = instancias[0]["id"]
                    try:
                        detalhe = get(f"instancias/{primeiro_id}")
                        ent_entry["detalhe_amostra"] = detalhe
                    except requests.HTTPError as exc:
                        ent_entry["erro_detalhe"] = str(exc)

                entry["entidades"].append({ent_id: ent_entry})

            ambiente_info["formularios"][form_id] = entry

        resultado["ambientes"][ambiente_id] = ambiente_info

    out_dir = Path(__file__).resolve().parent.parent / "downloads" / "cnmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "inspecao_api_resolucao_277.json"
    out_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(f"Inspeção salva em: {out_path}")


if __name__ == "__main__":
    main()
