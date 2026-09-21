import os
import pypdf
import pymupdf as fitz

def extract_text_from_pdf(pdf_path_or_bytes):
    """
    Extrai o texto legível de um arquivo PDF usando PyPDF e PyMuPDF como fallback.
    Retorna o texto concatenado de todas as páginas.
    """
    text = ""
    try:
        if isinstance(pdf_path_or_bytes, (str, bytes, bytearray)):
            doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf") if isinstance(pdf_path_or_bytes, (bytes, bytearray)) else fitz.open(pdf_path_or_bytes)
            for page in doc:
                text += page.get_text() + "\n"
            if text.strip():
                return text.strip()
    except Exception as e:
        print(f"Aviso PyMuPDF: {e}")

    try:
        reader = pypdf.PdfReader(pdf_path_or_bytes)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"Aviso PyPDF: {e}")

    return text.strip()

def get_pdf_metadata(pdf_path_or_bytes):
    """
    Obtém metadados do PDF (número de páginas, etc.).
    """
    try:
        if isinstance(pdf_path_or_bytes, (bytes, bytearray)):
            doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
        else:
            doc = fitz.open(pdf_path_or_bytes)
        return {
            "page_count": len(doc),
            "is_encrypted": doc.is_encrypted
        }
    except Exception:
        return {"page_count": 1, "is_encrypted": False}
