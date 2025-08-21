# utils/adaptive_segmenter.py
# -*- coding: utf-8 -*-
"""
Segmentatore adattivo per cartelle cliniche cardiologiche.
Permette di scegliere tra diversi approcci di segmentazione in base alle esigenze.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Importa i diversi segmenter
from utils.document_segmenter import find_document_sections, Section
from utils.advanced_segmenter import AdvancedSegmenter, AdvancedSection
from utils.llm_segmenter import LLMSegmenter, LLMSection

class SegmentationStrategy(Enum):
    """Strategie di segmentazione disponibili."""
    REGEX_ONLY = "regex_only"           # Solo regex (veloce, meno accurato)
    HYBRID = "hybrid"                   # Regex + LLM enhancement (bilanciato)
    LLM_FIRST = "llm_first"             # LLM primario (lento, più accurato)
    ADAPTIVE = "adaptive"               # Sceglie automaticamente in base al testo

@dataclass
class AdaptiveSection:
    doc_type: str
    start: int
    end: int
    text: str
    confidence: float
    metadata: Dict[str, Any] = None
    temporal_context: Optional[str] = None
    strategy_used: Optional[str] = None

class AdaptiveSegmenter:
    """
    Segmentatore adattivo che sceglie la strategia migliore in base al contesto.
    """
    
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3", strategy: SegmentationStrategy = SegmentationStrategy.ADAPTIVE):
        self.model_name = model_name
        self.strategy = strategy
        
        # Inizializza i diversi segmenter
        self.regex_segmenter = None  # Usa direttamente find_document_sections
        self.advanced_segmenter = AdvancedSegmenter(model_name)
        self.llm_segmenter = LLMSegmenter(model_name)
        
        # Parametri di configurazione
        self.confidence_thresholds = {
            "low": 0.5,      # Accetta quasi tutto
            "medium": 0.7,   # Bilanciato
            "high": 0.8      # Solo sezioni molto sicure
        }
        
        self.allow_multiple_sections = True  # Permette sezioni multiple dello stesso tipo
    
    def segment_document(self, text: str, confidence_level: str = "medium") -> List[AdaptiveSection]:
        """
        Segmentazione adattiva del documento.
        
        Args:
            text: Testo da segmentare
            confidence_level: "low", "medium", "high"
            
        Returns:
            Lista di sezioni adattive
        """
        logging.info(f"=== AVVIO SEGMENTAZIONE ADATTIVA ===")
        logging.info(f"Strategia: {self.strategy.value}")
        logging.info(f"Livello confidenza: {confidence_level}")
        
        # Scegli strategia se adattiva
        if self.strategy == SegmentationStrategy.ADAPTIVE:
            actual_strategy = self._choose_strategy(text)
            logging.info(f"Strategia scelta automaticamente: {actual_strategy.value}")
        else:
            actual_strategy = self.strategy
        
        # Esegui segmentazione con la strategia scelta
        if actual_strategy == SegmentationStrategy.REGEX_ONLY:
            sections = self._segment_regex_only(text)
        elif actual_strategy == SegmentationStrategy.HYBRID:
            sections = self._segment_hybrid(text)
        elif actual_strategy == SegmentationStrategy.LLM_FIRST:
            sections = self._segment_llm_first(text)
        else:
            raise ValueError(f"Strategia non supportata: {actual_strategy}")
        
        # Applica filtro di confidenza
        threshold = self.confidence_thresholds[confidence_level]
        filtered_sections = [s for s in sections if s.confidence >= threshold]
        
        logging.info(f"Sezioni trovate: {len(sections)}")
        logging.info(f"Sezioni dopo filtro confidenza: {len(filtered_sections)}")
        
        return filtered_sections
    
    def _choose_strategy(self, text: str) -> SegmentationStrategy:
        """
        Sceglie automaticamente la strategia migliore in base al testo.
        """
        # Analizza caratteristiche del testo
        text_length = len(text)
        has_complex_formatting = self._has_complex_formatting(text)
        has_ocr_artifacts = self._has_ocr_artifacts(text)
        has_ambiguous_sections = self._has_ambiguous_sections(text)
        
        logging.info(f"Caratteristiche testo:")
        logging.info(f"  - Lunghezza: {text_length}")
        logging.info(f"  - Formattazione complessa: {has_complex_formatting}")
        logging.info(f"  - Artefatti OCR: {has_ocr_artifacts}")
        logging.info(f"  - Sezioni ambigue: {has_ambiguous_sections}")
        
        # Logica di scelta
        if text_length < 5000 and not has_ocr_artifacts:
            # Testo corto e pulito -> regex veloce
            return SegmentationStrategy.REGEX_ONLY
        elif has_ocr_artifacts or has_ambiguous_sections:
            # Problemi OCR o ambiguità -> LLM
            return SegmentationStrategy.LLM_FIRST
        else:
            # Caso generale -> ibrido
            return SegmentationStrategy.HYBRID
    
    def _has_complex_formatting(self, text: str) -> bool:
        """
        Verifica se il testo ha formattazione complessa.
        """
        # Conta caratteri speciali, tabelle, ecc.
        special_chars = sum(1 for c in text if c in "|+-=*#@")
        lines = text.split('\n')
        avg_line_length = sum(len(line) for line in lines) / max(1, len(lines))
        
        return special_chars > 50 or avg_line_length > 100
    
    def _has_ocr_artifacts(self, text: str) -> bool:
        """
        Verifica se il testo ha artefatti OCR.
        """
        # Cerca pattern tipici di errori OCR
        ocr_indicators = [
            r'\b[a-z]{1,2}\d+\b',  # Caratteri isolati + numeri
            r'\b\d+[a-z]{1,2}\b',  # Numeri + caratteri isolati
            r'[|]{2,}',            # Barre multiple
            r'[=]{3,}',            # Uguali multiple
        ]
        
        import re
        for pattern in ocr_indicators:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _has_ambiguous_sections(self, text: str) -> bool:
        """
        Verifica se il testo ha sezioni ambigue.
        """
        # Cerca pattern che potrebbero indicare ambiguità
        ambiguous_patterns = [
            r'eco.*cardiografia',  # Eco generico
            r'ecocardiogramma',    # Eco generico
            r'verbale.*operatorio', # Potrebbe essere intervento
            r'referto.*operatorio', # Potrebbe essere intervento
        ]
        
        import re
        for pattern in ambiguous_patterns:
            if len(re.findall(pattern, text, re.IGNORECASE)) > 1:
                return True
        
        return False
    
    def _segment_regex_only(self, text: str) -> List[AdaptiveSection]:
        """
        Segmentazione usando solo regex (veloce).
        """
        logging.info("Esecuzione segmentazione regex-only")
        
        sections = find_document_sections(text)
        adaptive_sections = []
        
        for section in sections:
            if section.doc_type != "altro" and section.text.strip():
                adaptive_sections.append(AdaptiveSection(
                    doc_type=section.doc_type,
                    start=section.start,
                    end=section.end,
                    text=section.text,
                    confidence=0.8,  # Confidenza media per regex
                    strategy_used="regex_only"
                ))
        
        return adaptive_sections
    
    def _segment_hybrid(self, text: str) -> List[AdaptiveSection]:
        """
        Segmentazione ibrida (regex + LLM enhancement).
        """
        logging.info("Esecuzione segmentazione ibrida")
        
        advanced_sections = self.advanced_segmenter.segment_document(text)
        adaptive_sections = []
        
        for section in advanced_sections:
            adaptive_sections.append(AdaptiveSection(
                doc_type=section.doc_type,
                start=section.start,
                end=section.end,
                text=section.text,
                confidence=section.confidence,
                temporal_context=section.temporal_context,
                metadata=section.metadata,
                strategy_used="hybrid"
            ))
        
        return adaptive_sections
    
    def _segment_llm_first(self, text: str) -> List[AdaptiveSection]:
        """
        Segmentazione LLM-first (massima flessibilità).
        """
        logging.info("Esecuzione segmentazione LLM-first")
        
        llm_sections = self.llm_segmenter.segment_document(text)
        adaptive_sections = []
        
        for section in llm_sections:
            adaptive_sections.append(AdaptiveSection(
                doc_type=section.doc_type,
                start=section.start,
                end=section.end,
                text=section.text,
                confidence=section.confidence,
                temporal_context=section.temporal_context,
                metadata=section.metadata,
                strategy_used="llm_first"
            ))
        
        return adaptive_sections
    
    def set_confidence_threshold(self, level: str, threshold: float):
        """
        Imposta una soglia di confidenza personalizzata.
        """
        if level in self.confidence_thresholds:
            self.confidence_thresholds[level] = threshold
        else:
            raise ValueError(f"Livello non valido: {level}")
    
    def set_allow_multiple_sections(self, allow: bool):
        """
        Imposta se permettere sezioni multiple dello stesso tipo.
        """
        self.allow_multiple_sections = allow
    
    def get_segmentation_stats(self, sections: List[AdaptiveSection]) -> Dict[str, Any]:
        """
        Restituisce statistiche sulla segmentazione.
        """
        if not sections:
            return {"total": 0, "by_type": {}, "by_strategy": {}, "avg_confidence": 0}
        
        stats = {
            "total": len(sections),
            "by_type": {},
            "by_strategy": {},
            "avg_confidence": sum(s.confidence for s in sections) / len(sections)
        }
        
        # Statistiche per tipo
        for section in sections:
            doc_type = section.doc_type
            strategy = section.strategy_used or "unknown"
            
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
            stats["by_strategy"][strategy] = stats["by_strategy"].get(strategy, 0) + 1
        
        return stats 