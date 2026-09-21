import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def create_sample_nf_manutencao(filename="exemplo_nf_manutencao.pdf"):
    """
    Gera uma nota fiscal simulada de Peças e Manutenção (Iguaçu Máquinas Agrícolas)
    semelhante ao exemplo demonstrado em aula pelo professor.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "DANFE - DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRÔNICA")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 65, "CHAVE DE ACESSO: 5225 0913 1425 9700 0746 5500 1000 0084 3819 8490 0945")

    # Linha divisória
    c.setLineWidth(1)
    c.setStrokeColor(colors.gray)
    c.line(50, height - 75, width - 50, height - 75)

    # Dados do Emitente
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 95, "EMITENTE: IGUAÇU MÁQUINAS AGRÍCOLAS LTDA")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 110, "Nome Fantasia: IGUAÇU MÁQUINAS JOHN DEERE")
    c.drawString(50, height - 125, "CNPJ: 33.656.729/0023-85   Inscrição Estadual: 10.293.847-1")
    c.drawString(50, height - 140, "Endereço: Rodovia BR-060, Km 385 - Zona Rural, Rio Verde - GO, 75900-000")

    # Quadro da Nota
    c.rect(width - 220, height - 150, 170, 60)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(width - 210, height - 105, "NF-e Nº: 000.084.682")
    c.setFont("Helvetica", 9)
    c.drawString(width - 210, height - 120, "SÉRIE: 001")
    c.drawString(width - 210, height - 135, "EMISSÃO: 19/09/2025")

    c.line(50, height - 160, width - 50, height - 160)

    # Dados do Destinatário / Faturado
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 180, "DESTINATÁRIO / FATURADO")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 195, "Nome / Razão Social: CICLANO DA SILVA")
    c.drawString(50, height - 210, "CPF: 999.999.999-99")
    c.drawString(50, height - 225, "Endereço: Fazenda Boa Esperança, Lote 12 - Rio Verde - GO")
    c.drawString(50, height - 240, "Data de Vencimento: 17/10/2025")

    c.line(50, height - 255, width - 50, height - 255)

    # Tabela de Produtos / Serviços
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 275, "DADOS DOS PRODUTOS / SERVIÇOS")
    
    # Cabeçalho da tabela
    c.setFillColor(colors.whitesmoke)
    c.rect(50, height - 300, width - 100, 20, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, height - 295, "CÓDIGO")
    c.drawString(120, height - 295, "DESCRIÇÃO DO PRODUTO / SERVIÇO")
    c.drawString(380, height - 295, "QTD")
    c.drawString(430, height - 295, "VL. UNIT")
    c.drawString(490, height - 295, "VL. TOTAL")

    # Linhas dos produtos
    itens = [
        ("001", "GRAXA DE POLIUREIA MP SD 400G", "4 UN", "48,50", "194,00"),
        ("002", "ANEL DE VEDAÇÃO HIDRÁULICO 50MM", "6 UN", "32,00", "192,00"),
        ("003", "BUCHA DE GUIA PARA COLHEITADEIRA", "2 UN", "185,00", "370,00"),
        ("004", "ROLAMENTO DE ESFERAS 6205-2RS", "4 UN", "125,50", "502,00"),
        ("005", "ROLAMENTO DE ROLOS CONICOS 30208", "2 UN", "240,00", "480,00"),
        ("006", "ESTOPA DE LIMPEZA MECÂNICA 5KG", "3 PACOTES", "45,00", "135,00"),
        ("007", "PANO PARA LIMPEZA INDUSTRIAL", "10 UN", "18,00", "180,00"),
        ("008", "LIMPADOR PREMIUM DESENGRAXANTE 20L", "2 GL", "516,87", "1.033,75"),
    ]

    y = height - 320
    c.setFont("Helvetica", 9)
    for cod, desc, qtd, vu, vt in itens:
        c.drawString(55, y, cod)
        c.drawString(120, y, desc)
        c.drawString(380, y, qtd)
        c.drawString(430, y, vu)
        c.drawString(495, y, vt)
        y -= 18

    c.line(50, y - 10, width - 50, y - 10)

    # Fatura / Parcelas e Totais
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y - 30, "FATURA / DUPLICATA")
    c.setFont("Helvetica", 9)
    c.drawString(50, y - 45, "Parcela 1/1 - Vencimento: 17/10/2025 - Valor: R$ 3.086,75")

    c.rect(width - 220, y - 60, 170, 40)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 210, y - 40, "VALOR TOTAL DA NOTA:")
    c.drawString(width - 210, y - 55, "R$ 3.086,75")

    # Rodapé
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 40, "UniRV - Universidade de Rio Verde - Engenharia de Software - Projeto Prático N2")
    c.drawString(50, 28, "Documento simulado para extração e classificação de notas fiscais via IA")

    c.save()
    print(f"PDF de teste gerado com sucesso: {filename}")

def create_sample_nf_insumos(filename="exemplo_nf_insumos.pdf"):
    """
    Gera uma nota fiscal simulada de Insumos Agrícolas (Sementes e Fertilizantes).
    """
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "DANFE - NOTA FISCAL ELETRÔNICA")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 65, "CHAVE: 5226 0110 9988 7700 0123 5500 1000 0054 1211 2233 4455")
    c.line(50, height - 75, width - 50, height - 75)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 95, "EMITENTE: AGROVET INSUMOS E DEFENSIVOS AGRÍCOLAS S/A")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 110, "Nome Fantasia: AGROVET CERRADO")
    c.drawString(50, height - 125, "CNPJ: 18.234.567/0001-92   IE: 10.455.899-0")
    c.drawString(50, height - 140, "Endereço: Setor Industrial, Qd. 4 - Rio Verde - GO")

    c.rect(width - 220, height - 150, 170, 60)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(width - 210, height - 105, "NF-e Nº: 000.054.121")
    c.setFont("Helvetica", 9)
    c.drawString(width - 210, height - 120, "SÉRIE: 002")
    c.drawString(width - 210, height - 135, "EMISSÃO: 10/09/2026")

    c.line(50, height - 160, width - 50, height - 160)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 180, "DESTINATÁRIO / FATURADO")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 195, "Nome: LUCAS DE SOUZA MENEZES")
    c.drawString(50, height - 210, "CPF: 123.456.789-00")
    c.drawString(50, height - 225, "Endereço: Fazenda Santa Cruz - Rio Verde - GO")
    c.drawString(50, height - 240, "Data de Vencimento: 10/10/2026")

    c.line(50, height - 255, width - 50, height - 255)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 275, "DADOS DOS PRODUTOS / SERVIÇOS")

    c.setFillColor(colors.whitesmoke)
    c.rect(50, height - 300, width - 100, 20, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, height - 295, "CÓDIGO")
    c.drawString(120, height - 295, "DESCRIÇÃO")
    c.drawString(380, height - 295, "QTD")
    c.drawString(430, height - 295, "VL. UNIT")
    c.drawString(490, height - 295, "VL. TOTAL")

    itens = [
        ("IN01", "SEMENTES DE SOJA TRANSGÊNICA MONSOY 50KG", "40 SC", "220,00", "8.800,00"),
        ("IN02", "FERTILIZANTE MINERAL NPK 04-14-08 BAG 1000KG", "5 BG", "2.100,00", "10.500,00"),
        ("IN03", "DEFENSIVO AGRÍCOLA HERBICIDA GLIFOSATO 20L", "6 GL", "350,00", "2.100,00"),
        ("IN04", "CORRETIVO DE SOLO CALCÁRIO DOLOMÍTICO A GRANEL", "15 TON", "140,00", "2.100,00")
    ]

    y = height - 320
    c.setFont("Helvetica", 9)
    for cod, desc, qtd, vu, vt in itens:
        c.drawString(55, y, cod)
        c.drawString(120, y, desc)
        c.drawString(380, y, qtd)
        c.drawString(430, y, vu)
        c.drawString(490, y, vt)
        y -= 22

    c.line(50, y - 10, width - 50, y - 10)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y - 30, "FATURA / DUPLICATA")
    c.setFont("Helvetica", 9)
    c.drawString(50, y - 45, "Parcela 1/1 - Vencimento: 10/10/2026 - Valor: R$ 23.500,00")

    c.rect(width - 220, y - 60, 170, 40)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 210, y - 40, "VALOR TOTAL DA NOTA:")
    c.drawString(width - 210, y - 55, "R$ 23.500,00")

    c.save()
    print(f"PDF de teste de insumos gerado: {filename}")

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_notas")
    os.makedirs(output_dir, exist_ok=True)
    create_sample_nf_manutencao(os.path.join(output_dir, "nota_fiscal_manutencao_exemplo.pdf"))
    create_sample_nf_insumos(os.path.join(output_dir, "nota_fiscal_insumos_exemplo.pdf"))
