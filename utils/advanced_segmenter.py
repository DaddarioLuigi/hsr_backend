# utils/advanced_segmenter.py
# -*- coding: utf-8 -*-
"""
Segmentatore avanzato per cartelle cliniche cardiologiche.
Basato sulle specifiche dettagliate dei 9 tipi di documento da estrarre.
Combina regex precise, analisi temporale e LLM per massima robustezza.
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from llm.extractor import LLMExtractor

@dataclass
class AdvancedSection:
    doc_type: str
    start: int
    end: int
    text: str
    confidence: float
    metadata: Dict[str, Any] = None
    page_info: Optional[str] = None
    temporal_context: Optional[str] = None

class AdvancedSegmenter:
    """
    Segmentatore avanzato per documenti clinici cardiologici.
    Basato sulle specifiche dettagliate dei 9 tipi di documento.
    """
    
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3", environment: str = "production"):
        self.model_name = model_name
        self.llm = LLMExtractor()
        self.environment = environment
        
        # Carica configurazione
        from config.segmentation_config import get_config
        self.config = get_config(environment)
        
        # Definizione precisa dei pattern di riconoscimento
        self.document_patterns = {
            "lettera_dimissione": {
                "primary_patterns": [
                    r"(?:^|\n)\s*RELAZIONE\s+CLINICA\s+ALLA\s+DIMISSIONE\s*[-–—]\s*DEFINITIVA\b",
                    r"(?:^|\n)\s*relazione\s+clinica\s+alla\s+dimissione\b",
                    r"(?:^|\n)\s*lettera\s+di\s+dimissione\b",
                    r"(?:^|\n)\s*si\s+dimette\s+in\s+data\b",
                ],
                "keywords": ["dimissione", "ricovero", "storia", "decorso"],
                "description": "Relazione dell'intero ricovero con storia paziente e decorso post-operatorio"
            },
            
            "anamnesi": {
                "primary_patterns": [
                    r"(?:^|\n)\s*anamnesi\b",
                    r"(?:^|\n)\s*cenni\s+anamnestici\b",
                ],
                "keywords": ["storia", "terapia", "ingresso", "anamnestici"],
                "description": "Storia del paziente, terapia al momento dell'ingresso"
            },
            
            "epicrisi_ti": {
                "primary_patterns": [
                    r"(?:^|\n)\s*epicrisi\s+terapia\s+intensiva(?:\s*/?\s*TICCH)?\b",
                    r"(?:^|\n)\s*epicrisi\s+ticch\b",
                ],
                "keywords": ["terapia intensiva", "TICCH", "degenza", "post-operatorio"],
                "description": "Relazione sulla degenza in terapia intensiva post-intervento"
            },
            
            "cartellino_anestesiologico": {
                "primary_patterns": [
                    r"(?:^|\n)\s*scheda\s+anestesiologica\s+intraoperatoria\b",
                    r"(?:^|\n)\s*cartellino\s+anestesiologico\b",
                    r"(?:^|\n)\s*scheda\s+anestesiologica\b",
                ],
                "keywords": ["anestesiologica", "intraoperatoria", "CEC", "clampaggio"],
                "description": "Dati fissi con orari: CEC, clampaggio, tempi sala"
            },
            
            "intervento": {
                "primary_patterns": [
                    r"(?:^|\n)\s*verbale\s+operatorio\b",
                    r"(?:^|\n)\s*intervento\s+cardiochirurgico\b",
                    r"(?:^|\n)\s*referto\s+operatorio\b",
                ],
                "keywords": ["operatorio", "intervento", "chirurgico", "primo operatore"],
                "description": "Relazione dell'intervento con tipo e decorso"
            },
            
            "coronarografia": {
                "primary_patterns": [
                    r"(?:^|\n)\s*laboratorio\s+di\s+emodinamica\s+e\s+cardiologia\s+interventistica\b",
                    r"(?:^|\n)\s*coronarografia\b",
                    r"(?:^|\n)\s*cateterismo\s+cardiaco\b",
                    r"(?:^|\n)\s*angiografia\s+coronarica\b",
                ],
                "keywords": ["emodinamica", "coronarie", "tronco comune", "arteria circonflessa"],
                "description": "Stato delle coronarie con pattern fissi (Tronco comune, Arteria circonflessa...)"
            },
            
            "eco_preoperatorio": {
                "primary_patterns": [
                    r"(?:^|\n)\s*laborator[io]i?\s+di\s+ecocardiografia\b",
                    r"(?:^|\n)\s*ecocardiogramma\s+transtoracico\b",
                    r"(?:^|\n)\s*ecocardiogramma\s+transesofageo\b",
                    # Pattern più flessibili per OCR
                    r"(?:^|\n)\s*eco\s*cardiografia\b",
                    r"(?:^|\n)\s*eco\s*cardiogramma\b",
                    r"(?:^|\n)\s*ecocardio\b",
                ],
                "keywords": ["ecocardiografia", "ecocardiogramma", "FE", "valvulopatie"],
                "description": "Ecocardiogramma con variabili codificate, eseguito PRIMA dell'intervento"
            },
            
            "eco_postoperatorio": {
                "primary_patterns": [
                    r"(?:^|\n)\s*laborator[io]i?\s+di\s+ecocardiografia\b",
                    r"(?:^|\n)\s*ecocardiogramma\s+transtoracico\b",
                    r"(?:^|\n)\s*ecocardiogramma\s+transesofageo\b",
                    # Pattern più flessibili per OCR
                    r"(?:^|\n)\s*eco\s*cardiografia\b",
                    r"(?:^|\n)\s*eco\s*cardiogramma\b",
                    r"(?:^|\n)\s*ecocardio\b",
                ],
                "keywords": ["ecocardiografia", "ecocardiogramma", "FE", "bypass"],
                "description": "Ecocardiogramma con variabili codificate, eseguito DOPO l'intervento"
            },
            
            "tc_cuore": {
                "primary_patterns": [
                    r"(?:^|\n)\s*tc\s+cuore\b",
                    r"(?:^|\n)\s*tac\s+cuore\b",
                    r"(?:^|\n)\s*tc\s+coronaric[ae]\b",
                    r"(?:^|\n)\s*angio[-–—]?tc\s+cardiac[ae]\b",
                    r"(?:^|\n)\s*tc\s+cardiac[ae]\b",
                ],
                "keywords": ["TC", "TAC", "coronarie", "angio-TC"],
                "description": "TC cuore/coronarie con variabili codificate"
            }
        }
        
        # Priorità per risoluzione conflitti
        self.priority_order = [
            "lettera_dimissione",  # Documento principale
            "intervento",          # Riferimento temporale chiave
            "cartellino_anestesiologico",  # Stessa data dell'intervento
            "epicrisi_ti",         # Post-intervento
            "coronarografia",      # Pre-intervento
            "tc_cuore",           # Alternativa a coronarografia
            "eco_preoperatorio",   # Pre-intervento
            "eco_postoperatorio",  # Post-intervento
            "anamnesi",           # Informazioni generali
        ]
    
    def segment_document(self, text: str) -> List[AdvancedSection]:
        """
        Segmentazione avanzata del documento usando multiple strategie.
        """
        if self.config["logging"]["enable_detailed_logs"]:
            logging.info("=== AVVIO SEGMENTAZIONE AVANZATA ===")
            logging.info(f"Ambiente: {self.environment}")
        
        # Fase 1: Estrazione date per contesto temporale
        dates = self._extract_dates(text)
        intervention_date = self._find_intervention_date(text, dates)
        
        if self.config["logging"]["enable_detailed_logs"]:
            logging.info(f"Date trovate: {len(dates)}")
            logging.info(f"Data intervento: {intervention_date}")
        
        # Fase 2: Segmentazione regex primaria (con soglia più bassa)
        regex_sections = self._regex_segmentation(text)
        if self.config["logging"]["enable_detailed_logs"]:
            logging.info(f"Sezioni regex trovate: {len(regex_sections)}")
        
        # Fase 3: Analisi temporale per eco pre/post
        temporal_sections = self._apply_temporal_analysis(regex_sections, intervention_date)
        if self.config["logging"]["enable_detailed_logs"]:
            logging.info(f"Sezioni dopo analisi temporale: {len(temporal_sections)}")
        
        # Fase 4: LLM validation e enhancement (più aggressivo)
        final_sections = self._llm_validation_and_enhancement(text, temporal_sections)
        if self.config["logging"]["enable_detailed_logs"]:
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
        # (assumiamo che l'intervento sia la data centrale nel range)
        if dates:
            return dates[len(dates)//2]
        
        return None
    
    def _regex_segmentation(self, text: str) -> List[AdvancedSection]:
        """
        Segmentazione primaria usando regex precise.
        """
        sections = []
        
        for doc_type, config in self.document_patterns.items():
            for pattern in config["primary_patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    start = match.start()
                    
                    # Trova la fine della sezione (inizio della prossima o fine testo)
                    end = self._find_section_end(text, start, doc_type)
                    
                    section_text = text[start:end].strip()
                    min_length = self.config["flexible_patterns"]["min_section_length"]
                    if len(section_text) >= min_length:  # Filtra sezioni troppo corte
                        # Calcola confidenza basata su keyword match
                        keyword_score = self._count_keywords(section_text, config["keywords"]) / len(config["keywords"])
                        confidence = 0.6 + (keyword_score * 0.3)  # Range 0.6-0.9
                        
                        sections.append(AdvancedSection(
                            doc_type=doc_type,
                            start=start,
                            end=end,
                            text=section_text,
                            confidence=confidence,
                            metadata={
                                "pattern_matched": pattern,
                                "keywords_found": self._count_keywords(section_text, config["keywords"]),
                                "source": "regex"
                            }
                        ))
                        
                        if self.config["logging"]["log_confidence_scores"]:
                            logging.debug(f"📊 Sezione {doc_type}: confidenza {confidence:.2f} (keywords: {keyword_score:.2f})")
        
        # Ordina per posizione e rimuovi sovrapposizioni
        sections.sort(key=lambda x: x.start)
        return self._remove_overlaps(sections)
    
    def _find_section_end(self, text: str, start: int, current_type: str) -> int:
        """
        Trova la fine di una sezione basandosi su pattern di inizio di altre sezioni.
        """
        # Cerca il prossimo pattern di inizio sezione
        next_start = len(text)
        
        for doc_type, config in self.document_patterns.items():
            if doc_type == current_type:
                continue
                
            for pattern in config["primary_patterns"]:
                matches = re.finditer(pattern, text[start+1:], re.IGNORECASE)
                for match in matches:
                    candidate_start = start + 1 + match.start()
                    if candidate_start < next_start:
                        next_start = candidate_start
        
        return next_start
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """
        Conta le keyword trovate nel testo per validazione.
        """
        count = 0
        for keyword in keywords:
            if re.search(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE):
                count += 1
        return count
    
    def _remove_overlaps(self, sections: List[AdvancedSection]) -> List[AdvancedSection]:
        """
        Rimuove sovrapposizioni tra sezioni, mantenendo quelle con priorità maggiore.
        PERMETTE SEZIONI MULTIPLE DELLO STESSO TIPO se non si sovrappongono.
        """
        if not sections:
            return sections
        
        filtered = []
        current = sections[0]
        
        for next_section in sections[1:]:
            if self._sections_overlap(current, next_section):
                # Scegli quella con priorità maggiore
                current_priority = self.priority_order.index(current.doc_type) if current.doc_type in self.priority_order else 999
                next_priority = self.priority_order.index(next_section.doc_type) if next_section.doc_type in self.priority_order else 999
                
                if next_priority < current_priority:
                    current = next_section
            else:
                # Se non si sovrappongono, mantieni entrambe
                filtered.append(current)
                current = next_section
        
        filtered.append(current)
        return filtered
    
    def _sections_overlap(self, s1: AdvancedSection, s2: AdvancedSection) -> bool:
        """
        Verifica se due sezioni si sovrappongono.
        """
        return not (s1.end <= s2.start or s2.end <= s1.start)
    
    def _apply_temporal_analysis(self, sections: List[AdvancedSection], intervention_date: Optional[datetime]) -> List[AdvancedSection]:
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
                        boost_amount = self.config["temporal_analysis"]["boost_amount"]
                        section.confidence = min(0.95, section.confidence + boost_amount)
                        if self.config["logging"]["log_temporal_analysis"]:
                            logging.info(f"🕒 Temporal analysis: {section.doc_type} (date: {eco_date}, intervention: {intervention_date})")
                    else:
                        section.doc_type = "eco_postoperatorio"
                        section.temporal_context = "post_operatorio"
                        boost_amount = self.config["temporal_analysis"]["boost_amount"]
                        section.confidence = min(0.95, section.confidence + boost_amount)
                        if self.config["logging"]["log_temporal_analysis"]:
                            logging.info(f"🕒 Temporal analysis: {section.doc_type} (date: {eco_date}, intervention: {intervention_date})")
                else:
                    # Se non riusciamo a determinare, manteniamo il tipo originale
                    # ma riduciamo leggermente la confidenza
                    penalty_amount = self.config["temporal_analysis"]["penalty_amount"]
                    section.confidence = max(0.5, section.confidence - penalty_amount)
                    if self.config["logging"]["log_temporal_analysis"]:
                        logging.warning(f"⚠️ Could not determine temporal context for eco section")
            
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
    
    def _llm_validation_and_enhancement(self, text: str, sections: List[AdvancedSection]) -> List[AdvancedSection]:
        """
        Usa LLM per validare e migliorare le sezioni trovate.
        APPROCCIO PIÙ AGGRESSIVO: valida anche sezioni esistenti.
        """
        if not sections:
            return sections
        
        # Fase 1: Validazione LLM delle sezioni esistenti
        validated_sections = []
        for section in sections:
            if (self.config["llm_validation"]["enable"] and 
                section.confidence < self.config["llm_validation"]["threshold"]):
                llm_validation = self._llm_validate_section(section)
                if llm_validation:
                    boost_amount = self.config["llm_validation"]["boost_amount"]
                    section.confidence = min(0.9, section.confidence + boost_amount)
                    section.metadata["llm_validated"] = True
                    if self.config["logging"]["log_llm_validation"]:
                        logging.info(f"✅ LLM validation successful for {section.doc_type} (confidence: {section.confidence:.2f})")
            validated_sections.append(section)
        
        # Fase 2: Identifica testo non coperto
        covered_ranges = [(s.start, s.end) for s in validated_sections]
        uncovered_text = self._extract_uncovered_text(text, covered_ranges)
        
        if uncovered_text and len(uncovered_text) > 100:  # Solo se c'è testo significativo
            try:
                llm_sections = self._llm_segment_uncovered(uncovered_text)
                validated_sections.extend(llm_sections)
            except Exception as e:
                logging.warning(f"LLM validation failed: {e}")
        
        # Ordina e pulizia finale
        validated_sections.sort(key=lambda x: x.start)
        return self._final_cleanup(validated_sections)
    
    def _llm_validate_section(self, section: AdvancedSection) -> bool:
        """
        Usa LLM per validare una sezione specifica.
        """
        prompt = f"""
        Valida se questo testo appartiene al tipo di documento indicato.
        
        Tipo documento: {section.doc_type}
        Descrizione: {self.document_patterns.get(section.doc_type, {}).get('description', '')}
        
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
    
    def _llm_segment_uncovered(self, text: str) -> List[AdvancedSection]:
        """
        Usa LLM per segmentare il testo non coperto.
        """
        prompt = f"""
        Analizza questo testo di cartella clinica e identifica eventuali sezioni non riconosciute.
        
        Tipi di documento da cercare:
        1. Lettera di dimissione - "RELAZIONE CLINICA ALLA DIMISSIONE"
        2. Anamnesi - "Anamnesi"
        3. Epicrisi terapia intensiva - "Epicrisi terapia intensiva/TICCH"
        4. Cartellino anestesiologico - "Scheda anestesiologica"
        5. Verbale operatorio - "Verbale Operatorio"
        6. Coronarografia - "Laboratorio di Emodinamica"
        7. Ecocardiogramma preoperatorio - "Laboratori di ecocardiografia" (PRIMA intervento)
        8. Ecocardiogramma postoperatorio - "Laboratori di ecocardiografia" (DOPO intervento)
        9. TC cuore - "TC cuore", "TAC cuore"
        
        Testo da analizzare:
        {text[:3000]}  # Limita per token
        
        Rispondi con JSON:
        {{
            "sections": [
                {{
                    "doc_type": "tipo_documento",
                    "start": posizione_inizio,
                    "end": posizione_fine,
                    "text": "testo_sezione",
                    "confidence": 0.0-1.0
                }}
            ]
        }}
        """
        
        try:
            response = self.llm.get_response_from_document(text, "document_segmentation", self.model_name)
            result = json.loads(response)
            
            llm_sections = []
            for section_data in result.get("sections", []):
                llm_sections.append(AdvancedSection(
                    doc_type=section_data["doc_type"],
                    start=section_data["start"],
                    end=section_data["end"],
                    text=section_data["text"],
                    confidence=section_data["confidence"],
                    metadata={"source": "llm"}
                ))
            
            return llm_sections
            
        except Exception as e:
            logging.error(f"LLM segmentation error: {e}")
            return []
    
    def _final_cleanup(self, sections: List[AdvancedSection]) -> List[AdvancedSection]:
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