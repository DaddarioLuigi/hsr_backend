import os
import json
import pdfplumber
import numpy as np
import logging
from llm.extractor import LLMExtractor
from utils.excel_manager import ExcelManager
from utils.file_manager import FileManager
from utils.entity_extractor import EntityExtractor
from llm.prompts import PromptManager
from utils.table_parser import TableParser
from pipelines.ingestion import ClinicalPacketIngestion
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

        # 4. Parsifica risposta
        extractor = EntityExtractor(explicit_keys)
        entities = extractor.parse_llm_response(response_str, text)

        # 5. Sovrascrivi anagrafica se fornita
        if provided_anagraphic:
            for key in ("n_cartella", "nome", "cognome"):
                if provided_anagraphic.get(key):
                    entities[key] = provided_anagraphic[key]

        # 6. Controlli obbligatori
        if document_type == "lettera_dimissione" and provided_anagraphic:
            for key in ("n_cartella", "nome", "cognome", "data_di_nascita"):
                prov = provided_anagraphic.get(key)
                ext = entities.get(key)
                if prov and ext and str(prov) != str(ext):
                    os.remove(filepath)
                    self.file_manager.remove_patient_folder_if_exists(patient_id)
                    return {"error": f"Mismatch tra {key} fornito e documento."}, 400

        if document_type in ("lettera_dimissione", "eco_preoperatorio"):
            if not entities.get("n_cartella"):
                os.remove(filepath)
                self.file_manager.remove_patient_folder_if_exists(patient_id)
                return {"error": f"Numero di cartella mancante per {document_type}."}, 400

        # 7. Salva JSON in upload_folder configurata
        output_dir = os.path.join(self.file_manager.UPLOAD_FOLDER, patient_id, document_type)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "entities.json")
        # usa FileManager per salvare anche su Drive
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

    def _extract_patient_id_from_ocr(self, ocr_text: str) -> str | None:
        """
        Estrae il numero di cartella clinica dal testo OCR.
        Cerca pattern comuni per identificare l'ID paziente.
        """
        import re
        
        # Pattern comuni per numero cartella clinica
        patterns = [
            r'numero\s+cartella\s*:?\s*(\d+)',
            r'cartella\s+n[°º]?\s*:?\s*(\d+)',
            r'n[°º]?\s*cartella\s*:?\s*(\d+)',
            r'paziente\s+n[°º]?\s*:?\s*(\d+)',
            r'id\s+paziente\s*:?\s*(\d+)',
            r'(\d{4,})',  # Pattern generico per numeri di 4+ cifre
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, ocr_text, re.IGNORECASE)
            if matches:
                # Prendi il primo match che sembra un numero di cartella
                for match in matches:
                    if len(match) >= 4:  # Numero di cartella tipicamente 4+ cifre
                        return match
        
        return None

    def process_single_document_as_packet(self, filepath: str, patient_id: str, filename: str) -> dict:
        """
        Flusso unificato: tratta un singolo PDF come pacchetto clinico da segmentare.
        Ogni sezione viene gestita come documento indipendente con la stessa struttura
        dei singoli documenti.
        
        Args:
            filepath: percorso del PDF caricato
            patient_id: ID paziente (può essere pending)
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
        
        try:
            # 1. OCR del PDF
            logging.info(f"Avvio OCR per {filename}")
            
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
            
            # 1b. Estrai ID paziente dal testo OCR se non fornito
            final_patient_id = patient_id
            if patient_id.startswith("_pending_"):
                extracted_id = self._extract_patient_id_from_ocr(full_md)
                if extracted_id:
                    final_patient_id = extracted_id
                    results["patient_id"] = extracted_id
                    logging.info(f"ID paziente estratto dal testo: {extracted_id}")
                else:
                    logging.warning("Impossibile estrarre ID paziente dal testo OCR")
            
            # Salva il testo OCR completo come file standalone
            self._save_ocr_text_file(final_patient_id, filename, full_md)
            
            # 2. Segmentazione
            logging.info(f"Avvio segmentazione per {filename}")
            
            self._save_packet_processing_status(final_patient_id, {
                "status": "segmenting",
                "message": "Segmentazione in corso",
                "progress": 30,
                "filename": filename,
                "sections_found": [],
                "sections_missing": [],
                "documents_created": [],
                "errors": []
            })
            
            sections = find_document_sections(full_md)
            
            if not sections:
                results["errors"].append("Nessuna sezione identificata nel documento")
                self._save_packet_processing_status(final_patient_id, {
                    "status": "failed",
                    "message": "Nessuna sezione identificata nel documento",
                    "progress": 100,
                    "filename": filename,
                    "errors": results["errors"]
                })
                return results
            
            # 3. Processa ogni sezione come documento indipendente
            found_types = set()
            total_sections = len([s for s in sections if s.doc_type != "altro" and s.text.strip()])
            processed_sections = 0
            
            for section in sections:
                doc_type = normalize_doc_type(section.doc_type)
                section_text = section.text.strip()
                
                if not section_text or doc_type == "altro":
                    continue
                    
                found_types.add(doc_type)
                results["sections_found"].append(doc_type)
                processed_sections += 1
                
                # Aggiorna stato con progresso
                progress = 30 + int(60 * processed_sections / max(1, total_sections))
                self._save_packet_processing_status(final_patient_id, {
                    "status": "processing_sections",
                    "message": f"Elaborazione sezione {processed_sections}/{total_sections}: {doc_type}",
                    "progress": progress,
                    "filename": filename,
                    "sections_found": results["sections_found"],
                    "sections_missing": [],
                    "documents_created": results["documents_created"],
                    "errors": results["errors"]
                })
                
                # Crea struttura cartelle come per singoli documenti
                section_filename = f"{os.path.splitext(filename)[0]}_{doc_type}.pdf"
                
                try:
                    # Salva sezione come "documento indipendente"
                    self._save_section_as_document(
                        final_patient_id, doc_type, section_filename, 
                        section_text, filepath
                    )
                    
                    # Estrai entità usando il prompt dedicato
                    entities = self._extract_entities_for_section(
                        section_text, doc_type
                    )
                    
                    # Salva entità
                    self.file_manager.save_entities_json(final_patient_id, doc_type, entities)
                    self.excel_manager.update_excel(final_patient_id, doc_type, entities)
                    
                    # Crea document_id per la dashboard
                    document_id = f"doc_{final_patient_id}_{doc_type}_{os.path.splitext(section_filename)[0]}"
                    
                    results["documents_created"].append({
                        "document_id": document_id,
                        "document_type": doc_type,
                        "filename": section_filename,
                        "status": "processed",
                        "entities_count": len(entities) if isinstance(entities, dict) else 0
                    })
                    
                    logging.info(f"Sezione {doc_type} processata con successo")
                    
                except Exception as e:
                    error_msg = f"Errore processing sezione {doc_type}: {str(e)}"
                    results["errors"].append(error_msg)
                    logging.error(error_msg)
            
            # 4. Identifica sezioni mancanti
            missing_types = SUPPORTED_TYPES - found_types
            results["sections_missing"] = list(missing_types)
            
            if missing_types:
                logging.warning(f"Sezioni mancanti per {filename}: {missing_types}")
            
            # 5. PULIZIA: Rimuovi cartella temp_processing dopo il successo
            try:
                temp_folder = os.path.join(self.upload_folder, final_patient_id, "temp_processing")
                if os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder)
                    logging.info(f"Cartella temp_processing rimossa per {final_patient_id}")
            except Exception as e:
                logging.warning(f"Errore rimozione temp_processing: {e}")
            
            # Salva stato finale
            final_status = "completed" if not results["errors"] else "completed_with_errors"
            self._save_packet_processing_status(final_patient_id, {
                "status": final_status,
                "message": f"Elaborazione completata. Sezioni trovate: {len(results['sections_found'])}, mancanti: {len(results['sections_missing'])}",
                "progress": 100,
                "filename": filename,
                "sections_found": results["sections_found"],
                "sections_missing": results["sections_missing"],
                "documents_created": results["documents_created"],
                "errors": results["errors"]
            })
            
            return results
            
        except Exception as e:
            error_msg = f"Errore generale nel processing: {str(e)}"
            results["errors"].append(error_msg)
            logging.exception(error_msg)
            
            # Salva stato di errore
            self._save_packet_processing_status(final_patient_id, {
                "status": "failed",
                "message": error_msg,
                "progress": 100,
                "filename": filename,
                "errors": results["errors"]
            })
            
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
            
            # Salva il testo della sezione
            text_path = os.path.join(doc_folder, f"{os.path.splitext(section_filename)[0]}_section.txt")
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(section_text)
            
            # Salva metadata
            meta_path = pdf_path + ".meta.json"
            meta = {
                "filename": section_filename,
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "section_type": doc_type,
                "original_pdf": os.path.basename(original_pdf_path),
                "section_text_file": os.path.basename(text_path)
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Sezione {doc_type} salvata come documento in: {pdf_path}")
            
        except Exception as e:
            logging.error(f"Errore salvataggio sezione {doc_type}: {e}")
            raise
    
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
    
    def _save_packet_processing_status(self, patient_id: str, status_data: dict):
        """Salva lo stato del processing del pacchetto."""
        try:
            status_folder = os.path.join(self.upload_folder, patient_id, "temp_processing")
            os.makedirs(status_folder, exist_ok=True)
            
            status_path = os.path.join(status_folder, "processing_status.json")
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Stato processing salvato in: {status_path}")
            
        except Exception as e:
            logging.error(f"Errore salvataggio stato processing: {e}")


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
