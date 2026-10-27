# FINEASY Etapa 2 - Sistema Administrativo-Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expandir o FINEASY com cruzamento automatizado pós-extração de notas fiscais (análise de Fornecedor, Faturado e Despesa com lançamento automático transacional) e módulos administrativos completos (CRUD de Pessoas, Classificações e Contas a Pagar/Receber) com suporte a soft-delete, reativação e layout padrão UniRV.

**Architecture:** Monólito modular baseado em Flask e SQLite nativo (`database.db`), com camada de banco de dados relacional com integridade referencial e exclusão lógica (`status = 'ATIVO'/'INATIVO'`). No frontend, aplicação SPA moderna e responsiva em Vanilla JS com navegação por Sidebar/Tabs, integrando a tela de extração inteligente às interfaces administrativas.

**Tech Stack:** Python 3, Flask, SQLite3, Werkzeug Security, PyJWT, Vanilla JavaScript (ES6+), HTML5, CSS3 Moderno (Light/Dark mode). Testes com `unittest` da biblioteca padrão do Python.

**Spec:** `docs/superpowers/specs/2026-10-27-etapa2-administrativo-financeiro-design.md`

## Global Constraints

- Proibição absoluta de exclusão física (`DELETE`) em entidades cadastrais; deve-se usar exclusão lógica (`status = 'INATIVO'`).
- Todo cadastro novo deve receber implicitamente `status = 'ATIVO'`.
- Deve existir suporte a reativação de qualquer registro inativo (`status = 'ATIVO'`).
- Tabela de listagem nos módulos administrativos deve iniciar vazia; registros são carregados apenas por busca ou botão "TODOS".
- O botão "TODOS" deve filtrar estritamente registros com `status = 'ATIVO'`.
- Suporte a múltiplas classificações para um mesmo movimento e múltiplas parcelas com datas de vencimento distintas.
- Manter compatibilidade com os deploys ativos no Render (backend) e Cloudflare Pages (frontend estático).

## Review Focus

1. **Tentativa de exclusão física**: Execução de chamada de exclusão não pode remover linhas do banco, apenas marcar `status = 'INATIVO'`.
2. **Duplicação de fornecedor ou faturado no lançamento automático**: Se um fornecedor com o mesmo CNPJ (ou faturado com mesmo CPF) já existir, reutilizar o ID existente em vez de duplicar.
3. **Formatação heterogênea de CNPJ/CPF**: Busca e verificação devem normalizar documentos (com ou sem pontuação: `11.111.111/0001-00` vs `11111111000100`).
4. **Vencimento ausente ou com múltiplas parcelas**: Se a NF tiver parcela única, gerar identificação `'ÚNICA'`; se tiver $N$ parcelas, criar exatamente $N$ registros em `parcela_contas`.
5. **Busca multi-termo nas telas administrativas**: O filtro de busca deve pesquisar simultaneamente em nome/razão social, CPF/CNPJ e outros campos relevantes.

---

### Task 1: Modelagem e Migração do Banco de Dados Relacional

**Files:**
- Modify: `utils/database.py`
- Test: `tests/test_database_etapa2.py`

**Interfaces:**
- Consumes: Conexão SQLite existente em `utils/database.py` (`get_db_connection`).
- Produces: 
  - `init_db()` estendido com criação das tabelas `pessoas`, `classificacoes`, `movimento_contas`, `movimento_classificacoes`, `parcela_contas`.
  - Funções de acesso: `get_pessoas()`, `get_pessoa_by_id()`, `save_pessoa()`, `soft_delete_pessoa()`, `reactivate_pessoa()`.
  - Funções de classificação: `get_classificacoes()`, `save_classificacao()`, `soft_delete_classificacao()`, `reactivate_classificacao()`.

- [x] **Step 1: Escrever teste de unidade para o esquema relacional e exclusão lógica**
Criar `tests/test_database_etapa2.py` testando criação de tabelas, inserção com `status='ATIVO'`, exclusão lógica alterando para `'INATIVO'` e reativação.

