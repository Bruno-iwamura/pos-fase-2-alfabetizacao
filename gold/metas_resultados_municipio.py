# Importa o cliente do BigQuery
from google.cloud import bigquery


PROJECT_ID = "grupo-pos-fase-2-alfabetizacao"

client = bigquery.Client(project=PROJECT_ID)

# Consulta SQL responsável pela criação da tabela Gold
QUERY = """
CREATE OR REPLACE TABLE
`grupo-pos-fase-2-alfabetizacao.gold.metas_resultados_municipio`
AS

WITH metas_deduplicadas AS (

    SELECT
    id_municipio,
    rede,
    ano_referencia,
    ano_meta,
    meta_alfabetizacao
    FROM `grupo-pos-fase-2-alfabetizacao.silver.meta_municipio_tratada`

    WHERE rede = 'Municipal'

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY id_municipio, ano_meta, rede
        ORDER BY ano_referencia DESC
    ) = 1
)

SELECT
    i.ano,
    i.id_municipio,

    d.nome AS nome_municipio,
    d.sigla_uf,
    d.nome_uf,
    d.nome_regiao,

    i.indicador_alfabetizacao,
    m.meta_alfabetizacao,

    ROUND(
        i.indicador_alfabetizacao - m.meta_alfabetizacao,
        2
    ) AS diferenca_meta,

    CASE
        WHEN i.indicador_alfabetizacao >= m.meta_alfabetizacao
            THEN TRUE
        ELSE FALSE
    END AS atingiu_meta

FROM `grupo-pos-fase-2-alfabetizacao.silver.indicador_municipio` AS i

INNER JOIN metas_deduplicadas AS m
    ON i.id_municipio = m.id_municipio
    AND i.ano = m.ano_meta

LEFT JOIN `grupo-pos-fase-2-alfabetizacao.silver.diretorio_municipio_tratado` AS d
    ON i.id_municipio = d.id_municipio

WHERE i.rede = '3';
"""

# Função para execução
def executar_gold():

    job = client.query(QUERY)

    job.result()

    print("Tabela gold.metas_resultados_municipio criada com sucesso.")


if __name__ == "__main__":
    executar_gold()