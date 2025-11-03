import pdfplumber
import re
from typing import Dict, Any, List, Optional, Tuple


class PDFPositionExtractor:
    """
    Estrae le coordinate delle entità trovate nel PDF.
    Utilizza pdfplumber per trovare la posizione (x, y, width, height, page) di ogni entità.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._chars_cache = None
        self._pages_cache = []
    
    def _get_chars_by_page(self, page_num: int) -> List[Dict]:
        """Ottiene tutti i caratteri di una pagina con le loro coordinate."""
        if not self._pages_cache:
            with pdfplumber.open(self.pdf_path) as pdf:
                for p in pdf.pages:
                    chars = p.chars
                    self._pages_cache.append(chars)
        
        if page_num < len(self._pages_cache):
            return self._pages_cache[page_num]
        return []
    
    def _normalize_text(self, text: str) -> str:
        """Normalizza il testo per il confronto (rimuove spazi extra, lowercase)."""
        if not text:
            return ""
        # Rimuovi spazi multipli e normalizza
        normalized = re.sub(r'\s+', ' ', str(text).strip())
        return normalized.lower()
    
    def find_entity_position(
        self, 
        entity_value: str, 
        page_number: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Trova la posizione di un'entità nel PDF.
        
        Args:
            entity_value: Il valore dell'entità da cercare
            page_number: Numero pagina specifico (opzionale, cerca in tutte le pagine se None)
        
        Returns:
            Dict con le coordinate o None se non trovato:
            {
                "page": int,
                "x0": float,  # coordinate top-left
                "y0": float,
                "x1": float,  # coordinate bottom-right
                "y1": float,
                "width": float,
                "height": float
            }
        """
        if not entity_value or not str(entity_value).strip():
            return None
        
        entity_str = str(entity_value).strip()
        entity_normalized = self._normalize_text(entity_str)
        
        if not entity_normalized:
            return None
        
        pages_to_search = [page_number - 1] if page_number is not None else range(self._get_page_count())
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_idx in pages_to_search:
                if page_idx < 0 or page_idx >= len(pdf.pages):
                    continue
                    
                page = pdf.pages[page_idx]
                page_text_normalized = self._normalize_text(page.extract_text() or "")
                
                # Cerca il testo normalizzato nella pagina
                if entity_normalized not in page_text_normalized and len(entity_normalized) > 3:
                    # Prova a cercare solo le prime parole se l'entità è molto lunga
                    first_words = ' '.join(entity_normalized.split()[:3])
                    if first_words not in page_text_normalized:
                        continue
                
                # Estrai parole dalla pagina
                words = page.extract_words()
                if not words:
                    continue
                
                entity_words = entity_normalized.split()
                
                # Strategia 1: Cerca sequenza esatta di parole consecutive
                best_match = None
                best_match_length = 0
                
                for i in range(len(words)):
                    matched_words = []
                    entity_word_idx = 0
                    
                    for j in range(i, len(words)):
                        if entity_word_idx >= len(entity_words):
                            break
                        
                        word_text = self._normalize_text(words[j]['text'])
                        entity_word = entity_words[entity_word_idx]
                        
                        # Match esatto o parziale
                        if (entity_word in word_text or 
                            word_text in entity_word or
                            (len(entity_word) > 3 and len(word_text) > 3 and 
                             (entity_word[:4] in word_text or word_text[:4] in entity_word))):
                            matched_words.append(words[j])
                            entity_word_idx += 1
                        elif matched_words:
                            # Se avevamo già un match ma questo non corrisponde, fermati
                            break
                    
                    # Se abbiamo trovato almeno 2 parole o almeno il 50% delle parole
                    if matched_words and (len(matched_words) >= min(2, len(entity_words)) or 
                                         len(matched_words) >= len(entity_words) * 0.5):
                        if len(matched_words) > best_match_length:
                            best_match = matched_words
                            best_match_length = len(matched_words)
                
                if best_match:
                    # Calcola bounding box
                    x0 = min(w['x0'] for w in best_match)
                    y0 = min(w['top'] for w in best_match)
                    x1 = max(w['x1'] for w in best_match)
                    y1 = max(w['bottom'] for w in best_match)
                    
                    return {
                        "page": page_idx + 1,  # 1-indexed per l'utente
                        "x0": round(x0, 2),
                        "y0": round(y0, 2),
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "width": round(x1 - x0, 2),
                        "height": round(y1 - y0, 2)
                    }
        
        return None
    
    def _get_page_count(self) -> int:
        """Ottiene il numero totale di pagine nel PDF."""
        with pdfplumber.open(self.pdf_path) as pdf:
            return len(pdf.pages)
    
    def extract_entities_positions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae le posizioni per tutte le entità fornite.
        
        Args:
            entities: Dict con entità -> valore
        
        Returns:
            Dict con le stesse chiavi ma valori che includono anche le coordinate:
            {
                "entity_name": {
                    "value": "valore entità",
                    "position": { ... }  # coordinate o None
                }
            }
        """
        result = {}
        
        for entity_name, entity_value in entities.items():
            if entity_value:
                position = self.find_entity_position(str(entity_value))
                result[entity_name] = {
                    "value": entity_value,
                    "position": position
                }
            else:
                result[entity_name] = {
                    "value": entity_value,
                    "position": None
                }
        
        return result

