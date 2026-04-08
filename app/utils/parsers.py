import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from all pages of a PDF file."""
    pages = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text().strip()
            if text:
                pages.append(text)
    return "\n\n".join(pages)
