# Especificação de Design - FINEASY Etapa 2 (Projeto Administrativo-Financeiro)
**Universidade de Rio Verde - UniRV | Prática de Engenharia de Software (6º Período)**  
**Data:** 27/10/2026  
**Status:** Aprovado para Implementação  

---

## 1. Visão Geral e Objetivos

A **2ª Etapa** da avaliação N2 expande o sistema **FINEASY** (anteriormente focado na extração inteligente de notas fiscais via OCR e IA) para um sistema completo de gestão **Administrativo-Financeiro**.

O objetivo desta etapa é duplo:
1. **Análise e Integração Automatizada de Notas Fiscais**: Após a extração dos dados de uma NF, o sistema analisa os dados contra o Banco de Dados, verifica a existência de Fornecedor, Faturado e Classificação da Despesa, exibe o status de existência na tela e permite com um clique criar as entidades faltantes, registrando o movimento de contas a pagar e suas respectivas parcelas.
2. **Módulos Administrativos (CRUDs) Completos**: Disponibilização de telas para manutenção de cadastros seguindo estritamente as regras de negócio e de layout especificadas pela UniRV:
   - **Manter Pessoas**: Fornecedores, Clientes e Faturados.
   - **Manter Classificação**: Tipos de Despesa e Tipos de Receita.
   - **Registrar Contas**: Contas a Pagar e Contas a Receber (com suporte a rateio de despesas e múltiplas parcelas com datas distintas).

---

## 2. Requisitos e Regras de Negócio (Especificação UniRV)

### 2.1. Regras de Negócio Globais
- **Proibição de Exclusão Física**: Nenhum registro cadastral pode ser excluído do banco de dados (`DELETE`).
- **Exclusão Lógica**: Exclusões devem marcar o registro com `status = 'INATIVO'`.
- **Reativação**: Deve ser possível reativar registros com `status = 'INATIVO'`, restaurando-os para `status = 'ATIVO'`.
- **Múltiplas Classificações**: Um registro de contas a pagar pode ser classificado em um ou mais tipos de **DESPESA**; um registro de contas a receber pode ser classificado em um ou mais tipos de **RECEITA**.
- **Múltiplas Parcelas**: Uma conta (a pagar ou a receber) pode ter uma ou mais parcelas com vencimentos distintos (se apenas 1 parcela, identifica-se como `ÚNICA`; se mais de uma, como `1/N`, `2/N`, etc.).

### 2.2. Requisitos da Análise de Dados (Pós-Extração da NF)
Após a extração dos dados do documento fiscal:
1. **Consultas em Banco**:
   - **FORNECEDOR**: Consultar na base de dados por CNPJ ou Razão Social e informar se existe (com ID) ou não.
   - **FATURADO**: Consultar na base de dados por CPF ou Nome Completo e informar se existe (com ID) ou não.
   - **DESPESA**: Consultar na base de dados pela descrição da classificação e informar se existe (com ID) ou não.
2. **Exibição na Interface**:
   Exibir claramente a resposta das consultas, exatamente conforme especificado:
   ```text
   FORNECEDOR:
   <Razão Social>
   CNPJ: <CNPJ>
   NÃO EXISTE   ou   EXISTE – ID: <id>

   FATURADO:
   <Nome Completo>
   CPF: <CPF>
   EXISTE – ID: <id>   ou   NÃO EXISTE

   DESPESA:
   <Classificação da Despesa>
   EXISTE – ID: <id>   ou   NÃO EXISTE
   ```
3. **Persistência / Lançamento do Movimento**:
   Após apresentar a resposta, o sistema permite lançar o registro, executando:
   - Criar o novo Fornecedor caso não exista (`status = 'ATIVO'`);
   - Criar o novo Faturado caso não exista (`status = 'ATIVO'`);
   - Criar a nova Despesa na classificação caso não exista (`status = 'ATIVO'`);
   - Criar o novo registro em `MOVIMENTOCONTAS` (Tipo: `APAGAR`);
   - Vincular a classificação em `MOVIMENTO_CLASSIFICACOES`;
   - Criar a(s) parcela(s) em `PARCELACONTAS` com suas respectivas datas de vencimento e valores;
   - Notificar com sucesso o usuário: *"REGISTRO FOI LANÇADO COM SUCESSO."*

