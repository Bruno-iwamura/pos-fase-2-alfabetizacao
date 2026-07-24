# Guia de Acesso — Projeto GCP `grupo-pos-fase-2-alfabetizacao`

Bem-vindo(a). Este guia leva você do zero até conseguir consultar os dados,
tanto pelo **console web** quanto pelo **ambiente local (VS Code)**.

Pré-requisito: você já foi adicionado(a) ao projeto com o seu e-mail Google.
Se algum passo falhar com erro de permissão, avise o responsável pela
infraestrutura antes de continuar.

---

## Parte 1 — Console Web (mais rápido para começar)

### 1. Acessar o projeto

1. Abra <https://console.cloud.google.com>
2. Faça login com o **mesmo e-mail Google** que foi cadastrado no projeto.
3. No topo da tela, clique no **seletor de projeto** (ao lado do logo "Google
   Cloud") e selecione **`grupo-pos-fase-2-alfabetizacao`**.

> ⚠️ O erro mais comum é este: se você "não vê os dados", quase sempre é porque
> o seletor está em outro projeto. Confirme que o nome do projeto aparece no
> topo antes de qualquer coisa.

### 2. Abrir o BigQuery e consultar

1. Menu de navegação (☰) → **BigQuery**.
2. No painel **Explorer** (esquerda), procure o projeto
   `grupo-pos-fase-2-alfabetizacao` e expanda. Você verá os datasets aos quais
   tem acesso (`bronze`, `silver` e/ou `gold`, conforme seu papel).
3. Clique em **+ Nova consulta** (ou "Compor nova consulta") e teste:

```sql
SELECT ano, COUNT(*) AS linhas
FROM `grupo-pos-fase-2-alfabetizacao.bronze.municipio`
GROUP BY ano
ORDER BY ano;
```

**Resultado esperado:** `2023 → 11547` e `2024 → 12448`.
Se aparecer isso, seu acesso está 100% funcional.

### 3. Hábito de custo (importante)

Antes de clicar em **Executar**, olhe o **validador** no canto superior direito
do editor — ele mostra quantos bytes a consulta vai processar, **sem executar**.

- Nunca use `SELECT *` — selecione as colunas que precisa.
- Sempre que possível, filtre por `ano` (as tabelas são particionadas por ano).
- **Não consulte a Base dos Dados (`basedosdados.*`) diretamente** — a ingestão
  já foi feita; trabalhe sobre o `bronze` do nosso projeto.

---

## Parte 2 — Ambiente Local + VS Code

Necessário para quem vai rodar código Python ou dbt (Silver/Gold).

### 1. Instalar o Google Cloud CLI (`gcloud`)

- **Windows/WSL2 ou Linux:**
  ```bash
  curl https://sdk.cloud.google.com | bash
  exec -l $SHELL
  ```
- **Mac:** `brew install --cask google-cloud-sdk`
- Verifique: `gcloud --version`

### 2. Autenticar (dois logins — ambos necessários)

```bash
# Login da CLI — habilita os comandos gcloud/bq
gcloud auth login

# Define o projeto padrão
gcloud config set project grupo-pos-fase-2-alfabetizacao

# Login do ADC — é ESTE que as bibliotecas Python e o dbt usam
gcloud auth application-default login
```

> ⚠️ Os dois logins são diferentes e ambos são necessários. `gcloud auth login`
> autentica a ferramenta de linha de comando; `application-default login`
> autentica o **código** (Python, dbt). Pular o segundo faz o código falhar com
> "Could not automatically determine credentials".
>
> Não usamos chave JSON de service account — a autenticação é via ADC
> (credenciais do usuário). Não há arquivo de credencial para baixar.

Teste que o ADC está ativo:

```bash
gcloud auth application-default print-access-token
```

Se imprimir um token longo, está funcionando.

### 3. Testar acesso aos dados via `bq`

```bash
bq query --use_legacy_sql=false --location=us-central1 \
'SELECT ano, COUNT(*) AS linhas
 FROM `grupo-pos-fase-2-alfabetizacao.bronze.municipio`
 GROUP BY ano ORDER BY ano'
```

> ⚠️ O `--location=us-central1` é **obrigatório**. Nossos datasets estão na
> região `us-central1`, não na multi-região `US`. Sem esse parâmetro, você
> recebe um erro "not found" enganoso (o BigQuery procura na região errada).

### 4. VS Code

1. Instale o VS Code e a extensão **Python** (Microsoft).
2. Clone o repositório do projeto:
   ```bash
   git clone <URL-do-repo>
   cd <pasta-do-repo>
   ```
3. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```
4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
5. Copie o template de ambiente e preencha:
   ```bash
   cp .env.example .env
   ```
   O `.env` guarda projeto, bucket e nomes de recurso. **Nunca** suba o `.env`
   para o Git (o `.gitignore` já o protege).
6. No VS Code, selecione o interpretador do `.venv`:
   `Ctrl+Shift+P` → "Python: Select Interpreter" → escolha o `.venv`.

O código autentica automaticamente pelo ADC configurado no passo 2 — não é
preciso configurar credenciais dentro do VS Code.

---

## Parte 3 — Checklist de "está tudo funcionando?"

- [ ] Consigo selecionar o projeto no console e ver os datasets.
- [ ] A consulta de teste retorna 11547 / 12448.
- [ ] `gcloud auth application-default print-access-token` imprime um token.
- [ ] A mesma consulta funciona via `bq` com `--location=us-central1`.
- [ ] `.venv` criado, dependências instaladas, interpretador selecionado.
- [ ] `.env` criado a partir do `.env.example`.

Se todos os itens passam, você está pronto para trabalhar.

---

## Resumo das armadilhas (as 3 que mais pegam)

1. **Projeto errado no seletor** → "não vejo os dados". Confira o topo.
2. **Faltou o segundo login (ADC)** → código falha com erro de credenciais.
3. **Faltou `--location=us-central1`** → erro "not found" enganoso no `bq`.

Dúvidas: fale com o responsável pela infraestrutura (documentação técnica
completa em `docs/handoff-silver.md`).
