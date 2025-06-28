import os
import json
from llm import get_response_from_document

# Per ora la simulazione è sincrona per test locale (consigliato da GPT boh)
import asyncio

UPLOAD_FOLDER = "uploads"
MODEL_NAME = "your-model-name"


def process_document_and_entities(filepath: str, patient_id: str, document_type: str) -> dict:
    # solo testo (GPT)
    with open(filepath, "r") as f:
        document_text = f.read()

    # Chiama il modello LLM
    response_json_str = asyncio.run(
        get_response_from_document(document_text, document_type, model=MODEL_NAME)
    )

    try:
        entities = json.loads(response_json_str)
    except json.JSONDecodeError:
        entities = []

    # Salva il JSON per futura modifica
    output_path = os.path.join(UPLOAD_FOLDER, patient_id, document_type, "entities.json")
    with open(output_path, "w") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)

    return {"entities": entities}


#la logica è OK
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
    # Da implementare nel modulo excel_manager.py
    path = "export/output.xlsx"
    return path
