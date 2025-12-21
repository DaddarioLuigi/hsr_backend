import json
import re
from typing import List, Dict, Any


class EntityExtractor:
    """
    Parser per la risposta JSON del LLM con fallback su regex.
    Garantisce che tutte le entità dello schema siano sempre presenti.
    """

    def __init__(self, explicit_entities: List[str]):
        self.explicit = explicit_entities

    def parse_llm_response(self, response_str: str, text: str) -> Dict[str, Any]:
        """
        Restituisce SEMPRE tutte le entità dello schema.
        Quelle non trovate hanno valore None.
        """
        # inizializza output completo
        result: Dict[str, Any] = {ent: None for ent in self.explicit}

        try:
            data = json.loads(response_str)

            # Caso: lista di {entità, valore}
            if isinstance(data, list):
                for item in data:
                    ent = item.get("entità")
                    val = item.get("valore")
                    if ent in result:
                        result[ent] = val
                return result

            # Caso: dict diretto
            if isinstance(data, dict):
                for ent in self.explicit:
                    if ent in data:
                        result[ent] = data.get(ent)
                return result

        except json.JSONDecodeError:
            pass

        # Fallback regex
        explicit_found = self.extract_explicit(text)
        for ent, matches in explicit_found.items():
            # se più match, li manteniamo come lista
            result[ent] = matches if len(matches) > 1 else matches[0]

        return result

    def extract_explicit(self, text: str) -> Dict[str, List[str]]:
        """
        Estrae entità esplicite dal testo tramite keyword matching.
        """
        results: Dict[str, List[str]] = {}

        for ent in self.explicit:
            pattern = re.compile(
                rf"\b{re.escape(ent)}\b",
                re.IGNORECASE
            )
            matches = pattern.findall(text)
            if matches:
                results[ent] = matches

        return results
