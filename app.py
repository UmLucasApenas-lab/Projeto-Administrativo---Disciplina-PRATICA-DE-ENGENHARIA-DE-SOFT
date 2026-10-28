import os
import socket
import datetime
from functools import wraps
import jwt
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from agents.agent_extracadados import Agent1
from agents.agent_analise import AgentAnalise
from utils.database import (
    init_db, create_user, verify_user_credentials,
    save_pessoa, update_pessoa, get_pessoa_by_id, get_pessoas, soft_delete_pessoa, reactivate_pessoa,
    save_classificacao, update_classificacao, get_classificacao_by_id, get_classificacoes, soft_delete_classificacao, reactivate_classificacao,
    save_produto, update_produto, get_produto_by_id, get_produtos, soft_delete_produto, reactivate_produto,
    save_movimento_completo, get_movimento_by_id, get_movimentos, soft_delete_movimento, reactivate_movimento,
    get_dashboard_stats
)

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "X-Gemini-Key", "Authorization"])

JWT_SECRET = os.getenv("JWT_SECRET", "unirv-secret-jwt-key-n2-avaliacao-2026-super-segura")
JWT_ALGORITHM = "HS256"
AUTH_EMAIL = os.getenv("AUTH_EMAIL", "admin@unirv.edu.br")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin123")

def generate_token(email):
    payload = {
        "sub": email,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token de autenticação não fornecido."}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Formato de token inválido. Use 'Bearer <token>'."}), 401

        token = parts[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.user_email = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Sessão expirada. Faça login novamente."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido ou não autorizado."}), 401

        return f(*args, **kwargs)
    return decorated

agent = Agent1()
agent_analise = AgentAnalise()
init_db()

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/login')
@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/register')
@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or request.form
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()

    if not email or not password:
        return jsonify({"error": "E-mail e senha são obrigatórios."}), 400

    if len(password) < 6:
        return jsonify({"error": "A senha deve ter no mínimo 6 caracteres."}), 400

    if '@' not in email or '.' not in email:
        return jsonify({"error": "Por favor, informe um e-mail válido."}), 400

    user_id, error = create_user(email, password, name)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "success": True,
        "message": "Conta criada com sucesso! Faça login para continuar."
    }), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({"error": "E-mail e senha são obrigatórios."}), 400

    user = verify_user_credentials(email, password)
    if user:
        token = generate_token(user['email'])
        return jsonify({
            "success": True,
            "message": "Login realizado com sucesso!",
            "token": token,
            "user": {
                "email": user['email'],
                "name": user['name'] or user['email']
            }
        }), 200
    else:
        return jsonify({"error": "Credenciais inválidas. Verifique seu e-mail e senha."}), 401

@app.route('/api/status', methods=['GET'])
def api_status():
    env_key = os.getenv("GEMINI_API_KEY")
    has_key = bool(env_key and env_key.strip() != "sua_chave_gemini_aqui")
    return jsonify({
        "app_name": "FINEASY",
        "status": "online",
        "has_gemini_key": has_key,
        "framework": "Flask (Python)",
        "version": "1.5.0"
    })

@app.route('/api/extract', methods=['POST'])
@token_required
def extract_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "Nenhum arquivo PDF foi enviado na requisição."}), 400

    uploaded_file = request.files['pdf_file']

    if uploaded_file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    if not uploaded_file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Formato inválido. O arquivo deve ser um PDF."}), 400

    custom_api_key = request.headers.get('X-Gemini-Key') or request.form.get('api_key')

    try:
        dados_extraidos = agent.extract_pdf_data(uploaded_file, custom_api_key=custom_api_key)
        return jsonify(dados_extraidos), 200
    except Exception as e:
        print(f"Erro no processamento da NF: {e}")
        return jsonify({
            "error": "Falha ao processar o documento",
            "detalhes": str(e)
        }), 500

@app.route('/sample_notas/<path:filename>')
def serve_sample_pdf(filename):
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_notas')
    return send_from_directory(samples_dir, filename)

# ==============================================================================
# ENDPOINTS REST: GESTÃO DE PESSOAS (Fornecedores, Clientes, Faturados)
# ==============================================================================
@app.route('/api/pessoas', methods=['GET'])
def api_get_pessoas():
    q = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', '').strip()
    status = request.args.get('status', 'ATIVO').strip()
    todos = request.args.get('todos', '0').strip() in ('1', 'true', 'True')
    pessoas = get_pessoas(q=q, tipo=tipo, status=status, todos=todos)
    return jsonify(pessoas), 200

@app.route('/api/pessoas/<int:pessoa_id>', methods=['GET'])
def api_get_pessoa(pessoa_id):
    pessoa = get_pessoa_by_id(pessoa_id)
    if not pessoa:
        return jsonify({"error": "Pessoa não encontrada"}), 404
    return jsonify(pessoa), 200

