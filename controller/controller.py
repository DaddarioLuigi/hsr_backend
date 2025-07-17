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

    def process_document_and_entities(self, filepath, patient_id, document_type, provided_anagraphic=None):
        with pdfplumber.open(filepath) as pdf:
            document_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            print(document_text)
            response_json_str = self.llm.get_response_from_document(document_text, document_type, model=self.model_name)

        try:
            entities = json.loads(response_json_str)
            #print(entities)

            if isinstance(entities, dict):
                estratti = entities
            elif isinstance(entities, list):
                estratti = {e["entità"]: e["valore"] for e in entities if isinstance(e, dict)}
            else:
                estratti = {}

        except json.JSONDecodeError:
            estratti = {}

        numero_cartella = estratti.get("n_cartella")
        nome = estratti.get("nome")
        cognome = estratti.get("cognome")
        data_nascita = estratti.get("data_di_nascita")

        if provided_anagraphic:
            if numero_cartella and provided_anagraphic.get("n_cartella") and str(numero_cartella) != str(provided_anagraphic.get("n_cartella")):
                os.remove(filepath)
                self.file_manager.remove_patient_folder_if_exists(patient_id)
                return {"error": "Mismatch tra numero_cartella fornito e nel documento."}, 400
            for key in ["nome", "cognome", "data_di_nascita"]:
                if provided_anagraphic.get(key) and estratti.get(key) and str(estratti.get(key)) != str(provided_anagraphic.get(key)):
                    os.remove(filepath)
                    self.file_manager.remove_patient_folder_if_exists(patient_id)
                    return {"error": f"Mismatch tra {key} fornito e nel documento."}, 400
        else:
            if document_type in ["lettera_dimissione", "eco_preoperatorio"] and not numero_cartella:
                os.remove(filepath)
                self.file_manager.remove_patient_folder_if_exists(patient_id)
                return {"error": "Numero cartella mancante e non fornito."}, 400

        patient_folder = os.path.join(self.upload_folder, patient_id)
        document_folder = os.path.join(patient_folder, document_type)
        os.makedirs(document_folder, exist_ok=True)

        output_path = os.path.join(document_folder, "entities.json")
        with open(output_path, "w") as f:
            json.dump(estratti, f, indent=2, ensure_ascii=False)

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
