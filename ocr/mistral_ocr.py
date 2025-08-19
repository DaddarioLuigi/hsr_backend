# ocr/mistral_ocr.py
from pathlib import Path
from typing import Dict, List, Any
import os
import re

# Import lazy: non fallire a import-time se manca il pacchetto
_MISTRAL_IMPORT_ERROR = None
try:
    from mistralai import Mistral
    # alcuni SDK espongono DocumentURLChunk in moduli diversi; evitiamo hard import
    try:
        from mistralai.models import DocumentURLChunk  # ok su alcune versioni
    except Exception:
        DocumentURLChunk = None  # lo gestiamo sotto
except Exception as e:
    Mistral = None
    DocumentURLChunk = None
    _MISTRAL_IMPORT_ERROR = e


class MistralOCR:
    def __init__(self, api_key: str | None = None):
        if Mistral is None:
            raise ImportError(
                "La libreria 'mistralai' non è installata oppure non è importabile. "
                f"Dettagli: {_MISTRAL_IMPORT_ERROR}"
            )
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY non configurata")
        self.client = Mistral(api_key=self.api_key)

    def _make_doc_chunk(self, url: str) -> Any:
        """Crea il payload document per l'API OCR senza assumere il path esatto della classe."""
        if DocumentURLChunk is not None:
            return DocumentURLChunk(document_url=url)
        # fallback: molte versioni accettano un dict serializzabile
        return {"document_url": url}

    def process_pdf(self, pdf_path: str) -> Any:
        pdf_file = Path(pdf_path)
        if not pdf_file.is_file():
            raise FileNotFoundError(f"File not found: {pdf_path}")

        uploaded_file = self.client.files.upload(
            file={"file_name": pdf_file.stem, "content": pdf_file.read_bytes()},
            purpose="ocr",
        )
        signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
        doc = self._make_doc_chunk(signed_url.url)

        pdf_response = self.client.ocr.process(
            document=doc,
            model="mistral-ocr-latest",
            include_image_base64=False,
        )
        return pdf_response

_IMG_MD_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')  # ![alt](...)
_DATAURI_RE = re.compile(r'data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+')


def replace_images_in_markdown(markdown_str: str, images_dict: Dict[str, str]) -> str:
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})"
        )
    return markdown_str


def _strip_markdown_images(md: str) -> str:
    md = _IMG_MD_RE.sub('', md)
    md = _DATAURI_RE.sub('', md)
    return md

def ocr_response_to_markdown(ocr_response) -> str:
    pages = getattr(ocr_response, "pages", []) or []
    md_pages = []
    for page in pages:
        # usa text puro se disponibile, altrimenti markdown ripulito
        txt = getattr(page, "text", None)
        if txt:
            md_pages.append(txt)
        else:
            page_md = getattr(page, "markdown", "") or ""
            md_pages.append(_strip_markdown_images(page_md))
    return "\n\n".join(md_pages)


def ocr_response_to_markdown(ocr_response: Any) -> str:
    """
    Combina testo+immagini in un unico markdown lineare.
    """
    md_pages: List[str] = []
    # siamo tolleranti al formato di risposta tra versioni
    pages = getattr(ocr_response, "pages", None) or []
    for page in pages:
        images = {img.id: img.image_base64 for img in getattr(page, "images", []) or []}
        page_md = getattr(page, "markdown", "") or ""
        md = replace_images_in_markdown(page_md, images) if images else page_md
        md_pages.append(md)
    return "\n\n".join(md_pages)
