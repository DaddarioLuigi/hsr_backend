import pdfplumber
import re
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz


class PDFPositionExtractor:
    """
    Estrae le coordinate delle entità trovate nel PDF.
    Utilizza pdfplumber per trovare la posizione (x, y, width, height, page) di ogni entità.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._chars_cache = None
        self._pages_cache = []
    
    def _get_page_count(self) -> int:
        """Ottiene il numero totale di pagine nel PDF."""
        with pdfplumber.open(self.pdf_path) as pdf:
            return len(pdf.pages)

    def _normalize_text(self, text: str) -> str:
        """Normalizza il testo per il confronto (rimuove spazi extra, lowercase)."""
        if not text:
            return ""
        # Rimuovi spazi multipli e normalizza
        normalized = re.sub(r'\s+', ' ', str(text).strip())
        return normalized.lower()
    
    def _merge_hyphenation(self,words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Unisce parole sillabate a cavallo di riga (es. 'inter-' + 'azione')."""
        if not words:
            return words

        merged: List[Dict[str, Any]] = []
        i = 0
        while i < len(words):
            w = words[i]
            text = w["text"]
            if text.endswith("-") and i + 1 < len(words):
                nxt = words[i + 1]
                cy = (w.get("bottom", 0) + w.get("top", 0)) / 2
                ny = (nxt.get("bottom", 0) + nxt.get("top", 0)) / 2
                same_line = abs(cy - ny) < 6

                if same_line or nxt["text"].isalpha():
                    merged.append({
                        **w,
                        "text": text[:-1] + nxt["text"],
                        "x0": min(w["x0"], nxt["x0"]),
                        "x1": max(w["x1"], nxt["x1"]),
                        "top": min(w["top"], nxt["top"]),
                        "bottom": max(w["bottom"], nxt["bottom"]),
                    })
                    i += 2
                    continue

            merged.append(w)
            i += 1

        return merged
    
    def _bbox_from_words(self,words_subset: List[Dict[str, Any]]) -> Tuple[float, float, float, float]:
        x0 = min(w["x0"] for w in words_subset)
        y0 = min(w["top"] for w in words_subset)
        x1 = max(w["x1"] for w in words_subset)
        y1 = max(w["bottom"] for w in words_subset)
        return x0, y0, x1, y1


    def find_entity_position(
        self,
        entity_value: str,
        page_number: Optional[int] = None,
        *,
        min_score: float = 80.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Trova la posizione (bbox) di un'entità nel PDF usando un fuzzy matching semplificato.

        Logica:
        - normalizza entità e testo
        - caso 1 parola: cerca il token più simile
        - caso multi-parola: usa una finestra di lunghezza = n° parole entità
        - se entità è numerica/data → confronto più rigido (quasi esatto)
        """


        # ------------------ Normalizzazione entità ------------------ #

        if not entity_value or not str(entity_value).strip():
            return None

        raw_entity = str(entity_value).strip()
        entity_norm = self._normalize_text(raw_entity)
        if not entity_norm:
            return None

        entity_tokens = entity_norm.split()
        if not entity_tokens:
            return None

        # Riconosci “modalità numerica / data”
        numeric_like = bool(re.fullmatch(r"[0-9\s.,/\-]+", raw_entity))
        date_like = bool(re.search(r"\d{1,4}[./\-]\d{1,2}[./\-]\d{2,4}", raw_entity))
        numeric_mode = numeric_like or date_like

        # per numeri/date alza leggermente la soglia
        if numeric_mode:
            min_score = max(min_score, 85.0)

        # ------------------ Pagine da cercare ------------------ #

        pages_to_search = [page_number - 1] if page_number is not None else range(self._get_page_count())

        best: Optional[Dict[str, Any]] = None  # {"score": ..., "page": ..., "x0": ..., ...}

        # ------------------ Scansione PDF ------------------ #

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_idx in pages_to_search:
                if page_idx < 0 or page_idx >= len(pdf.pages):
                    continue

                page = pdf.pages[page_idx]
                words = page.extract_words() or []
                if not words:
                    continue

                words = self._merge_hyphenation(words)

                # costruiamo una lista di token normalizzati + riferimento alla word originale
                tokens: List[Dict[str, Any]] = []
                for w in words:
                    norm = self._normalize_text(w["text"])
                    if not norm:
                        continue
                    tokens.append({"norm": norm, "word": w})

                if not tokens:
                    continue

                # ------------------ Caso: entità di 1 parola ------------------ #
                if len(entity_tokens) == 1:
                    target = entity_tokens[0]
                    for tok in tokens:
                        t = tok["norm"]
                        if numeric_mode:
                            # per numeri/date preferisci uguaglianza, altrimenti ratio
                            if t == target:
                                score = 100.0
                            else:
                                score = float(fuzz.ratio(target, t))
                        else:
                            score = float(fuzz.ratio(target, t))

                        if score < min_score:
                            continue

                        if (best is None) or (score > best["score"]):
                            x0, y0, x1, y1 = self._bbox_from_words([tok["word"]])
                            best = {
                                "score": score,
                                "page": page_idx,
                                "x0": x0,
                                "y0": y0,
                                "x1": x1,
                                "y1": y1,
                            }

                # ------------------ Caso: entità multi-parola ------------------ #
                else:
                    win_len = min((len(entity_tokens)),5)
                    for i in range(0, len(tokens) - win_len + 1):
                        window_tokens = tokens[i:i + win_len]
                        cand_text = " ".join(t["norm"] for t in window_tokens)

                        if numeric_mode:
                            score = float(fuzz.ratio(entity_norm, cand_text))
                        else:
                            score = float(fuzz.token_set_ratio(entity_norm, cand_text))

                        if score < min_score:
                            continue

                        if (best is None) or (score > best["score"]):
                            words_subset = [t["word"] for t in window_tokens]
                            x0, y0, x1, y1 = self._bbox_from_words(words_subset)
                            best = {
                                "score": score,
                                "page": page_idx,
                                "x0": x0,
                                "y0": y0,
                                "x1": x1,
                                "y1": y1,
                            }

        # ------------------ Ritorno bbox migliore ------------------ #

        if not best:
            return None

        return {
            "page": best["page"] + 1,
            "x0": round(float(best["x0"]), 2),
            "y0": round(float(best["y0"]), 2),
            "x1": round(float(best["x1"]), 2),
            "y1": round(float(best["y1"]), 2),
            "width": round(float(best["x1"] - best["x0"]), 2),
            "height": round(float(best["y1"] - best["y0"]), 2),
        }



        
    def extract_entities_positions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae le posizioni per tutte le entità fornite.

        Args:
            entities: Dict con entità -> valore

        """
        result: Dict[str, Any] = {}

        for entity_name, entity_value in entities.items():
            if entity_value:
                position = self.find_entity_position(str(entity_value))
                result[entity_name] = {
                    "value": entity_value,
                    "positions": position 
                }
            else:
                result[entity_name] = {
                    "value": entity_value,
                    "positions": None
                }

        return result