@app.route('/api/pessoas', methods=['POST'])
def api_create_pessoa():
    data = request.get_json(silent=True) or request.form
    if not data or not data.get('razao_social_nome'):
        return jsonify({"error": "Nome ou Razão Social é obrigatório"}), 400

    pessoa_id = save_pessoa(dict(data))
    return jsonify({
        "success": True,
        "message": "Pessoa cadastrada com sucesso!",
        "id": pessoa_id
    }), 201

@app.route('/api/pessoas/<int:pessoa_id>', methods=['PUT'])
def api_update_pessoa(pessoa_id):
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    updated = update_pessoa(pessoa_id, dict(data))
    if not updated:
        return jsonify({"error": "Pessoa não encontrada para atualização"}), 404

    return jsonify({"success": True, "message": "Pessoa atualizada com sucesso!"}), 200

@app.route('/api/pessoas/<int:pessoa_id>', methods=['DELETE'])
def api_delete_pessoa(pessoa_id):
    # Exclusão lógica: altera status para INATIVO
    success = soft_delete_pessoa(pessoa_id)
    if not success:
        return jsonify({"error": "Pessoa não encontrada"}), 404
    return jsonify({"success": True, "message": "Cadastro inativado com sucesso!"}), 200

@app.route('/api/pessoas/<int:pessoa_id>/reativar', methods=['PATCH'])
def api_reactivate_pessoa(pessoa_id):
    # Reativação lógica: retorna status para ATIVO
    success = reactivate_pessoa(pessoa_id)
    if not success:
        return jsonify({"error": "Pessoa não encontrada"}), 404
    return jsonify({"success": True, "message": "Cadastro reativado com sucesso!"}), 200

# ==============================================================================
# ENDPOINTS REST: CLASSIFICAÇÃO FINANCEIRA (Despesas e Receitas)
# ==============================================================================
@app.route('/api/classificacoes', methods=['GET'])
def api_get_classificacoes():
    q = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', '').strip()
    status = request.args.get('status', 'ATIVO').strip()
    todos = request.args.get('todos', '0').strip() in ('1', 'true', 'True')
    classificacoes = get_classificacoes(q=q, tipo=tipo, status=status, todos=todos)
    return jsonify(classificacoes), 200

@app.route('/api/classificacoes/<int:classif_id>', methods=['GET'])
def api_get_classificacao(classif_id):
    classif = get_classificacao_by_id(classif_id)
    if not classif:
        return jsonify({"error": "Classificação não encontrada"}), 404
    return jsonify(classif), 200

@app.route('/api/classificacoes', methods=['POST'])
def api_create_classificacao():
    data = request.get_json(silent=True) or request.form
    if not data or not data.get('descricao'):
        return jsonify({"error": "Descrição da classificação é obrigatória"}), 400

    classif_id = save_classificacao(dict(data))
    return jsonify({
        "success": True,
        "message": "Classificação cadastrada com sucesso!",
        "id": classif_id
    }), 201

@app.route('/api/classificacoes/<int:classif_id>', methods=['PUT'])
def api_update_classificacao(classif_id):
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    updated = update_classificacao(classif_id, dict(data))
    if not updated:
        return jsonify({"error": "Classificação não encontrada para atualização"}), 404

    return jsonify({"success": True, "message": "Classificação atualizada com sucesso!"}), 200

@app.route('/api/classificacoes/<int:classif_id>', methods=['DELETE'])
def api_delete_classificacao(classif_id):
    success = soft_delete_classificacao(classif_id)
    if not success:
        return jsonify({"error": "Classificação não encontrada"}), 404
    return jsonify({"success": True, "message": "Classificação inativada com sucesso!"}), 200

@app.route('/api/classificacoes/<int:classif_id>/reativar', methods=['PATCH'])
def api_reactivate_classificacao(classif_id):
    success = reactivate_classificacao(classif_id)
    if not success:
        return jsonify({"error": "Classificação não encontrada"}), 404
    return jsonify({"success": True, "message": "Classificação reativada com sucesso!"}), 200

# ==============================================================================
# ENDPOINTS REST: PRODUTOS E INSUMOS (Extraídos / Agrícolas)
# ==============================================================================
@app.route('/api/produtos', methods=['GET'])
def api_get_produtos():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'ATIVO').strip()
    todos = request.args.get('todos', '0').strip() in ('1', 'true', 'True')
    if request.args.get('incluir_inativos', '0').strip() in ('1', 'true', 'True'):
        status = 'TODOS'
    produtos = get_produtos(q=q, status=status, todos=todos)
    return jsonify(produtos), 200

@app.route('/api/produtos/<int:produto_id>', methods=['GET'])
def api_get_produto(produto_id):
    produto = get_produto_by_id(produto_id)
    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404
    return jsonify(produto), 200

@app.route('/api/produtos', methods=['POST'])
def api_create_produto():
    data = request.get_json(silent=True) or request.form
    if not data or not data.get('descricao'):
        return jsonify({"error": "Descrição do produto é obrigatória"}), 400

    produto_id = save_produto(dict(data))
    return jsonify({
        "success": True,
        "message": "Produto cadastrado com sucesso!",
        "id": produto_id
    }), 201

