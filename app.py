import os
import socket
import datetime
from functools import wraps
import jwt
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from agents.agent_extracadados import Agent1

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads

# Habilitar CORS para permitir requisições do Cloudflare Pages e cabeçalhos como X-Gemini-Key e Authorization
CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "X-Gemini-Key", "Authorization"])

# Configurações de Autenticação JWT
JWT_SECRET = os.getenv("JWT_SECRET", "unirv-secret-jwt-key-n2-avaliacao-2026-super-segura")
JWT_ALGORITHM = "HS256"
AUTH_EMAIL = os.getenv("AUTH_EMAIL", "admin@unirv.edu.br")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin123")

def generate_token(email):
    """Gera um token JWT com validade de 24 horas."""
    payload = {
        "sub": email,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def token_required(f):
    """Decorator para proteger endpoints exigindo token Bearer JWT válido."""
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

from utils.database import init_db, create_user, verify_user_credentials

# Instância padrão do agente de extração
agent = Agent1()

# Inicializar banco de dados SQLite e criar usuário padrão
init_db()

@app.route('/')
def index():
    """Renderiza a interface web principal conforme especificações da N2."""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Renderiza a interface web de login."""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Renderiza a interface web de cadastro."""
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    """
    Endpoint para cadastro de novos usuários no banco SQLite com hash seguro de senha.
    """
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
    """
    Endpoint que autentica as credenciais no SQLite e devolve o token JWT para o front-end.
    """
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
    """Retorna o status da aplicação e da integração com a API Gemini."""
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
    """
    Endpoint que recebe o arquivo PDF da Nota Fiscal,
    aciona o Agent1 e devolve os dados estruturados e classificados em formato JSON.
    """
    if 'pdf_file' not in request.files:
        return jsonify({"error": "Nenhum arquivo PDF foi enviado na requisição."}), 400

    uploaded_file = request.files['pdf_file']

    if uploaded_file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    if not uploaded_file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Formato inválido. O arquivo deve ser um PDF."}), 400

    # Permitir chave passada dinamicamente pelo cabeçalho
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
    """Serve arquivos de nota fiscal de exemplo para demonstração rápida."""
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_notas')
    return send_from_directory(samples_dir, filename)

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
