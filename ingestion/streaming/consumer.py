"""Consome eventos de submissão da subscription Pub/Sub (pull),
acumula em micro-lotes e grava Parquet no Bronze (GCS)."""

import json
import time
import argparse
import pandas as pd
from google.cloud import pubsub_v1

import os
from dotenv import load_dotenv

load_dotenv()


PROJETO = os.environ["GCP_PROJECT"]
TOPICO = os.environ["PUBSUB_TOPIC"]              # producer
SUBSCRIPTION = os.environ["PUBSUB_SUBSCRIPTION"] # consumer
BUCKET = os.environ["GCS_BUCKET_BRONZE"]         # consumer

print(f"Projeto: {PROJETO} | Subscription: {SUBSCRIPTION}")

# ingestion/streaming/consumer.py
"""Consome eventos de submissão da subscription Pub/Sub (pull),
acumula em micro-lotes e grava Parquet no Bronze (GCS)."""

import json
import time
import argparse
import pandas as pd
from google.cloud import pubsub_v1
from google.api_core.exceptions import DeadlineExceeded



def consumir(tam_lote: int, timeout_ocioso: int):
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(PROJETO, SUBSCRIPTION)

    buffer = []          # micro-lote em memória
    ack_ids = []         # ids a confirmar quando o lote for gravado
    total = 0
    ultimo_evento = time.time()

    print(f"Consumindo de {SUBSCRIPTION} (lote={tam_lote}) ...\n")

    while True:
        try:
            resp = subscriber.pull(
                request={"subscription": sub_path, "max_messages": tam_lote},
                timeout=10,
            )
        except DeadlineExceeded:
            # Timeout do long-polling = fila vazia no momento. Não é erro.
            resp = None

        if not resp or not resp.received_messages:
            # Sem mensagens: se passou o tempo ocioso, drena o resto e sai
            if time.time() - ultimo_evento > timeout_ocioso:
                if buffer:
                    gravar_lote(buffer, ack_ids, subscriber, sub_path)
                    total += len(buffer)
                print(f"\nOcioso por {timeout_ocioso}s. Total: {total} eventos.")
                break
            continue

        for msg in resp.received_messages:
            evento = json.loads(msg.message.data.decode("utf-8"))
            buffer.append(evento)
            ack_ids.append(msg.ack_id)
            ultimo_evento = time.time()

        if len(buffer) >= tam_lote:
            gravar_lote(buffer, ack_ids, subscriber, sub_path)
            total += len(buffer)
            print(f"  lote gravado | acumulado: {total}")
            buffer, ack_ids = [], []


def gravar_lote(buffer, ack_ids, subscriber, sub_path):
    df = pd.DataFrame(buffer)
    ano = df["ano"].iloc[0]  # lote coeso por ano (amostra é de um ano só)
    ts = time.strftime("%Y%m%d-%H%M%S")
    destino = (f"gs://{BUCKET}/bronze/alunos_streaming/"
               f"ano={ano}/lote_{ts}.parquet")
    df.to_parquet(destino, index=False, engine="pyarrow")
    print(f"    → {len(df)} eventos em {destino}")

    # Só confirma (ack) DEPOIS da gravação bem-sucedida
    subscriber.acknowledge(request={"subscription": sub_path, "ack_ids": ack_ids})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--lote", type=int, default=25, help="Eventos por Parquet")
    p.add_argument("--timeout-ocioso", type=int, default=15,
                   help="Segundos sem mensagens até encerrar")
    args = p.parse_args()
    consumir(args.lote, args.timeout_ocioso)