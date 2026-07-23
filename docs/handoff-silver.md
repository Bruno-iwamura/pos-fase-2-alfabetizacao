# Handoff: Bronze → Silver

Documento de entrega da camada Bronze para quem constrói a Silver.
Contém o **contrato de interface** (o que está pronto e como acessar) e os
**achados de discovery** que evitam retrabalho e erros silenciosos.

---

## 1. O que está pronto

| Recurso | Identificador |
|---|---|
| Projeto GCP | `grupo-pos-fase-2-alfabetizacao` |
| Bucket Bronze | `gs://grupo-pos-fase-2-alfabetizacao-bronze` |
| Dataset Bronze (external tables) | `grupo-pos-fase-2-alfabetizacao.bronze` |
| Dataset Silver (destino de vocês) | `grupo-pos-fase-2-alfabetizacao.silver` |
| Dataset Gold | `grupo-pos-fase-2-alfabetizacao.gold` |
| Location (**tudo**) | `us-central1` |

O dado bruto é **Parquet no GCS**, particionado no padrão Hive (`ano=YYYY/`).
As **external tables** no dataset `bronze` são a ponte: o BigQuery lê o Parquet
onde ele está, sem cópia. Vocês consultam como tabela normal.

### Tabelas disponíveis

| External table | Origem | Grão |
|---|---|---|
| `bronze.uf` | batch | ano, sigla_uf, serie, rede |
| `bronze.municipio` | batch | ano, id_municipio, serie, rede |
| `bronze.meta_alfabetizacao_brasil` | batch | ano, rede |
| `bronze.meta_alfabetizacao_uf` | batch | ano, sigla_uf, rede |
| `bronze.meta_alfabetizacao_municipio` | batch | ano, id_municipio, rede |
| `bronze.alunos` | batch | microdado por aluno (~2M/ano) |
| `bronze.alunos_streaming` | streaming | microdado (amostra via Pub/Sub) |
| `bronze.diretorio_municipio` | batch | id_municipio (dimensão geográfica) |

### Acesso

Autenticação por **ADC** (não há chave JSON — bloqueada por política):

```bash
gcloud auth login
gcloud config set project grupo-pos-fase-2-alfabetizacao
gcloud auth application-default login
```

Permissões concedidas a vocês: `bigquery.jobUser` (projeto),
`dataViewer` em `bronze`, `dataEditor` em `silver`, `objectViewer` no bucket.
O `objectViewer` é necessário — ao consultar external table, é a identidade de
quem roda a query que lê o GCS.

---

## 2. Achados que vocês precisam saber

Estes vieram de perfilagem com dado real. Ignorá-los produz números errados
que **não** geram erro — falham em silêncio.

### ⚠️ `rede` é hierarquia, não dimensão

Os códigos se sobrepõem:

| código | significado | tipo |
|---|---|---|
| 0 | Total (Federal + Estadual + Municipal + Privada) | **agregado** |
| 1 | Federal | atômico |
| 2 | Estadual | atômico |
| 3 | Municipal | atômico |
| 4 | Privada | atômico |
| 5 | Pública (Estadual + Municipal) | **agregado** |
| 6 | Pública (Federal + Estadual + Municipal) | **agregado** |

**Somar todas as redes conta cada município múltiplas vezes.** Sempre filtrar
por um nível da hierarquia.

Além disso, os agregados **não são deriváveis** das atômicas — a cobertura por
rede é irregular entre municípios. Recalcular "Pública" somando Estadual +
Municipal dá resultado **diferente** do oficial. Use o agregado que a fonte já
fornece (`rede = 5` para o indicador público).

### ⚠️ Toda taxa é ponderada

`alunos` traz `peso_aluno`, e os pesos diferem sistematicamente entre grupos.
Contagem simples **diverge do indicador oficial**. Sempre:

```sql
sum(case when <alfabetizado> then peso_aluno end) / sum(peso_aluno)
```

### ⚠️ Filtro de validade

Só conta para o indicador quem tem `presenca = 1 AND preenchimento_caderno = 1`.
Os demais (ausentes, ou presentes sem caderno preenchido) não geraram resultado
válido e devem ser excluídos do cálculo — mas recomenda-se **marcar com flag**
em vez de deletar, para preservar auditabilidade.

### ⚠️ `alunos_streaming` contém duplicatas

