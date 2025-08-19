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
        Estrae le entità dalla sezione passata.

        Args:
            section_text: testo (markdown o plain text) della sezione da analizzare
            doc_type: tipologia documento (es. 'lettera_dimissione', 'intervento', ...)

        Returns:
            Dict[str, Any]: mappa entità -> valore
        """
        canonical_type = normalize_doc_type(doc_type)

        # 1) Specifica (elenco entità attese dallo schema)
        spec = self.prompts.get_spec_for(canonical_type)  # -> {"entities": [...]}
        explicit_keys = spec["entities"]

        # 2) Chiamata LLM con controlli schema/json (è dentro LLMExtractor)
        response_str = self.llm.get_response_from_document(
            section_text, canonical_type, model=self.model_name
        )

        # 3) Parsing robusto dell'output
        extractor = EntityExtractor(explicit_keys)
        entities = extractor.parse_llm_response(response_str, section_text)

        return entities
