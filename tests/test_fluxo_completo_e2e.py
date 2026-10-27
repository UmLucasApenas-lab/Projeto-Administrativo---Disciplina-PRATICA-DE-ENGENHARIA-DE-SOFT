import unittest
import json
import os
import tempfile
from unittest.mock import patch
from app import app

class TestFluxoCompletoE2E(unittest.TestCase):
    """
    Teste de Integração Ponta a Ponta (E2E) cobrindo todos os requisitos
    da 2ª Etapa do Projeto Administrativo-Financeiro (UniRV).
    """
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

    def test_ciclo_completo_etapa_2(self):
        # 1. Dados simulados de uma NF extraída (DANFE IGUAÇU MAQUINAS LTDA)
        dados_nf = {
            "Número da Nota Fiscal": "000.084.682",
            "Data de Emissão": "15/09/2026",
            "Data de Vencimento": "15/10/2026",
            "Valor Total": "12.500,00",
            "Descrição dos Produtos": "ROLAMENTOS, GRAXAS E PEÇAS DE MANUTENÇÃO",
            "Fornecedor": {
                "Razão Social": "IGUAÇU MAQUINAS LTDA",
                "Fantasia": "Iguaçu Máquinas",
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
                "Quantidade": 2,
                "detalhes": [
                    {"parcela": 1, "vencimento": "15/10/2026", "valor": "6.250,00"},
                    {"parcela": 2, "vencimento": "15/11/2026", "valor": "6.250,00"}
                ]
            }
        }

        # -------------------------------------------------------------
        # PASSO 1: Análise antes do lançamento (deve apontar NÃO EXISTE)
        # -------------------------------------------------------------
        res_analise_inicial = self.client.post('/api/analise', json=dados_nf)
        self.assertEqual(res_analise_inicial.status_code, 200)
        analise_inicial = res_analise_inicial.get_json()

        self.assertFalse(analise_inicial['fornecedor']['existe'])
        self.assertEqual(analise_inicial['fornecedor']['mensagem'], 'NÃO EXISTE')

        self.assertFalse(analise_inicial['faturado']['existe'])
        self.assertEqual(analise_inicial['faturado']['mensagem'], 'NÃO EXISTE')

        # Despesa já existe no banco (pré-semeada)
        self.assertTrue(analise_inicial['despesa']['existe'])

        # -------------------------------------------------------------
        # PASSO 2: Lançar no Sistema Financeiro (Lançamento Automático)
        # -------------------------------------------------------------
        res_lancamento = self.client.post('/api/movimentos/lancar-automatico', json=dados_nf)
        self.assertEqual(res_lancamento.status_code, 201)
        lancamento_json = res_lancamento.get_json()

        self.assertTrue(lancamento_json['success'])
        self.assertIn("LANÇADO COM SUCESSO", lancamento_json['message'].upper())
        movimento_id = lancamento_json['movimento_id']
        fornecedor_id = lancamento_json['fornecedor_id']
        faturado_id = lancamento_json['faturado_id']

        self.assertIsNotNone(movimento_id)
        self.assertIsNotNone(fornecedor_id)
        self.assertIsNotNone(faturado_id)

        # -------------------------------------------------------------
        # PASSO 3: Re-análise (agora Fornecedor e Faturado devem EXISTIR)
        # -------------------------------------------------------------
        res_analise_pos = self.client.post('/api/analise', json=dados_nf)
        self.assertEqual(res_analise_pos.status_code, 200)
        analise_pos = res_analise_pos.get_json()

        self.assertTrue(analise_pos['fornecedor']['existe'])
        self.assertEqual(analise_pos['fornecedor']['id'], fornecedor_id)
        self.assertIn(f"EXISTE – ID: {fornecedor_id}", analise_pos['fornecedor']['mensagem'])

        self.assertTrue(analise_pos['faturado']['existe'])
        self.assertEqual(analise_pos['faturado']['id'], faturado_id)
        self.assertIn(f"EXISTE – ID: {faturado_id}", analise_pos['faturado']['mensagem'])

        # -------------------------------------------------------------
        # PASSO 4: Verificar reflexo no CRUD de Pessoas
        # -------------------------------------------------------------
        # Busca sem filtros traz vazio (Regra UniRV)
        res_pessoas_vazia = self.client.get('/api/pessoas')
        self.assertEqual(res_pessoas_vazia.get_json(), [])

        # Botão TODOS traz os 2 cadastros ativos
        res_pessoas_todos = self.client.get('/api/pessoas?todos=1')
        pessoas_ativas = res_pessoas_todos.get_json()
        self.assertEqual(len(pessoas_ativas), 2)

        # -------------------------------------------------------------
        # PASSO 5: Verificar reflexo no CRUD de Contas e Parcelas
        # -------------------------------------------------------------
        res_contas = self.client.get('/api/contas?todos=1&tipo=APAGAR')
        contas_ativas = res_contas.get_json()
        self.assertEqual(len(contas_ativas), 1)
        self.assertEqual(contas_ativas[0]['numero_documento'], "000.084.682")
        self.assertEqual(contas_ativas[0]['qtd_parcelas'], 2)

        # Detalhes do movimento
        res_detalhes = self.client.get(f'/api/contas/{movimento_id}')
        detalhes = res_detalhes.get_json()
        self.assertEqual(len(detalhes['parcelas']), 2)
        self.assertEqual(detalhes['parcelas'][0]['identificacao'], "1/2")
        self.assertEqual(detalhes['parcelas'][1]['identificacao'], "2/2")

        # -------------------------------------------------------------
        # PASSO 6: Testar Exclusão Lógica e Reativação
        # -------------------------------------------------------------
        # Excluir pessoa (soft-delete)
        res_del_pessoa = self.client.delete(f'/api/pessoas/{fornecedor_id}')
        self.assertEqual(res_del_pessoa.status_code, 200)

        # Lista de ativos agora deve ter apenas 1 pessoa
        res_pessoas_pos_del = self.client.get('/api/pessoas?todos=1')
        self.assertEqual(len(res_pessoas_pos_del.get_json()), 1)

        # Mas o fornecedor ainda existe no banco como INATIVO
        p_inativa = self.db.get_pessoa_by_id(fornecedor_id)
        self.assertEqual(p_inativa['status'], 'INATIVO')

        # Reativar pessoa
        res_reativar_p = self.client.patch(f'/api/pessoas/{fornecedor_id}/reativar')
        self.assertEqual(res_reativar_p.status_code, 200)
        p_reativada = self.db.get_pessoa_by_id(fornecedor_id)
        self.assertEqual(p_reativada['status'], 'ATIVO')

if __name__ == '__main__':
    unittest.main()
