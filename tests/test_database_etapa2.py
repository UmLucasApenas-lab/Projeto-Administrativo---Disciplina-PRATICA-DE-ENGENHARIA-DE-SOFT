import unittest
import os
import sqlite3
import tempfile
from unittest.mock import patch

class TestDatabaseEtapa2(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.db_patcher = patch('utils.database.DB_PATH', self.temp_db_path)
        self.db_patcher.start()

        import utils.database as db
        self.db = db
        self.db.init_db()

    def tearDown(self):
        self.db_patcher.stop()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except Exception:
            pass

    def test_tables_created(self):
        conn = self.db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        conn.close()

        for expected_table in ['pessoas', 'classificacoes', 'movimento_contas', 'movimento_classificacoes', 'parcela_contas']:
            self.assertIn(expected_table, tables, f"Tabela '{expected_table}' deve ser criada pelo init_db")

    def test_pessoa_crud_and_soft_delete(self):
        # 1. Create pessoa (deve ter status 'ATIVO' implicitamente)
        pessoa_id = self.db.save_pessoa({
            'tipo': 'FORNECEDOR',
            'razao_social_nome': 'IGUAÇU MAQUINAS LTDA',
            'fantasia': 'Iguaçu Máquinas',
            'cnpj_cpf': '11.111.111/0001-00',
            'email': 'contato@iguacu.com.br',
            'telefone': '(64) 3611-0000'
        })
        self.assertIsNotNone(pessoa_id)

        pessoa = self.db.get_pessoa_by_id(pessoa_id)
        self.assertEqual(pessoa['razao_social_nome'], 'IGUAÇU MAQUINAS LTDA')
        self.assertEqual(pessoa['status'], 'ATIVO')

        # 2. Soft delete (exclusão lógica)
        success = self.db.soft_delete_pessoa(pessoa_id)
        self.assertTrue(success)

        # Registro ainda existe no banco, mas com status INATIVO
        pessoa_inativa = self.db.get_pessoa_by_id(pessoa_id)
        self.assertIsNotNone(pessoa_inativa)
        self.assertEqual(pessoa_inativa['status'], 'INATIVO')

        # Listagem padrão (status='ATIVO') não deve trazer o registro inativo
        ativas = self.db.get_pessoas(status='ATIVO')
        self.assertEqual(len(ativas), 0)

        # 3. Reativação lógica
        reactivated = self.db.reactivate_pessoa(pessoa_id)
        self.assertTrue(reactivated)
        pessoa_reativada = self.db.get_pessoa_by_id(pessoa_id)
        self.assertEqual(pessoa_reativada['status'], 'ATIVO')

    def test_classificacao_crud_and_soft_delete(self):
        classif_id = self.db.save_classificacao({
            'tipo': 'DESPESA',
            'descricao': 'MANUTENÇÃO E OPERAÇÃO'
        })
        self.assertIsNotNone(classif_id)

        classif = self.db.get_classificacao_by_id(classif_id)
        self.assertEqual(classif['status'], 'ATIVO')
        self.assertEqual(classif['descricao'], 'MANUTENÇÃO E OPERAÇÃO')

        # Soft delete
        self.db.soft_delete_classificacao(classif_id)
        classif_inativa = self.db.get_classificacao_by_id(classif_id)
        self.assertEqual(classif_inativa['status'], 'INATIVO')

        # Reativação
        self.db.reactivate_classificacao(classif_id)
        classif_reativada = self.db.get_classificacao_by_id(classif_id)
        self.assertEqual(classif_reativada['status'], 'ATIVO')

if __name__ == '__main__':
    unittest.main()
