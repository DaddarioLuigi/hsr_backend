import os
import json
import pdfplumber
import numpy as np
from llm.extractor import LLMExtractor
from utils.excel_manager import ExcelManager
from utils.file_manager import FileManager
from utils.entity_extractor import EntityExtractor
from llm.prompts import PromptManager
from utils.table_parser import TableParser
from pipelines.ingestion import ClinicalPacketIngestion

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
