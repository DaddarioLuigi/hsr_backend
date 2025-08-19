# ocr/mistral_ocr.py
from pathlib import Path
from typing import Dict, List
import os

# Dipendenze Mistral:
# pip install mistralai  (se usi il loro SDK) oppure il client mostrato nel tuo snippet
from mistralai.models import OCRResponse  # adatta alle tue import reali
from mistralai import Mistral, DocumentURLChunk

class MistralOCR:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY non configurata")
        self.client = Mistral(api_key=self.api_key)

    def process_pdf(self, pdf_path: str) -> OCRResponse:
        pdf_file = Path(pdf_path)
        if not pdf_file.is_file():
            raise FileNotFoundError(f"File not found: {pdf_path}")

        uploaded_file = self.client.files.upload(
            file={"file_name": pdf_file.stem, "content": pdf_file.read_bytes()},
            purpose="ocr",
        )
        signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
        pdf_response = self.client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=True,
        )
        return pdf_response

def replace_images_in_markdown(markdown_str: str, images_dict: Dict[str, str]) -> str:
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})"
        )
    return markdown_str

def ocr_response_to_markdown(ocr_response) -> str:
    """
    Combina testo+immagini dell'OCR Mistral in un unico markdown lineare.
    """
    md_pages: List[str] = []
    for page in ocr_response.pages:
        images = {img.id: img.image_base64 for img in getattr(page, "images", []) or []}
        md = replace_images_in_markdown(page.markdown, images)
        md_pages.append(md)
    return "\n\n".join(md_pages)
