# pipelines/router.py
# -*- coding: utf-8 -*-
"""
Router di estrazione per singola sezione:
- Normalizza alias di tipo documento (es. 'verbale_operatorio' -> 'intervento')
- Recupera lo schema e la lista di entità dal PromptManager
- Interroga il modello via LLMExtractor
- Converte l'output in dict entità->valore con EntityExtractor

Dipendenze (già presenti nel progetto):
- LLMExtractor (usa Together API e i tuoi prompt/schemi) :contentReference[oaicite:0]{index=0}
- PromptManager (SCHEMAS/PROMPTS + get_spec_for) :contentReference[oaicite:1]{index=1}
- EntityExtractor (parser robusto + fallback) :contentReference[oaicite:2]{index=2}
"""

from __future__ import annotations
from typing import Dict, Any

from llm.extractor import LLMExtractor        # :contentReference[oaicite:3]{index=3}
from llm.prompts import PromptManager         # :contentReference[oaicite:4]{index=4}
from utils.entity_extractor import EntityExtractor  # :contentReference[oaicite:5]{index=5}


# Alias noti -> tipo canonico
ALIAS_TO_CANONICAL: Dict[str, str] = {
    "verbale_operatorio": "intervento",
    "referto_operatorio": "intervento",
}

def normalize_doc_type(doc_type: str) -> str:
    """Ritorna il tipo canonico dato un eventuale alias."""
    return ALIAS_TO_CANONICAL.get(doc_type, doc_type)


class SectionExtractor:
    """
    Esegue l'estrazione entità su un testo di sezione, in base al tipo documento.

    Esempio d'uso:
        extractor = SectionExtractor(model_name="deepseek-ai/DeepSeek-V3")
        entities = extractor.extract(section_text, "lettera_dimissione")
    """

    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3"):
        self.model_name = model_name
        self.llm = LLMExtractor()
        self.prompts = PromptManager()

    def extract(self, section_text: str, doc_type: str) -> Dict[str, Any]:
        """
        Estrae le entità dalla sezione. Se il testo è lungo, lo processa a chunk
        e unisce i risultati riempiendo solo i campi vuoti.
        """
        canonical_type = normalize_doc_type(doc_type)
        spec = self.prompts.get_spec_for(canonical_type)
        explicit_keys = spec["entities"]

        # --- CHUNKING DIFENSIVO ---
        MAX_CHARS = 40000  # ~10k token circa; margine ampio
        chunks: list[str] = []
        if len(section_text) <= MAX_CHARS:
            chunks = [section_text]
        else:
            # split per paragrafi e ri-impacchetta
            parts = section_text.split("\n\n")
            buf = []
            size = 0
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if size + len(p) + 2 > MAX_CHARS and buf:
                    chunks.append("\n\n".join(buf))
                    buf = [p]
                    size = len(p)
                else:
                    buf.append(p)
                    size += len(p) + 2
            if buf:
                chunks.append("\n\n".join(buf))

        # --- ESECUZIONE E MERGE ---
        extractor = EntityExtractor(explicit_keys)
        merged: Dict[str, Any] = {}
        for ch in chunks:
            try:
                response_str = self.llm.get_response_from_document(
                    ch, canonical_type, model=self.model_name
                )
                ents = extractor.parse_llm_response(response_str, ch)
                # riempi solo i vuoti
                for k, v in (ents or {}).items():
                    if (k not in merged) or (merged[k] in (None, "", [], {})):
                        merged[k] = v
            except Exception as e:
                # continua con i chunk successivi
                continue

        return merged

