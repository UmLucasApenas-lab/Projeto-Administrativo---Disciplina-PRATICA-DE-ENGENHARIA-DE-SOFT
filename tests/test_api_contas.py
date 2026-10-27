import unittest
import json
import os
import tempfile
from unittest.mock import patch
from app import app

class TestApiContas(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.db_patcher = patch('utils.database.DB_PATH', self.temp_db_path)
        self.db_patcher.start()

        import utils.database as db
        self.db = db
        self.db.init_db()

        self.client = app.test_client()

        # Cadastrar Fornecedor, Faturado e Classificação de base
        self.fornecedor_id = self.db.save_pessoa({
            "tipo": "CLIENTE-FORNECEDOR",
            "razao_social_nome": "COMBO EMBALAGENS LTDA",
            "cnpj_cpf": "22.222.222/0001-22"
        })
        self.faturado_id = self.db.save_pessoa({
            "tipo": "FATURADO",
            "razao_social_nome": "JOAO DA SILVA",
            "cnpj_cpf": "111.222.333-44"
        })
        self.classif_id = self.db.save_classificacao({
            "tipo": "DESPESA",
            "descricao": "INSUMOS AGRICOLAS"
        })

    def tearDown(self):
        self.db_patcher.stop()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except Exception:
            pass

    def test_contas_crud_multiplas_parcelas_e_soft_delete(self):
        # 1. Tabela deve iniciar vazia (layout UniRV a)
        res_empty = self.client.get('/api/contas')
        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(res_empty.get_json(), [])

        # 2. Cadastro manual de Contas a Pagar com 2 parcelas (Multiplas parcelas com datas distintas)
        payload_conta = {
            "tipo": "APAGAR",
            "numero_documento": "NF-9988",
            "descricao": "AQUISIÇÃO DE SEMENTES DE SOJA",
            "data_emissao": "10/10/2026",
            "valor_total": 5000.00,
            "pessoa_fornecedor_id": self.fornecedor_id,
            "pessoa_faturado_id": self.faturado_id,
            "classificacoes": [{"classificacao_id": self.classif_id, "valor": 5000.00}],
            "parcelas": [
                {"numero_parcela": 1, "data_vencimento": "10/11/2026", "valor": 2500.00},
                {"numero_parcela": 2, "data_vencimento": "10/12/2026", "valor": 2500.00}
            ]
        }
        res_post = self.client.post('/api/contas', json=payload_conta)
        self.assertEqual(res_post.status_code, 201)
        mov_id = res_post.get_json().get('id')
        self.assertIsNotNone(mov_id)

        # 3. Consulta via botão "TODOS" (traz status = ATIVO)
        res_todos = self.client.get('/api/contas?todos=1&tipo=APAGAR')
        self.assertEqual(res_todos.status_code, 200)
        lista = res_todos.get_json()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]['fornecedor_nome'], "COMBO EMBALAGENS LTDA")
        self.assertEqual(lista[0]['qtd_parcelas'], 2)

        # 4. Detalhes da conta (GET /api/contas/<id>)
        res_detalhes = self.client.get(f'/api/contas/{mov_id}')
        self.assertEqual(res_detalhes.status_code, 200)
        detalhes = res_detalhes.get_json()
        self.assertEqual(len(detalhes['parcelas']), 2)
        self.assertEqual(detalhes['parcelas'][0]['data_vencimento'], "10/11/2026")
        self.assertEqual(detalhes['parcelas'][1]['data_vencimento'], "10/12/2026")

        # 5. Exclusão Lógica (status = INATIVO)
        res_del = self.client.delete(f'/api/contas/{mov_id}')
        self.assertEqual(res_del.status_code, 200)

        # 'TODOS' agora não deve retornar nada porque filtra ATIVO
        res_todos_pos_del = self.client.get('/api/contas?todos=1&tipo=APAGAR')
        self.assertEqual(len(res_todos_pos_del.get_json()), 0)

        # 6. Reativação lógica
        res_reativar = self.client.patch(f'/api/contas/{mov_id}/reativar')
        self.assertEqual(res_reativar.status_code, 200)
        res_todos_pos_reativar = self.client.get('/api/contas?todos=1&tipo=APAGAR')
        self.assertEqual(len(res_todos_pos_reativar.get_json()), 1)

if __name__ == '__main__':
    unittest.main()
