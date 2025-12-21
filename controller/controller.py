import os
import json
import pdfplumber
import numpy as np
import logging
import time
from llm.extractor import LLMExtractor, logger
from utils.excel_manager import ExcelManager
from utils.file_manager import FileManager
from utils.entity_extractor import EntityExtractor
from llm.prompts import PromptManager
from utils.table_parser import TableParser
from utils.progress import ProgressStore
from utils.metadata_coherence_manager import MetadataCoherenceManager
from utils.pdf_position_extractor import PDFPositionExtractor

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
        provided_anagraphic: dict = None,
        text: str = None
    ) -> dict:
        try:
            # 1. Estrai testo se non fornito
            #TO DO non credo serva perchè se non lo ha estratto vuol dire che c'è stato un errore nel caricamento del documento
            if text is None:
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
        logger.debug(f"RISPOSTA: {response_str}")
        extractor = EntityExtractor(explicit_keys)
        entities = extractor.parse_llm_response(response_str, text)

        # 5. Sovrascrivi anagrafica se fornita
        if provided_anagraphic:
            for key in ("n_cartella", "nome", "cognome"):
                if provided_anagraphic.get(key):
                    entities[key] = provided_anagraphic[key]

        # 5.5 Estrai posizioni delle entità dal PDF
        try:
            position_extractor = PDFPositionExtractor(filepath)
            entities_with_positions = position_extractor.extract_entities_positions(entities)
            # Converte il formato per mantenere compatibilità con il resto del codice
            entities_for_save = {}
            for key, data in entities_with_positions.items():
                if isinstance(data, dict) and "value" in data:
                    entities_for_save[key] = data["value"]
                else:
                    entities_for_save[key] = data
                # Salva anche le posizioni in un file separato per non rompere la compatibilità
                positions_data = {
                    key: data.get("positions") if isinstance(data, dict) else None
                    for key, data in entities_with_positions.items()
                }
        except Exception as e:
            logging.warning(f"Errore durante l'estrazione delle posizioni: {e}")
            entities_for_save = entities
            positions_data = {}

        # 6. Verifica coerenza dei metadati
        coherence_result = self.coherence_manager.check_document_coherence(patient_id, document_type, entities_for_save)
        
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
            if not entities_for_save.get("n_cartella"):
                os.remove(filepath)
                self.file_manager.remove_patient_folder_if_exists(patient_id)
                return {"error": f"Numero di cartella mancante per {document_type}."}, 400

        # 8. Salva JSON in upload_folder configurata
        output_dir = os.path.join(self.file_manager.UPLOAD_FOLDER, patient_id, document_type)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "entities.json")
        # usa FileManager per salvare i dati
        self.file_manager.save_entities_json(patient_id, document_type, entities_for_save)
        
        # Salva anche le posizioni nel file entities.json come metadata
        entities_with_metadata = {
            "entities": entities_for_save,
            "positions": positions_data
        }
        metadata_path = os.path.join(output_dir, "entities_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(entities_with_metadata, f, indent=2, ensure_ascii=False)

        # Aggiorna anche l'Excel dinamico
        self.excel_manager.update_excel(patient_id, document_type, entities_for_save)

        return entities_for_save


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

    def get_available_document_types(self) -> list:
        """
        Restituisce la lista dei tipi di documento disponibili (escluso "altro").
        Questi sono i tipi che hanno un prompt definito e possono essere usati per l'estrazione.
        """
        # Ottieni tutti i tipi con prompt definito
        available_types = []
        for doc_type in self.prompt_manager.SCHEMAS.keys():
            if doc_type != "altro":  # Escludi "altro" che non ha prompt
                available_types.append(doc_type)
        
        # Ordina per mantenere un ordine consistente
        return sorted(available_types)

    def change_document_type_and_reprocess(
        self,
        document_id: str,
        new_document_type: str
    ) -> dict:
        """
        Cambia il tipo di documento da "altro" a un nuovo tipo e riavvia il processing.
        
        Args:
            document_id: ID del documento di tipo "altro"
            new_document_type: Nuovo tipo di documento
        
        Returns:
            dict con il risultato dell'operazione
        """
        # Cambia il tipo del documento (sposta i file)
        result = self.file_manager.change_document_type(document_id, new_document_type)
        
        if not result.get("success"):
            return result
        
        # Estrai informazioni per il riprocessamento
        new_document_id = result["new_document_id"]
        patient_id = result["patient_id"]
        filepath = result["new_path"]
        
        # Leggi anagrafica esistente se disponibile
        provided_anagraphic = None
        if new_document_type != "lettera_dimissione":
            provided_anagraphic = self.file_manager.read_existing_entities(
                patient_id, "lettera_dimissione"
            )
        
        # Avvia processing in background
        from threading import Thread
        
        def process_with_error_logging():
            try:
                self.process_document_and_entities(
                    filepath, patient_id, new_document_type, provided_anagraphic
                )
            except Exception as e:
                logging.exception(f"Errore critico nel processing di {filepath}: {e}")
        
        Thread(target=process_with_error_logging, daemon=True).start()
        
        return {
            "success": True,
            "message": f"Tipo documento cambiato da 'altro' a '{new_document_type}'. Processing avviato.",
            "old_document_id": document_id,
            "new_document_id": new_document_id,
            "patient_id": patient_id,
            "old_document_type": "altro",
            "new_document_type": new_document_type,
            "status": "processing"
        }

    def re_extract_entities(
        self,
        document_id: str,
        extraction_document_type: str = None
    ) -> dict:
        """
        Rilancia l'estrazione delle entità da un documento già processato.
        Permette di scegliere quale prompt usare per l'estrazione.
        L'estrazione viene avviata in background.
        
        Args:
            document_id: ID del documento esistente
            extraction_document_type: Tipo di documento per l'estrazione (prompt da usare).
                                     Se None, usa il tipo del documento esistente.
        
        Returns:
            dict con il risultato dell'operazione (ritorna immediatamente, processing in background)
        """
        # Ottieni i dettagli del documento per trovare il filepath
        document_detail = self.file_manager.get_document_detail(document_id)
        
        if not document_detail:
            return {"success": False, "error": "Documento non trovato"}
        
        # Estrai informazioni dal document_detail
        patient_id = document_detail["patient_id"]
        current_document_type = document_detail["document_type"]
        pdf_path = document_detail["pdf_path"]
        
        # Rimuovi il prefisso "/uploads/" se presente per ottenere il percorso relativo
        if pdf_path.startswith("/uploads/"):
            relative_path = pdf_path[len("/uploads/"):]
        else:
            relative_path = pdf_path
        
        # Costruisci il percorso assoluto del PDF
        filepath = os.path.join(self.file_manager.UPLOAD_FOLDER, relative_path)
        
        if not os.path.exists(filepath):
            return {"success": False, "error": "File PDF non trovato"}
        
        # Usa il tipo specificato o quello esistente
        extraction_type = extraction_document_type or current_document_type
        
        # Verifica che il tipo di estrazione sia valido
        try:
            self.prompt_manager.get_prompt_for(extraction_type)
        except ValueError as e:
            return {"success": False, "error": f"Tipo documento '{extraction_type}' non supportato: {str(e)}"}
        
        # Avvia processing in background
        from threading import Thread
        
        def process_in_background():
            try:
                # Leggi anagrafica esistente se disponibile (solo se non è lettera_dimissione)
                provided_anagraphic = None
                if extraction_type != "lettera_dimissione":
                    provided_anagraphic = self.file_manager.read_existing_entities(
                        patient_id, "lettera_dimissione"
                    )
                
                # Esegui l'estrazione (usando il tipo specificato per il prompt)
                entities_result = self.process_document_and_entities(
                    filepath,
                    patient_id,
                    extraction_type,  # Usa il tipo specificato per il prompt
                    provided_anagraphic
                )
                
                # Se il risultato è una tupla con codice di errore, gestiscilo
                if isinstance(entities_result, tuple):
                    logging.error(f"Errore durante estrazione: {entities_result[0].get('error')}")
                    return
                
                # Se il tipo di estrazione è diverso dal tipo originale, sposta le entità nella cartella originale
                if extraction_type != current_document_type:
                    # Salva le entità nella cartella del documento originale (sovrascrivendo quelle esistenti)
                    self.file_manager.save_entities_json(patient_id, current_document_type, entities_result)
                    
                    # Aggiorna anche l'Excel con il tipo originale
                    self.excel_manager.update_excel(patient_id, current_document_type, entities_result)
                    
                    # Rimuovi le entità salvate nella cartella del tipo di estrazione (se diversa)
                    extraction_dir = os.path.join(self.file_manager.UPLOAD_FOLDER, patient_id, extraction_type)
                    extraction_entities_path = os.path.join(extraction_dir, "entities.json")
                    if os.path.exists(extraction_entities_path) and extraction_dir != os.path.join(self.file_manager.UPLOAD_FOLDER, patient_id, current_document_type):
                        try:
                            os.remove(extraction_entities_path)
                        except Exception as e:
                            logging.warning(f"Impossibile rimuovere entities.json dalla cartella {extraction_type}: {e}")
                
            except Exception as e:
                logging.exception(f"Errore durante la ri-estrazione in background di {document_id}: {e}")
        
        # Avvia il thread in background
        Thread(target=process_in_background, daemon=True).start()
        
        # Ritorna immediatamente
        return {
            "success": True,
            "message": f"Estrazione avviata con prompt '{extraction_type}' in background",
            "document_id": document_id,
            "patient_id": patient_id,
            "extraction_document_type": extraction_type,
            "original_document_type": current_document_type,
            "status": "processing"
        }