### 2.3. Recomendações de Layout e UX (UniRV)
Para as telas de gerenciamento (CRUDs):
- **Tabela Vazia Inicialmente**: A tabela de registros carrega vazia ao entrar na tela.
- **Carregamento por Busca ou Botão "TODOS"**:
  - Botão **TODOS** carrega todos os registros com `status = 'ATIVO'`.
  - Caixa de busca permite filtrar por mais de um elemento simultaneamente (ex: nome, documento, contato).
- **Indexação / Ordenação por Colunas**: Possibilidade de ordenar a tabela clicando nos cabeçalhos das colunas.
- **Ações na Tabela**:
  - **Editar**: Abre formulário com dados pré-preenchidos. No Update, o campo `status` permanece oculto.
  - **Excluir**: Executa exclusão lógica (muda `status` para `INATIVO`).
  - **Reativar**: Em registros inativos (se visualizados), permite restaurar para `ATIVO`.
- **Criação de Registros**:
  - No Create, o campo `status` é oculto com valor padrão `ATIVO`.

---

## 3. Arquitetura e Modelagem do Banco de Dados

Utiliza-se o SQLite nativo (`database.db`), com suporte completo a chaves estrangeiras (`PRAGMA foreign_keys = ON`).

### 3.1. Esquema Relacional

```sql
-- 1. TABELA DE PESSOAS (Fornecedores, Clientes e Faturados)
CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('FORNECEDOR', 'CLIENTE', 'CLIENTE-FORNECEDOR', 'FATURADO')),
    razao_social_nome TEXT NOT NULL,
    fantasia TEXT,
    cnpj_cpf TEXT,
    email TEXT,
    telefone TEXT,
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABELA DE CLASSIFICAÇÕES (Tipos de Despesa e Receita)
CREATE TABLE IF NOT EXISTS classificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('DESPESA', 'RECEITA')),
    descricao TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABELA DE MOVIMENTO DE CONTAS (Contas a Pagar e a Receber)
CREATE TABLE IF NOT EXISTS movimento_contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('APAGAR', 'ARECEBER')),
    numero_documento TEXT,
    descricao TEXT,
    data_emissao TEXT,
    valor_total REAL NOT NULL,
    pessoa_fornecedor_id INTEGER,
    pessoa_faturado_id INTEGER,
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pessoa_fornecedor_id) REFERENCES pessoas(id),
    FOREIGN KEY (pessoa_faturado_id) REFERENCES pessoas(id)
);

-- 4. TABELA INTERMEDIÁRIA MOVIMENTO_CLASSIFICAÇÕES (1..N Classificações)
CREATE TABLE IF NOT EXISTS movimento_classificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movimento_id INTEGER NOT NULL,
    classificacao_id INTEGER NOT NULL,
    valor REAL,
    percentual REAL,
    FOREIGN KEY (movimento_id) REFERENCES movimento_contas(id) ON DELETE CASCADE,
    FOREIGN KEY (classificacao_id) REFERENCES classificacoes(id)
);

-- 5. TABELA DE PARCELAS DE CONTAS (1..N Parcelas)
CREATE TABLE IF NOT EXISTS parcela_contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movimento_id INTEGER NOT NULL,
    numero_parcela INTEGER NOT NULL,
    total_parcelas INTEGER NOT NULL,
    identificacao TEXT NOT NULL, -- Ex: 'ÚNICA', '1/3', '2/3', '3/3'
    data_vencimento TEXT NOT NULL,
    valor REAL NOT NULL,
    status_pagamento TEXT NOT NULL DEFAULT 'PENDENTE' CHECK(status_pagamento IN ('PENDENTE', 'PAGO', 'CANCELADO')),
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movimento_id) REFERENCES movimento_contas(id) ON DELETE CASCADE
);
```

---

## 4. Design da API Backend (Flask)

Todos os endpoints são servidos em `/api/*`, autenticados por JWT quando aplicável e retornando JSON padronizado.

### 4.1. Análise e Lançamento de NF
- `POST /api/analise`:
  - Entrada: `{ "fornecedor": {...}, "faturado": {...}, "classificacao": {...} }`
  - Saída: Status de existência de cada item (`existe: true/false`, `id: int | null`, `registro: obj`).
- `POST /api/movimentos/lancar-automatico`:
  - Entrada: Objeto completo com dados da NF, Fornecedor, Faturado, Classificação e Parcelas.
  - Execução: Transação ACID para criar entidades não existentes, inserir movimento e parcelas.
  - Saída: `{ "success": true, "message": "REGISTRO FOI LANÇADO COM SUCESSO.", "movimento_id": int }`.

