import unittest
import json
import os
import tempfile
from unittest.mock import patch
from app import app

class TestAnaliseELancamento(unittest.TestCase):
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

    def test_analise_e_lancamento_automatico_fluxo(self):
        # Dados de exemplo idênticos à especificação da UniRV (Página 2 do PDF)
        dados_nf = {
            "Número da Nota Fiscal": "000.126.981",
            "Data de Emissão": "25/08/2026",
            "Data de Vencimento": "25/09/2026",
            "Valor Total": "6.478,76",
            "Descrição dos Produtos": "PEÇAS E REPAROS PARA TRATOR JOHN DEERE",
            "Fornecedor": {
                "Razão Social": "IGUAÇU MAQUINAS LTDA",
                "CNPJ": "11.111.111/0001-00"
            },
            "Faturado": {
                "Nome Completo": "BELTRANO DA SILVA",
                "CPF": "999.999.999-99"
            },
            "CLASSIFICAÇÃO": {
                "categoria": "MANUTENÇÃO E OPERAÇÃO"
            },
            "Parcelas": {
                "Quantidade": 1,
                "detalhes": [
                    {
                        "parcela": 1,
                        "vencimento": "25/09/2026",
                        "valor": "6.478,76"
                    }
                ]
            }
        }

        # 1. Primeira Análise:
        # A classificação "MANUTENÇÃO E OPERAÇÃO" já foi pré-semeada pelo init_db (EXISTE).
        # Porém FORNECEDOR e FATURADO NÃO EXISTEM ainda.
        res_analise_1 = self.client.post('/api/analise', json=dados_nf)
        self.assertEqual(res_analise_1.status_code, 200)
        analise_1 = res_analise_1.get_json()

        # Fornecedor NÃO EXISTE
        self.assertFalse(analise_1['fornecedor']['existe'])
        self.assertIsNone(analise_1['fornecedor']['id'])

        # Faturado NÃO EXISTE
        self.assertFalse(analise_1['faturado']['existe'])
        self.assertIsNone(analise_1['faturado']['id'])

        # Despesa EXISTE (semeada no init_db)
        self.assertTrue(analise_1['despesa']['existe'])
        self.assertIsNotNone(analise_1['despesa']['id'])

        # 2. Executar Lançamento Automático
        res_lancamento = self.client.post('/api/movimentos/lancar-automatico', json=dados_nf)
        self.assertEqual(res_lancamento.status_code, 201)
        res_data = res_lancamento.get_json()
        self.assertTrue(res_data.get('success'))
        self.assertIn("LANÇADO COM SUCESSO", res_data.get('message').upper())
        movimento_id = res_data.get('movimento_id')
        self.assertIsNotNone(movimento_id)

        # 3. Segunda Análise pós-lançamento:
        # Agora TODOS devem retornar EXISTE com seus respectivos IDs!
        res_analise_2 = self.client.post('/api/analise', json=dados_nf)
        self.assertEqual(res_analise_2.status_code, 200)
        analise_2 = res_analise_2.get_json()

        self.assertTrue(analise_2['fornecedor']['existe'])
        self.assertIsNotNone(analise_2['fornecedor']['id'])
        self.assertEqual(analise_2['fornecedor']['razao_social'], "IGUAÇU MAQUINAS LTDA")

        self.assertTrue(analise_2['faturado']['existe'])
        self.assertIsNotNone(analise_2['faturado']['id'])
        self.assertEqual(analise_2['faturado']['nome'], "BELTRANO DA SILVA")

        self.assertTrue(analise_2['despesa']['existe'])
        self.assertIsNotNone(analise_2['despesa']['id'])

        # 4. Verificar detalhes do movimento gravado
        mov = self.db.get_movimento_by_id(movimento_id)
        self.assertIsNotNone(mov)
        self.assertEqual(mov['tipo'], 'APAGAR')
        self.assertEqual(mov['numero_documento'], '000.126.981')
        self.assertEqual(len(mov['parcelas']), 1)
        self.assertEqual(mov['parcelas'][0]['identificacao'], 'ÚNICA')
        self.assertEqual(mov['parcelas'][0]['data_vencimento'], '25/09/2026')

if __name__ == '__main__':
    unittest.main()
