import unittest
import json
import os
import tempfile
from unittest.mock import patch
from app import app
from utils.database import init_db

class TestApiCrudBasico(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.db_patcher = patch('utils.database.DB_PATH', self.temp_db_path)
        self.db_patcher.start()

        import utils.database as db
        self.db = db
        self.db.init_db()

        self.client = app.test_client()

    def tearDown(self):
        self.db_patcher.stop()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except Exception:
            pass

    def test_pessoas_layout_regras_and_crud(self):
                                                                                                       
        res = self.client.get('/api/pessoas')
        self.assertEqual(res.status_code, 200)
        dados = res.get_json()
        self.assertEqual(dados, [], "Inicialmente a listagem sem busca/todos deve vir vazia")

        novo_payload = {
            "tipo": "CLIENTE-FORNECEDOR",
            "razao_social_nome": "AGROPECUARIA RIO VERDE LTDA",
            "cnpj_cpf": "12.345.678/0001-99",
            "email": "contato@agro.com.br",
            "telefone": "(64) 3621-1234"
        }
        res_post = self.client.post('/api/pessoas', json=novo_payload)
        self.assertEqual(res_post.status_code, 201)
        created = res_post.get_json()
        self.assertTrue(created.get('success'))
        pessoa_id = created.get('id')

        res_todos = self.client.get('/api/pessoas?todos=1')
        self.assertEqual(res_todos.status_code, 200)
        lista = res_todos.get_json()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]['status'], 'ATIVO')

        res_busca_nome = self.client.get('/api/pessoas?q=AGROPECUARIA')
        self.assertEqual(len(res_busca_nome.get_json()), 1)

        res_busca_doc = self.client.get('/api/pessoas?q=12345678000199')
        self.assertEqual(len(res_busca_doc.get_json()), 1)

        res_put = self.client.put(f'/api/pessoas/{pessoa_id}', json={"telefone": "(64) 99999-8888"})
        self.assertEqual(res_put.status_code, 200)

        res_del = self.client.delete(f'/api/pessoas/{pessoa_id}')
        self.assertEqual(res_del.status_code, 200)

        res_todos_pos_del = self.client.get('/api/pessoas?todos=1')
        self.assertEqual(len(res_todos_pos_del.get_json()), 0)

        res_inativos = self.client.get('/api/pessoas?todos=1&status=INATIVO')
        self.assertEqual(len(res_inativos.get_json()), 1)
        self.assertEqual(res_inativos.get_json()[0]['status'], 'INATIVO')

        res_reactivate = self.client.patch(f'/api/pessoas/{pessoa_id}/reativar')
        self.assertEqual(res_reactivate.status_code, 200)
        res_todos_pos_reactivate = self.client.get('/api/pessoas?todos=1')
        self.assertEqual(len(res_todos_pos_reactivate.get_json()), 1)
        self.assertEqual(res_todos_pos_reactivate.get_json()[0]['status'], 'ATIVO')

    def test_classificacoes_crud_and_soft_delete(self):
                                   
        res = self.client.get('/api/classificacoes?todos=1&tipo=DESPESA')
        self.assertEqual(res.status_code, 200)
        lista = res.get_json()
        self.assertGreater(len(lista), 0)

        res_post = self.client.post('/api/classificacoes', json={
            "tipo": "DESPESA",
            "descricao": "HONORARIOS ADVOCATICIOS"
        })
        self.assertEqual(res_post.status_code, 201)
        c_id = res_post.get_json().get('id')

        res_del = self.client.delete(f'/api/classificacoes/{c_id}')
        self.assertEqual(res_del.status_code, 200)

        res_reativar = self.client.patch(f'/api/classificacoes/{c_id}/reativar')
        self.assertEqual(res_reativar.status_code, 200)

if __name__ == '__main__':
    unittest.main()
