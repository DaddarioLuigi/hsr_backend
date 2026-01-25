"""
Document Type Detector Service
Determina il tipo di documento basandosi sul testo o sul nome del file.
"""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

DocumentType = Literal[
    "lettera_dimissione",
    "coronarografia",
    "intervento",
    "eco_preoperatorio",
    "eco_postoperatorio",
    "tc_cuore",
    "anamnesi",
    "epicrisi_ti",
    "cartellino_anestesiologico",
    "altro"
]


class DocumentTypeDetector:
    """
    Servizio per determinare il tipo di documento dal nome del file.
    """
    
    @staticmethod
    def detect(filename: str, text: str = None) -> DocumentType:
        detected_type, _, _ = DocumentTypeDetector.detect_with_confidence(filename, text)
        return detected_type

    @staticmethod
    def detect_with_confidence(filename: str, text: str = None) -> tuple[DocumentType, float, list[str]]:
        """
        Determina il tipo di documento basandosi sul testo o sul nome del file.
        Prima controlla il testo per le keyword, poi usa il nome del file come fallback.
        
        Args:
            filename: Nome del file (case-insensitive, usato come fallback)
            text: Testo del documento in cui cercare le keyword
            
        Returns:
            Tipo di documento identificato o "altro" se non riconosciuto
        """
        text_lower = (text or "").lower()
        name = (filename or "").lower()

        scores: dict[DocumentType, int] = {
            "lettera_dimissione": 0,
            "coronarografia": 0,
            "intervento": 0,
            "eco_preoperatorio": 0,
            "eco_postoperatorio": 0,
            "tc_cuore": 0,
            "anamnesi": 0,
            "epicrisi_ti": 0,
            "cartellino_anestesiologico": 0,
            "altro": 0,
        }
        reasons: dict[DocumentType, list[str]] = {k: [] for k in scores.keys()}

        def bump(doc_type: DocumentType, points: int, reason: str) -> None:
            scores[doc_type] += points
            reasons[doc_type].append(reason)

        # Text signals
        if "relazione clinica alla dimissione" in text_lower or "lettera di dimissione" in text_lower:
            bump("lettera_dimissione", 6, "testo: dimissione")

        if "coronarografia" in text_lower or "angiografia coronarica" in text_lower:
            bump("coronarografia", 4, "testo: coronarografia")

        if "verbale operatorio" in text_lower or "intervento chirurgico" in text_lower:
            bump("intervento", 5, "testo: intervento/verbale")

        if "ecocardiogramma" in text_lower or "ecocardiografia" in text_lower:
            if "pre op" in text_lower or "pre-operator" in text_lower or "pre operator" in text_lower:
                bump("eco_preoperatorio", 5, "testo: eco pre")
            if "post op" in text_lower or "post-operator" in text_lower or "post operator" in text_lower:
                bump("eco_postoperatorio", 5, "testo: eco post")

        if "anamnesi" in text_lower or "cenni anamnestici" in text_lower:
            bump("anamnesi", 4, "testo: anamnesi")

        if "epicrisi" in text_lower and ("terapia intensiva" in text_lower or "rianimazione" in text_lower):
            bump("epicrisi_ti", 5, "testo: epicrisi TI")

        if (
            "scheda anestesiologica" in text_lower
            or "cartellino anestesiologico" in text_lower
            or ("anestesi" in text_lower and "intervento" in text_lower)
        ):
            bump("cartellino_anestesiologico", 5, "testo: anestesia")

        if "tomografia computerizzata" in text_lower or "tac" in text_lower or "tc" in text_lower:
            if "cuore" in text_lower or "cardiac" in text_lower:
                bump("tc_cuore", 4, "testo: TC/TAC cuore")

        # Filename signals
        if "dimiss" in name:
            bump("lettera_dimissione", 3, "filename: dimissione")
        if "coronaro" in name or "coro" in name:
            bump("coronarografia", 2, "filename: coronaro")
        if "verb" in name or "intervento" in name or "operator" in name:
            bump("intervento", 2, "filename: intervento")
        if "eco" in name and "pre" in name:
            bump("eco_preoperatorio", 2, "filename: eco pre")
        if "eco" in name and "post" in name:
            bump("eco_postoperatorio", 2, "filename: eco post")
        if "anamnesi" in name:
            bump("anamnesi", 2, "filename: anamnesi")
        if "epicrisi" in name or "ti" in name or "rianim" in name:
            bump("epicrisi_ti", 1, "filename: epicrisi/ti")
        if "anes" in name or "anest" in name:
            bump("cartellino_anestesiologico", 2, "filename: anes")
        if "tc" in name or "tac" in name:
            bump("tc_cuore", 1, "filename: tc/tac")

        best_type = max(scores.keys(), key=lambda t: scores[t])
        best_score = scores[best_type]

        if best_score < 3:
            return "altro", 0.0, ["confidence bassa"]

        confidence = min(1.0, best_score / 8.0)
        return best_type, confidence, reasons[best_type]

