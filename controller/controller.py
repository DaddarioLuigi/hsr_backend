import os
import json
import pdfplumber
from llm import get_response_from_document
import asyncio
import numpy as np

# Per ora la simulazione è sincrona per test locale (consigliato da GPT boh)
import asyncio

UPLOAD_FOLDER = "uploads"
MODEL_NAME = "deepseek-ai/DeepSeek-V3"

def get_text_to_remove(all_tables):
    text_to_remove = []
    if len(all_tables) > 1:
        for table in all_tables:
            table_np = np.array(table)
            text_to_remove.extend([
                str(" ".join(row)).replace(" ", "").replace("\n", "") for row in table_np
            ])
    else:
        all_tables_np = np.array(all_tables)
        all_tables_flat = all_tables_np.reshape(-1, all_tables_np.shape[-1])
        text_to_remove.extend([
            str(" ".join(row)).replace(" ", "").replace("\n", "") for row in all_tables_flat
        ])
    return text_to_remove

def remove_tables(all_text, text_to_remove):
    clean_text = all_text
    for row in clean_text.split('\n'):
        row_ = row.replace(" ", "").replace("\n", "")
        if row_ in text_to_remove:
            clean_text = clean_text.replace(row + '\n', '')
    return clean_text

def get_cleaned_text(all_text, all_tables):
    if len(all_tables) > 0:
        text_to_remove = get_text_to_remove(all_tables)
        cleaned_text = remove_tables(all_text, text_to_remove)
    else:
        cleaned_text = all_text
    return cleaned_text

def process_document_and_entities(filepath: str, patient_id: str, document_type: str) -> dict:
    with pdfplumber.open(filepath) as pdf:
        all_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)

    document_text = get_cleaned_text(all_text, all_tables)

    response_json_str = get_response_from_document(document_text, document_type, model=MODEL_NAME)

    try:
        entities = json.loads(response_json_str)
    except json.JSONDecodeError:
        entities = []

    # Validazione coerenza tra patient_id e entità
    estratti = {e["entità"]: e["valore"] for e in entities if isinstance(e, dict)}

    numero_cartella = estratti.get("n_cartella")
    nome = estratti.get("nome")
    cognome = estratti.get("cognome")
    data_nascita = estratti.get("data_di_nascita")

    if numero_cartella:
        if str(numero_cartella) != str(patient_id):
            return {"error": "Il numero cartella nel documento non corrisponde al patient_id fornito."}, 400
    elif nome and cognome and data_nascita:
        match_found = False
        for pid in os.listdir(UPLOAD_FOLDER):
            json_path = os.path.join(UPLOAD_FOLDER, pid, document_type, "entities.json")
            if os.path.exists(json_path):
                with open(json_path) as f:
                    previous = json.load(f)
                    p = {e["entità"]: e["valore"] for e in previous if isinstance(e, dict)}
                    if (
                        p.get("n_cartella") == str(patient_id)
                        and p.get("nome") == nome
                        and p.get("cognome") == cognome
                        and p.get("data_di_nascita") == data_nascita
                    ):
                        match_found = True
                        break
        if not match_found:
            return {"error": "I dati anagrafici non corrispondono ad alcuna cartella clinica esistente."}, 400

    # Salva le entità in un file JSON
    output_path = os.path.join(UPLOAD_FOLDER, patient_id, document_type, "entities.json")
    with open(output_path, "w") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)

    return {"entities": entities}

def update_entities_for_document(patient_id: str, document_type: str, filename: str, updated_entities=None, preview=False):
    path = os.path.join(UPLOAD_FOLDER, patient_id, document_type, "entities.json")
    if preview or not updated_entities:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return []

    with open(path, "w") as f:
        json.dump(updated_entities, f, indent=2, ensure_ascii=False)

    return {"status": "updated"}

def export_excel_file():
    path = "export/output.xlsx"
    return path

def list_existing_patients():
    patients = []
    if os.path.exists(UPLOAD_FOLDER):
        for patient_id in os.listdir(UPLOAD_FOLDER):
            patient_path = os.path.join(UPLOAD_FOLDER, patient_id)
            if os.path.isdir(patient_path):
                patients.append(patient_id)
    return {"patients": patients}
