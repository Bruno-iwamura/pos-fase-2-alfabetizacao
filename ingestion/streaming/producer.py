"""Simula a janela de coleta: lê uma amostra de `alunos` da Base dos Dados
e publica cada registro como um evento no tópico Pub/Sub."""

import json
import time
import argparse
from google.cloud import bigquery, pubsub_v1

import os
from dotenv import load_dotenv

load_dotenv()

PROJETO = os.environ["GCP_PROJECT"]
TOPICO = os.environ["PUBSUB_TOPIC"]              # producer
SUBSCRIPTION = os.environ["PUBSUB_SUBSCRIPTION"] # consumer
BUCKET = os.environ["GCS_BUCKET_BRONZE"]         # consumer

TABELA = "basedosdados.br_inep_avaliacao_alfabetizacao.alunos"

def publicar_amostra(sigla_uf: str, ano: int, limite: int, intervalo: float):
    bq = bigquery.Client(project=PROJETO)
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJETO, TOPICO)

    # Amostra: alunos de um estado/ano específico (recorte coeso)
    query = f"""
        SELECT a.ano, a.id_municipio, a.id_escola, a.id_aluno,
               a.serie, a.rede, a.presenca, a.preenchimento_caderno,
               a.alfabetizado, a.proficiencia, a.peso_aluno
        FROM `{TABELA}` a
        JOIN `basedosdados.br_bd_diretorios_brasil.municipio` d
          ON a.id_municipio = d.id_municipio
        WHERE d.sigla_uf = @uf AND a.ano = @ano
        LIMIT @limite
    """
    cfg = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("uf", "STRING", sigla_uf),
        bigquery.ScalarQueryParameter("ano", "INT64", ano),
        bigquery.ScalarQueryParameter("limite", "INT64", limite),
    ])

    print(f"Buscando amostra: {sigla_uf}/{ano} (limite {limite}) ...")
    linhas = list(bq.query(query, job_config=cfg).result())
    print(f"  {len(linhas)} eventos a publicar.\n")

    for i, linha in enumerate(linhas, 1):
        evento = dict(linha)
        # Metadado de ingestão: quando o evento "chegou" na janela de coleta
        evento["ts_submissao"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        dados = json.dumps(evento, default=str).encode("utf-8")
        future = publisher.publish(topic_path, dados,
                                   uf=sigla_uf, ano=str(ano))
        future.result()  # confirma a publicação

        if i % 100 == 0 or i == len(linhas):
            print(f"  publicados {i}/{len(linhas)}")
        time.sleep(intervalo)

    print(f"\nConcluído: {len(linhas)} eventos publicados em {TOPICO}.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--uf", default="AC", help="Sigla da UF (recorte da amostra)")
    p.add_argument("--ano", type=int, default=2024)
    p.add_argument("--limite", type=int, default=500)
    p.add_argument("--intervalo", type=float, default=0.05, help="Segundos entre publicações (simula chegada no tempo)")
    args = p.parse_args()    
    publicar_amostra(args.uf, args.ano, args.limite, args.intervalo)