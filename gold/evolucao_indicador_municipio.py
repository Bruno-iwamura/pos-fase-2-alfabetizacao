from google.cloud import bigquery


PROJECT_ID = "grupo-pos-fase-2-alfabetizacao"

client = bigquery.Client(project=PROJECT_ID)


QUERY = """
CREATE OR REPLACE TABLE
`grupo-pos-fase-2-alfabetizacao.gold.evolucao_indicador_municipio`
AS

SELECT
    i2023.id_municipio,

    d.nome AS nome_municipio,
    d.sigla_uf,
    d.nome_uf,
    d.nome_regiao,

    i2023.indicador_alfabetizacao AS indicador_2023,
    i2024.indicador_alfabetizacao AS indicador_2024,

    ROUND(
        i2024.indicador_alfabetizacao
        - i2023.indicador_alfabetizacao,
        2
    ) AS variacao_pontos,

    CASE
        WHEN i2024.indicador_alfabetizacao
             > i2023.indicador_alfabetizacao
            THEN 'MELHOROU'

        WHEN i2024.indicador_alfabetizacao
             < i2023.indicador_alfabetizacao
            THEN 'PIOROU'

        ELSE 'ESTAVEL'
    END AS situacao_evolucao

FROM `grupo-pos-fase-2-alfabetizacao.silver.indicador_municipio` AS i2023

INNER JOIN `grupo-pos-fase-2-alfabetizacao.silver.indicador_municipio` AS i2024
    ON i2023.id_municipio = i2024.id_municipio

LEFT JOIN `grupo-pos-fase-2-alfabetizacao.silver.diretorio_municipio_tratado` AS d
    ON i2023.id_municipio = d.id_municipio

WHERE i2023.ano = 2023
  AND i2024.ano = 2024
  AND i2023.rede = '3'
  AND i2024.rede = '3'
  AND i2023.indicador_alfabetizacao IS NOT NULL
  AND i2024.indicador_alfabetizacao IS NOT NULL;
"""


def executar_gold():

    job = client.query(QUERY)

    job.result()

    print("Tabela gold.evolucao_indicador_municipio criada com sucesso.")


if __name__ == "__main__":
    executar_gold()