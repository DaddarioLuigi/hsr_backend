import os
import json
import pdfplumber
import numpy as np
from llm.extractor import LLMExtractor
from utils.excel_manager import ExcelManager
from utils.file_manager import FileManager

class DocumentController:
    def __init__(self, model_name="deepseek-ai/DeepSeek-V3"):
        self.model_name = model_name
        self.llm = LLMExtractor()
        self.excel_manager = ExcelManager()
        self.file_manager = FileManager()
        self.upload_folder = "uploads"

    def get_text_to_remove(self, all_tables):
        text_to_remove = []
        for table in all_tables:
            table_np = np.array(table)
            text_to_remove.extend([
                str(" ".join(row)).replace(" ", "").replace("\n", "") for row in table_np
            ])
        return text_to_remove

    def remove_tables(self, all_text, text_to_remove):
        clean_text = all_text
        for row in clean_text.split('\n'):
            row_ = row.replace(" ", "").replace("\n", "")
            if row_ in text_to_remove:
                clean_text = clean_text.replace(row + '\n', '')
        return clean_text

    def get_cleaned_text(self, all_text, all_tables):
        if len(all_tables) > 0:
            text_to_remove = self.get_text_to_remove(all_tables)
            cleaned_text = self.remove_tables(all_text, text_to_remove)
        else:
            cleaned_text = all_text
        return cleaned_text

    def process_document_and_entities(
        self,
        filepath: str,
        patient_id: str,
        document_type: str,
        provided_anagraphic: dict = None
    ):
        """
        Estrae testo dal PDF, chiama l’LLM, valida mismatch e salva le entità
        """
        # 1. Estrai testo e pulisci
        with pdfplumber.open(filepath) as pdf:
            all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        cleaned_text = self.get_cleaned_text(all_text, [])

        # 2. Chiamata LLM per tutte le entità
        response_json_str = self.llm.get_response_from_document(
            cleaned_text, document_type, model=self.model_name
        )
        try:
            raw = json.loads(response_json_str)
            if isinstance(raw, dict):
                estratti = raw
            else:
                estratti = {e["entità"]: e["valore"] for e in raw if isinstance(e, dict)}
        except json.JSONDecodeError:
            estratti = {}

        # 3. Validazione mismatch con dati forniti dall’utente (se presenti)
        if provided_anagraphic:
            # controlliamo n_cartella, nome, cognome, data_di_nascita
            for key in ("n_cartella", "nome", "cognome", "data_di_nascita"):
                prov = provided_anagraphic.get(key)
                ext = estratti.get(key)
                if prov and ext and str(prov) != str(ext):
                    # rollback file + cartella paziente
                    os.remove(filepath)
                    self.file_manager.remove_patient_folder_if_exists(patient_id)
                    return {
                        "error": f"Mismatch tra {key} fornito e valore nel documento."
                    }, 400

        # 4. Controllo obbligatorietà per alcuni tipi di documento
        if document_type in ("lettera_dimissione", "eco_preoperatorio"):
            if not (estratti.get("n_cartella") or (provided_anagraphic or {}).get("n_cartella")):
                os.remove(filepath)
                self.file_manager.remove_patient_folder_if_exists(patient_id)
                return {
                    "error": f"Numero di cartella mancante per documento {document_type}."
                }, 400

        # 5. Salvo il JSON delle entità in un file dedicato
        filename_base = os.path.splitext(os.path.basename(filepath))[0]
        document_folder = os.path.join(self.upload_folder, patient_id, document_type)
        os.makedirs(document_folder, exist_ok=True)
        output_path = os.path.join(document_folder, f"entities.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(estratti, f, indent=2, ensure_ascii=False)

        # 6. Aggiorno il foglio Excel
        self.excel_manager.update_excel(patient_id, document_type, estratti)

        return {"entities": estratti}


    def update_entities_for_document(self, patient_id, document_type, filename, updated_entities=None, preview=False):
        path = os.path.join(self.upload_folder, patient_id, document_type, "entities.json")
        if preview or not updated_entities:
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
            return []

        with open(path, "w") as f:
            json.dump(updated_entities, f, indent=2, ensure_ascii=False)

        return {"status": "updated"}

    def update_document_entities(self, document_id, entities):
        return self.file_manager.update_document_entities(document_id, entities)

    def list_existing_patients(self):
        return self.file_manager.get_patients_summary()

    def get_patient_detail(self, patient_id):
        return self.file_manager.get_patient_detail(patient_id)

    def get_document_detail(self, document_id):
        return self.file_manager.get_document_detail(document_id)