@app.route('/api/produtos/<int:produto_id>', methods=['PUT'])
def api_update_produto(produto_id):
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    updated = update_produto(produto_id, dict(data))
    if not updated:
        return jsonify({"error": "Produto não encontrado para atualização"}), 404

    return jsonify({"success": True, "message": "Produto atualizado com sucesso!"}), 200

@app.route('/api/produtos/<int:produto_id>', methods=['DELETE'])
def api_delete_produto(produto_id):
    success = soft_delete_produto(produto_id)
    if not success:
        return jsonify({"error": "Produto não encontrado"}), 404
    return jsonify({"success": True, "message": "Produto inativado com sucesso!"}), 200

@app.route('/api/produtos/<int:produto_id>/reativar', methods=['PATCH'])
def api_reactivate_produto(produto_id):
    success = reactivate_produto(produto_id)
    if not success:
        return jsonify({"error": "Produto não encontrado"}), 404
    return jsonify({"success": True, "message": "Produto reativado com sucesso!"}), 200

# ==============================================================================
# ENDPOINTS REST: ANÁLISE PÓS-EXTRAÇÃO E LANÇAMENTO AUTOMÁTICO (2ª ETAPA)
# ==============================================================================
@app.route('/api/analise', methods=['POST'])
def api_analisar_nf():
    data = request.get_json(silent=True) or {}
    try:
        resultado = agent_analise.analisar_dados_nf(data)
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro na análise de NF: {e}")
        return jsonify({"error": "Falha na análise dos dados", "detalhes": str(e)}), 500

@app.route('/api/movimentos/lancar-automatico', methods=['POST'])
def api_lancar_movimento_automatico():
    data = request.get_json(silent=True) or {}
    try:
        resultado = agent_analise.lancar_registro_automatico(data)
        return jsonify(resultado), 201
    except Exception as e:
        print(f"Erro no lançamento automático: {e}")
        return jsonify({"error": "Falha ao lançar movimento", "detalhes": str(e)}), 500

# ==============================================================================
# ENDPOINTS REST: REGISTRAR CONTAS (A Pagar / A Receber e Parcelas)
# ==============================================================================
@app.route('/api/contas', methods=['GET'])
def api_get_contas():
    q = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', '').strip()
    status = request.args.get('status', 'ATIVO').strip()
    todos = request.args.get('todos', '0').strip() in ('1', 'true', 'True')
    contas = get_movimentos(q=q, tipo=tipo, status=status, todos=todos)
    return jsonify(contas), 200

@app.route('/api/contas/<int:conta_id>', methods=['GET'])
def api_get_conta_detalhes(conta_id):
    conta = get_movimento_by_id(conta_id)
    if not conta:
        return jsonify({"error": "Conta não encontrada"}), 404
    return jsonify(conta), 200

@app.route('/api/contas', methods=['POST'])
def api_create_conta():
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    try:
        movimento_id = save_movimento_completo(dict(data))
        return jsonify({
            "success": True,
            "message": "Conta registrada com sucesso!",
            "id": movimento_id
        }), 201
    except Exception as e:
        print(f"Erro ao salvar conta: {e}")
        return jsonify({"error": "Falha ao registrar conta", "detalhes": str(e)}), 400

@app.route('/api/contas/<int:conta_id>', methods=['DELETE'])
def api_delete_conta(conta_id):
    success = soft_delete_movimento(conta_id)
    if not success:
        return jsonify({"error": "Conta não encontrada"}), 404
    return jsonify({"success": True, "message": "Conta inativada com sucesso!"}), 200

@app.route('/api/contas/<int:conta_id>/reativar', methods=['PATCH'])
def api_reactivate_conta(conta_id):
    success = reactivate_movimento(conta_id)
    if not success:
        return jsonify({"error": "Conta não encontrada"}), 404
    return jsonify({"success": True, "message": "Conta reativada com sucesso!"}), 200

# ==============================================================================
# ENDPOINT REST: DASHBOARD FINANCEIRO & ESTATÍSTICAS GERAIS
# ==============================================================================
@app.route('/api/dashboard', methods=['GET'])
@app.route('/api/dashboard/stats', methods=['GET'])
def api_get_dashboard():
    try:
        stats = get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as e:
        print(f"Erro ao obter estatísticas do dashboard: {e}")
        return jsonify({"error": "Falha ao carregar dashboard", "detalhes": str(e)}), 500

if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print("\n" + "=" * 62)
    print("  [>] FINEASY - Processador Inteligente de Notas Fiscais (N2)")
    print("=" * 62)
    print(f"  [WEB] Servidor Flask Ativo:     http://localhost:{port}")
    print(f"  [DOCS] API Base:                 http://localhost:{port}/api/status")
    print("=" * 62 + "\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
