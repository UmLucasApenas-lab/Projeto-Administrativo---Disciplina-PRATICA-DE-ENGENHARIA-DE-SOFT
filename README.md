# FINEASY - Processamento Inteligente de Notas Fiscais
## UniRV - Prática de Engenharia de Software (6º Período)
### Projeto Administrativo-Financeiro - Avaliação N2 (1ª Etapa)

![Projeto](https://img.shields.io/badge/projeto-FINEASY-0f766e.svg)
![Versão](https://img.shields.io/badge/versão-1.5.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)
![Cloudflare](https://img.shields.io/badge/frontend-Cloudflare_Pages-orange.svg)
![Deploy](https://img.shields.io/badge/backend-Render-46E3B7.svg)

**FINEASY** é um sistema Web completo para processamento e extração inteligente de dados de Notas Fiscais (Contas a Pagar) com classificação automática de despesas utilizando Inteligência Artificial (Google Gemini LLM).

---

## 🌐 Ambientes Hospedados em Produção

- **Frontend (Cloudflare Pages)**: [https://fineasyaiproject.pages.dev](https://fineasyaiproject.pages.dev)
- **Backend API (Render)**: [https://fineasy.onrender.com](https://fineasy.onrender.com)

---

## 🛠️ Tecnologias e Linguagens Utilizadas

Conforme orientado em aula e detalhado no anexo da lousa (**`linguagens.jpeg`**):
- **Linguagem Backend**: Python 3
- **Framework Web**: Flask
- **Linguagem Frontend**: JavaScript (ES6+), HTML5, CSS3 Moderno
- **Inteligência Artificial**: Google Gemini API (`google-genai`)
- **Processamento de Documentos**: `pypdf`, `pymupdf` (PDF Multimodal e OCR text extraction)
- **SGBD Planejado para Etapa 2**: PostgreSQL / SQLite / MySQL

---

## 📋 Regras de Negócio e Campos Obrigatórios Atendidos

Conforme o documento **`PROJETO ADMINISTRATIVO - N2 - Etapa 1.pdf`**:

| Campo Obrigatório | Detalhe |
| :--- | :--- |
| **Fornecedor** | Razão Social, Nome Fantasia e CNPJ |
| **Faturado (Destinatário)** | Nome Completo e CPF/CNPJ |
| **Número da Nota Fiscal** | Número oficial do documento (ex: `000.084.682`) |
| **Data de Emissão** | Data em formato `DD/MM/AAAA` |
| **Data de Vencimento** | Data de vencimento (*Regra*: caso não localizada, assume a data de emissão) |
| **Descrição dos Produtos** | Texto detalhado com itens adquiridos |
| **Quantidade de Parcelas** | Estruturado para 1 ou múltiplas parcelas |
| **Valor Total** | Valor total do documento em reais (R$) |
| **Classificação da Despesa** | Categoria interpretada pela IA + Lista de `termos_detectados` |

### Categorias de Despesas Suportadas
1. `INSUMOS AGRÍCOLAS` (Sementes, Fertilizantes, Defensivos, Corretivos)
2. `MANUTENÇÃO E OPERAÇÃO` (Combustíveis, Peças, Graxas, Rolamentos, Ferramentas)
3. `RECURSOS HUMANOS` (Mão de Obra Temporária, Salários e Encargos)
4. `SERVIÇOS OPERACIONAIS` (Frete e Transporte, Colheita Terceirizada, Secagem)
5. `INFRAESTRUTURA E UTILIDADES` (Energia Elétrica, Arrendamento, Materiais de Construção)
6. `ADMINISTRATIVAS` (Honorários Contábeis, Bancárias e Financeiras)
7. `SEGUROS E PROTEÇÃO` (Seguro Agrícola, Seguro de Ativos)
8. `IMPOSTOS E TAXAS` (ITR, IPTU, IPVA, INCRA-CCIR)
9. `INVESTIMENTOS` (Aquisição de Máquinas, Imóveis, Veículos)

---

## 🚀 Como Executar o Projeto Localmente

### 1. Instalar as dependências
Caso não estejam instaladas:
```bash
python -m pip install -r requirements.txt
```

### 2. Configurar a Chave do Gemini (Opcional)
Você pode adicionar sua chave gratuita no arquivo `.env`:
```env
GEMINI_API_KEY=sua_chave_aqui
```
> *Nota: Você também pode inserir sua chave diretamente pela interface clicando no botão **"Configurar API"** no cabeçalho da página, ou utilizar os exemplos incluídos que contam com processamento heurístico local imediato.*

### 3. Iniciar a Aplicação
```bash
python app.py
```
- **Acesso no Navegador**: **[http://localhost:5000](http://localhost:5000)**

---

## 📁 Estrutura de Arquivos

```text
├── agents/
│   ├── agent_extracadados.py    # Agente de extração com prompt do professor e Gemini
│   └── agent1/                  # Estrutura modular compatível com o slide do professor
├── sample_notas/                # PDFs de notas fiscais prontas para teste imediato
├── static/
│   ├── css/style.css            # Estilos refinados com design system moderno e Dark Mode
│   └── js/
│       ├── main.js              # Upload, chamadas assíncronas, tabs e cópia de JSON
│       └── theme.js             # Gerenciador global de temas (Claro/Escuro)
├── templates/
│   ├── index.html               # Aplicação Principal de Extração
│   ├── login.html               # Tela de Autenticação JWT
│   └── register.html            # Tela de Cadastro de Novos Usuários
├── utils/
│   ├── database.py              # Gestão do banco de dados SQLite e senhas seguras
│   ├── pdf_processor.py         # Leitura e extração de PDFs
│   └── generate_sample_nf.py    # Gerador de notas fiscais de teste
├── app.py                       # Servidor Flask com endpoints REST
├── requirements.txt             # Dependências Python
└── .env                         # Variáveis de ambiente
```

---

## 🖥️ Interface Gráfica Web
A interface foi construída espelhando exatamente os modelos exigidos:
- **Figura 1**: Área de upload limpa e direta com seleção de PDF e botão **"EXTRAIR DADOS"**.
- **Figura 2**: Card com dados do arquivo carregado, abas **"Visualização Formatada"** e **"JSON"**, exibindo os dados estruturados e botão funcional **"Copiar JSON"**.

---

## 🏷️ Versionamento da Aplicação

Este projeto adota as convenções de [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/):

- **`v1.5.0` (Versão Atual - Identidade Oficial FINEASY & Simplificação de Acesso)**
  - Consolidação do nome oficial do projeto: **FINEASY**.
  - Remoção do modal de rede local / QR Code obsoleto, visto que a aplicação já está totalmente hospedada na nuvem (Cloudflare Pages + Render) e com design 100% responsivo para celulares e computadores via link direto.
- **`v1.4.0` (Suporte a Modo Noturno / Dark Mode)**
  - Implementação de alternância de tema Claro/Noturno com persistência em `localStorage` e detecção de preferência do sistema operacional (`prefers-color-scheme`).
  - Paleta de cores escuras de alto contraste com foco em acessibilidade e conforto visual.
  - Disponível em todas as telas: Extrator Principal, Login e Cadastro de Usuários.
- **`v1.3.0` (Banco SQLite & Registro de Usuários)**
  - Migração de credenciais fixas para banco de dados relacional **SQLite** com senhas criptografadas (`werkzeug.security`).
  - Nova funcionalidade e tela de cadastro de novos usuários (`templates/register.html` e `/api/register`).
  - Correção de fluxo no front-end com guardas imediatos no `<head>` para evitar loops de redirecionamento ou telas em branco.
- **`v1.2.0` (Sistema de Autenticação JWT)**
  - Implementação de tela e sistema de autenticação segura via tokens JWT (`pyjwt`).
  - Proteção da rota `/api/extract` com decorator `@token_required` (Bearer Token).
  - Front-end de login responsivo (`templates/login.html`).
  - Guarda de rota no front-end com redirecionamento automático e botão de Logout.
- **`v1.1.0` (Deploy & Produção)**
  - Adição do servidor WSGI **`gunicorn`** para execução em ambiente de produção no [Render](https://render.com).
- **`v1.0.0` (Lançamento Inicial - Etapa 1 da N2)**
  - Implementação do agente de extração multimodal (`agent_extracadados.py`) integrado à API Google Gemini.
  - Classificação automática de despesas nas 9 categorias padrão do agronegócio/financeiro.
  - Processamento e leitura de PDFs com fallback heurístico.
  - Interface web responsiva em HTML5/CSS3/Vanilla JS (espelhando Figuras 1 e 2 da especificação N2).

