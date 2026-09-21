import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from agents.agent_extracadados import Agent1

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads

# Instância padrão do agente de extração
agent = Agent1()

@app.route('/')
def index():
    """Renderiza a interface web principal conforme especificações da N2."""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def api_status():
    """Retorna o status da aplicação e da integração com a API Gemini."""
    env_key = os.getenv("GEMINI_API_KEY")
    has_key = bool(env_key and env_key.strip() != "sua_chave_gemini_aqui")
    return jsonify({
        "status": "online",
        "has_gemini_key": has_key,
        "framework": "Flask (Python)",
        "version": "1.0.0"
    })

@app.route('/api/extract', methods=['POST'])
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
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    print(f"[*] Iniciando Servidor UniRV - Processador de Notas Fiscais na porta {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
