import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

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

    conn.close()

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