- [x] **Step 2: Executar teste para verificar falha inicial**
Run: `python -m unittest tests/test_database_etapa2.py -v`
Expected: FAIL (tabelas e funções ainda não existem).

- [x] **Step 3: Implementar as tabelas e funções em `utils/database.py`**
Adicionar DDL das tabelas relacionais com `PRAGMA foreign_keys = ON`, `CHECK(status IN ('ATIVO', 'INATIVO'))` e métodos auxiliares para consultas, soft delete e reativação.

- [x] **Step 4: Executar testes de banco para verificar sucesso**
Run: `python -m unittest tests/test_database_etapa2.py -v`
Expected: PASS.

- [x] **Step 5: Commit**
```bash
git add utils/database.py tests/test_database_etapa2.py
git commit -m "feat(db): implementar schema relacional da etapa 2 com soft-delete e reativacao"
```

---

### Task 2: Endpoints REST dos Módulos Básicos (Pessoas e Classificações)

**Files:**
- Modify: `app.py`
- Test: `tests/test_api_crud_basico.py`

**Interfaces:**
- Consumes: Funções de `utils/database.py` para Pessoas e Classificações.
- Produces:
  - Rotas `/api/pessoas` (GET, POST, PUT, DELETE, PATCH `/api/pessoas/<id>/reativar`)
  - Rotas `/api/classificacoes` (GET, POST, PUT, DELETE, PATCH `/api/classificacoes/<id>/reativar`)

- [x] **Step 1: Escrever teste de API para CRUD de Pessoas e Classificações**
Criar `tests/test_api_crud_basico.py` cobrindo: busca com filtros múltiplos, listagem vazia se sem parâmetros, botão "TODOS" retornando apenas `status='ATIVO'`, exclusão lógica e reativação.

- [x] **Step 2: Executar teste para verificar falha inicial**
Run: `python -m unittest tests/test_api_crud_basico.py -v`
Expected: FAIL (rotas retornam 404).

- [x] **Step 3: Implementar endpoints em `app.py`**
Implementar as rotas `/api/pessoas` e `/api/classificacoes` validando campos obrigatórios, aplicando `status='ATIVO'` oculto no cadastro e tratando soft-delete no DELETE.

- [x] **Step 4: Executar testes de API para verificar sucesso**
Run: `python -m unittest tests/test_api_crud_basico.py -v`
Expected: PASS.

- [x] **Step 5: Commit**
```bash
git add app.py tests/test_api_crud_basico.py
git commit -m "feat(api): implementar endpoints CRUD de pessoas e classificacoes"
```

---

### Task 3: Serviço de Análise Pós-Extração e Lançamento Automático

**Files:**
- Create: `agents/agent_analise.py`
- Modify: `app.py`
- Modify: `utils/database.py`
- Test: `tests/test_analise_e_lancamento.py`

**Interfaces:**
- Consumes: Dados JSON extraídos da NF pelo `agent_extracadados.py` e tabelas de banco.
- Produces:
  - `POST /api/analise`: Retorna `{ "fornecedor": { "existe": bool, "id": int|null, ... }, "faturado": { "existe": bool, "id": int|null, ... }, "despesa": { "existe": bool, "id": int|null, ... } }`.
  - `POST /api/movimentos/lancar-automatico`: Cria entidades não existentes, registra `movimento_contas`, vincula `movimento_classificacoes` e gera `parcela_contas`. Retorna `"REGISTRO FOI LANÇADO COM SUCESSO."`.

- [x] **Step 1: Escrever teste para análise e lançamento transacional**
Criar `tests/test_analise_e_lancamento.py` validando:
- NF com Fornecedor e Faturado inexistentes -> retorna `existe=False`.
- Chamada de lançamento -> cria Fornecedor, Faturado, Despesa, Movimento e Parcelas.
- Segunda chamada de análise -> agora retorna `existe=True` com os IDs recém-criados.

