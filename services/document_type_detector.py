"""
Document Type Detector Service
Determina il tipo di documento basandosi sul nome del file.
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
    def detect(filename: str) -> DocumentType:
        """
        Determina il tipo di documento dal nome del file.
        
        Args:
            filename: Nome del file (case-insensitive)
            
        Returns:
            Tipo di documento identificato o "altro" se non riconosciuto
        """
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

