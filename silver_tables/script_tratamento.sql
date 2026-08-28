CREATE OR REPLACE TABLE `grupo-pos-fase-2-alfabetizacao.silver.alunos_tratados` AS 
SELECT 
ano, 
  id_municipio, 
  id_escola, 
  id_aluno, 
  serie, 
  rede, 
 
  SAFE_CAST(presenca AS INT64) = 1 AS presenca, 
  SAFE_CAST(preenchimento_caderno AS INT64) = 1 AS preenchimento_caderno, 
 
  CASE WHEN SAFE_CAST(alfabetizado AS INT64) = 1 THEN TRUE ELSE FALSE END 
    AS alfabetizado_original, 
 
  SAFE_CAST(proficiencia AS FLOAT64) AS proficiencia, 
 
  (SAFE_CAST(proficiencia AS FLOAT64) >= 743) 
    AS alfabetizado_calculado, 
 
  SAFE_CAST(peso_aluno AS FLOAT64) AS peso_aluno, 
 
  ( 
    SAFE_CAST(presenca AS INT64) = 1 
    AND SAFE_CAST(preenchimento_caderno AS INT64) = 1 
  ) AS registro_valido 
 
FROM `grupo-pos-fase-2-alfabetizacao.bronze.alunos`; 
 
 
 
—------------------ 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.municipio_tratado` 
AS 
SELECT 
  SAFE_CAST(ano AS INT64) AS ano, 
  CAST(id_municipio AS STRING) AS id_municipio, 
  SAFE_CAST(serie AS INT64) AS serie, 
  CAST(rede AS STRING) AS rede, 
 
  SAFE_CAST(taxa_alfabetizacao AS FLOAT64) AS taxa_alfabetizacao, 
  SAFE_CAST(media_portugues AS FLOAT64) AS media_portugues, 
 
  SAFE_CAST(proporcao_aluno_nivel_0 AS FLOAT64) AS proporcao_aluno_nivel_0, 
  SAFE_CAST(proporcao_aluno_nivel_1 AS FLOAT64) AS proporcao_aluno_nivel_1, 
  SAFE_CAST(proporcao_aluno_nivel_2 AS FLOAT64) AS proporcao_aluno_nivel_2, 
  SAFE_CAST(proporcao_aluno_nivel_3 AS FLOAT64) AS proporcao_aluno_nivel_3, 
  SAFE_CAST(proporcao_aluno_nivel_4 AS FLOAT64) AS proporcao_aluno_nivel_4, 
  SAFE_CAST(proporcao_aluno_nivel_5 AS FLOAT64) AS proporcao_aluno_nivel_5, 
  SAFE_CAST(proporcao_aluno_nivel_6 AS FLOAT64) AS proporcao_aluno_nivel_6, 
  SAFE_CAST(proporcao_aluno_nivel_7 AS FLOAT64) AS proporcao_aluno_nivel_7, 
  SAFE_CAST(proporcao_aluno_nivel_8 AS FLOAT64) AS proporcao_aluno_nivel_8 
 
FROM `grupo-pos-fase-2-alfabetizacao.bronze.municipio`; 
 
 
—------------------------------------------------------------------------------ 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.uf_tratado` 
AS 
SELECT 
  SAFE_CAST(ano AS INT64) AS ano, 
  UPPER(TRIM(sigla_uf)) AS sigla_uf, 
  CAST(rede AS STRING) AS rede, 
  SAFE_CAST(serie AS INT64) AS serie 
FROM `grupo-pos-fase-2-alfabetizacao.bronze.uf`; 
 
 
—--------------------------------------------------- 
 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.indicador_municipio` 
AS 
SELECT 
    ano, 
    id_municipio, 
    rede, 
 
    COUNT(*) AS qtd_alunos, 
 
    SUM( 
        CASE 
            WHEN registro_valido THEN peso_aluno 
            ELSE 0 
        END 
    ) AS peso_total, 
 
    SUM( 
        CASE 
            WHEN registro_valido 
             AND alfabetizado_calculado 
            THEN peso_aluno 
            ELSE 0 
        END 
    ) AS peso_alfabetizados, 
 
    ROUND( 
        100 * SAFE_DIVIDE( 
            SUM( 
                CASE 
                    WHEN registro_valido 
                     AND alfabetizado_calculado 
                    THEN peso_aluno 
                    ELSE 0 
                END 
            ), 
            SUM( 
                CASE 
                    WHEN registro_valido 
                    THEN peso_aluno 
                    ELSE 0 
                END 
            ) 
        ), 
        2 
    ) AS indicador_alfabetizacao 
 
FROM `grupo-pos-fase-2-alfabetizacao.silver.alunos_tratados` 
GROUP BY 
    ano, 
    id_municipio, 
    rede; 
 
 
—------------------------------------------------------------------------ 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.diretorio_municipio_tratado` 
AS 
SELECT DISTINCT * 
FROM `grupo-pos-fase-2-alfabetizacao.bronze.diretorio_municipio`; 
 
 
 
—--------------------------------------------------------------------------------- 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.meta_municipio_tratada` 
AS 
 
SELECT 
    ano AS ano_referencia, 
    CAST(id_municipio AS STRING) AS id_municipio, 
    rede, 
    taxa_alfabetizacao, 
    nivel_alfabetizacao, 
    percentual_participacao, 
 
    CAST(REPLACE(ano_meta, 'meta_alfabetizacao_', '') AS INT64) 
      AS ano_meta, 
 
    meta_alfabetizacao 
 
FROM ( 
    SELECT * 
    FROM `grupo-pos-fase-2-alfabetizacao.bronze.meta_alfabetizacao_municipio` 
) 
 
UNPIVOT ( 
    meta_alfabetizacao 
    FOR ano_meta IN ( 
        meta_alfabetizacao_2024, 
        meta_alfabetizacao_2025, 
        meta_alfabetizacao_2026, 
        meta_alfabetizacao_2027, 
        meta_alfabetizacao_2028, 
        meta_alfabetizacao_2029, 
        meta_alfabetizacao_2030 
    ) 
); 
 
—----------------------------------------------------------------------------------- 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.meta_brasil_tratada` 
AS 
 
