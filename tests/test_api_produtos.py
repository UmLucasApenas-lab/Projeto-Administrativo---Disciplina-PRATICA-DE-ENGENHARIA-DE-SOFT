import unittest
import json
import os
import tempfile
from unittest.mock import patch
from app import app
import utils.database as db

class TestApiProdutos(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.db_patcher = patch('utils.database.DB_PATH', self.temp_db_path)
        self.db_patcher.start()

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

    def test_produtos_layout_regras_and_crud(self):
                                                                                           
        res = self.client.get('/api/produtos')
        self.assertEqual(res.status_code, 200)
        dados = res.get_json()
        self.assertEqual(dados, [], "Inicialmente a listagem sem busca/todos deve vir vazia")

        res_todos = self.client.get('/api/produtos?todos=1')
        self.assertEqual(res_todos.status_code, 200)
        lista_inicial = res_todos.get_json()
        self.assertGreater(len(lista_inicial), 0, "Deve conter produtos ativos após init_db()")

        novo_payload = {
            "descricao": "Adubo Foliar Micronutrientes Zinc 5L",
            "categoria": "Fertilizantes e Adubos",
            "unidade": "L",
            "valor_unitario": 185.50
        }
        res_post = self.client.post('/api/produtos', json=novo_payload)
        self.assertEqual(res_post.status_code, 201)
        created = res_post.get_json()
        self.assertTrue(created.get('success'))
        prod_id = created.get('id')
        self.assertIsNotNone(prod_id)

        res_busca = self.client.get('/api/produtos?q=Adubo Foliar')
        self.assertEqual(res_busca.status_code, 200)
        encontrados = res_busca.get_json()
        self.assertTrue(any(p['id'] == prod_id for p in encontrados))

        res_busca_cat = self.client.get('/api/produtos?q=Fertilizantes')
        self.assertEqual(res_busca_cat.status_code, 200)
        encontrados_cat = res_busca_cat.get_json()
        self.assertTrue(any(p['id'] == prod_id for p in encontrados_cat))

        update_payload = {
            "descricao": "Adubo Foliar Micronutrientes Zinc 5L - Concentrado",
            "categoria": "Fertilizantes e Adubos",
            "unidade": "L",
            "valor_unitario": 210.00
        }
        res_put = self.client.put(f'/api/produtos/{prod_id}', json=update_payload)
        self.assertEqual(res_put.status_code, 200)

        res_get_single = self.client.get(f'/api/produtos/{prod_id}')
        self.assertEqual(res_get_single.status_code, 200)
        prod_alterado = res_get_single.get_json()
        self.assertEqual(prod_alterado['descricao'], update_payload['descricao'])
        self.assertEqual(float(prod_alterado['valor_unitario']), 210.00)

        res_del = self.client.delete(f'/api/produtos/{prod_id}')
        self.assertEqual(res_del.status_code, 200)

        res_busca_ativo = self.client.get(f'/api/produtos?q=Adubo Foliar')
        self.assertFalse(any(p['id'] == prod_id for p in res_busca_ativo.get_json()))

        res_com_inativos = self.client.get('/api/produtos?todos=1&incluir_inativos=1')
        inativo_item = next((p for p in res_com_inativos.get_json() if p['id'] == prod_id), None)
        self.assertIsNotNone(inativo_item)
        self.assertEqual(inativo_item['status'], 'INATIVO')

        res_patch = self.client.patch(f'/api/produtos/{prod_id}/reativar')
        self.assertEqual(res_patch.status_code, 200)

        res_reativado = self.client.get(f'/api/produtos/{prod_id}')
        self.assertEqual(res_reativado.get_json()['status'], 'ATIVO')

    def test_dashboard_stats_features(self):
                                                                                                           
        res = self.client.get('/api/dashboard/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn('saldo_projetado', data)
        self.assertIn('total_produtos', data)
        self.assertIn('despesas_categorias', data)
        self.assertIsInstance(data['despesas_categorias'], list)
        self.assertGreaterEqual(data['total_produtos'], 0)

if __name__ == '__main__':
    unittest.main()