O Pub/Sub garante entrega *at-least-once*: mensagens não confirmadas são
reentregues. Durante a ingestão houve reentrega real — **546 registros gravados
para 200 eventos publicados**. Isso é comportamento correto (preferimos
duplicação recuperável a perda irrecuperável), e o Bronze preserva o bruto.

**A deduplicação é trabalho da Silver:**

```sql
row_number() over (partition by id_aluno, ano order by <critério>) = 1
```

### Corte de alfabetização: 743

`alfabetizado` é derivado de `proficiencia >= 743` (fronteira confirmada
empiricamente; 743 conta como alfabetizado). Sugestão: **re-derivar** o corte
explicitamente e testar contra a coluna oficial — valida entendimento e fonte.

### Outros pontos

- **`id_municipio`**: STRING de 7 dígitos (código IBGE completo) em todas as
  tabelas. Cast para INT ou uso de código de 6 dígitos → *join vazio silencioso*.
- **`serie`**: constante (só valor `2` = 2º ano do EF). Não discrimina nada hoje.
- **Cobertura não censitária**: ~5.550 municípios nos resultados (contra 5.570
  do país). É cobertura real, não erro. O `diretorio_municipio` é censitário.
- **Metas em formato WIDE**: colunas `meta_alfabetizacao_2024 … _2030` precisam
  de *unpivot* para (`ano_meta`, `valor_meta`). Atenção a distinguir o ano de
  referência do ano-alvo da meta.
- **Cobertura temporal assimétrica**: resultados 2023–2024; metas até 2030
  (Brasil/UF até 2025). Os anos **não batem** entre tabelas no join.
- **Sem `sigla_uf` em `alunos`/`municipio`**: só `id_municipio`. Para recorte
  geográfico, juntar com `bronze.diretorio_municipio`.

---

## 3. Teste de sanidade

O pipeline reproduz o **indicador oficial do MEC**. Use como validação:

| Ano | Indicador Criança Alfabetizada (oficial) |
|---|---|
| 2023 | 56,0% |
| 2024 | 59,2% |

Se a Silver de vocês produzir esses números (rede pública, ponderado, com
filtro de validade e corte de 743), o cálculo está correto.

Contagens de referência para `bronze.municipio`: **11.547** linhas em 2023 e
**12.448** em 2024.

---

## 4. Armadilhas técnicas do ambiente

- **`US` ≠ `us-central1`.** `US` é multi-região, `us-central1` é regional — uma
  query numa não enxerga datasets na outra, e o erro é um "not found" enganoso.
  Sempre `--location=us-central1` no `bq`, ou *Data location* no console.
- **INFORMATION_SCHEMA da Base dos Dados é negado** no nível de projeto. Para
  inspecionar schema, use o catálogo do site da BD+ ou `client.get_table()`.
- **Instalem `google-cloud-bigquery-storage`** se forem ler tabelas grandes via
  Python — sem ele a leitura cai no REST e fica lenta.

---

## 5. FinOps — combinados do time

O projeto opera dentro do *free tier* (1 TiB/mês de consulta). As tabelas do
Bronze são pequenas (a maior escaneia ~256 MB), então o risco real está em
consultar a **Base dos Dados** através deste projeto — lá existem tabelas de
centenas de GB.

Combinados:

1. **Dry-run antes de rodar** — o validador no canto do editor mostra os bytes
   sem executar. Custa 10 segundos.
2. **Nunca `SELECT *`** — selecionem colunas explicitamente.
3. **Filtrem por `ano`** — as tabelas são particionadas; o *partition pruning*
   foi a maior alavanca de economia medida (256 MB → 125 MB).
4. **Não consultem a Base dos Dados** — a ingestão já foi feita; trabalhem
   sobre o Bronze.

Billing alert configurado. Cotas de consulta serão aplicadas após ativação da
conta paga.

---

## 6. Como reproduzir a ingestão (se necessário)

```bash
cp .env.example .env      # preencher com os valores do ambiente
pip install -r requirements.txt

python ingestion/batch/extract.py              # batch → Bronze
python ingestion/streaming/producer.py --uf AC --ano 2024 --limite 200
python ingestion/streaming/consumer.py --lote 50 --timeout-ocioso 15
python ingestion/create_external_tables.py     # ponte Bronze → BigQuery
```

A ingestão é **idempotente** (sobrescreve partições) e **determinística** —
produz as mesmas contagens em qualquer ambiente.
