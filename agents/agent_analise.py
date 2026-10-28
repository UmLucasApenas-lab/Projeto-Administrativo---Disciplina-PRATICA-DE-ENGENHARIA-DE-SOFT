import re
from utils.database import (
    find_pessoa_by_doc_or_name,
    find_classificacao_by_desc,
    find_produto_by_desc,
    save_pessoa,
    save_classificacao,
    save_produto,
    save_movimento_completo,
    clean_doc
)

def parse_moeda(valor_str) -> float:
    """Converte formato monetário BR ('6.478,76' ou 'R$ 6.478,76') para float (6478.76)."""
    if valor_str is None:
        return 0.0
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    
    s = str(valor_str).strip()
    s = re.sub(r'[^\d,.-]', '', s)                     
    if ',' in s and '.' in s:
                                     
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
                                     
        s = s.replace(',', '.')
    
    try:
        return float(s)
    except Exception:
        return 0.0

class AgentAnalise:
    """
    Agente responsável pela 2ª Etapa do Projeto Administrativo-Financeiro (UniRV).
    Realiza o cruzamento de dados de NF com o banco de dados (Fornecedor, Faturado e Despesa)
    e efetua o lançamento automático transacional.
    """

    def analisar_dados_nf(self, dados_nf: dict) -> dict:
        """
        Consulta no Banco de Dados se:
        - FORNECEDOR existe ou não
        - FATURADO existe ou não
        - DESPESA existe ou não
        - PRODUTO/INSUMO existe ou não
        Retorna o dicionário de status no padrão visual exigido na Página 2 do PDF.
        """
        fornecedor_data = dados_nf.get("Fornecedor", {})
        faturado_data = dados_nf.get("Faturado", {})
        classif_data = dados_nf.get("CLASSIFICAÇÃO", {})

        f_razao = fornecedor_data.get("Razão Social") or dados_nf.get("Nome do Emitente", "")
        f_cnpj = fornecedor_data.get("CNPJ") or dados_nf.get("CNPJ do Emitente", "")
        
        pessoa_fornecedor = find_pessoa_by_doc_or_name(cnpj_cpf=f_cnpj, nome=f_razao, tipo="FORNECEDOR")
        
        status_fornecedor = {
            "existe": bool(pessoa_fornecedor),
            "id": pessoa_fornecedor["id"] if pessoa_fornecedor else None,
            "razao_social": f_razao or (pessoa_fornecedor["razao_social_nome"] if pessoa_fornecedor else "Não identificado"),
            "cnpj": f_cnpj or (pessoa_fornecedor["cnpj_cpf"] if pessoa_fornecedor else ""),
            "mensagem": f"EXISTE – ID: {pessoa_fornecedor['id']}" if pessoa_fornecedor else "NÃO EXISTE"
        }

        fat_nome = faturado_data.get("Nome Completo") or dados_nf.get("Nome do Destinatário", "")
        fat_cpf = faturado_data.get("CPF") or dados_nf.get("CPF/CNPJ do Destinatário", "")
        
        pessoa_faturado = find_pessoa_by_doc_or_name(cnpj_cpf=fat_cpf, nome=fat_nome, tipo="FATURADO")
        
        status_faturado = {
            "existe": bool(pessoa_faturado),
            "id": pessoa_faturado["id"] if pessoa_faturado else None,
            "nome": fat_nome or (pessoa_faturado["razao_social_nome"] if pessoa_faturado else "Não identificado"),
            "cpf": fat_cpf or (pessoa_faturado["cnpj_cpf"] if pessoa_faturado else ""),
            "mensagem": f"EXISTE – ID: {pessoa_faturado['id']}" if pessoa_faturado else "NÃO EXISTE"
        }

        categoria_despesa = classif_data.get("categoria") or dados_nf.get("Classificação da Despesa", "")
        classificacao_obj = find_classificacao_by_desc(categoria_despesa, tipo="DESPESA")

        status_despesa = {
            "existe": bool(classificacao_obj),
            "id": classificacao_obj["id"] if classificacao_obj else None,
            "descricao": categoria_despesa or (classificacao_obj["descricao"] if classificacao_obj else "Não Classificado"),
            "mensagem": f"EXISTE – ID: {classificacao_obj['id']}" if classificacao_obj else "NÃO EXISTE"
        }

        descricao_prod = dados_nf.get("Descrição dos Produtos") or dados_nf.get("descricao_produtos", "")
        desc_limpa = descricao_prod.split("\n")[0].split(";")[0].strip() if descricao_prod else ""
        prod_obj = find_produto_by_desc(desc_limpa) if desc_limpa else None
        
        status_produto = {
            "existe": bool(prod_obj),
            "id": prod_obj["id"] if prod_obj else None,
            "descricao": desc_limpa or "Item de Nota Fiscal",
            "mensagem": f"EXISTE – ID: {prod_obj['id']}" if prod_obj else "NÃO EXISTE"
        }

        return {
            "fornecedor": status_fornecedor,
            "faturado": status_faturado,
            "despesa": status_despesa,
            "produto": status_produto
        }

    def lancar_registro_automatico(self, dados_nf: dict) -> dict:
        """
        Executa os 5 passos exigidos na Página 2 do PDF:
        1. CRIAR O NOVO FORNECEDOR (se for o caso)
        2. CRIAR O NOVO FATURADO (se for o caso)
        3. CRIAR NOVA DESPESA (se for o caso)
        4. CRIAR UM NOVO REGISTRO DO MOVIMENTO E SUA PARCELA
        5. INFORMAR AO USUÁRIO QUE REGISTRO FOI LANÇADO COM SUCESSO.
        """
        analise = self.analisar_dados_nf(dados_nf)

        if analise["fornecedor"]["existe"]:
            fornecedor_id = analise["fornecedor"]["id"]
        else:
            fornecedor_id = save_pessoa({
                "tipo": "CLIENTE-FORNECEDOR",
                "razao_social_nome": analise["fornecedor"]["razao_social"],
                "cnpj_cpf": analise["fornecedor"]["cnpj"]
            })

        if analise["faturado"]["existe"]:
            faturado_id = analise["faturado"]["id"]
        else:
            faturado_id = save_pessoa({
                "tipo": "FATURADO",
                "razao_social_nome": analise["faturado"]["nome"],
                "cnpj_cpf": analise["faturado"]["cpf"]
            })

        if analise["despesa"]["existe"]:
            despesa_id = analise["despesa"]["id"]
        else:
            despesa_id = save_classificacao({
                "tipo": "DESPESA",
                "descricao": analise["despesa"]["descricao"]
            })

        valor_total_float = parse_moeda(dados_nf.get("Valor Total", 0))
        numero_doc = dados_nf.get("Número da Nota Fiscal", "S/N")
        data_emissao = dados_nf.get("Data de Emissão", "")
        data_vencimento = dados_nf.get("Data de Vencimento") or data_emissao
        descricao_produtos = dados_nf.get("Descrição dos Produtos", f"Nota Fiscal {numero_doc}")

        if analise["produto"]["existe"]:
            produto_id = analise["produto"]["id"]
        else:
            produto_id = save_produto({
                "descricao": analise["produto"]["descricao"],
                "categoria": analise["despesa"]["descricao"],
                "unidade": "UN",
                "valor_unitario": valor_total_float
            })

        parcelas_dados = []
        raw_parcelas = dados_nf.get("Parcelas", {}).get("detalhes", [])
        if raw_parcelas:
            for p in raw_parcelas:
                parcelas_dados.append({
                    "numero_parcela": p.get("parcela", 1),
                    "data_vencimento": p.get("vencimento", data_vencimento),
                    "valor": parse_moeda(p.get("valor", valor_total_float / len(raw_parcelas)))
                })
        else:
            parcelas_dados.append({
                "numero_parcela": 1,
                "data_vencimento": data_vencimento,
                "valor": valor_total_float
            })

        movimento_payload = {
            "tipo": "APAGAR",
            "numero_documento": numero_doc,
            "descricao": descricao_produtos,
            "data_emissao": data_emissao,
            "valor_total": valor_total_float,
            "pessoa_fornecedor_id": fornecedor_id,
            "pessoa_faturado_id": faturado_id,
            "classificacoes": [{"classificacao_id": despesa_id, "valor": valor_total_float}],
            "parcelas": parcelas_dados
        }

        movimento_id = save_movimento_completo(movimento_payload)

        return {
            "success": True,
            "message": "REGISTRO FOI LANÇADO COM SUCESSO.",
            "movimento_id": movimento_id,
            "fornecedor_id": fornecedor_id,
            "faturado_id": faturado_id,
            "classificacao_id": despesa_id,
            "produto_id": produto_id
        }
