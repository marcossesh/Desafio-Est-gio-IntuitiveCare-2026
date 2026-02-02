# IntuitiveCare Analytics

Uma solução completa de ETL, Banco de Dados e Dashboard interativo para análise de despesas de operadoras de planos de saúde (ANS), desenvolvida com foco em **Robustez**, **Precisão Contábil** e **Experiência do Usuário**.

---

## Tecnologias Utilizadas

-   **Backend**: Python 3.12, FastAPI, SQLAlchemy, Pandas.
-   **Frontend**: Vue.js 3, Vite, Chart.js.
-   **Banco de Dados**: PostgreSQL.
-   **Infraestrutura**: Docker (Opcional), Virtualenv.

---

## Como Executar o Projeto

### Pré-requisitos
-   Python 3.10+
-   Node.js 18+
-   PostgreSQL instalado e rodando.

### 1. Configuração do Ambiente e Banco de Dados

Crie um arquivo `.env` na raiz do projeto com a string de conexão:
```env
DATABASE_URL="postgresql://usuario:senha@localhost:5432/intuitive_care_db"
```

> **Nota de Segurança**: O arquivo `.env` foi incluído com credenciais padrão apenas para facilitar a execução local do teste via Docker. Em um ambiente de produção real, este arquivo seria ignorado pelo Git e as credenciais seriam gerenciadas via Secrets/Environment Variables.

Instale as dependências do Python:
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 2. Execução do Pipeline de Dados (ETL)

O script `main.py` orquestra todo o processo: Download -> Processamento -> Carga no Banco -> Testes.

```bash
python main.py
```
*Isso pode levar alguns minutos. O script baixará os arquivos da ANS, processará os CSVs e populará o banco.*

### 3. Execução da API e Dashboard

Em terminais separados:

**Backend (API):**
```bash
uvicorn src.5_api:app --reload
```

**Frontend (Interface):**
```bash
cd frontend
npm install
npm run dev
```

Acesse o sistema em: `http://localhost:5173`

---

## Arquitetura e Trade-offs Técnicos

