# UniRV - Prática de Engenharia de Software (6º Período)
## Projeto Administrativo-Financeiro - Avaliação N2 (1ª Etapa)

Sistema Web para processamento e extração inteligente de dados de Notas Fiscais (Contas a Pagar) com classificação automática de despesas utilizando IA (Google Gemini LLM).

---

## 🛠️ Tecnologias e Linguagens Utilizadas

Conforme orientado em aula e detalhado no anexo da lousa (**`linguagens.jpeg`**):
- **Linguagem Backend**: Python 3
- **Framework Web**: Flask
- **Linguagem Frontend**: JavaScript (ES6+), HTML5, CSS3 Moderno
- **Inteligência Artificial**: Google Gemini API (`google-genai`)
- **Processamento de Documentos**: `pypdf`, `pymupdf` (PDF Multimodal e OCR text extraction)
- **SGBD Planejado para Etapa 2**: PostgreSQL / MySQL

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

## 🚀 Como Executar o Projeto

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
> *Nota: Você também pode inserir sua chave diretamente pela interface clicando no botão **"Configurar API Gemini"** no canto superior direito, ou utilizar os exemplos incluídos que contam com processamento heurístico local imediato.*

### 3. Iniciar a Aplicação
```bash
python app.py
```
Acesse no seu navegador: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📁 Estrutura de Arquivos

```text
├── agents/
│   ├── agent_extracadados.py    # Agente de extração com prompt do professor e Gemini
│   └── agent1/                  # Estrutura modular compatível com o slide do professor
├── sample_notas/                # PDFs de notas fiscais prontas para teste imediato
├── static/
│   ├── css/style.css            # Estilos refinados com design system moderno
│   └── js/main.js               # Upload, chamadas assíncronas, tabs e cópia de JSON
├── templates/
│   └── index.html               # Interface Web fiel às Figuras 1 e 2 da N2
├── utils/
│   ├── pdf_processor.py         # Leitura e extração de PDFs
│   └── generate_sample_nf.py    # Gerador de notas fiscais de teste
├── app.py                       # Servidor Flask com endpoints da API
├── requirements.txt             # Dependências Python
└── .env                         # Variáveis de ambiente
```

---

## 🖥️ Interface Gráfica Web
A interface foi construída espelhando exatamente os modelos exigidos:
- **Figura 1**: Área de upload limpa e direta com seleção de PDF e botão **"EXTRAIR DADOS"**.
- **Figura 2**: Card com dados do arquivo carregado, abas **"Visualização Formatada"** e **"JSON"**, exibindo os dados estruturados e botão funcional **"Copiar JSON"**.
