from metas_resultados_municipio import executar_gold as executar_metas
from evolucao_indicador_municipio import executar_gold as executar_evolucao
from resumo_uf import executar_gold as executar_resumo


def executar_pipeline_gold():

    print("=" * 50)
    print("INICIANDO PIPELINE GOLD")
    print("=" * 50)

    print("\n[1/3] Gerando metas x resultados...")
    executar_metas()

    print("\n[2/3] Gerando evolucao dos indicadores...")
    executar_evolucao()

    print("\n[3/3] Gerando resumo por UF...")
    executar_resumo()

    print("\n" + "=" * 50)
    print("PIPELINE GOLD CONCLUIDO")
    print("=" * 50)


if __name__ == "__main__":
    executar_pipeline_gold()