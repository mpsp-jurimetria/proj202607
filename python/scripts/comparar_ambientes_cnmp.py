"""Compara ambientes/formularios disponiveis para o usuario de servico do MPSP
entre UAT e producao na API de Resolucoes do CNMP (Resolucao 277).

Uso:
    CNMP_USUARIO=... CNMP_SENHA_UAT=... CNMP_SENHA_PROD=... uv run python scripts/comparar_ambientes_cnmp.py
"""
import json
import os
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

UAT_URL = "https://homologacaoeapext.cnmp.mp.br/resolucoes/seam/resource/rest"
PROD_URL = "https://sistemaresolucoes.cnmp.mp.br/seam/resource/rest"

usuario = os.environ["CNMP_USUARIO"]
senha_uat = os.environ["CNMP_SENHA_UAT"]
senha_prod = os.environ["CNMP_SENHA_PROD"]


def listar_ambientes(base_url: str, senha: str) -> list[dict]:
    auth = HTTPBasicAuth(usuario, senha)
    resp = requests.get(f"{base_url}/ambientes", auth=auth, timeout=30)
    resp.raise_for_status()
    return resp.json()


def listar_formularios(base_url: str, senha: str, ambiente_id: int) -> list[dict]:
    auth = HTTPBasicAuth(usuario, senha)
    resp = requests.get(
        f"{base_url}/formularios",
        params={"ambiente": ambiente_id},
        auth=auth,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    ambientes_uat = listar_ambientes(UAT_URL, senha_uat)
    ambientes_prod = listar_ambientes(PROD_URL, senha_prod)

    ids_uat = {a["id"]: a for a in ambientes_uat}
    ids_prod = {a["id"]: a for a in ambientes_prod}

    so_no_uat = sorted(set(ids_uat) - set(ids_prod))
    em_ambos = sorted(set(ids_uat) & set(ids_prod))

    saida = {
        "total_ambientes_uat": len(ambientes_uat),
        "total_ambientes_prod": len(ambientes_prod),
        "ambientes_uat": ambientes_uat,
        "ambientes_prod": ambientes_prod,
        "ids_so_no_uat": [ids_uat[i] for i in so_no_uat],
        "ids_em_ambos": [ids_uat[i] for i in em_ambos],
    }

    out_dir = Path(__file__).resolve().parent.parent / "downloads" / "cnmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "comparacao_ambientes_uat_prod.json"
    out_path.write_text(json.dumps(saida, ensure_ascii=False, indent=2))

    print(f"UAT: {len(ambientes_uat)} ambientes | PROD: {len(ambientes_prod)} ambientes")
    print(f"Ambientes presentes apenas no UAT: {len(so_no_uat)}")
    for amb in saida["ids_so_no_uat"]:
        print(f"  - {amb}")
    print(f"\nResultado completo salvo em: {out_path}")


if __name__ == "__main__":
    main()
