import json
import re
from typing import List, Dict, Any

class EntityExtractor:
    """
    Parser per la risposta JSON del LLM con fallback su regex per estrazioni esplicite.
    """
    def __init__(self, explicit_entities: List[str]):
        # Lista delle entità esplicite definite nello schema
        self.explicit = explicit_entities

    def parse_llm_response(self, response_str: str, text: str) -> Dict[str, Any]:
        """
        Prova a convertire la risposta del LLM in JSON.
        Se riceve una lista di oggetti con chiavi 'entità' e 'valore', restituisce un dict entità->valore.
        In caso di JSON malformato, esegue fallback di estrazione esplicita via regex.
        """
        try:
            data = json.loads(response_str)
            # Se è lista di dict, converto in mappa
            if isinstance(data, list):
                return {item['entità']: item['valore'] for item in data}
            # Se è già dict, restituisco così com'è
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        # Fallback rudimentale: estrai solo esplicite dal testo
        return self.extract_explicit(text)

    def extract_explicit(self, text: str) -> Dict[str, List[str]]:
        """
        Estrae entità esplicite dal testo tramite ricerca keyword-based.
        Ritorna dict entità->lista di occorrenze trovate.
        """
        results: Dict[str, List[str]] = {}
        for ent in self.explicit:
            # regex per match case-insensitive di parola intera
            pattern = re.compile(rf"\b{re.escape(ent)}\b", re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                results[ent] = matches
        return results