SELECT 
    ano AS ano_referencia, 
    rede, 
    taxa_alfabetizacao, 
    percentual_participacao, 
 
    CAST(REPLACE(ano_meta, 'meta_alfabetizacao_', '') AS INT64) 
      AS ano_meta, 
 
    meta_alfabetizacao 
 
FROM ( 
    SELECT * 
    FROM `grupo-pos-fase-2-alfabetizacao.bronze.meta_alfabetizacao_brasil` 
) 
 
UNPIVOT ( 
    meta_alfabetizacao 
    FOR ano_meta IN ( 
        meta_alfabetizacao_2024, 
        meta_alfabetizacao_2025, 
        meta_alfabetizacao_2026, 
        meta_alfabetizacao_2027, 
        meta_alfabetizacao_2028, 
        meta_alfabetizacao_2029, 
        meta_alfabetizacao_2030 
    ) 
); 
 
 
—---------------------------------------------- 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.meta_uf_tratada` 
AS 
 
SELECT 
    ano AS ano_referencia, 
    sigla_uf, 
    rede, 
    taxa_alfabetizacao, 
    percentual_participacao, 
 
    CAST(REPLACE(ano_meta, 'meta_alfabetizacao_', '') AS INT64) 
      AS ano_meta, 
 
    meta_alfabetizacao 
 
FROM ( 
    SELECT * 
    FROM `grupo-pos-fase-2-alfabetizacao.bronze.meta_alfabetizacao_uf` 
) 
 
UNPIVOT ( 
    meta_alfabetizacao 
    FOR ano_meta IN ( 
        meta_alfabetizacao_2024, 
        meta_alfabetizacao_2025, 
        meta_alfabetizacao_2026, 
        meta_alfabetizacao_2027, 
        meta_alfabetizacao_2028, 
        meta_alfabetizacao_2029, 
        meta_alfabetizacao_2030 
    ) 
); 
 
 
—---------------- 
 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.controle_qualidade_ano` 
AS 
 
SELECT 
  ano, 
 
  COUNT(*) AS total_alunos, 
 
  COUNTIF(registro_valido) 
    AS alunos_validos, 
 
  COUNT(*) - COUNTIF(registro_valido) 
    AS alunos_invalidos, 
 
  ROUND( 
    100 * COUNTIF(registro_valido) / COUNT(*), 
    2 
  ) AS pct_validos, 
 
  COUNTIF( 
    alfabetizado_original <> alfabetizado_calculado 
  ) AS divergencias, 
 
  COUNT(DISTINCT id_municipio) 
    AS municipios 
 
FROM `grupo-pos-fase-2-alfabetizacao.silver.alunos_tratados` 
GROUP BY ano; 
 
—---------------------------------------------------------------------- 
 
 
 
CREATE OR REPLACE TABLE 
`grupo-pos-fase-2-alfabetizacao.silver.consolidado_municipio` 
 
PARTITION BY RANGE_BUCKET( 
  ano, 
  GENERATE_ARRAY(2020, 2030, 1) 
) 
 
CLUSTER BY id_municipio, sigla_uf, rede 
 
AS 
 
SELECT 
 
    -- Chaves 
    i.ano, 
    i.id_municipio, 
    i.rede, 
 
    -- Diretório municipal 
    d.nome AS nome_municipio, 
    d.sigla_uf, 
    d.nome_uf, 
    d.nome_regiao, 
    d.capital_uf, 
    d.amazonia_legal, 
    d.ddd, 
 
    -- Indicadores calculados 
    i.qtd_alunos, 
    i.peso_total, 
    i.peso_alfabetizados, 
    i.indicador_alfabetizacao, 
 
    -- Indicadores municipais oficiais 
    m.taxa_alfabetizacao, 
    m.media_portugues, 
 
    m.proporcao_aluno_nivel_0, 
    m.proporcao_aluno_nivel_1, 
    m.proporcao_aluno_nivel_2, 
    m.proporcao_aluno_nivel_3, 
    m.proporcao_aluno_nivel_4, 
    m.proporcao_aluno_nivel_5, 
    m.proporcao_aluno_nivel_6, 
    m.proporcao_aluno_nivel_7, 
    m.proporcao_aluno_nivel_8, 
 
    -- Metas 
    mm.ano_referencia, 
    mm.ano_meta, 
    mm.meta_alfabetizacao, 
    mm.percentual_participacao, 
    mm.nivel_alfabetizacao, 
 
    -- Comparação realizado x meta 
    ROUND( 
      i.indicador_alfabetizacao - mm.meta_alfabetizacao, 
      2 
    ) AS diferenca_meta 
 
FROM 
`grupo-pos-fase-2-alfabetizacao.silver.indicador_municipio` i 
 
LEFT JOIN 
`grupo-pos-fase-2-alfabetizacao.silver.municipio_tratado` m 
ON i.ano = m.ano 
AND i.id_municipio = m.id_municipio 
AND i.rede = m.rede 
 
LEFT JOIN 
`grupo-pos-fase-2-alfabetizacao.silver.diretorio_municipio_tratado` d 
ON i.id_municipio = d.id_municipio 
 
LEFT JOIN 
`grupo-pos-fase-2-alfabetizacao.silver.meta_municipio_tratada` mm 
ON i.id_municipio = mm.id_municipio 
AND i.rede = mm.rede 
AND i.ano = mm.ano_referencia;