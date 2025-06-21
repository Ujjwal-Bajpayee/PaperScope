import fitz  

def extract_text_from_pdf(file_path):
    """
    Extract full text from a PDF file using PyMuPDF.
    """
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text
