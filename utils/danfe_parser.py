import re
import unicodedata

def clean_doc(doc_str):
    if not doc_str:
        return ""
    return re.sub(r'[^\d]', '', doc_str)

def format_cnpj(cnpj):
    nums = clean_doc(cnpj)
    if len(nums) == 14:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:]}"
    return cnpj

def format_cpf(cpf):
    nums = clean_doc(cpf)
    if len(nums) == 11:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"
    return cpf

def parse_date(date_str):
    if not date_str:
        return ""
    date_str = date_str.strip()
    m = re.search(r'(\d{2})[\./\-](\d{2})[\./\-](\d{4})', date_str)
    if m:
        day, month, year = m.groups()
        return f"{day}/{month}/{year}"
    return date_str

def format_nf_number(raw):
    raw = clean_doc(raw)
    if not raw:
        return ""
    if len(raw) <= 9:
        padded = raw.zfill(9)
        return f"{padded[:3]}.{padded[3:6]}.{padded[6:]}"
    return raw

def parse_danfe_text(text):
    if not text:
        text = ""

    chave_acesso = ""
    chave_match = re.search(r'(?:CHAVE DE ACESSO|CHAVE)[:\s_]*((?:\d{4}[\s_]*){11})', text, re.IGNORECASE)
    if chave_match:
        chave_acesso = re.sub(r'[\s_]', '', chave_match.group(1))
    else:
        clean_text_digits = re.sub(r'[^\d]', '', text)
        m_chave = re.search(r'(\d{44})', clean_text_digits)
        if m_chave:
            chave_acesso = m_chave.group(1)

    numero_nf = ""
    nf_match = re.search(r'(?:N[ºo\.]|No\.|NF-?e\s*(?:N[ºo\.]?)?|Nota Fiscal[^\d\n]*)[:\s]*([0-9]{1,3}(?:\.[0-9]{3}){1,2}|[0-9]{6,9})', text, re.IGNORECASE)
    if nf_match:
        numero_nf = format_nf_number(nf_match.group(1))
    elif len(chave_acesso) == 44:
        numero_nf = format_nf_number(chave_acesso[25:34])
    else:
        m_simple = re.search(r'N[ºo\.]\s*([0-9\.]+)', text, re.IGNORECASE)
        if m_simple:
            numero_nf = format_nf_number(m_simple.group(1))

    all_cnpjs = re.findall(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', text)
    all_cpfs = re.findall(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', text)

    emitente_nome = ""
    emitente_cnpj = ""
    emitente_fantasia = ""

    rec_match = re.search(r'RECEBEMOS DE\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\s+([^,\n\r]+?)\s+OS PRODUTOS', text, re.IGNORECASE)
    if rec_match:
        emitente_cnpj = rec_match.group(1).strip()
        emitente_nome = rec_match.group(2).strip()

    if not emitente_nome:
        emit_header_match = re.search(r'EMITENTE:\s*([^\n\r]+)', text, re.IGNORECASE)
        if emit_header_match:
            emitente_nome = emit_header_match.group(1).strip()

    if not emitente_nome:
        danfe_pos = text.find("DANFE")
        if danfe_pos != -1:
            top_part = text[:danfe_pos]
            cand_lines = [
                l.strip() for l in top_part.split('\n')
                if l.strip() and not l.startswith('-') and not any(k in l.upper() for k in [
                    'RECEBEMOS', 'DATA DE RECEBIMENTO', 'IDENTIFICA', 'ASSINATURA', 'NFE', 'NO.', 'SÉRIE', 'SERIE'
                ])
            ]
            if cand_lines:
                cand = cand_lines[0]
                if len(cand_lines) > 1 and any(s in cand_lines[1].upper() for s in ["S.A.", "LTDA", "EIRELI", "S/A", "ME"]):
                    cand += " " + cand_lines[1]
                emitente_nome = cand

    if not emitente_cnpj and len(chave_acesso) == 44:
        emitente_cnpj = format_cnpj(chave_acesso[6:20])
    elif not emitente_cnpj and all_cnpjs:
        emitente_cnpj = all_cnpjs[0]

    fant_match = re.search(r'Nome Fantasia:\s*([^\n\r]+)', text, re.IGNORECASE)
    if fant_match:
        emitente_fantasia = fant_match.group(1).strip()
    else:
        ident_match = re.search(r'IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\s*\n\s*([A-Z0-9\s]+?)(?:\n|No\.)', text)
        if ident_match and len(ident_match.group(1).strip()) > 3:
            emitente_fantasia = ident_match.group(1).strip()
        else:
            emitente_fantasia = emitente_nome

    destinatario_nome = ""
    destinatario_doc = ""

    m_dest_start = re.search(r'DESTINAT[AÁ\w]*\s*(?:/|\be\b|\s)*\s*(?:REMETENTE|FATURADO)?', text, re.IGNORECASE)
    if m_dest_start:
        start_idx = m_dest_start.end()
        dest_chunk = text[start_idx:start_idx+1200]

        m_name = re.search(r'(?:NOME/RAZÃO SOCIAL|Nome / Razão Social|Nome Razão Social|Nome)[:\s]*\n?\s*([^\n\r]+)', dest_chunk, re.IGNORECASE)
        if m_name:
            cand_name = m_name.group(1).strip()
            if not any(rot in cand_name.upper() for rot in ["CNPJ", "CPF", "ENDEREÇO", "BAIRRO", "DATA"]):
                destinatario_nome = cand_name

        m_doc = re.search(r'(?:CNPJ/CPF|CPF/CNPJ|CNPJ|CPF)[:\s]*\n?\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})', dest_chunk, re.IGNORECASE)
        if m_doc:
            destinatario_doc = m_doc.group(1).strip()

    if not destinatario_doc:
        if all_cpfs:
            destinatario_doc = all_cpfs[0]
        elif len(all_cnpjs) > 1:
            for c in all_cnpjs:
                if c != emitente_cnpj:
                    destinatario_doc = c
                    break

    data_emissao = ""
    data_vencimento = ""

    emissao_match = re.search(r'(?:DATA DA EMISSÃO|DATA DE EMISSÃO|EMISS[ÃA]O)[:\s\n]*(\d{2}[\./\-]\d{2}[\./\-]\d{4})', text, re.IGNORECASE)
    if emissao_match:
        data_emissao = parse_date(emissao_match.group(1))
    else:
        proto_match = re.search(r'PROTOCOLO DE AUTORIZAÇÃO[^\n]*\n[^\n]*?(\d{2}[\./\-]\d{2}[\./\-]\d{4})', text, re.IGNORECASE)
        if proto_match:
            data_emissao = parse_date(proto_match.group(1))
        else:
            dates = re.findall(r'\b\d{2}[\./\-]\d{2}[\./\-]\d{4}\b', text)
            if dates:
                data_emissao = parse_date(dates[0])

    venc_match = re.search(r'(?:Data de Vencimento|VENCIMENTO|Venc\.?)[:\s\n]*(\d{2}[\./\-]\d{2}[\./\-]\d{4})', text, re.IGNORECASE)
    if venc_match:
        data_vencimento = parse_date(venc_match.group(1))

    if not data_vencimento and data_emissao:
        data_vencimento = data_emissao

    valor_total = ""
    val_tot_match = re.search(r'(?:V\.TOT\. DA NF|VALOR TOTAL DA NOTA|VALOR TOTAL|V\. TOT\. DA NF)[:\s\n]*R?\$?\s*([\d\.,]+)', text, re.IGNORECASE)
    if not val_tot_match:
        val_tot_match = re.search(r'(?:V\.\s*TOT\.\s*PROD\.?)[:\s\n]*R?\$?\s*([\d\.,]+)', text, re.IGNORECASE)
    
    if val_tot_match:
        valor_total = val_tot_match.group(1).strip()
    else:
        money_matches = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', text)
        if money_matches:
            valor_total = money_matches[-1]

    produtos = []
    prod_matches = list(re.finditer(r'DADOS DOS PRODUTOS[\s/SERVIÇOS]*\n', text, re.IGNORECASE))
    
    stop_headers = {
        "CÓD.", "COD.", "CÓDIGO", "CODIGO", "DESCRIÇÃO DO PRODUTO/SERVIÇO",
        "DESCRIÇÃO DO PRODUTO", "DESCRICAO DO PRODUTO", "DESCRIÇÃO", "DESCRICAO",
        "NCM/SH", "NCM", "CST", "CFOP", "VALOR TOTAL", "VL. TOTAL", "VLTOTAL",
        "BC ICMS", "VL. ICMS", "VL ICMS", "VL. IPI", "ALIQ ICMS", "ALIQ IPI",
        "ALIQ", "QTD", "QTDE.", "QTDE", "VL. UNIT.", "VL. UNIT", "VL UNIT", "UN"
    }

    for pm in prod_matches:
        start_idx = pm.end()
        end_match = re.search(r'\n(?:\s*DADOS ADICIONAIS|\s*INFORMAÇÕES COMPLEMENTARES|\s*CÁLCULO DO ISSQN|\s*TRANSPORTADOR|\s*FATURA|\s*VALOR TOTAL DA NOTA|\s*CHAVE DE ACESSO|\s*RECEBEMOS DE)', text[start_idx:], re.IGNORECASE)
        end_idx = start_idx + end_match.start() if end_match else start_idx + 4000
        block_text = text[start_idx:end_idx]

        for line in block_text.split('\n'):
            line = line.strip()
            if not line or len(line) < 3:
                continue

            if re.match(r'^[\d\s\.,/-]+$', line):
                continue

            upper_line = line.upper()
            if upper_line in stop_headers or any(upper_line == h for h in stop_headers):
                continue
            if any(upper_line.startswith(h) for h in ["CÓD.", "COD.", "DESCRIÇÃO DO PRODUTO", "DADOS DOS PRODUTOS", "NCM/SH", "EAN:"]):
                continue
            if line.startswith("---") or line.startswith("___"):
                continue

            m_item = re.match(r'^(?:[0-9]{3,12}|[A-Z]{1,4}[0-9]{1,6})\s+([A-Za-zÀ-ÖØ-öø-ÿ0-9\s\.\-/_%]+?)(?:\s+[0-9]{6,8}|\s+(?:UN|PC|PEÇ|KG|SC|BG|TON|GL|LT|M2|M3)\b|\s+[0-9]+,[0-9]+|\s*$)', line, re.IGNORECASE)
            if m_item:
                desc = m_item.group(1).strip()
                desc = re.sub(r'\s+\d{6,8}$', '', desc).strip()
                if len(desc) > 3 and desc.upper() not in stop_headers and desc not in produtos:
                    if not re.match(r'^[\d\s]+$', desc):
                        produtos.append(desc)
            else:
                clean_line = re.sub(r'\b(?:UN|PC|PEÇ|KG|SC|BG|TON|GL|LT|M2|M3)\b.*', '', line).strip()
                if len(clean_line) > 4 and clean_line.upper() not in stop_headers:
                    if re.match(r'^\d+\s*[A-Za-z]+\s*[\d,\.]+$', clean_line):
                        continue
                    if not re.match(r'^[\d\s]+$', clean_line):
                        if not any(stop_word in clean_line.upper() for stop_word in [
                            "PROTOCOLO", "INSCRIÇÃO", "CHAVE", "PREÇO", "TOTAL", "VALOR", "IMPOSTO", "ICMS", "FATURA", "PARCELA", "DADOS DOS PRODUTOS"
                        ]):
                            if clean_line not in produtos:
                                produtos.append(clean_line)

    descricao_final = ""
    if produtos:
        descricao_final = " | ".join(produtos)
    else:
        m_items = re.findall(r'\b(?:CAMISA|CAMISETA|CAPACETE|SEMENTE|FERTILIZANTE|DEFENSIVO|CALC[ÁA]RIO|GRAXA|ANEL|BUCHA|ROLAMENTO|ESTOPA|PANO|LIMPADOR|DIESEL|OLEO|PE[ÇC]A)[A-Za-zÀ-ÖØ-öø-ÿ0-9\s\.\-/_%]+', text, re.IGNORECASE)
        if m_items:
            descricao_final = " | ".join(dict.fromkeys([it.strip() for it in m_items if len(it.strip()) > 5]))

    if not descricao_final:
        descricao_final = "Produtos e serviços listados no corpo da Nota Fiscal"

    text_analise = (descricao_final + " " + emitente_nome + " " + emitente_fantasia + " " + text).upper()
    categoria = "Não Classificado"
    termos = []

    regras_categorias = [
        ("INSUMOS AGRÍCOLAS", [
            ("SEMENTE", "SEMENTES AGRÍCOLAS"),
            ("FERTILIZANTE", "FERTILIZANTE MINERAL / NPK"),
            ("ADUBO", "ADUBO"),
            ("DEFENSIVO", "DEFENSIVO AGRÍCOLA"),
            ("HERBICIDA", "HERBICIDA"),
            ("GLIFOSATO", "GLIFOSATO"),
            ("FUNGICIDA", "FUNGICIDA"),
            ("INSETICIDA", "INSETICIDA"),
            ("CALCÁRIO", "CORRETIVO DE SOLO / CALCÁRIO"),
            ("CALCARIO", "CORRETIVO DE SOLO / CALCÁRIO"),
            ("CORRETIVO", "CORRETIVO AGRÍCOLA"),
            ("MONSOY", "SEMENTES MONSOY"),
            ("AGROVET", "INSUMOS AGROVET")
        ]),
        ("RECURSOS HUMANOS", [
            ("CAPACETE", "CAPACETE DE SEGURANÇA (EPI)"),
            ("CAMISA", "UNIFORME / CAMISA OPERACIONAL"),
            ("CAMISETA", "UNIFORME / CAMISETA OPERACIONAL"),
            ("EPI", "EQUIPAMENTO DE PROTEÇÃO INDIVIDUAL (EPI)"),
            ("UNIFORME", "UNIFORME DE TRABALHO"),
            ("BOTA", "BOTA DE SEGURANÇA"),
            ("LUVA", "LUVAS DE PROTEÇÃO"),
            ("MACACÃO", "MACACÃO DE OPERAÇÃO"),
            ("SALÁRIO", "SALÁRIO E ENCARGOS"),
            ("MÃO DE OBRA", "MÃO DE OBRA TEMPORÁRIA")
        ]),
        ("MANUTENÇÃO E OPERAÇÃO", [
            ("GRAXA", "GRAXA / LUBRIFICANTE"),
            ("ROLAMENTO", "ROLAMENTOS"),
            ("PEÇA", "PEÇAS DE REPOSIÇÃO"),
            ("PECA", "PEÇAS DE REPOSIÇÃO"),
            ("FILTRO", "FILTROS"),
            ("CORREIA", "CORREIAS"),
            ("PNEU", "PNEUS"),
            ("OLEO", "ÓLEOS E LUBRIFICANTES"),
            ("ÓLEO", "ÓLEOS E LUBRIFICANTES"),
            ("DIESEL", "COMBUSTÍVEL DIESEL"),
            ("BUCHA", "BUCHAS E GUIAS MECÂNICAS"),
            ("ANEL DE VEDAÇÃO", "VEDAÇÕES MECÂNICAS"),
            ("VEDAÇÃO", "VEDAÇÕES"),
            ("ESTOPA", "MATERIAL DE LIMPEZA MECÂNICA"),
            ("DESENGRAXANTE", "DESENGRAXANTE INDUSTRIAL"),
            ("PARAFUSO", "PARAFUSOS E FIXADORES")
        ]),
        ("SERVIÇOS OPERACIONAIS", [
            ("FRETE", "FRETE E TRANSPORTE"),
            ("TRANSPORTE", "TRANSPORTE DE CARGAS"),
            ("COLHEITA", "SERVIÇO DE COLHEITA TERCEIRIZADA"),
            ("SECAGEM", "SECAGEM DE GRÃOS"),
            ("ARMAZENAGEM", "ARMAZENAGEM")
        ]),
        ("INFRAESTRUTURA E UTILIDADES", [
            ("ENERGIA", "ENERGIA ELÉTRICA"),
            ("EQUATORIAL", "ENERGIA ELÉTRICA"),
            ("ENEL", "ENERGIA ELÉTRICA"),
            ("ARRENDAMENTO", "ARRENDAMENTO DE TERRAS"),
            ("CONSTRUÇÃO", "MATERIAIS DE CONSTRUÇÃO"),
            ("CIMENTO", "CIMENTO E MATERIAIS")
        ]),
        ("ADMINISTRATIVAS", [
            ("HONORÁRIOS", "HONORÁRIOS PROFISSIONAIS"),
            ("CONTABIL", "SERVIÇOS CONTÁBEIS"),
            ("ADVOCACIA", "SERVIÇOS JURÍDICOS"),
            ("TARIFA", "TARIFAS BANCÁRIAS")
        ]),
        ("SEGUROS E PROTEÇÃO", [
            ("SEGURO", "SEGURO AGRÍCOLA / PATRIMONIAL"),
            ("APÓLICE", "APÓLICE DE SEGURO")
        ]),
        ("IMPOSTOS E TAXAS", [
            ("ITR", "IMPOSTO TERRITORIAL RURAL (ITR)"),
            ("IPTU", "IPTU"),
            ("IPVA", "IPVA"),
            ("INCRA", "TAXA INCRA-CCIR")
        ]),
        ("INVESTIMENTOS", [
            ("TRATOR", "AQUISIÇÃO DE TRATOR"),
            ("COLHEITADEIRA", "AQUISIÇÃO DE COLHEITADEIRA"),
            ("IMPLEMENTO", "IMPLEMENTOS AGRÍCOLAS"),
            ("CAMINHÃO", "VEÍCULOS / CAMINHÕES")
        ])
    ]

    for cat_nome, palavras in regras_categorias:
        detectados = []
        for kw, desc_termo in palavras:
            if kw in text_analise:
                detectados.append(desc_termo)
        if detectados:
            categoria = cat_nome
            termos = list(dict.fromkeys(detectados))
            break

    if categoria == "Não Classificado":
        categoria = "MANUTENÇÃO E OPERAÇÃO"
        termos = ["MATERIAL DE USO OU CONSUMO"]

    parcelas_info = {
        "Quantidade": 1,
        "detalhes": [
            {
                "parcela": 1,
                "vencimento": data_vencimento,
                "valor": valor_total
            }
        ]
    }

    dups = re.findall(r'(?:Parcela\s+(\d+/\d+)|\b(\d{3})\b)\s*[-:]?\s*(?:Vencimento:?|Venc\.?)?\s*(\d{2}[\./\-]\d{2}[\./\-]\d{4})\s*[-:]?\s*(?:Valor:?|Val\.?)?\s*R?\$?\s*([\d\.,]+)', text, re.IGNORECASE)
    if dups:
        detalhes = []
        for idx, item in enumerate(dups, 1):
            p_num = item[0] or item[1] or str(idx)
            p_venc = parse_date(item[2])
            p_val = item[3]
            detalhes.append({
                "parcela": idx,
                "identificacao": p_num,
                "vencimento": p_venc,
                "valor": p_val
            })
        if detalhes:
            parcelas_info = {
                "Quantidade": len(detalhes),
                "detalhes": detalhes
            }

    return {
        "Número da Nota Fiscal": numero_nf,
        "Data de Emissão": data_emissao,
        "Data de Vencimento": data_vencimento,
        "Descrição dos Produtos": descricao_final,
        "Valor Total": valor_total,
        "Nome do Emitente": emitente_nome,
        "CNPJ do Emitente": emitente_cnpj,
        "Nome Fantasia do Emitente": emitente_fantasia,
        "Nome do Destinatário": destinatario_nome,
        "CPF/CNPJ do Destinatário": destinatario_doc,
        "Quantidade de Parcelas": parcelas_info["Quantidade"],
        "Fornecedor": {
            "Razão Social": emitente_nome,
            "Fantasia": emitente_fantasia,
            "CNPJ": emitente_cnpj
        },
        "Faturado": {
            "Nome Completo": destinatario_nome,
            "CPF": destinatario_doc
        },
        "Parcelas": parcelas_info,
        "CLASSIFICAÇÃO": {
            "categoria": categoria,
            "termos_detectados": termos
        }
    }
