from google.cloud import bigquery


PROJECT_ID = "grupo-pos-fase-2-alfabetizacao"

client = bigquery.Client(project=PROJECT_ID)


QUERY = """
CREATE OR REPLACE TABLE
`grupo-pos-fase-2-alfabetizacao.gold.resumo_uf`
AS

SELECT
    ano,
    sigla_uf,

    COUNT(*) AS total_municipios,

    ROUND(
        AVG(indicador_alfabetizacao),
        2
    ) AS media_indicador,

    ROUND(
        AVG(meta_alfabetizacao),
        2
    ) AS media_meta,

    COUNTIF(atingiu_meta) AS municipios_atingiram_meta,

    ROUND(
        SAFE_DIVIDE(
            COUNTIF(atingiu_meta),
            COUNT(*)
        ) * 100,
        2
    ) AS percentual_atingiram_meta

FROM `grupo-pos-fase-2-alfabetizacao.gold.metas_resultados_municipio`

GROUP BY
    ano,
    sigla_uf;
"""


def executar_gold():

    job = client.query(QUERY)

    job.result()

    print("Tabela gold.resumo_uf criada com sucesso.")


if __name__ == "__main__":
    executar_gold()