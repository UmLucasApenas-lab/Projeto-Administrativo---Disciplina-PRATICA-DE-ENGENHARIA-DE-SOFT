import os
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.create_function("CLEAN_DOC", 1, clean_doc)
    return conn

def clean_doc(doc: str) -> str:
    """Remove caracteres não numéricos de CPF/CNPJ para comparação padronizada."""
    if not doc:
        return ""
    return re.sub(r'\D', '', str(doc))

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Usuários do Sistema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Pessoas (Fornecedor, Cliente, Faturado)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            razao_social_nome TEXT NOT NULL,
            fantasia TEXT,
            cnpj_cpf TEXT,
            email TEXT,
            telefone TEXT,
            status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Classificações (Receitas e Despesas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('DESPESA', 'RECEITA')),
            descricao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Movimento de Contas (Contas a Pagar e Contas a Receber)
    cursor.execute('''
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
        )
    ''')

    # 5. Associação Movimento <-> Classificações (Permite rateio de 1..N despesas/receitas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimento_classificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movimento_id INTEGER NOT NULL,
            classificacao_id INTEGER NOT NULL,
            valor REAL,
            percentual REAL,
            FOREIGN KEY (movimento_id) REFERENCES movimento_contas(id) ON DELETE CASCADE,
            FOREIGN KEY (classificacao_id) REFERENCES classificacoes(id)
        )
    ''')

    # 6. Parcelas de Contas (1..N parcelas com vencimentos distintos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parcela_contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movimento_id INTEGER NOT NULL,
            numero_parcela INTEGER NOT NULL,
            total_parcelas INTEGER NOT NULL,
            identificacao TEXT NOT NULL,
            data_vencimento TEXT NOT NULL,
            valor REAL NOT NULL,
            status_pagamento TEXT NOT NULL DEFAULT 'PENDENTE' CHECK(status_pagamento IN ('PENDENTE', 'PAGO', 'CANCELADO')),
            status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movimento_id) REFERENCES movimento_contas(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

    # Criar usuário admin padrão se não existir
    default_email = os.getenv("AUTH_EMAIL", "admin@unirv.edu.br").strip().lower()
    default_password = os.getenv("AUTH_PASSWORD", "admin123").strip()

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (default_email,))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        hashed = generate_password_hash(default_password)
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (default_email, hashed, "Administrador UniRV")
        )
        conn.commit()
        print(f"[DB] Usuário padrão criado: {default_email}")

    # Semear classificações oficiais se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) AS total FROM classificacoes")
    if cursor.fetchone()['total'] == 0:
        categorias_padrao = [
            ("DESPESA", "INSUMOS AGRÍCOLAS"),
            ("DESPESA", "MANUTENÇÃO E OPERAÇÃO"),
            ("DESPESA", "RECURSOS HUMANOS"),
            ("DESPESA", "SERVIÇOS OPERACIONAIS"),
            ("DESPESA", "INFRAESTRUTURA E UTILIDADES"),
            ("DESPESA", "ADMINISTRATIVAS"),
            ("DESPESA", "SEGUROS E PROTEÇÃO"),
            ("DESPESA", "IMPOSTOS E TAXAS"),
            ("DESPESA", "INVESTIMENTOS"),
            ("RECEITA", "VENDA DE GRÃOS"),
            ("RECEITA", "PRESTAÇÃO DE SERVIÇOS AGRÍCOLAS"),
            ("RECEITA", "RECEITAS FINANCEIRAS"),
            ("RECEITA", "OUTRAS RECEITAS OPERACIONAIS")
        ]
        cursor.executemany(
            "INSERT INTO classificacoes (tipo, descricao, status) VALUES (?, ?, 'ATIVO')",
            categorias_padrao
        )
        conn.commit()
        print(f"[DB] {len(categorias_padrao)} classificações padrão inseridas com sucesso.")

    conn.close()

# ==============================================================================
# FUNÇÕES: USERS
# ==============================================================================
def create_user(email: str, password: str, name: str = None):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return None, "Este e-mail já está cadastrado no sistema."

    try:
        hashed = generate_password_hash(password)
        display_name = name.strip() if name else email_clean.split('@')[0]
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email_clean, hashed, display_name)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id, None
    except Exception as e:
        conn.close()
        return None, f"Erro ao criar usuário: {str(e)}"

def get_user_by_email(email: str):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash, name FROM users WHERE LOWER(email) = ?", (email_clean,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row["id"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "name": row["name"]
        }
    return None

def verify_user_credentials(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None

# ==============================================================================
# FUNÇÕES: PESSOAS (Fornecedores, Clientes, Faturados)
# ==============================================================================
def save_pessoa(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    tipo = data.get('tipo', 'FORNECEDOR').strip()
    razao_social_nome = data.get('razao_social_nome', '').strip()
    fantasia = data.get('fantasia', '').strip() if data.get('fantasia') else None
    cnpj_cpf = data.get('cnpj_cpf', '').strip() if data.get('cnpj_cpf') else None
    email = data.get('email', '').strip() if data.get('email') else None
    telefone = data.get('telefone', '').strip() if data.get('telefone') else None
    status = 'ATIVO'

    cursor.execute('''
        INSERT INTO pessoas (tipo, razao_social_nome, fantasia, cnpj_cpf, email, telefone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tipo, razao_social_nome, fantasia, cnpj_cpf, email, telefone, status))
    conn.commit()
    pessoa_id = cursor.lastrowid
    conn.close()
    return pessoa_id

