from google.cloud import bigquery


PROJECT_ID = "grupo-pos-fase-2-alfabetizacao"

client = bigquery.Client(project=PROJECT_ID)


# METAS X RESULTADOS
QUERY_METAS = """
SELECT
    COUNT(*) AS total_registros,

    COUNTIF(indicador_alfabetizacao IS NULL)
        AS indicador_nulo,

    COUNTIF(meta_alfabetizacao IS NULL)
        AS meta_nula,

    COUNTIF(diferenca_meta IS NULL)
        AS diferenca_nula,

    COUNTIF(nome_municipio IS NULL)
        AS municipio_nulo

FROM `grupo-pos-fase-2-alfabetizacao.gold.metas_resultados_municipio`;
"""


QUERY_DUPLICADOS_METAS = """
SELECT
    COUNT(*) AS duplicados
FROM (
    SELECT
        ano,
        id_municipio
    FROM `grupo-pos-fase-2-alfabetizacao.gold.metas_resultados_municipio`
    GROUP BY
        ano,
        id_municipio
    HAVING COUNT(*) > 1
);
"""

# EVOLUÇÃO DO INDICADOR
QUERY_EVOLUCAO = """
SELECT
    COUNT(*) AS total_registros,

    COUNTIF(indicador_2023 IS NULL)
        AS indicador_2023_nulo,

    COUNTIF(indicador_2024 IS NULL)
        AS indicador_2024_nulo,

    COUNTIF(variacao_pontos IS NULL)
        AS variacao_nula,

    COUNTIF(nome_municipio IS NULL)
        AS municipio_nulo

FROM `grupo-pos-fase-2-alfabetizacao.gold.evolucao_indicador_municipio`;
"""


QUERY_DUPLICADOS_EVOLUCAO = """
SELECT
    COUNT(*) AS duplicados
FROM (
    SELECT
        id_municipio
    FROM `grupo-pos-fase-2-alfabetizacao.gold.evolucao_indicador_municipio`
    GROUP BY id_municipio
    HAVING COUNT(*) > 1
);
"""

# VALIDAÇÃO - METAS
def verificar_metas():

    resultado = client.query(QUERY_METAS).result()

    for linha in resultado:

        print("\nQUALIDADE - METAS X RESULTADOS")
        print("=" * 50)

        print(f"Total de registros : {linha.total_registros}")
        print(f"Indicadores nulos  : {linha.indicador_nulo}")
        print(f"Metas nulas        : {linha.meta_nula}")
        print(f"Diferenças nulas   : {linha.diferenca_nula}")
        print(f"Municípios nulos   : {linha.municipio_nulo}")

    duplicados = list(
        client.query(QUERY_DUPLICADOS_METAS).result()
    )[0]

    print(f"Duplicidades       : {duplicados.duplicados}")
    print("=" * 50)


# VALIDAÇÃO - EVOLUÇÃO
def verificar_evolucao():

    resultado = client.query(QUERY_EVOLUCAO).result()

    for linha in resultado:

        print("\nQUALIDADE - EVOLUÇÃO 2023 X 2024")
        print("=" * 50)

        print(f"Total de registros : {linha.total_registros}")
        print(f"Indicador 2023 nulo: {linha.indicador_2023_nulo}")
        print(f"Indicador 2024 nulo: {linha.indicador_2024_nulo}")
        print(f"Variação nula      : {linha.variacao_nula}")
        print(f"Municípios nulos   : {linha.municipio_nulo}")

    duplicados = list(
        client.query(QUERY_DUPLICADOS_EVOLUCAO).result()
    )[0]

    print(f"Duplicidades       : {duplicados.duplicados}")
    print("=" * 50)


# EXECUÇÃO
if __name__ == "__main__":

    verificar_metas()
    verificar_evolucao()