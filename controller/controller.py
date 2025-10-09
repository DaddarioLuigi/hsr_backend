import os
import json
import pdfplumber
import numpy as np
import logging
import time
from llm.extractor import LLMExtractor
from utils.excel_manager import ExcelManager
from utils.file_manager import FileManager
from utils.entity_extractor import EntityExtractor
from llm.prompts import PromptManager
from utils.table_parser import TableParser
from pipelines.ingestion import ClinicalPacketIngestion
from utils.progress import ProgressStore
from utils.metadata_coherence_manager import MetadataCoherenceManager

from datetime import datetime

class DocumentController:
    def __init__(
        self,
        #model_name: str = "openai/gpt-oss-120b",
        model_name: str = "deepseek-ai/DeepSeek-V3",
        upload_folder: str | None = None,
        export_folder: str | None = None,
    ):
        self.model_name = model_name
        self.llm = LLMExtractor()
        self.excel_manager = ExcelManager()
        self.file_manager = FileManager()
        self.table_parser = TableParser()
        self.prompt_manager = PromptManager()

        # usa la cartella passata da app.py o quella in env
        self.upload_folder = upload_folder or os.getenv("UPLOAD_FOLDER", "uploads")
        # allinea FileManager al medesimo percorso
        self.file_manager.UPLOAD_FOLDER = self.upload_folder

        # (opzionale) allinea anche ExcelManager
        if export_folder:
            self.excel_manager.EXPORT_FOLDER = export_folder
            self.excel_manager.EXPORT_PATH = os.path.join(export_folder, "output.xlsx")
        
        # Inizializza il gestore di coerenza dei metadati
        self.coherence_manager = MetadataCoherenceManager(self.upload_folder)        


    def validate_upload_request(self, files, patient_id: str = None, process_as_packet: bool = False) -> tuple[bool, str, list]:
        """
        Valida una richiesta di upload.
        
        Returns:
            tuple[bool, str, list]: (is_valid, error_message, validated_files)
        """
        if not files:
            return False, "Nessun file fornito", []
        
        # Converti in lista se necessario
        file_list = files if isinstance(files, list) else [files]
        
        # Validazione file
        validated_files = []
        for file in file_list:
            if not file or not file.filename:
                return False, "File non valido", []
            
            # Verifica estensione
            if not file.filename.lower().endswith('.pdf'):
                return False, "Sono consentiti solo file PDF", []
            
            # Verifica dimensione
            try:
                file.stream.seek(0, os.SEEK_END)
                size = file.stream.tell()
                file.stream.seek(0)
                
                max_size = float(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
                if size > max_size:
                    return False, f"File {file.filename} troppo grande (max {os.getenv('MAX_UPLOAD_MB', '25')}MB)", []
            except Exception as e:
                return False, f"Errore nella verifica del file {file.filename}: {str(e)}", []
            
            validated_files.append(file)
        
        # Validazione patient_id per flusso non-packet
        if not process_as_packet and not patient_id:
            return False, "Patient ID obbligatorio per il flusso singolo", []
        
        # Validazione dimensione totale
        total_size = 0
        for file in validated_files:
            file.stream.seek(0, os.SEEK_END)
            total_size += file.stream.tell()
            file.stream.seek(0)
        
        max_total_mb = float(os.getenv("MAX_TOTAL_UPLOAD_MB", "100"))
        if total_size > max_total_mb * 1024 * 1024:
            return False, f"Dimensione totale upload supera {max_total_mb}MB", []
        
        return True, "", validated_files

    def get_text_to_remove(self, all_tables: list[list[list[str]]]) -> list[str]:
        text_to_remove: list[str] = []
        for table in all_tables:
            arr = np.array(table)
            for row in arr:
                norm = "".join(str(cell) for cell in row).replace(" ", "").replace("\n", "")
                if norm:
                    text_to_remove.append(norm)
        return text_to_remove

    def remove_tables(self, all_text: str, text_to_remove: list[str]) -> str:
        clean_lines: list[str] = []
        for line in all_text.splitlines():
            norm = line.replace(" ", "").replace("\n", "")
            if norm not in text_to_remove:
                clean_lines.append(line)
        return "\n".join(clean_lines)

    def get_cleaned_text(self, all_text: str, all_tables: list[list[list[str]]]) -> str:
        if all_tables:
            text_to_remove = self.get_text_to_remove(all_tables)
            return self.remove_tables(all_text, text_to_remove)
        return all_text 

    def extract_from_tables(self, tables: list[list[list[str]]]) -> dict:
        entities: dict[str, str] = {}
        for table in tables:
            if not table or len(table) < 2:
                continue
            headers = [h.strip() for h in table[0] if h]
            for row in table[1:]:
                for header, cell in zip(headers, row):
                    if header and cell and str(cell).strip():
                        val = str(cell).strip()
                        if header in entities:
                            entities[header] = f"{entities[header]}, {val}"
                        else:
                            entities[header] = val
        return entities

    def process_document_and_entities(
        self,
        filepath: str,
        patient_id: str,
        document_type: str,
        provided_anagraphic: dict = None
    ) -> dict:
        try:
            # 1. Estrai testo
            with pdfplumber.open(filepath) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            # 2. Prepara prompt
            prompt = self.prompt_manager.get_prompt_for(document_type)
            full_prompt = prompt + "\n```\n" + text + "\n```"
            spec = self.prompt_manager.get_spec_for(document_type)
            explicit_keys = spec['entities']

            # 3. Richiesta al modello
            response_str = self.llm.get_response_from_document(
                text, document_type, model=self.model_name
            )
        except RuntimeError as e:
            # API key mancante o altri errori runtime
            logging.error(f"Errore runtime nel processing del documento {filepath}: {e}")
            # Salva uno stato di errore
            self._save_processing_error(patient_id, document_type, str(e))
            raise
        except Exception as e:
            logging.exception(f"Errore nel processing del documento {filepath}: {e}")
            self._save_processing_error(patient_id, document_type, str(e))
            raise

        # 4. Parsifica risposta
        extractor = EntityExtractor(explicit_keys)
        entities = extractor.parse_llm_response(response_str, text)

        # 5. Sovrascrivi anagrafica se fornita
        if provided_anagraphic:
            for key in ("n_cartella", "nome", "cognome"):
                if provided_anagraphic.get(key):
                    entities[key] = provided_anagraphic[key]

        # 6. Verifica coerenza dei metadati
        coherence_result = self.coherence_manager.check_document_coherence(patient_id, document_type, entities)
        
        if coherence_result.status == "rejected":
            # Rimuovi il file e la cartella del paziente se necessario
            os.remove(filepath)
            if document_type == "lettera_dimissione":
                self.file_manager.remove_patient_folder_if_exists(patient_id)
            
            # Prepara la risposta di errore
            error_response = {
                "error": coherence_result.reason,
                "coherence_check": {
                    "status": coherence_result.status,
                    "reason": coherence_result.reason,
                    "diff": coherence_result.diff,
                    "references": coherence_result.references,
                    "incoerenti": coherence_result.incoerenti
                }
            }
            
            return error_response, 400

        # 7. Controlli obbligatori (mantenuti per compatibilità)
        if document_type in ("lettera_dimissione", "eco_preoperatorio"):
            if not entities.get("n_cartella"):
                os.remove(filepath)
                self.file_manager.remove_patient_folder_if_exists(patient_id)
                return {"error": f"Numero di cartella mancante per {document_type}."}, 400

        # 8. Salva JSON in upload_folder configurata
        output_dir = os.path.join(self.file_manager.UPLOAD_FOLDER, patient_id, document_type)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "entities.json")
        # usa FileManager per salvare i dati
        self.file_manager.save_entities_json(patient_id, document_type, entities)

        # Aggiorna anche l'Excel dinamico
        self.excel_manager.update_excel(patient_id, document_type, entities)

        return entities

    def process_clinical_packet_with_ocr(self, pdf_path: str, patient_id: str) -> dict:
        """
        OCR Mistral -> segmentazione -> estrazione per tipologia -> cross-doc -> persistenza.
        Ritorna un riepilogo con sezioni rilevate, tipi processati e mappa globale consolidata.
        """
        ingestion = ClinicalPacketIngestion(
            model_name=getattr(self, "model_name", "deepseek-ai/DeepSeek-V3"),
            ocr_api_key=getattr(self, "ocr_api_key", None),
            upload_folder=getattr(self, "upload_folder", None),
        )
        return ingestion.ingest_pdf_packet(pdf_path, patient_id)

    def _extract_entities_for_section(self, section_text: str, doc_type: str) -> dict:
        """Estrae entità da una sezione usando il prompt dedicato."""
        try:
            # Verifica che esista lo schema/prompt
            spec = self.prompt_manager.get_spec_for(doc_type)
            explicit_keys = spec['entities']
            
            # Limita input per LLM
            MAX_CHARS = 40000
            if len(section_text) > MAX_CHARS:
                section_text = section_text[:MAX_CHARS]
            
            # Estrazione con LLM
            response_str = self.llm.get_response_from_document(
                section_text, doc_type, model=self.model_name
            )
            
            # Parsing della risposta
            extractor = EntityExtractor(explicit_keys)
            entities = extractor.parse_llm_response(response_str, section_text)
            
            return entities
            
        except Exception as e:
            logging.error(f"Errore estrazione entità per {doc_type}: {e}")
            return {}

    def process_single_document_as_packet(self, filepath: str, patient_id: str, filename: str) -> dict:
        """
        Flusso unificato: tratta un singolo PDF come pacchetto clinico da segmentare.
        Ogni sezione viene gestita come documento indipendente con la stessa struttura
        dei singoli documenti.
        
        Args:
            filepath: percorso del PDF caricato
            patient_id: ID paziente (già estratto o fornito)
            filename: nome originale del file
            
        Returns:
            dict con risultati del processing e sezioni mancanti
        """
        from ocr.mistral_ocr import MistralOCR, ocr_response_to_markdown
        from utils.document_segmenter import find_document_sections
        from pipelines.router import normalize_doc_type
        from llm.prompts import PromptManager
        import re
        import uuid
        import shutil
        import json
        
        logging.info(f"=== INIZIO PROCESSING PACCHETTO ===")
        logging.info(f"File: {filename}")
        logging.info(f"Patient ID iniziale: {patient_id}")
        logging.info(f"Percorso file: {filepath}")
        
        # Inizializza componenti
        ocr = MistralOCR()
        prompts = PromptManager()
        
        # Tipi supportati per verificare sezioni mancanti
        SUPPORTED_TYPES = {
            "lettera_dimissione", "anamnesi", "epicrisi_ti", "cartellino_anestesiologico",
            "intervento", "coronarografia", "eco_preoperatorio", "eco_postoperatorio", "tc_cuore"
        }
        
        results = {
            "patient_id": patient_id,
            "filename": filename,
            "sections_found": [],
            "sections_missing": [],
            "documents_created": [],
            "errors": []
        }
        
        # Flag per tracciare se il patient_id è stato estratto dal documento
        patient_id_extracted = False
        
        try:
            # 1. OCR del PDF
            logging.info(f"🔄 FASE 1: Avvio OCR per {filename}")
            
            # Salva stato iniziale
            self._save_packet_processing_status(patient_id, {
                "status": "ocr_start",
                "message": "OCR in esecuzione",
                "progress": 10,
                "filename": filename,
                "sections_found": [],
                "sections_missing": [],
                "documents_created": [],
                "errors": []
            })
            
            ocr_resp = ocr.process_pdf(filepath)
            full_md = ocr_response_to_markdown(ocr_resp)
            
            # Sanitizzazione del testo
            def _sanitize_for_llm(txt: str) -> str:
                s = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', txt or '')  # immagini markdown
                s = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+', '', s)  # data-uri
                s = re.sub(r'[ \t]+', ' ', s)
                s = re.sub(r'\n{3,}', '\n\n', s)
                return s.strip()
            
            full_md = _sanitize_for_llm(full_md)
            
            if not full_md:
                results["errors"].append("OCR ha restituito testo vuoto")
                self._save_packet_processing_status(patient_id, {
                    "status": "failed",
                    "message": "OCR ha restituito testo vuoto",
                    "progress": 100,
                    "filename": filename,
                    "errors": results["errors"]
                })
                return results
            
            logging.info(f"✅ OCR completato. Testo estratto: {len(full_md)} caratteri")
            
            # 2. Estrazione del patient_id dal documento se non fornito o se sembra temporaneo
            if not patient_id or patient_id.startswith("patient_") or patient_id.startswith("_pending_"):
                logging.info(f"🔄 Estrazione patient_id dal documento...")
                try:
                    # Cerca pattern comuni per numero cartella
                    cartella_patterns = [
                        r'cartella\s*n[°\s]*(\d+)',
                        r'n[°\s]*cartella[:\s]*(\d+)',
                        r'cartella\s*clinica[:\s]*(\d+)',
                        r'numero\s*cartella[:\s]*(\d+)',
                        r'paziente\s*n[°\s]*(\d+)',
                        r'id\s*paziente[:\s]*(\d+)'
                    ]
                    
                    extracted_id = None
                    for pattern in cartella_patterns:
                        match = re.search(pattern, full_md, re.IGNORECASE)
                        if match:
                            extracted_id = match.group(1)
                            break
                    
                    if extracted_id:
                        patient_id = str(extracted_id)
                        patient_id_extracted = True
                        logging.info(f"✅ Patient ID estratto dal documento: {patient_id}")
                    else:
                        # Fallback: usa LLM per estrazione
                        logging.info(f"🔄 Fallback a LLM per estrazione patient_id...")
                        try:
                            resp = self.llm.get_response_from_document(
                                full_md, "lettera_dimissione", model=self.model_name
                            )
                            extracted_json = json.loads(resp)
                            extracted_id = extracted_json.get("n_cartella")
                            if extracted_id:
                                patient_id = str(extracted_id)
                                patient_id_extracted = True
                                logging.info(f"✅ Patient ID estratto via LLM: {patient_id}")
                        except Exception as e:
                            logging.warning(f"⚠️ Errore estrazione LLM patient_id: {e}")
                            
                except Exception as e:
                    logging.error(f"❌ Errore estrazione patient_id: {e}")
            
            # Aggiorna results con l'ID finale
            results["patient_id"] = patient_id
            
            # Aggiorna progress dopo OCR
            self._save_packet_processing_status(patient_id, {
                "status": "ocr_done",
                "message": "OCR completato, avvio segmentazione",
                "progress": 30,
                "filename": filename,
                "sections_found": [],
                "sections_missing": [],
                "documents_created": [],
                "errors": []
            })
            
            # Salva il testo OCR completo come file standalone
            logging.info(f"💾 Salvataggio testo OCR...")
            self._save_ocr_text_file(patient_id, filename, full_md)
            
            # 3. Segmentazione
            logging.info(f"🔄 FASE 2: Avvio segmentazione per {filename}")
            
            self._save_packet_processing_status(patient_id, {
                "status": "segmenting",
                "message": "Segmentazione in corso",
                "progress": 40,
                "filename": filename,
                "sections_found": [],
                "sections_missing": [],
                "documents_created": [],
                "errors": []
            })
            
            # Usa il segmenter avanzato migliorato
            from utils.advanced_segmenter import AdvancedSegmenter
            advanced_segmenter = AdvancedSegmenter(model_name=self.model_name)
            advanced_sections = advanced_segmenter.segment_document(full_md)
            
            # Log delle sezioni trovate per debugging
            logging.info(f"✅ Advanced segmenter completato. Trovate {len(advanced_sections)} sezioni")
            for section in advanced_sections:
                logging.info(f"  - {section.doc_type}: {len(section.text)} caratteri (confidenza: {section.confidence:.2f})")
            
            # Fallback al segmenter originale se necessario
            if not advanced_sections:
                logging.warning(f"⚠️ Advanced segmenter non ha trovato sezioni, fallback al segmenter originale")
                sections = find_document_sections(full_md)
                
                if not sections:
                    results["errors"].append("Nessuna sezione identificata nel documento")
                    self._save_packet_processing_status(patient_id, {
                        "status": "failed",
                        "message": "Nessuna sezione identificata nel documento",
                        "progress": 100,
                        "filename": filename,
                        "errors": results["errors"]
                    })
                    return results
                
                # Converti sezioni originali in formato compatibile
                sections_to_process = []
                for section in sections:
                    if section.doc_type != "altro" and section.text.strip():
                        sections_to_process.append({
                            'doc_type': section.doc_type,
                            'text': section.text,
                            'confidence': 0.8  # Confidenza default per sezioni originali
                        })
            else:
                # Usa le sezioni avanzate
                sections_to_process = []
                for section in advanced_sections:
                    sections_to_process.append({
                        'doc_type': section.doc_type,
                        'text': section.text,
                        'confidence': section.confidence
                    })
            
            # 4. Processa ogni sezione come documento indipendente
            logging.info(f"🔄 FASE 3: Elaborazione sezioni...")
            found_types = set()
            total_sections = len(sections_to_process)
            processed_sections = 0
            
            # Dizionario per tracciare i metadati estratti per la verifica di coerenza
            extracted_metadata = {}
            
            # Aggiorna progress per inizio elaborazione sezioni
            self._save_packet_processing_status(patient_id, {
                "status": "processing_sections",
                "message": f"Elaborazione sezioni in corso (0/{total_sections})",
                "progress": 50,
                "filename": filename,
                "sections_found": [s['doc_type'] for s in sections_to_process],
                "sections_missing": [],
                "documents_created": [],
                "errors": []
            })
            
            for section in sections_to_process:
                doc_type = normalize_doc_type(section['doc_type'])
                section_text = section['text'].strip()
                confidence = section['confidence']
                
                if not section_text:
                    continue
                    
                found_types.add(doc_type)
                results["sections_found"].append(doc_type)
                processed_sections += 1
                
                logging.info(f"🔄 Elaborazione sezione {processed_sections}/{total_sections}: {doc_type} (confidenza: {confidence:.2f})")
                
                # Aggiorna stato con progresso dettagliato
                progress = 50 + int(40 * processed_sections / max(1, total_sections))
                self._save_packet_processing_status(patient_id, {
                    "status": "processing_sections",
                    "message": f"Elaborazione sezione {processed_sections}/{total_sections}: {doc_type}",
                    "progress": progress,
                    "filename": filename,
                    "sections_found": results["sections_found"],
                    "sections_missing": [],
                    "documents_created": results["documents_created"],
                    "errors": results["errors"],
                    "current_section": doc_type
                })
                
                # Crea struttura cartelle come per singoli documenti
                section_filename = f"{os.path.splitext(filename)[0]}_{doc_type}.pdf"
                
                try:
                    # Salva sezione come "documento indipendente"
                    logging.info(f"💾 Salvataggio sezione {doc_type}...")
                    self._save_section_as_document(
                        patient_id, doc_type, section_filename, 
                        section_text, filepath
                    )
                    
                    # Estrai entità usando il prompt dedicato
                    logging.info(f"🤖 Estrazione entità per {doc_type}...")
                    entities = self._extract_entities_for_section(
                        section_text, doc_type
                    )
                    
                    # Salva i metadati per la verifica di coerenza
                    if entities and isinstance(entities, dict):
                        extracted_metadata[doc_type] = entities
                    
                    # Verifica coerenza dei metadati tra tutte le sezioni estratte
                    if len(extracted_metadata) > 1:
                        logging.info(f"🔍 Verifica coerenza tra sezioni per {doc_type}...")
                        coherence_result = self.coherence_manager.check_multiple_sections_coherence(patient_id, extracted_metadata)
                        
                        if coherence_result.status == "rejected":
                            error_msg = f"Errore coerenza metadati tra sezioni: {coherence_result.reason}"
                            results["errors"].append(error_msg)
                            logging.error(error_msg)
                            
                            # Se il patient_id è stato estratto dal documento, potrebbe essere sbagliato
                            if patient_id_extracted:
                                logging.warning(f"⚠️ Patient ID estratto potrebbe essere errato. Verificare: {patient_id}")
                            
                            # Non saltare il documento, ma segnalare l'errore
                            # Questo permette di continuare l'elaborazione ma con un warning
                    
                    # Salva entità
                    logging.info(f"💾 Salvataggio entità per {doc_type}...")
                    self.file_manager.save_entities_json(patient_id, doc_type, entities)
                    self.excel_manager.update_excel(patient_id, doc_type, entities)
                    
                    # Crea document_id per la dashboard - usa il nome file originale senza doc_type
                    original_filename_noext = os.path.splitext(filename)[0]
                    document_id = f"doc_{patient_id}_{doc_type}_{original_filename_noext}"
                    
                    results["documents_created"].append({
                        "document_id": document_id,
                        "document_type": doc_type,
                        "filename": section_filename,
                        "status": "processed",
                        "entities_count": len(entities) if isinstance(entities, dict) else 0
                    })
                    
                    logging.info(f"✅ Sezione {doc_type} processata con successo per paziente {patient_id}")
                    
                except Exception as e:
                    error_msg = f"Errore processing sezione {doc_type}: {str(e)}"
                    results["errors"].append(error_msg)
                    logging.error(error_msg)
            
            # 5. Identifica sezioni mancanti
            missing_types = SUPPORTED_TYPES - found_types
            results["sections_missing"] = list(missing_types)
            
            if missing_types:
                logging.warning(f"⚠️ Sezioni mancanti per {filename}: {missing_types}")
            
            # 6. PULIZIA: Rimuovi cartella temp_processing
            try:
                temp_folder = os.path.join(self.upload_folder, patient_id, "temp_processing")
                if os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder)
                    logging.info(f"🧹 Cartella temp_processing rimossa per {patient_id}")
            except Exception as e:
                logging.warning(f"⚠️ Errore rimozione temp_processing: {e}")
            
            # Salva stato finale
            final_status = "completed" if not results["errors"] else "completed_with_errors"
            self._save_packet_processing_status(patient_id, {
                "status": final_status,
                "message": f"Elaborazione completata. Sezioni trovate: {len(results['sections_found'])}, mancanti: {len(results['sections_missing'])}",
                "progress": 100,
                "filename": filename,
                "sections_found": results["sections_found"],
                "sections_missing": results["sections_missing"],
                "documents_created": results["documents_created"],
                "errors": results["errors"]
            })
            
            logging.info(f"=== COMPLETATO PROCESSING PACCHETTO ===")
            logging.info(f"Patient ID finale: {patient_id}")
            logging.info(f"Sezioni trovate: {results['sections_found']}")
            logging.info(f"Documenti creati: {len(results['documents_created'])}")
            
            return results
            
        except Exception as e:
            error_msg = f"Errore critico nel processing del pacchetto: {str(e)}"
            logging.exception(error_msg)
            results["errors"].append(error_msg)
            
            # Salva stato di errore
            self._save_packet_processing_status(patient_id, {
                "status": "failed",
                "message": error_msg,
                "progress": 100,
                "filename": filename,
                "errors": results["errors"]
            })
            
            # Cleanup in caso di errore
            try:
                temp_folder = os.path.join(self.upload_folder, patient_id, "temp_processing")
                if os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder)
                    logging.info(f"🧹 Cleanup cartella temp_processing dopo errore per {patient_id}")
            except Exception as cleanup_error:
                logging.warning(f"⚠️ Errore cleanup dopo errore: {cleanup_error}")
            
            return results

    def _save_ocr_text_file(self, patient_id: str, original_filename: str, ocr_text: str):
        """Salva il testo OCR completo come file standalone."""
        try:
            # Crea cartella per il testo OCR
            ocr_folder = os.path.join(self.upload_folder, patient_id, "ocr_text")
            os.makedirs(ocr_folder, exist_ok=True)
            
            # Nome file per il testo OCR
            base_name = os.path.splitext(original_filename)[0]
            ocr_filename = f"{base_name}_ocr_text.txt"
            ocr_path = os.path.join(ocr_folder, ocr_filename)
            
            # Salva il testo
            with open(ocr_path, "w", encoding="utf-8") as f:
                f.write(ocr_text)
            
            # Salva metadata
            meta_path = ocr_path + ".meta.json"
            meta = {
                "filename": ocr_filename,
                "original_filename": original_filename,
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "content_type": "ocr_text"
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Testo OCR salvato in: {ocr_path}")
            
        except Exception as e:
            logging.error(f"Errore salvataggio testo OCR: {e}")
    
    def _save_section_as_document(self, patient_id: str, doc_type: str, 
                                 section_filename: str, section_text: str, 
                                 original_pdf_path: str):
        """Salva una sezione come documento indipendente."""
        try:
            # Crea cartella per il tipo di documento
            doc_folder = os.path.join(self.upload_folder, patient_id, doc_type)
            os.makedirs(doc_folder, exist_ok=True)
            
            # Copia il PDF originale nella cartella della sezione
            pdf_path = os.path.join(doc_folder, section_filename)
            if os.path.abspath(original_pdf_path) != os.path.abspath(pdf_path):
                with open(original_pdf_path, "rb") as src, open(pdf_path, "wb") as dst:
                    dst.write(src.read())
                logging.info(f"PDF copiato in: {pdf_path}")
            
            # Salva il testo della sezione
            text_path = os.path.join(doc_folder, f"{os.path.splitext(section_filename)[0]}_section.txt")
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(section_text)
            logging.info(f"Testo sezione salvato in: {text_path}")
            
            # Salva metadata
            meta_path = pdf_path + ".meta.json"
            meta = {
                "filename": section_filename,
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "section_type": doc_type,
                "original_pdf": os.path.basename(original_pdf_path),
                "section_text_file": os.path.basename(text_path),
                "patient_id": patient_id,
                "processing_method": "unified_flow"
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            logging.info(f"Metadata salvato in: {meta_path}")
                
            logging.info(f"Sezione {doc_type} salvata come documento in: {pdf_path}")
            
        except Exception as e:
            logging.error(f"Errore salvataggio sezione {doc_type}: {e}")
            raise
    
    def _save_packet_processing_status(self, patient_id: str, status_data: dict):
        """Salva lo stato del processing del pacchetto."""
        try:
            # Salva in entrambi i formati per compatibilità
            # 1. Formato nuovo (temp_processing)
            status_folder = os.path.join(self.upload_folder, patient_id, "temp_processing")
            os.makedirs(status_folder, exist_ok=True)
            
            status_path = os.path.join(status_folder, "processing_status.json")
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            
            # 2. Salva anche nella cartella principale del paziente per accesso persistente
            main_status_path = os.path.join(self.upload_folder, patient_id, "processing_status.json")
            with open(main_status_path, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
            # 3. Formato ProgressStore (packet_ocr) per compatibilità
            progress_store = ProgressStore(self.upload_folder)
            progress_data = {
                "pending_id": patient_id,
                "stage": status_data.get("status", "processing"),
                "percent": status_data.get("progress", 0),
                "message": status_data.get("message", ""),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "extra": status_data
            }
            progress_store.update(patient_id, progress_data["stage"], progress_data["percent"], 
                                progress_data["message"], progress_data["extra"])
                
            logging.info(f"Stato processing salvato in entrambi i formati per {patient_id}")
            
        except Exception as e:
            logging.error(f"Errore salvataggio stato processing: {e}")
    
    def _save_processing_error(self, patient_id: str, document_type: str, error_message: str):
        """Salva informazioni sull'errore di processing per debug."""
        try:
            error_folder = os.path.join(self.upload_folder, patient_id, "errors")
            os.makedirs(error_folder, exist_ok=True)
            
            error_path = os.path.join(error_folder, f"{document_type}_error.json")
            error_data = {
                "document_type": document_type,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(error_path, "w", encoding="utf-8") as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Errore salvato per debug: {error_path}")
        except Exception as e:
            logging.error(f"Impossibile salvare errore: {e}")


    def update_entities_for_document(
        self,
        patient_id: str,
        document_type: str,
        filename: str,
        updated_entities: dict = None,
        preview: bool = False
    ) -> dict | list:
        path = os.path.join(self.upload_folder, patient_id, document_type, "entities.json")
        if preview or not updated_entities:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        with open(path, "w", encoding="utf-8") as f:
            json.dump(updated_entities, f, indent=2, ensure_ascii=False)
        return {"status": "updated"}

    def update_document_entities(self, document_id: str, entities: dict) -> bool:
        return self.file_manager.update_document_entities(document_id, entities)

    def list_existing_patients(self) -> list:
        return self.file_manager.get_patients_summary()

    def get_patient_detail(self, patient_id: str) -> dict:
        return self.file_manager.get_patient_detail(patient_id)

    def get_document_detail(self, document_id: str) -> dict:
        return self.file_manager.get_document_detail(document_id)

    def delete_document(self, document_id: str) -> dict:
        return self.file_manager.delete_document(document_id)
