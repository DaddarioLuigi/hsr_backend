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
    "altro"
]


class DocumentTypeDetector:
    """
    Servizio per determinare il tipo di documento dal nome del file.
    """
    
    @staticmethod
    def detect(filename: str, text: str = None) -> DocumentType:
        """
        Determina il tipo di documento basandosi sul testo o sul nome del file.
        Prima controlla il testo per le keyword, poi usa il nome del file come fallback.
        
        Args:
            filename: Nome del file (case-insensitive, usato come fallback)
            text: Testo del documento in cui cercare le keyword
            
        Returns:
            Tipo di documento identificato o "altro" se non riconosciuto
        """
        # Se il testo è fornito, cerca le keyword nel testo
        if text:
            text_lower = text.lower()
            
            # Controlla le keyword nel testo
            if "relazione clinica alla dimissione" in text_lower:
                return "lettera_dimissione"

            if (
                "coronarografia" in text_lower
                and "intervento chirurgico" not in text_lower
                and "verbale operatorio" not in text_lower
            ):
                return "coronarografia"

            if "intervento chirurgico" in text_lower or "verbale operatorio" in text_lower:
                return "intervento"

            if "ecocardiogramma" in text_lower and "pre op" in text_lower:
                return "eco_preoperatorio"

            if "ecocardiogramma" in text_lower and "post op" in text_lower:
                return "eco_postoperatorio"

            if "tc" in text_lower or "tac" in text_lower:
                return "tc_cuore"
        
        # Se non c'è testo o non si trova nulla nel testo, usa il nome del file come fallback
        name = filename.lower()
        
        if "dimissione" in name:
            return "lettera_dimissione"
        if "coronaro" in name:
            return "coronarografia"
        if "intervento" in name or "verbale" in name:
            return "intervento"
        if "eco" in name and "pre" in name:
            return "eco_preoperatorio"
        if "eco" in name and "post" in name:
            return "eco_postoperatorio"
        if "tc" in name or "tac" in name:
            return "tc_cuore"
        
        return "altro"