### 4.2. CRUD Pessoas (`/api/pessoas`)
- `GET /api/pessoas`: Parâmetros: `q` (busca por nome, documento ou telefone), `tipo`, `todos` (se 1, ignora busca vazia), `status` (padrão `ATIVO`, opcional `TODOS` ou `INATIVO`).
- `POST /api/pessoas`: Criação com `status = 'ATIVO'` forçado.
- `PUT /api/pessoas/<id>`: Atualização de dados cadastrais.
- `DELETE /api/pessoas/<id>`: Exclusão lógica (`UPDATE pessoas SET status = 'INATIVO'`).
- `PATCH /api/pessoas/<id>/reativar`: Reativação (`UPDATE pessoas SET status = 'ATIVO'`).

### 4.3. CRUD Classificações (`/api/classificacoes`)
- `GET /api/classificacoes`: Filtros por `q`, `tipo` (`DESPESA` ou `RECEITA`), `status`.
- `POST /api/classificacoes`: Cadastro de nova classificação (`status = 'ATIVO'`).
- `PUT /api/classificacoes/<id>`: Edição da descrição.
- `DELETE /api/classificacoes/<id>`: Exclusão lógica (`status = 'INATIVO'`).
- `PATCH /api/classificacoes/<id>/reativar`: Reativação (`status = 'ATIVO'`).

### 4.4. CRUD Contas e Parcelas (`/api/contas`)
- `GET /api/contas`: Filtro por `tipo` (`APAGAR` ou `ARECEBER`), `q` (número doc, nome pessoa), `status`. Traz resumo com quantidade de parcelas e status de pagamento.
- `GET /api/contas/<id>`: Detalhes do movimento, itens de rateio e lista completa de parcelas.
- `POST /api/contas`: Cadastro manual de conta com 1..N parcelas e 1..N classificações.
- `DELETE /api/contas/<id>`: Exclusão lógica do movimento e suas parcelas.
- `PATCH /api/contas/<id>/reativar`: Reativação do movimento.

---

## 5. Design de Interface (Frontend)

### 5.1. Layout SPA com Sidebar Unificada
A interface adota navegação moderna e responsiva mantendo a estética premium e modo noturno:
- **Barra Lateral (Sidebar)**:
  - 📄 **Extrator de Notas**: Visualizador da NF + Painel de Análise (Página 2 do PDF) com os blocos de Fornecedor, Faturado e Despesa + Botão "Lançar Registro".
  - 👥 **Pessoas**: Telas para Fornecedores, Clientes e Faturados.
  - 🏷️ **Classificações**: Tipos de Despesas e Receitas.
  - 💳 **Contas**: Gestão e consulta de Contas a Pagar e a Receber.
  - 🚪 **Logout & Tema**: Alternador Claro/Escuro e encerramento de sessão.

### 5.2. Componente de Consulta e Tabela Dinâmica
Para cada módulo administrativo:
- Barra de filtros com campo de busca multi-elemento (`input`), botão **Buscar** e botão **Todos**.
- Botão primário **+ Inserir Novo [Registro]**.
- Tabela com ordenação clicável nos cabeçalhos (`th`).
- Linhas com badges de status (`ATIVO` em verde, `INATIVO` em cinza).
- Coluna de Ações:
  - Botão **Editar** (abre modal moderno pré-preenchido).
  - Botão **Excluir** (exclusão lógica com confirmação visual).
  - Botão **Reativar** (visível quando visualizados registros inativos).

---

## 6. Estratégia de Testes e Validação
1. **Banco de Dados**: Teste das operações CRUD, garantia de não-exclusão física e cascata de inativação.
2. **Análise Pós-Extração**:
   - Teste de documento com Fornecedor existente vs inexistente.
   - Teste com Faturado existente vs inexistente.
   - Teste com Despesa existente vs inexistente.
   - Teste de Lançamento Automático: verificação das inserções em `pessoas`, `classificacoes`, `movimento_contas` e `parcela_contas`.
3. **Regras de Negócio UniRV**:
   - Validação da tabela vazia por padrão.
   - Validação do botão "TODOS" carregando apenas registros `status = 'ATIVO'`.
   - Validação de busca por múltiplos termos.
   - Validação de exclusão lógica e reativação.
4. **Deploy**:
   - Garantir compatibilidade no Render e Cloudflare Pages.