def update_pessoa(pessoa_id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    tipo = data.get('tipo')
    razao_social_nome = data.get('razao_social_nome')
    fantasia = data.get('fantasia')
    cnpj_cpf = data.get('cnpj_cpf')
    email = data.get('email')
    telefone = data.get('telefone')

    cursor.execute('''
        UPDATE pessoas
        SET tipo = COALESCE(?, tipo),
            razao_social_nome = COALESCE(?, razao_social_nome),
            fantasia = COALESCE(?, fantasia),
            cnpj_cpf = COALESCE(?, cnpj_cpf),
            email = COALESCE(?, email),
            telefone = COALESCE(?, telefone),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (tipo, razao_social_nome, fantasia, cnpj_cpf, email, telefone, pessoa_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def get_pessoa_by_id(pessoa_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pessoas WHERE id = ?", (pessoa_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_pessoas(q: str = None, tipo: str = None, status: str = 'ATIVO', todos: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Se não clicou em TODOS e nem forneceu busca, a recomendação de layout UniRV exige trazer vazio
    if not todos and not q and not tipo:
        conn.close()
        return []

    conditions = []
    params = []

    if status and status.upper() != 'TODOS':
        conditions.append("status = ?")
        params.append(status.upper())

    if tipo and tipo.upper() != 'TODOS':
        conditions.append("tipo = ?")
        params.append(tipo.upper())

    if q and q.strip():
        term = f"%{q.strip()}%"
        doc_term = f"%{clean_doc(q)}%" if clean_doc(q) else term
        conditions.append("(razao_social_nome LIKE ? OR fantasia LIKE ? OR cnpj_cpf LIKE ? OR CLEAN_DOC(cnpj_cpf) LIKE ? OR email LIKE ? OR telefone LIKE ?)")
        params.extend([term, term, term, doc_term, term, term])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM pessoas {where_clause} ORDER BY razao_social_nome ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def soft_delete_pessoa(pessoa_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pessoas SET status = 'INATIVO', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (pessoa_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def reactivate_pessoa(pessoa_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pessoas SET status = 'ATIVO', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (pessoa_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def find_pessoa_by_doc_or_name(cnpj_cpf: str = None, nome: str = None, tipo: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_target_doc = clean_doc(cnpj_cpf)
    
    # 1. Tentar por documento (CNPJ/CPF limpo)
    if clean_target_doc:
        cursor.execute("SELECT * FROM pessoas")
        rows = cursor.fetchall()
        for r in rows:
            if clean_doc(r['cnpj_cpf']) == clean_target_doc:
                conn.close()
                return dict(r)

    # 2. Tentar por Razão Social ou Nome exato / aproximado
    if nome and nome.strip():
        nome_clean = nome.strip()
        cursor.execute("SELECT * FROM pessoas WHERE UPPER(razao_social_nome) = UPPER(?)", (nome_clean,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    conn.close()
    return None

# ==============================================================================
# FUNÇÕES: CLASSIFICAÇÕES
# ==============================================================================
def save_classificacao(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    tipo = data.get('tipo', 'DESPESA').strip().upper()
    descricao = data.get('descricao', '').strip().upper()
    status = 'ATIVO'

    cursor.execute('''
        INSERT INTO classificacoes (tipo, descricao, status)
        VALUES (?, ?, ?)
    ''', (tipo, descricao, status))
    conn.commit()
    classif_id = cursor.lastrowid
    conn.close()
    return classif_id

def update_classificacao(classif_id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    tipo = data.get('tipo')
    descricao = data.get('descricao')

    cursor.execute('''
        UPDATE classificacoes
        SET tipo = COALESCE(?, tipo),
            descricao = COALESCE(?, descricao),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (tipo.upper() if tipo else None, descricao.upper() if descricao else None, classif_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def get_classificacao_by_id(classif_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classificacoes WHERE id = ?", (classif_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_classificacoes(q: str = None, tipo: str = None, status: str = 'ATIVO', todos: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()

    if not todos and not q and not tipo:
        conn.close()
        return []

    conditions = []
    params = []

    if status and status.upper() != 'TODOS':
        conditions.append("status = ?")
        params.append(status.upper())

    if tipo and tipo.upper() != 'TODOS':
        conditions.append("tipo = ?")
        params.append(tipo.upper())

    if q and q.strip():
        term = f"%{q.strip()}%"
        conditions.append("descricao LIKE ?")
        params.append(term)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM classificacoes {where_clause} ORDER BY descricao ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def soft_delete_classificacao(classif_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE classificacoes SET status = 'INATIVO', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (classif_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def reactivate_classificacao(classif_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE classificacoes SET status = 'ATIVO', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (classif_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def find_classificacao_by_desc(descricao: str, tipo: str = 'DESPESA'):
    if not descricao or not descricao.strip():
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    desc_clean = descricao.strip().upper()
    
    # Busca exata ou que contenha
    cursor.execute("SELECT * FROM classificacoes WHERE tipo = ? AND UPPER(descricao) = ?", (tipo.upper(), desc_clean))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT * FROM classificacoes WHERE tipo = ? AND UPPER(descricao) LIKE ?", (tipo.upper(), f"%{desc_clean}%"))
        row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None

# ==============================================================================
# FUNÇÕES: MOVIMENTO DE CONTAS & PARCELAS
# ==============================================================================
def save_movimento_completo(dados: dict):
    """
    Executa a transação completa (ACID) de criação de um movimento de contas,
    incluindo suas classificações e suas parcelas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tipo = dados.get('tipo', 'APAGAR').strip().upper()
        numero_documento = dados.get('numero_documento', '').strip()
        descricao = dados.get('descricao', '').strip()
        data_emissao = dados.get('data_emissao', '').strip()
        valor_total = float(dados.get('valor_total', 0.0))
        pessoa_fornecedor_id = dados.get('pessoa_fornecedor_id')
        pessoa_faturado_id = dados.get('pessoa_faturado_id')
        status = 'ATIVO'

        cursor.execute('''
            INSERT INTO movimento_contas (
                tipo, numero_documento, descricao, data_emissao, valor_total,
                pessoa_fornecedor_id, pessoa_faturado_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tipo, numero_documento, descricao, data_emissao, valor_total,
            pessoa_fornecedor_id, pessoa_faturado_id, status
        ))
        movimento_id = cursor.lastrowid

        # 1. Vincular classificações (Rateio)
        classificacoes = dados.get('classificacoes', [])
        for c in classificacoes:
            c_id = c.get('classificacao_id') if isinstance(c, dict) else c
            c_valor = c.get('valor', valor_total) if isinstance(c, dict) else valor_total
            c_perc = c.get('percentual', 100.0) if isinstance(c, dict) else 100.0
            if c_id:
                cursor.execute('''
                    INSERT INTO movimento_classificacoes (movimento_id, classificacao_id, valor, percentual)
                    VALUES (?, ?, ?, ?)
                ''', (movimento_id, c_id, c_valor, c_perc))

        # 2. Criar parcelas
        parcelas = dados.get('parcelas', [])
        if not parcelas:
            # Parcela única default
            data_venc = dados.get('data_vencimento') or data_emissao or 'À Vista'
            cursor.execute('''
                INSERT INTO parcela_contas (
                    movimento_id, numero_parcela, total_parcelas, identificacao,
                    data_vencimento, valor, status_pagamento, status
                ) VALUES (?, 1, 1, 'ÚNICA', ?, ?, 'PENDENTE', 'ATIVO')
            ''', (movimento_id, data_venc, valor_total))
        else:
            total_parc = len(parcelas)
            for idx, p in enumerate(parcelas, start=1):
                num = p.get('numero_parcela', idx)
                ident = 'ÚNICA' if total_parc == 1 else f"{idx}/{total_parc}"
                venc = p.get('data_vencimento') or p.get('vencimento') or data_emissao
                val = float(p.get('valor', valor_total / total_parc))
                cursor.execute('''
                    INSERT INTO parcela_contas (
                        movimento_id, numero_parcela, total_parcelas, identificacao,
                        data_vencimento, valor, status_pagamento, status
                    ) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE', 'ATIVO')
                ''', (movimento_id, num, total_parc, ident, venc, val))

        conn.commit()
        conn.close()
        return movimento_id
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def get_movimento_by_id(movimento_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.*,
               f.razao_social_nome AS fornecedor_nome,
               f.cnpj_cpf AS fornecedor_cnpj,
               fat.razao_social_nome AS faturado_nome,
               fat.cnpj_cpf AS faturado_cpf
        FROM movimento_contas m
        LEFT JOIN pessoas f ON m.pessoa_fornecedor_id = f.id
        LEFT JOIN pessoas fat ON m.pessoa_faturado_id = fat.id
        WHERE m.id = ?
    ''', (movimento_id,))
    mov_row = cursor.fetchone()
    if not mov_row:
        conn.close()
        return None

    mov = dict(mov_row)

    # Classificações
    cursor.execute('''
        SELECT mc.*, c.descricao, c.tipo AS classificacao_tipo
        FROM movimento_classificacoes mc
        JOIN classificacoes c ON mc.classificacao_id = c.id
        WHERE mc.movimento_id = ?
    ''', (movimento_id,))
    mov['classificacoes'] = [dict(r) for r in cursor.fetchall()]

    # Parcelas
    cursor.execute('''
        SELECT * FROM parcela_contas
        WHERE movimento_id = ?
        ORDER BY numero_parcela ASC
    ''', (movimento_id,))
    mov['parcelas'] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return mov

def get_movimentos(q: str = None, tipo: str = None, status: str = 'ATIVO', todos: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()

    if not todos and not q and not tipo:
        conn.close()
        return []

    conditions = []
    params = []

    if status and status.upper() != 'TODOS':
        conditions.append("m.status = ?")
        params.append(status.upper())

    if tipo and tipo.upper() != 'TODOS':
        conditions.append("m.tipo = ?")
        params.append(tipo.upper())

    if q and q.strip():
        term = f"%{q.strip()}%"
        conditions.append("(m.numero_documento LIKE ? OR m.descricao LIKE ? OR f.razao_social_nome LIKE ? OR fat.razao_social_nome LIKE ?)")
        params.extend([term, term, term, term])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f'''
        SELECT m.*,
               f.razao_social_nome AS fornecedor_nome,
               fat.razao_social_nome AS faturado_nome,
               (SELECT COUNT(*) FROM parcela_contas p WHERE p.movimento_id = m.id AND p.status = 'ATIVO') AS qtd_parcelas,
               (SELECT MIN(data_vencimento) FROM parcela_contas p WHERE p.movimento_id = m.id AND p.status = 'ATIVO') AS proximo_vencimento
        FROM movimento_contas m
        LEFT JOIN pessoas f ON m.pessoa_fornecedor_id = f.id
        LEFT JOIN pessoas fat ON m.pessoa_faturado_id = fat.id
        {where_clause}
        ORDER BY m.id DESC
    '''
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def soft_delete_movimento(movimento_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE movimento_contas SET status = 'INATIVO', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (movimento_id,))
    cursor.execute("UPDATE parcela_contas SET status = 'INATIVO' WHERE movimento_id = ?", (movimento_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def reactivate_movimento(movimento_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE movimento_contas SET status = 'ATIVO', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (movimento_id,))
    cursor.execute("UPDATE parcela_contas SET status = 'ATIVO' WHERE movimento_id = ?", (movimento_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success
