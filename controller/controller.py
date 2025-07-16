import os
import json
import pdfplumber
from llm import get_response_from_document
import numpy as np
import pandas as pd

from utils.excel_manager import update_excel, export_excel_file
from utils.file_manager import (
    remove_patient_folder_if_exists,
    save_entities_json,
    read_existing_entities,
    list_existing_patients
)

UPLOAD_FOLDER = "uploads"
EXPORT_PATH = "export/output.xlsx"
MODEL_NAME = "deepseek-ai/DeepSeek-V3"
SHEET_ENTITIES = {
    "lettera_dimissione": [
        "n_cartella",
        "data_ingresso_cch",
        "data_dimissione_cch",
        "nome",
        "cognome",
        "sesso",
        "numero di telefono",
        "età al momento dell'intervento",
        "data_di_nascita",
        "Diagnosi",
        "Anamnesi",
        "Motivo ricovero",
        "classe_nyha",
        "angor",
        "STEMI/NSTEMI",
        "scompenso_cardiaco_nei_3_mesi_precedenti",
        "fumo",
        "diabete",
        "ipertensione",
        "dislipidemia",
        "BPCO",
        "stroke_pregresso",
        "TIA_pregresso",
        "vasculopatiaperif",
        "neoplasia_pregressa",
        "irradiazionetoracica",
        "insufficienza_renale_cronica",
        "familiarita_cardiovascolare",
        "limitazione_mobilita",
        "endocardite",
        "ritmo_all_ingresso",
        "fibrillazione_atriale",
        "dialisi",
        "elettivo_urgenza_emergenza",
        "pm",
        "crt",
        "icd",
        "pci_pregressa",
        "REDO",
        "Anno REDO",
        "Tipo di REDO",
        "Terapia",
        "lasix",
        "lasix_dosaggio",
        "nitrati",
        "antiaggregante",
        "dapt",
        "anticoagorali",
        "aceinib",
        "betabloc",
        "sartanici",
        "caantag",
        "esami_all_ingresso",
        "Decorso_post_operatorio",
        "IABP/ECMO/IMPELLA",
        "Inotropi",
        "secondo_intervento",
        "Tipo_secondo_intervento",
        "II_Run",
        "Causa_II_Run_CEC",
        "LCOS",
        "Impianto_PM_post_intervento",
        "Stroke_TIA_post_op",
        "Necessità_di_trasfusioni",
        "IRA",
        "Insufficienza_respiratoria",
        "FA_di_nuova_insorgenza",
        "Ritmo_alla_dimissione",
        "H_Stay_giorni (da intervento a dimissione)",
        "Morte",
        "Causa_morte",
        "data_morte",
        "esami_alla_dimissione",
        "terapia_alla_dimissione"
    ],
    "coronarografia": [
        "n_cartella",
        "nome",
        "cognome",
        "data_di_nascita",
        "data_esame",
        "coronarografia text",
        "coro_tc_stenosi50",
        "coro_iva_stenosi50",
        "coro_cx_stenosi50",
        "coro_mo1_stenosi50",
        "coro_mo2_stenosi50",
        "coro_mo3_stenosi50",
        "coro_int_stenosi50",
        "coro_plcx_stenosi50",
        "coro_dx_stenosi50",
        "coro_pl_stenosi50",
        "coro_ivp_stenosi50"
    ],
    "intervento": [
        "n_cartella",
        "data_intervento",
        "intervento text",
        "primo operatore",
        "redo",
        "cec",
        "cannulazionearteriosa",
        "statopaz",
        "cardioplegia",
        "approcciochirurgico",
        "entratainsala",
        "iniziointervento",
        "iniziocec",
        "inizioclamp",
        "inizioacc",
        "fineacc",
        "fineclamp",
        "finecec",
        "fineintervento",
        "uscitasala",
        "intervento",
        "protesi",
        "modello",
        "numero"
    ]
}



def get_text_to_remove(all_tables):
    text_to_remove = []
    for table in all_tables:
        table_np = np.array(table)
        text_to_remove.extend([
            str(" ".join(row)).replace(" ", "").replace("\n", "") for row in table_np
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

# Estrae il testo e le tabelle da un PDF, rimuove le tabelle dal testo, invia il testo a un LLM per estrarre entità.
# Verifica le entità estratte contro i dati anagrafici forniti (se presenti).
# Se il controllo va a buon fine, salva le entità in entities.json e aggiorna l'excel con i dati del paziente.
def process_document_and_entities(filepath: str, patient_id: str, document_type: str, provided_anagraphic=None) -> dict:
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

    estratti = {e["entità"]: e["valore"] for e in entities if isinstance(e, dict)}
    numero_cartella = estratti.get("n_cartella")
    nome = estratti.get("nome")
    cognome = estratti.get("cognome")
    data_nascita = estratti.get("data_di_nascita")

    if provided_anagraphic:
        if numero_cartella and provided_anagraphic.get("n_cartella") and str(numero_cartella) != str(provided_anagraphic.get("n_cartella")):
            os.remove(filepath)
            remove_patient_folder_if_exists(patient_id)
            return {"error": "Mismatch tra numero_cartella fornito e nel documento."}, 400
        for key in ["nome", "cognome", "data_di_nascita"]:
            if provided_anagraphic.get(key) and estratti.get(key) and str(estratti.get(key)) != str(provided_anagraphic.get(key)):
                os.remove(filepath)
                remove_patient_folder_if_exists(patient_id)
                return {"error": f"Mismatch tra {key} fornito e nel documento."}, 400
    else:
        if not numero_cartella:
            os.remove(filepath)
            remove_patient_folder_if_exists(patient_id)
            return {"error": "Numero cartella mancante e non fornito."}, 400

    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id)
    document_folder = os.path.join(patient_folder, document_type)
    os.makedirs(document_folder, exist_ok=True)
    output_path = os.path.join(document_folder, "entities.json")
    with open(output_path, "w") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)

    update_excel(patient_id, document_type, estratti)

    return {"entities": entities}


# Permette di aggiornare manualmente il file entities.json di un paziente o di visualizzarne un'anteprima.
# Se updated_entities è None o preview è True, restituisce il contenuto esistente.
# Altrimenti sovrascrive entities.json con gli updated_entities forniti.
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


def list_existing_patients():
    patients = []
    if os.path.exists(UPLOAD_FOLDER):
        for patient_id in os.listdir(UPLOAD_FOLDER):
            patient_path = os.path.join(UPLOAD_FOLDER, patient_id)
            if os.path.isdir(patient_path):
                patients.append(patient_id)
    return {"patients": patients}
