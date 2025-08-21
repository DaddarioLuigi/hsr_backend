# utils/llm_segmenter.py
# -*- coding: utf-8 -*-
"""
Segmentatore basato su LLM per cartelle cliniche cardiologiche.
Approccio completamente LLM-driven per massima flessibilità e adattabilità.
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from llm.extractor import LLMExtractor

@dataclass
class LLMSection:
    doc_type: str
    start: int
    end: int
    text: str
    confidence: float
    metadata: Dict[str, Any] = None
    temporal_context: Optional[str] = None
    reasoning: Optional[str] = None

class LLMSegmenter:
    """
    Segmentatore completamente basato su LLM per documenti clinici cardiologici.
    Massima flessibilità e adattabilità a variazioni formattazione.
    """
    
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3"):
        self.model_name = model_name
        self.llm = LLMExtractor()
        
        # Definizione dei tipi di documento supportati
        self.document_types = {
            "lettera_dimissione": {
                "description": "Relazione dell'intero ricovero con storia paziente e decorso post-operatorio",
                "keywords": ["dimissione", "ricovero", "storia", "decorso", "relazione clinica"],
                "priority": 1
            },
            "anamnesi": {
                "description": "Storia del paziente, terapia al momento dell'ingresso",
                "keywords": ["storia", "terapia", "ingresso", "anamnestici", "anamnesi"],
                "priority": 2
            },
            "epicrisi_ti": {
                "description": "Relazione sulla degenza in terapia intensiva post-intervento",
                "keywords": ["terapia intensiva", "TICCH", "degenza", "post-operatorio", "epicrisi"],
                "priority": 3
            },
            "cartellino_anestesiologico": {
                "description": "Dati fissi con orari: CEC, clampaggio, tempi sala",
                "keywords": ["anestesiologica", "intraoperatoria", "CEC", "clampaggio", "scheda"],
                "priority": 4
            },
            "intervento": {
                "description": "Relazione dell'intervento con tipo e decorso",
                "keywords": ["operatorio", "intervento", "chirurgico", "primo operatore", "verbale"],
                "priority": 5
            },
            "coronarografia": {
                "description": "Stato delle coronarie con pattern fissi",
                "keywords": ["emodinamica", "coronarie", "tronco comune", "arteria circonflessa", "cateterismo"],
                "priority": 6
            },
            "eco_preoperatorio": {
                "description": "Ecocardiogramma eseguito PRIMA dell'intervento",
                "keywords": ["ecocardiografia", "ecocardiogramma", "FE", "valvulopatie", "preoperatorio"],
                "priority": 7
            },
            "eco_postoperatorio": {
                "description": "Ecocardiogramma eseguito DOPO l'intervento",
                "keywords": ["ecocardiografia", "ecocardiogramma", "FE", "bypass", "postoperatorio"],
                "priority": 8
            },
            "tc_cuore": {
                "description": "TC cuore/coronarie con variabili codificate",
                "keywords": ["TC", "TAC", "coronarie", "angio-TC", "tomografia"],
                "priority": 9
            }
        }
    
    def segment_document(self, text: str) -> List[LLMSection]:
        """
        Segmentazione completa basata su LLM.
        """
        logging.info("=== AVVIO SEGMENTAZIONE LLM ===")
        
        # Fase 1: Estrazione date per contesto temporale
        dates = self._extract_dates(text)
        intervention_date = self._find_intervention_date(text, dates)
        
        logging.info(f"Date trovate: {len(dates)}")
        logging.info(f"Data intervento: {intervention_date}")
        
        # Fase 2: Segmentazione LLM primaria
        llm_sections = self._llm_primary_segmentation(text)
        logging.info(f"Sezioni LLM trovate: {len(llm_sections)}")
        
        # Fase 3: Analisi temporale per eco pre/post
        temporal_sections = self._apply_temporal_analysis(llm_sections, intervention_date)
        logging.info(f"Sezioni dopo analisi temporale: {len(temporal_sections)}")
        
        # Fase 4: Validazione e raffinamento
        final_sections = self._validate_and_refine(text, temporal_sections)
        logging.info(f"Sezioni finali: {len(final_sections)}")
        
        return final_sections
    
    def _extract_dates(self, text: str) -> List[datetime]:
        """
        Estrae tutte le date dal testo per analisi temporale.
        """
        date_patterns = [
            r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b',  # DD/MM/YYYY
            r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b',        # DD.MM.YYYY
            r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b',    # YYYY/MM/DD
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups[2]) == 2:  # Anno a 2 cifre
                        year = int(groups[2])
                        if year < 50:  # Assumiamo 20xx per anni < 50
                            year += 2000
                        else:
                            year += 1900
                    else:
                        year = int(groups[2])
                    
                    month = int(groups[1])
                    day = int(groups[0])
                    
                    date = datetime(year, month, day)
                    dates.append(date)
                except (ValueError, IndexError):
                    continue
        
        return sorted(dates)
    
    def _find_intervention_date(self, text: str, dates: List[datetime]) -> Optional[datetime]:
        """
        Trova la data dell'intervento analizzando il contesto.
        """
        # Cerca pattern specifici per data intervento
        intervention_patterns = [
            r'data\s+intervento[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
            r'intervento\s+del[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
            r'verbale\s+operatorio[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
        ]
        
        for pattern in intervention_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    year = int(groups[2])
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                    month = int(groups[1])
                    day = int(groups[0])
                    return datetime(year, month, day)
                except (ValueError, IndexError):
                    continue
        
        # Se non troviamo pattern specifici, prendiamo la data più probabile
        if dates:
            return dates[len(dates)//2]
        
        return None
    
    def _llm_primary_segmentation(self, text: str) -> List[LLMSection]:
        """
        Segmentazione primaria completamente basata su LLM.
        """
        prompt = f"""
        Analizza questo testo di cartella clinica cardiologica e identifica tutte le sezioni presenti.
        
        Tipi di documento da identificare:
        {self._format_document_types()}
        
        Testo da analizzare:
        {text[:8000]}  # Limita per token
        
        Istruzioni:
        1. Identifica TUTTE le sezioni presenti nel testo
        2. Ogni sezione deve avere un tipo di documento specifico
        3. Se trovi più ecocardiogrammi, classificali come "eco_preoperatorio" o "eco_postoperatorio" basandoti sul contesto
        4. Fornisci una confidenza da 0.0 a 1.0 per ogni sezione
        5. Spiega brevemente perché hai classificato ogni sezione in quel modo
        
        Rispondi con JSON:
        {{
            "sections": [
                {{
                    "doc_type": "tipo_documento",
                    "start": posizione_inizio,
                    "end": posizione_fine,
                    "text": "testo_sezione",
                    "confidence": 0.0-1.0,
                    "reasoning": "spiegazione_breve"
                }}
            ]
        }}
        """
        
        try:
            response = self.llm.get_response_from_document(text[:8000], "llm_segmentation", self.model_name)
            result = json.loads(response)
            
            llm_sections = []
            for section_data in result.get("sections", []):
                llm_sections.append(LLMSection(
                    doc_type=section_data["doc_type"],
                    start=section_data["start"],
                    end=section_data["end"],
                    text=section_data["text"],
                    confidence=section_data["confidence"],
                    reasoning=section_data.get("reasoning", ""),
                    metadata={"source": "llm_primary"}
                ))
            
            return llm_sections
            
        except Exception as e:
            logging.error(f"LLM primary segmentation error: {e}")
            return []
    
    def _format_document_types(self) -> str:
        """
        Formatta i tipi di documento per il prompt LLM.
        """
        formatted = []
        for doc_type, info in self.document_types.items():
            formatted.append(f"- {doc_type}: {info['description']}")
        return "\n".join(formatted)
    
    def _apply_temporal_analysis(self, sections: List[LLMSection], intervention_date: Optional[datetime]) -> List[LLMSection]:
        """
        Applica analisi temporale per distinguere eco pre/post operatorio.
        """
        if not intervention_date:
            return sections
        
        enhanced_sections = []
        
        for section in sections:
            if section.doc_type in ["eco_preoperatorio", "eco_postoperatorio"]:
                # Estrai data dall'ecocardiogramma
                eco_date = self._extract_eco_date(section.text)
                
                if eco_date:
                    if eco_date < intervention_date:
                        section.doc_type = "eco_preoperatorio"
                        section.temporal_context = "pre_operatorio"
                        section.confidence = min(0.95, section.confidence + 0.1)
                    else:
                        section.doc_type = "eco_postoperatorio"
                        section.temporal_context = "post_operatorio"
                        section.confidence = min(0.95, section.confidence + 0.1)
                else:
                    # Se non riusciamo a determinare, manteniamo il tipo originale
                    section.confidence = max(0.5, section.confidence - 0.1)
            
            enhanced_sections.append(section)
        
        return enhanced_sections
    
    def _extract_eco_date(self, text: str) -> Optional[datetime]:
        """
        Estrae la data dell'esame ecocardiografico.
        """
        date_patterns = [
            r'data\s+esame[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
            r'eseguito\s+il[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',
            r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',  # Pattern generico
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    year = int(groups[2])
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                    month = int(groups[1])
                    day = int(groups[0])
                    return datetime(year, month, day)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _validate_and_refine(self, text: str, sections: List[LLMSection]) -> List[LLMSection]:
        """
        Valida e raffinamento finale delle sezioni.
        """
        if not sections:
            return sections
        
        # Fase 1: Validazione LLM delle sezioni con confidenza bassa
        validated_sections = []
        for section in sections:
            if section.confidence < 0.7:  # Valida sezioni con confidenza bassa
                llm_validation = self._llm_validate_section(section)
                if llm_validation:
                    section.confidence = min(0.9, section.confidence + 0.2)
                    section.metadata["llm_validated"] = True
            validated_sections.append(section)
        
        # Fase 2: Identifica testo non coperto e cerca sezioni mancanti
        covered_ranges = [(s.start, s.end) for s in validated_sections]
        uncovered_text = self._extract_uncovered_text(text, covered_ranges)
        
        if uncovered_text and len(uncovered_text) > 200:  # Solo se c'è testo significativo
            try:
                missing_sections = self._llm_find_missing_sections(uncovered_text)
                validated_sections.extend(missing_sections)
            except Exception as e:
                logging.warning(f"LLM missing sections search failed: {e}")
        
        # Ordina e pulizia finale
        validated_sections.sort(key=lambda x: x.start)
        return self._final_cleanup(validated_sections)
    
    def _llm_validate_section(self, section: LLMSection) -> bool:
        """
        Usa LLM per validare una sezione specifica.
        """
        prompt = f"""
        Valida se questo testo appartiene al tipo di documento indicato.
        
        Tipo documento: {section.doc_type}
        Descrizione: {self.document_types.get(section.doc_type, {}).get('description', '')}
        
        Testo da validare:
        {section.text[:1000]}
        
        Rispondi solo con "SI" o "NO".
        """
        
        try:
            response = self.llm.get_response_from_document(section.text[:1000], "section_validation", self.model_name)
            return "si" in response.lower()
        except Exception as e:
            logging.warning(f"LLM validation error: {e}")
            return False
    
    def _llm_find_missing_sections(self, text: str) -> List[LLMSection]:
        """
        Usa LLM per trovare sezioni mancanti nel testo non coperto.
        """
        prompt = f"""
        Analizza questo testo di cartella clinica e identifica eventuali sezioni non riconosciute.
        
        Tipi di documento da cercare:
        {self._format_document_types()}
        
        Testo da analizzare:
        {text[:4000]}
        
        Rispondi con JSON:
        {{
            "sections": [
                {{
                    "doc_type": "tipo_documento",
                    "start": posizione_inizio,
                    "end": posizione_fine,
                    "text": "testo_sezione",
                    "confidence": 0.0-1.0,
                    "reasoning": "spiegazione_breve"
                }}
            ]
        }}
        """
        
        try:
            response = self.llm.get_response_from_document(text[:4000], "missing_sections", self.model_name)
            result = json.loads(response)
            
            missing_sections = []
            for section_data in result.get("sections", []):
                missing_sections.append(LLMSection(
                    doc_type=section_data["doc_type"],
                    start=section_data["start"],
                    end=section_data["end"],
                    text=section_data["text"],
                    confidence=section_data["confidence"],
                    reasoning=section_data.get("reasoning", ""),
                    metadata={"source": "llm_missing"}
                ))
            
            return missing_sections
            
        except Exception as e:
            logging.error(f"LLM missing sections error: {e}")
            return []
    
    def _extract_uncovered_text(self, text: str, covered_ranges: List[Tuple[int, int]]) -> str:
        """
        Estrae il testo non coperto dalle sezioni identificate.
        """
        if not covered_ranges:
            return text
        
        covered_ranges.sort(key=lambda x: x[0])
        uncovered_parts = []
        last_end = 0
        
        for start, end in covered_ranges:
            if start > last_end:
                uncovered_parts.append(text[last_end:start])
            last_end = max(last_end, end)
        
        if last_end < len(text):
            uncovered_parts.append(text[last_end:])
        
        return "\n".join(uncovered_parts)
    
    def _final_cleanup(self, sections: List[LLMSection]) -> List[LLMSection]:
        """
        Pulizia finale delle sezioni.
        PERMETTE SEZIONI MULTIPLE DELLO STESSO TIPO.
        """
        # Rimuovi sezioni troppo corte
        sections = [s for s in sections if len(s.text.strip()) >= 30]
        
        # Rimuovi solo duplicati esatti (stesso testo)
        seen_texts = set()
        unique_sections = []
        
        for section in sections:
            text_hash = hash(section.text.strip())
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_sections.append(section)
            else:
                # Se testo identico, mantieni quello con confidenza maggiore
                existing = next(s for s in unique_sections if hash(s.text.strip()) == text_hash)
                if section.confidence > existing.confidence:
                    unique_sections.remove(existing)
                    unique_sections.append(section)
        
        return unique_sections 