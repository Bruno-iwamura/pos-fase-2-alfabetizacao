'''
Camada Gold

Usa os dados da camada Silver, seleciona o necessário e cria a primeira tabela para consumo.

'''

# imports
import pandas as pd

from utils import ler_parquet
from utils import salvar_parquet

# Obter dados da camada Silver
def carregar_indicador():

    return ler_parquet(
        "silver/indicador_municipio.parquet"
    )

def preparar(df):

    df = df.copy()

    df["indicador"] = pd.to_numeric(
        df["indicador"],
        errors="coerce"
    )

    return df

# Retiro as colunas que não vou usar
def selecionar_colunas(df):

    colunas = [
        "ano",
        "id_municipio",
        "rede",
        "total_alunos",
        "peso_total",
        "peso_alfabetizados",
        "indicador"
    ]

    return df[colunas]

# Criação Tabela
def executar_gold():

    indicador = carregar_indicador()

    indicador = preparar(indicador)

    indicador = selecionar_colunas(indicador)

    salvar_parquet(
        indicador,
        "gold/indicador_municipio.parquet"
    )

    print("Indicador municipal feita com sucesso.")
    
# Executar a camada gold pelo CMD
if __name__ == "__main__":

    executar_gold()