Este projeto foi desenvolvido seguindo princípios de **SOLID**, **KISS** (Keep It Simple, Stupid) e **DRY** (Don't Repeat Yourself). Abaixo, justifico as decisões técnicas tomadas para cada desafio proposto.

### 1. Processamento de Dados (ETL)

*   **Abordagem**: Processamento em streaming de arquivos (File-by-File) com Pandas.
*   **Decisão (Memory vs Incremental)**: Optei por processar arquivo por arquivo em vez de carregar tudo em memória de uma só vez.
    *   *Trade-off*: Embora carregar tudo fosse mais rápido para datasets pequenos, a abordagem escolhida é escalável. Se a ANS liberar arquivos de 10GB amanhã, este pipeline não quebrará por falta de RAM (Onde *KISS* encontra *Robustez*).
*   **Tratamento de Inconsistências**: 
    *   **Parsing Numérico**: Identifiquei que arquivos da ANS misturam formatação (vírgula decimal para valores monetários). Implementei um parser explícito que sanitiza a entrada antes da conversão, recuperando dados críticos que seriam perdidos (NaN/Zero) caso fosse utilizada a conversão padrão.
    *   **Contabilidade (Filtro Nível 9)**: Para evitar duplicação de valores (Pai + Filho), o processador filtra estritamente **contas analíticas (9 dígitos)**.
        *   *Justificativa*: A precisão contábil é prioritária. Somar contas sintéticas (resumo) causaria inflação artificial de despesas.

### 2. Banco de Dados e Modelagem

*   **Schema**: Modelo Estrela Simplificado (`operadoras` -> `despesas_consolidadas`).
*   **Decisão (Normalização)**: Separei dados cadastrais das transações financeiras.
    *   *Trade-off*: Evita redundância massiva de strings na tabela de fatos, economizando armazenamento e acelerando I/O. As queries utilizam `JOIN` indexados, mantendo alta performance.
*   **Tipos de Dados**: 
    *   `DECIMAL(15, 2)` para valores monetários.
        *   *Justificativa*: **Jamais usar FLOAT para dinheiro**. Erros de ponto flutuante acumulados em bilhões de reais gerariam discrepâncias inaceitáveis.

### 3. API Backend

*   **Framework**: **FastAPI**.
    *   *Decisão vs Flask*: Escolhi FastAPI pela tipagem estática (Pydantic) e validação automática.
    *   *Justificativa*: Reduz boilerplate (DRY) e gera documentação automática, facilitando o consumo pelo Frontend.
*   **Paginação**: **Offset-based**.
    *   *Trade-off*: Simples e performático para o volume esperado (~1000 operadoras). Cursor-based adicionaria complexidade desnecessária para este caso de uso.

### 4. Interface Frontend

*   **Estratégia de Busca**: **Server-side**.
    *   *Decisão*: A busca delega a filtragem ao banco de dados.
    *   *Justificativa*: Filtragem no cliente (Client-side) não escala. Manter a lógica no servidor garante performance constante independente do crescimento da base.
*   **Gerenciamento de Estado**: **Locais (Refs)**.
    *   *Justificativa*: O estado da aplicação é simples e não justifica a overhead de uma State Store global (Pinia/Vuex).

---

## Desafios de Dados Encontrados e Soluções

Durante a análise exploratória dos dados da ANS, identifiquei anomalias críticas que demandaram correções específicas no pipeline. Citar estas ocorrências demonstra a importância da verificação manual dos dados brutos:

1.  **Duplicidade Contábil (Caso Bradesco Saúde)**:
    *   **Problema**: Inicialmente, apurou-se um valor de ~R$ 144 Bilhões em despesas trimestrais para o Bradesco Saúde, valor incompatível com o mercado.
    *   **Diagnóstico**: Os arquivos CSV continham tanto as contas sintéticas (totais) quanto as analíticas (detalhes). Ao somar tudo, o valor real era multiplicado pela profundidade da árvore contábil.
    *   **Solução**: Implementação de filtro rigoroso por `len(CD_CONTA_CONTABIL) == 9`, somando apenas as folhas da árvore contábil. O valor corrigido (~R$ 24 Bilhões acumulados) reflete a realidade.

2.  **Operadoras "Zeradas" (Parsing Numérico)**:
    *   **Problema**: Diversas operadoras apareciam com despesa zero.
    *   **Diagnóstico**: O formato numérico brasileiro (`1.000,00`) não estava sendo parseado corretamente pela biblioteca padrão, resultando em valores nulos (`NaN` convertidos para 0).
    *   **Solução**: Sanitização pré-conversão substituindo vírgulas por pontos, recuperando os dados de dezenas de operadoras.

3.  **Netting em Autogestões (Caso FCA Saúde)**:
    *   **Observação**: A operadora apresentava despesas finais próximas a zero (ex: R$ 1,02).
    *   **Validação**: Confirmado nos dados brutos que se trata de uma característica do modelo de negócio (reembolso integral), onde despesas e recuperações se anulam contabilmente. O dado estava correto.

---

## Verificação e Qualidade

*   **Testes Automatizados**: Unitários e de Integração.
*   **Script de Auditoria**: `check_db.py` incluído para validação cruzada entre arquivos brutos e banco de dados.

### 6. Cloud Readiness (Afinidade com Nuvem)

Embora o projeto tenha sido testado localmente, ele foi arquitetado seguindo os princípios de aplicações nativas de nuvem:

*   **Conteinerização**: Uso de Docker para garantir paridade entre ambientes de desenvolvimento e produção.
*   **Twelve-Factor App**: Configuração centralizada em variáveis de ambiente e processos desacoplados.
*   **Persistência de Dados**: Separação clara entre computação (FastAPI) e armazenamento (Postgres), permitindo escalabilidade horizontal.

---

Feito por Marcos Vinicius Ramos da Luz.
