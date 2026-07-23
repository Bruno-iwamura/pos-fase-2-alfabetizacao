"""Gera e executa o DDL das external tables que fazem a ponte
Bronze (GCS/Parquet) → BigQuery. Fontes lidas de sources.yml."""

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJETO = os.environ["GCP_PROJECT"]
BUCKET = os.environ["GCS_BUCKET_BRONZE"]
DATASET = os.environ["BQ_DATASET_BRONZE"]
LOCATION = os.environ["BQ_LOCATION"]

CONFIG_PATH = Path(__file__).parent / "batch" / "sources.yml"


def carregar_fontes():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["sources"]


def montar_ddl(fonte):
    nome = fonte["name"]
    particao = fonte.get("partition_column")
    base_uri = f"gs://{BUCKET}/bronze/{nome}"
    tabela = f"`{PROJETO}.{DATASET}.{nome}`"

    if particao:
        # Particionamento estilo Hive: o valor vem do caminho (ano=YYYY)
        return f"""
CREATE OR REPLACE EXTERNAL TABLE {tabela}
WITH PARTITION COLUMNS ({particao} INT64)
OPTIONS (
  format = 'PARQUET',
  uris = ['{base_uri}/*'],
  hive_partition_uri_prefix = '{base_uri}',
  require_hive_partition_filter = false
)"""
    return f"""
CREATE OR REPLACE EXTERNAL TABLE {tabela}
OPTIONS (
  format = 'PARQUET',
  uris = ['{base_uri}/*.parquet']
)"""


def main():
    print(f"Projeto: {PROJETO} | Dataset: {DATASET} | Bucket: {BUCKET}\n")
    client = bigquery.Client(project=PROJETO, location=LOCATION)

    fontes = list(carregar_fontes())

    # O streaming grava em pasta própria (proveniência separada do batch),
    # então ganha sua própria external table.
    if any(f["name"] == "alunos" for f in fontes):
        fontes.append({"name": "alunos_streaming", "partition_column": "ano"})

    for fonte in fontes:
        nome = fonte["name"]
        ddl = montar_ddl(fonte)
        print(f"[{nome}] criando external table ...")
        client.query(ddl).result()
        print("  ok")

    print(f"\n{len(fontes)} external tables criadas em {PROJETO}.{DATASET}")


if __name__ == "__main__":
    main()