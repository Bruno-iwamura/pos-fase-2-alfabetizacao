"""Extrai as tabelas-fonte da Base dos Dados e grava como Parquet
particionado no bucket Bronze (GCS). Ambiente via .env; fontes via sources.yml."""

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJETO = os.environ["GCP_PROJECT"]
BUCKET = os.environ["GCS_BUCKET_BRONZE"]
CONFIG_PATH = Path(__file__).parent / "sources.yml"


def carregar_fontes():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["sources"]


def descobrir_colunas(client, tabela_fqn):
    """Descoberta dinâmica via metadados (tables.get) — sem INFORMATION_SCHEMA."""
    return [c.name for c in client.get_table(tabela_fqn).schema]


def extrair_fonte(client, fonte):
    tabela_fqn, nome = fonte["source"], fonte["name"]
    particao = fonte.get("partition_column")

    colunas = descobrir_colunas(client, tabela_fqn)
    print(f"\n[{nome}] {tabela_fqn}  ({len(colunas)} colunas)")

    lista = ",\n               ".join(colunas)
    df = client.query(f"SELECT {lista}\n        FROM `{tabela_fqn}`").to_dataframe()
    print(f"  {len(df):,} linhas")

    base = f"gs://{BUCKET}/bronze/{nome}"
    if particao and particao in df.columns:
        for valor, grupo in df.groupby(particao):
            destino = f"{base}/{particao}={valor}/{nome}.parquet"
            grupo.to_parquet(destino, index=False, engine="pyarrow")
            print(f"  → {len(grupo):,} linhas em {particao}={valor}")
    else:
        destino = f"{base}/{nome}.parquet"
        df.to_parquet(destino, index=False, engine="pyarrow")
        print(f"  → {len(df):,} linhas (sem partição)")


def main():
    print(f"Projeto: {PROJETO} | Bucket: {BUCKET}\n")
    client = bigquery.Client(project=PROJETO)
    for fonte in carregar_fontes():
        if fonte.get("skip"):
            print(f"\n[{fonte['name']}] pulada (skip=true)")
            continue
        extrair_fonte(client, fonte)
    print("\nExtração concluída.")


if __name__ == "__main__":
    main()