- [x] **Step 2: Executar teste para verificar falha inicial**
Run: `python -m unittest tests/test_analise_e_lancamento.py -v`
Expected: FAIL.

- [x] **Step 3: Implementar `agents/agent_analise.py` e rotas em `app.py`**
Criar a classe `AgentAnalise` com métodos de busca normalizada (removendo pontos, traços e barras para comparação de CNPJ/CPF) e a função transacional de gravação completa.

- [x] **Step 4: Executar testes para verificar sucesso**
Run: `python -m unittest tests/test_analise_e_lancamento.py -v`
Expected: PASS.

- [x] **Step 5: Commit**
```bash
git add agents/agent_analise.py app.py utils/database.py tests/test_analise_e_lancamento.py
git commit -m "feat(analise): implementar motor de analise pos-extracao e lancamento automatico"
```

---

### Task 4: Endpoints e Gestão de Contas a Pagar e a Receber

**Files:**
- Modify: `app.py`
- Modify: `utils/database.py`
- Test: `tests/test_api_contas.py`

**Interfaces:**
- Consumes: Tabelas `movimento_contas`, `movimento_classificacoes` e `parcela_contas`.
- Produces:
  - `GET /api/contas`: Lista contas filtrando por tipo (`APAGAR` / `ARECEBER`), busca e status.
  - `GET /api/contas/<id>`: Detalhes com pessoas vinculadas, classificações e lista de parcelas.
  - `POST /api/contas`: Cadastro manual de conta com parcelas e rateios.
  - `DELETE /api/contas/<id>`: Exclusão lógica do movimento e suas parcelas associadas.
  - `PATCH /api/contas/<id>/reativar`: Reativação do movimento.

- [x] **Step 1: Escrever teste de API para gestão de contas e parcelas**
Criar `tests/test_api_contas.py` testando listagem com resumo, busca de detalhes com parcelas, exclusão lógica em cascata e reativação.

- [x] **Step 2: Executar teste para verificar falha inicial**
Run: `python -m unittest tests/test_api_contas.py -v`
Expected: FAIL.

- [x] **Step 3: Implementar métodos em `utils/database.py` e endpoints em `app.py`**
Adicionar queries com JOINs para trazer dados consolidados de movimento, credor/devedor e parcelas.

- [x] **Step 4: Executar testes de contas para verificar sucesso**
Run: `python -m unittest tests/test_api_contas.py -v`
Expected: PASS.

- [x] **Step 5: Commit**
```bash
git add app.py utils/database.py tests/test_api_contas.py
git commit -m "feat(contas): implementar endpoints de contas a pagar/receber e parcelas"
```

---

### Task 5: Frontend - Painel de Análise e Lançamento Pós-Extração (Páginas 1 e 2 do PDF)

**Files:**
- Modify: `templates/index.html`
- Modify: `static/js/main.js`
- Modify: `static/css/style.css`

**Interfaces:**
- Consumes: Endpoints `/api/analise` e `/api/movimentos/lancar-automatico`.
- Produces: Cartão visual com o formato exigido na Página 2 do PDF após a extração da NF, contendo badges coloridos (`EXISTE - ID: X` em verde/azul ou `NÃO EXISTE` em vermelho), botão "Lançar no Sistema Financeiro" e alerta de sucesso "REGISTRO FOI LANÇADO COM SUCESSO."

- [x] **Step 1: Atualizar `templates/index.html` com o contêiner do painel de análise**
Inserir o bloco estrutural do Painel de Análise logo abaixo do resultado da extração da NF.

- [x] **Step 2: Implementar lógica de renderização e chamada de lançamento em `static/js/main.js`**
Após o retorno da extração, disparar a análise contra o banco, exibir os blocos de Fornecedor, Faturado e Despesa com seus respectivos IDs/status e conectar o clique do botão de lançamento ao endpoint transacional.

- [x] **Step 3: Estilizar componentes de análise em `static/css/style.css`**
Adicionar estilos modernos para os cards de existência, badges de status, botões de ação e modal/notificação de sucesso (suportando temas Claro e Escuro).

