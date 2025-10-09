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
        
        # Validazione patient_id
        if not patient_id:
            return False, "Patient ID obbligatorio", []
        
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
