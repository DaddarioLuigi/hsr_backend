import os
import json
import shutil


UPLOAD_FOLDER = "uploads"


def remove_patient_folder_if_exists(patient_id: str):
    folder_path = os.path.join(UPLOAD_FOLDER, patient_id)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)


def save_entities_json(patient_id: str, document_type: str, entities: list):
    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id)
    document_folder = os.path.join(patient_folder, document_type)
    os.makedirs(document_folder, exist_ok=True)
    output_path = os.path.join(document_folder, "entities.json")
    with open(output_path, "w") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)


def read_existing_entities(patient_id: str, document_type: str):
    json_path = os.path.join(UPLOAD_FOLDER, patient_id, document_type, "entities.json")
    if os.path.exists(json_path):
        with open(json_path) as f:
            return json.load(f)
    return []


def list_existing_patients():
    patients = []
    if os.path.exists(UPLOAD_FOLDER):
        for patient_id in os.listdir(UPLOAD_FOLDER):
            patient_path = os.path.join(UPLOAD_FOLDER, patient_id)
            if os.path.isdir(patient_path):
                patients.append(patient_id)
    return patients
