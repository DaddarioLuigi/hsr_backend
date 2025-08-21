# utils/metadata_coherence_manager.py
# -*- coding: utf-8 -*-
"""
Metadata Coherence Manager:
Gestisce la coerenza dei metadati paziente tra tutti i documenti caricati,
in particolare rispetto alla Lettera di Dimissione.
"""

import os
import json
import logging
import unicodedata
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CoherenceResult:
    """Risultato della verifica di coerenza."""
    status: str  # "accepted" | "rejected"
    reason: Optional[str] = None
    diff: Optional[Dict[str, Dict[str, str]]] = None  # campo -> {atteso, trovato}
    references: Optional[str] = None  # ID LD usata per il confronto
    incoerenti: Optional[List[Dict[str, Any]]] = None  # lista documenti incoerenti

class MetadataCoherenceManager:
    """
    Gestisce la coerenza dei metadati del paziente tra documenti.
    """
    
    # Campi di riferimento per la coerenza
    COHERENCE_FIELDS = ["n_cartella", "nome", "cognome"]
    
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        self.logger = logging.getLogger(__name__)
    
    def normalize_text(self, text: str) -> str:
        """
        Normalizza il testo per il confronto:
        - trim spazi iniziali/finali e multipli → singolo spazio interno
        - case-insensitive (confronto in minuscolo)
        - rimuovere accenti/diacritici
        - rimuovere punteggiatura non alfanumerica irrilevante
        """
        if not text:
            return ""
        
        # Converti in stringa e normalizza
        text = str(text).strip()
        
        # Normalizza Unicode (rimuove accenti)
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Converti in minuscolo
        text = text.lower()
        
        # Rimuovi punteggiatura irrilevante (mantieni spazi e alfanumerici)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalizza spazi (multipli → singolo)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Normalizza tutti i campi di coerenza."""
        normalized = {}
        for field in self.COHERENCE_FIELDS:
            if field in metadata:
                normalized[field] = self.normalize_text(metadata[field])
            else:
                normalized[field] = ""
        return normalized
    
    def metadata_equals(self, meta1: Dict[str, str], meta2: Dict[str, str]) -> bool:
        """Verifica se due metadati normalizzati sono uguali."""
        for field in self.COHERENCE_FIELDS:
            if meta1.get(field, "") != meta2.get(field, ""):
                return False
        return True
    
    def get_metadata_differences(self, meta1: Dict[str, str], meta2: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Trova le differenze tra due metadati normalizzati."""
        differences = {}
        for field in self.COHERENCE_FIELDS:
            val1 = meta1.get(field, "")
            val2 = meta2.get(field, "")
            if val1 != val2:
                differences[field] = {
                    "atteso": val1,
                    "trovato": val2
                }
        return differences
    
    def find_lettera_dimissione(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Trova la lettera di dimissione per un paziente."""
        lettera_path = os.path.join(self.upload_folder, patient_id, "lettera_dimissione", "entities.json")
        
        if not os.path.exists(lettera_path):
            return None
        
        try:
            with open(lettera_path, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            return entities
        except Exception as e:
            self.logger.error(f"Errore nella lettura della lettera di dimissione: {e}")
            return None
    
    def get_all_documents_metadata(self, patient_id: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Ottiene i metadati di tutti i documenti di un paziente (esclusa la LD)."""
        documents = []
        patient_folder = os.path.join(self.upload_folder, patient_id)
        
        if not os.path.exists(patient_folder):
            return documents
        
        for doc_type in os.listdir(patient_folder):
            # Salta la lettera di dimissione
            if doc_type == "lettera_dimissione":
                continue
            
            doc_folder = os.path.join(patient_folder, doc_type)
            if not os.path.isdir(doc_folder):
                continue
            
            entities_path = os.path.join(doc_folder, "entities.json")
            if os.path.exists(entities_path):
                try:
                    with open(entities_path, 'r', encoding='utf-8') as f:
                        entities = json.load(f)
                    documents.append((doc_type, entities))
                except Exception as e:
                    self.logger.warning(f"Errore nella lettura del documento {doc_type}: {e}")
        
        return documents
    
    def check_coherence_with_lettera_dimissione(self, patient_id: str, new_metadata: Dict[str, Any]) -> CoherenceResult:
        """
        Verifica la coerenza di un nuovo documento con la lettera di dimissione.
        """
        # Trova la lettera di dimissione
        ld_entities = self.find_lettera_dimissione(patient_id)
        
        if not ld_entities:
            # Non c'è lettera di dimissione, accetta il documento
            return CoherenceResult(
                status="accepted",
                reason="Nessuna lettera di dimissione presente"
            )
        
        # Normalizza i metadati
        ld_normalized = self.normalize_metadata(ld_entities)
        new_normalized = self.normalize_metadata(new_metadata)
        
        # Verifica coerenza
        if self.metadata_equals(ld_normalized, new_normalized):
            return CoherenceResult(
                status="accepted",
                reason="Metadati coerenti con la lettera di dimissione",
                references="lettera_dimissione"
            )
        else:
            # Trova le differenze
            differences = self.get_metadata_differences(ld_normalized, new_normalized)
            
            return CoherenceResult(
                status="rejected",
                reason="ERRORE_COHERENCE_WITH_LD: I metadati del documento non corrispondono alla Lettera di Dimissione.",
                diff=differences,
                references="lettera_dimissione"
            )
    
    def check_lettera_dimissione_coherence(self, patient_id: str, ld_metadata: Dict[str, Any]) -> CoherenceResult:
        """
        Verifica la coerenza di una nuova lettera di dimissione con i documenti esistenti.
        """
        # Ottieni tutti i documenti esistenti
        existing_docs = self.get_all_documents_metadata(patient_id)
        
        if not existing_docs:
            # Nessun documento esistente, accetta la lettera di dimissione
            return CoherenceResult(
                status="accepted",
                reason="Nessun documento esistente per il confronto"
            )
        
        # Normalizza i metadati della lettera di dimissione
        ld_normalized = self.normalize_metadata(ld_metadata)
        
        # Verifica coerenza con ogni documento
        incoerenti = []
        for doc_type, doc_entities in existing_docs:
            doc_normalized = self.normalize_metadata(doc_entities)
            
            if not self.metadata_equals(ld_normalized, doc_normalized):
                differences = self.get_metadata_differences(ld_normalized, doc_normalized)
                incoerenti.append({
                    "document_type": doc_type,
                    "differences": differences
                })
        
        if not incoerenti:
            return CoherenceResult(
                status="accepted",
                reason="Lettera di dimissione coerente con tutti i documenti esistenti"
            )
        else:
            return CoherenceResult(
                status="rejected",
                reason="ERRORE_LD_INCOERENTE: La Lettera di Dimissione non corrisponde ai documenti già caricati.",
                incoerenti=incoerenti
            )
    
    def check_document_coherence(self, patient_id: str, document_type: str, metadata: Dict[str, Any]) -> CoherenceResult:
        """
        Verifica la coerenza di un nuovo documento con tutti i documenti esistenti.
        """
        # Se è una lettera di dimissione, usa la logica specifica
        if document_type == "lettera_dimissione":
            return self.check_lettera_dimissione_coherence(patient_id, metadata)
        
        # Per altri documenti, verifica prima con la lettera di dimissione
        ld_result = self.check_coherence_with_lettera_dimissione(patient_id, metadata)
        
        if ld_result.status == "rejected":
            return ld_result
        
        # Se non c'è lettera di dimissione, verifica coerenza con altri documenti
        if ld_result.reason == "Nessuna lettera di dimissione presente":
            existing_docs = self.get_all_documents_metadata(patient_id)
            
            if not existing_docs:
                return CoherenceResult(
                    status="accepted",
                    reason="Primo documento caricato"
                )
            
            # Verifica coerenza con tutti i documenti esistenti
            new_normalized = self.normalize_metadata(metadata)
            incoerenti = []
            
            for doc_type, doc_entities in existing_docs:
                doc_normalized = self.normalize_metadata(doc_entities)
                
                if not self.metadata_equals(new_normalized, doc_normalized):
                    differences = self.get_metadata_differences(new_normalized, doc_normalized)
                    incoerenti.append({
                        "document_type": doc_type,
                        "differences": differences
                    })
            
            if incoerenti:
                return CoherenceResult(
                    status="rejected",
                    reason="ERRORE_COHERENCE_WITH_EXISTING: I metadati del documento non corrispondono ai documenti già caricati.",
                    incoerenti=incoerenti
                )
        
        return CoherenceResult(
            status="accepted",
            reason="Documento coerente con i metadati esistenti"
        )
    
    def check_multiple_sections_coherence(self, patient_id: str, sections_metadata: Dict[str, Dict[str, Any]]) -> CoherenceResult:
        """
        Verifica la coerenza tra multiple sezioni estratte dallo stesso documento.
        Utile per il flusso unificato che estrae più sezioni da un singolo PDF.
        
        Args:
            patient_id: ID del paziente
            sections_metadata: Dict con {doc_type: entities} per ogni sezione estratta
            
        Returns:
            CoherenceResult con lo stato di coerenza
        """
        if not sections_metadata or len(sections_metadata) < 2:
            return CoherenceResult(
                status="accepted",
                reason="Insufficienti sezioni per verificare coerenza"
            )
        
        # Trova la lettera di dimissione se presente
        ld_entities = None
        if "lettera_dimissione" in sections_metadata:
            ld_entities = sections_metadata["lettera_dimissione"]
        
        # Normalizza tutti i metadati
        normalized_sections = {}
        for doc_type, entities in sections_metadata.items():
            if entities and isinstance(entities, dict):
                normalized_sections[doc_type] = self.normalize_metadata(entities)
        
        if len(normalized_sections) < 2:
            return CoherenceResult(
                status="accepted",
                reason="Insufficienti sezioni normalizzate per verificare coerenza"
            )
        
        # Se c'è una lettera di dimissione, usa quella come riferimento
        if ld_entities:
            reference_metadata = normalized_sections["lettera_dimissione"]
            incoerenti = []
            
            for doc_type, doc_normalized in normalized_sections.items():
                if doc_type == "lettera_dimissione":
                    continue
                
                if not self.metadata_equals(reference_metadata, doc_normalized):
                    differences = self.get_metadata_differences(reference_metadata, doc_normalized)
                    incoerenti.append({
                        "document_type": doc_type,
                        "differences": differences
                    })
            
            if incoerenti:
                return CoherenceResult(
                    status="rejected",
                    reason="ERRORE_COHERENCE_BETWEEN_SECTIONS: Le sezioni estratte non sono coerenti tra loro.",
                    incoerenti=incoerenti,
                    references="lettera_dimissione"
                )
        else:
            # Non c'è lettera di dimissione, verifica coerenza tra tutte le sezioni
            section_types = list(normalized_sections.keys())
            reference_type = section_types[0]
            reference_metadata = normalized_sections[reference_type]
            incoerenti = []
            
            for doc_type in section_types[1:]:
                doc_normalized = normalized_sections[doc_type]
                
                if not self.metadata_equals(reference_metadata, doc_normalized):
                    differences = self.get_metadata_differences(reference_metadata, doc_normalized)
                    incoerenti.append({
                        "document_type": doc_type,
                        "differences": differences
                    })
            
            if incoerenti:
                return CoherenceResult(
                    status="rejected",
                    reason="ERRORE_COHERENCE_BETWEEN_SECTIONS: Le sezioni estratte non sono coerenti tra loro.",
                    incoerenti=incoerenti,
                    references=reference_type
                )
        
        return CoherenceResult(
            status="accepted",
            reason="Tutte le sezioni sono coerenti tra loro"
        )
    
    def get_coherence_status(self, patient_id: str) -> Dict[str, Any]:
        """
        Ottiene lo stato di coerenza per un paziente.
        """
        ld_entities = self.find_lettera_dimissione(patient_id)
        existing_docs = self.get_all_documents_metadata(patient_id)
        
        if not ld_entities:
            return {
                "has_lettera_dimissione": False,
                "total_documents": len(existing_docs),
                "coherence_status": "pending_ld"
            }
        
        # Verifica coerenza di tutti i documenti con la LD
        ld_normalized = self.normalize_metadata(ld_entities)
        incoerenti = []
        
        for doc_type, doc_entities in existing_docs:
            doc_normalized = self.normalize_metadata(doc_entities)
            
            if not self.metadata_equals(ld_normalized, doc_normalized):
                differences = self.get_metadata_differences(ld_normalized, doc_normalized)
                incoerenti.append({
                    "document_type": doc_type,
                    "differences": differences
                })
        
        return {
            "has_lettera_dimissione": True,
            "total_documents": len(existing_docs),
            "incoerenti": len(incoerenti),
            "coherence_status": "coherent" if not incoerenti else "incoherent",
            "incoerenti_details": incoerenti
        } 