- [x] **Step 4: Validar manualmente com a NF de exemplo e checar visualmente**
Testar a extração e conferir a exibição exata da resposta na tela.

- [x] **Step 5: Commit**
```bash
git add templates/index.html static/js/main.js static/css/style.css
git commit -m "feat(ui): implementar painel de analise pos-extracao e lancamento automatico"
```

---

### Task 6: Frontend - Estrutura SPA com Sidebar e Módulos CRUD UniRV

**Files:**
- Modify: `templates/index.html`
- Modify: `static/js/main.js`
- Modify: `static/css/style.css`

**Interfaces:**
- Consumes: Endpoints `/api/pessoas`, `/api/classificacoes`, `/api/contas`.
- Produces: 
  - Barra de navegação lateral (Sidebar) permitindo alternar entre "Extrator de NF", "Manter Pessoas", "Manter Classificações" e "Registrar Contas".
  - Telas de listagem para cada entidade com: tabela vazia inicial, campo de busca multi-termo, botão "Buscar", botão "Todos" (`status=ATIVO`), ordenação por cabeçalho, botão "+ Inserir Novo", modal de cadastro/edição e botões de ação "Editar" / "Excluir (Lógico)" / "Reativar".

- [x] **Step 1: Implementar Sidebar e seções de visualização em `templates/index.html`**
Criar containers semânticos para cada módulo administrativo e os modais genéricos reutilizáveis de cadastro/edição.

- [x] **Step 2: Implementar controladores frontend de listagem, busca, ordenação e CRUD em `static/js/main.js`**
Adicionar funções para carregamento assíncrono, filtro de busca, ordenação de colunas da tabela ao clicar no `<th>`, envio de formulários e inativação/reativação lógica.

- [x] **Step 3: Ajustar estilos da Sidebar, tabelas dinâmicas e formulários em `static/css/style.css`**
Garantir alinhamento com os requisitos da UniRV (página 5 do PDF), mantendo visual limpo, espaçamentos consistentes e responsividade para dispositivos móveis.

- [x] **Step 4: Validar navegação e interações das tabelas**
Verificar se a tabela inicia vazia, se o botão "Todos" traz ativos e se as ações de editar e inativar funcionam corretamente.

- [x] **Step 5: Commit**
```bash
git add templates/index.html static/js/main.js static/css/style.css
git commit -m "feat(ui): implementar sidebar e telas de crud administrativo padrao unirv"
```

---

### Task 7: Testes Integrados de Ponta a Ponta, Documentação e Validação Final

**Files:**
- Create: `tests/test_fluxo_completo_e2e.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: Todo o sistema integrado (banco, backend, APIs e regras da 2ª Etapa).
- Produces: Teste de ponta a ponta validando o ciclo de vida completo e documentação atualizada para entrega N2.

- [x] **Step 1: Escrever teste de integração E2E**
Criar `tests/test_fluxo_completo_e2e.py` que executa todo o fluxo:
1. Extração simulada de NF;
2. Análise verificando inexistência;
3. Lançamento automático gerando IDs;
4. Segunda análise comprovando existência (`EXISTE - ID: X`);
5. Consulta de Pessoas via `/api/pessoas?todos=1` confirmando presença de Fornecedor e Faturado;
6. Consulta de Contas via `/api/contas?todos=1` confirmando movimento e parcelas;
7. Inativação lógica e reativação comprovando não exclusão física.

- [x] **Step 2: Executar todos os testes do projeto**
Run: `python -m unittest discover -s tests -p "test_*.py" -v`
Expected: ALL PASS.

- [x] **Step 3: Atualizar documentação `README.md`**
Atualizar o README descrevendo as novas funcionalidades da 2ª Etapa, endpoints adicionados, instruções de execução e regras atendidas.

- [x] **Step 4: Commit**
```bash
git add tests/test_fluxo_completo_e2e.py README.md
git commit -m "docs: atualizar readme e testes integrados e2e para entrega da etapa 2"
```
