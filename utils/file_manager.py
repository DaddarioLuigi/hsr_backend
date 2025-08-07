import os
import json
import shutil
import re
import logging
from datetime import datetime

from .drive_uploader import (
    upload_to_drive,
    ensure_folder,
    download_from_drive,
)

class FileManager:

    #UPLOAD_FOLDER = "uploads"
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

    def __init__(self):
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
    
    def save_file(self, patient_id: str, document_type: str, filename: str, file_stream) -> str:
        # 1) crea cartella locale
        folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
        os.makedirs(folder, exist_ok=True)

        # 2) scrivi su disco
        filepath = os.path.join(folder, filename)
        with open(filepath, "wb") as f:
            f.write(file_stream.read())

        # 3) metadati
        meta = {"filename": filename, "upload_date": datetime.now().strftime("%Y-%m-%d")}
        meta_path = filepath + ".meta.json"
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, indent=2, ensure_ascii=False)

        # 4) upload su Drive
        drive_root_id = os.getenv("DRIVE_FOLDER_ID")
        if drive_root_id:
            try:
                patient_folder_id = ensure_folder(patient_id, drive_root_id)
                doc_folder_id = ensure_folder(document_type, patient_folder_id)
                # Upload PDF
                pdf_meta = upload_to_drive(filepath, doc_folder_id)
                with open(filepath + ".drive.json", "w", encoding="utf-8") as md:
                    json.dump(pdf_meta, md, indent=2, ensure_ascii=False)
                # Upload meta.json
                meta_drive = upload_to_drive(meta_path, doc_folder_id)
                with open(meta_path + ".drive.json", "w", encoding="utf-8") as md:
                    json.dump(meta_drive, md, indent=2, ensure_ascii=False)
            except Exception as e:
                logging.warning(f"Drive upload fallito per {filepath}: {e}")

        return filepath


    def remove_patient_folder_if_exists(self, patient_id: str):
        folder_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    def _entities_list_to_dict(self, entities):
        # Converte una lista di entità [{"type":..., "value":...}] in un oggetto chiave/valore
        if isinstance(entities, dict):
            return entities
        if isinstance(entities, list):
            return {e.get("type") or e.get("entità"): e.get("value") or e.get("valore") for e in entities if (e.get("type") or e.get("entità")) is not None}
        return {}

    def save_entities_json(self, patient_id: str, document_type: str, entities):
        patient_folder = os.path.join(self.UPLOAD_FOLDER, patient_id)
        document_folder = os.path.join(patient_folder, document_type)
        os.makedirs(document_folder, exist_ok=True)
        output_path = os.path.join(document_folder, "entities.json")
        entities_obj = self._entities_list_to_dict(entities)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entities_obj, f, indent=2, ensure_ascii=False)

        drive_root_id = os.getenv("DRIVE_FOLDER_ID")
        if drive_root_id:
            try:
                patient_folder_id = ensure_folder(patient_id, drive_root_id)
                doc_folder_id = ensure_folder(document_type, patient_folder_id)
                drive_meta = upload_to_drive(output_path, doc_folder_id)
                with open(output_path + ".drive.json", "w", encoding="utf-8") as md:
                    json.dump(drive_meta, md, indent=2, ensure_ascii=False)
            except Exception as e:
                logging.warning(f"Drive upload fallito per {output_path}: {e}")

    def read_existing_entities(self, patient_id: str, document_type: str):
        json_path = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type, "entities.json")
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)

        drive_meta_path = json_path + ".drive.json"
        if os.path.exists(drive_meta_path):
            try:
                with open(drive_meta_path, encoding="utf-8") as df:
                    meta = json.load(df)
                    file_id = meta.get("id")
                if file_id:
                    content = download_from_drive(file_id)
                    return json.loads(content.decode("utf-8"))
            except Exception as e:
                logging.warning(f"Impossibile leggere entities da Drive: {e}")
        return []

    def list_existing_patients(self):
        patients = []
        if os.path.exists(self.UPLOAD_FOLDER):
            for patient_id in os.listdir(self.UPLOAD_FOLDER):
                patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
                if os.path.isdir(patient_path):
                    patients.append(patient_id)
        return patients

    def get_patients_summary(self):
        patients = []
        if os.path.exists(self.UPLOAD_FOLDER):
            for patient_id in os.listdir(self.UPLOAD_FOLDER):
                patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
                if not os.path.isdir(patient_path):
                    continue
                name = None
                document_count = 0
                last_document_date = None
                # Cerca nome/cognome e conta PDF
                for doc_type in os.listdir(patient_path):
                    doc_type_path = os.path.join(patient_path, doc_type)
                    if not os.path.isdir(doc_type_path):
                        continue
                    # Cerca entities.json per nome/cognome
                    entities_path = os.path.join(doc_type_path, "entities.json")
                    if not name and os.path.exists(entities_path):
                        try:
                            with open(entities_path) as f:
                                entities = json.load(f)
                                nome = entities.get("nome", "")
                                cognome = entities.get("cognome", "")
                                name = f"{nome} {cognome}".strip()
                        except Exception:
                            pass
                    # Conta PDF e cerca meta.json
                    for file in os.listdir(doc_type_path):
                        if file.endswith(".pdf"):
                            document_count += 1
                            meta_path = os.path.join(doc_type_path, file + ".meta.json")
                            if os.path.exists(meta_path):
                                try:
                                    with open(meta_path) as f:
                                        meta = json.load(f)
                                        upload_date = meta.get("upload_date")
                                        if upload_date:
                                            if not last_document_date or upload_date > last_document_date:
                                                last_document_date = upload_date
                                except Exception:
                                    pass
                patients.append({
                    "id": patient_id,
                    "name": name or patient_id,
                    "document_count": document_count,
                    "last_document_date": last_document_date
                })
        return patients

    def get_patient_detail(self, patient_id):
        patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
        if not os.path.isdir(patient_path):
            return None
        name = None
        documents = []
        for doc_type in os.listdir(patient_path):
            doc_type_path = os.path.join(patient_path, doc_type)
            if not os.path.isdir(doc_type_path):
                continue
            # Cerca entities.json per nome/cognome
            entities_path = os.path.join(doc_type_path, "entities.json")
            if not name and os.path.exists(entities_path):
                try:
                    with open(entities_path) as f:
                        entities = json.load(f)
                        nome = entities.get("nome", "")
                        cognome = entities.get("cognome", "")
                        name = f"{nome} {cognome}".strip()
                except Exception:
                    pass
            # Cerca PDF e meta.json
            for file in os.listdir(doc_type_path):
                if file.endswith(".pdf"):
                    filename = file
                    meta_path = os.path.join(doc_type_path, file + ".meta.json")
                    upload_date = None
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path) as f:
                                meta = json.load(f)
                                upload_date = meta.get("upload_date")
                        except Exception:
                            pass
                    # entities.json per count e status
                    entities_count = 0
                    status = "processing"
                    if os.path.exists(entities_path):
                        try:
                            with open(entities_path) as f:
                                entities = json.load(f)
                                entities_count = len(entities) if isinstance(entities, dict) else 0
                                status = "processed"
                        except Exception:
                            pass
                    drive_meta_path = os.path.join(doc_type_path, file + ".drive.json")
                    drive_id = drive_link = None
                    if os.path.exists(drive_meta_path):
                        try:
                            with open(drive_meta_path) as dm:
                                dmeta = json.load(dm)
                                drive_id = dmeta.get("id")
                                drive_link = dmeta.get("webViewLink")
                        except Exception:
                            pass
                    # id documento: doc_{patient_id}_{doc_type}_{filename senza estensione}
                    doc_id = f"doc_{patient_id}_{doc_type}_{os.path.splitext(filename)[0]}"
                    documents.append({
                        "id": doc_id,
                        "filename": filename,
                        "document_type": doc_type,
                        "upload_date": upload_date,
                        "entities_count": entities_count,
                        "status": status,
                        "drive_id": drive_id,
                        "drive_link": drive_link,
                    })
        return {
            "id": patient_id,
            "name": name or patient_id,
            "documents": documents
        }

    def get_document_detail(self, document_id):
        # document_id: doc_{patient_id}_{document_type}_{filename senza estensione}
        import os, re, json
        # Funzione di normalizzazione per confronto case-insensitive e senza caratteri speciali
        def normalize(s):
            return re.sub(r'[^a-z0-9]', '', s.lower())

        # Parsing robusto dell'ID
        if not document_id.startswith("doc_"):
            return None
        rest = document_id[len("doc_"):]
        try:
            patient_id, remainder = rest.split('_', 1)
        except ValueError:
            return None

        # Lista dei tipi di documenti supportati
        possible_types = [
            "lettera_dimissione",
            "coronarografia",
            "intervento",
            "eco_preoperatorio",
            "eco_postoperatorio",
            "tc_cuore",
            "altro"
        ]
        # Ricerca del document_type nel resto della stringa
        document_type = next(
            (t for t in possible_types if remainder.startswith(t + "_")),
            None
        )
        if not document_type:
            return None

        # Estrai il nome del file senza estensione
        filename_noext = remainder[len(document_type) + 1:]
        # Costruisci il percorso della cartella
        folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)

        # Cerca il PDF in modo case-insensitive e ignorando underscore/spazi
        pdf_file = None
        normalized_target = normalize(filename_noext)
        try:
            for f in os.listdir(folder):
                if f.lower().endswith('.pdf') and normalize(os.path.splitext(f)[0]) == normalized_target:
                    pdf_file = f
                    break
        except FileNotFoundError:
            return None

        if not pdf_file:
            return None

        drive_meta_path = os.path.join(folder, pdf_file + ".drive.json")
        drive_id = drive_link = None
        if os.path.exists(drive_meta_path):
            try:
                with open(drive_meta_path) as dm:
                    dmeta = json.load(dm)
                    drive_id = dmeta.get("id")
                    drive_link = dmeta.get("webViewLink")
            except Exception:
                pass

        # Leggi entities.json
        entities = []
        entities_path = os.path.join(folder, "entities.json")
        data = None
        if os.path.exists(entities_path):
            with open(entities_path) as f:
                data = json.load(f)
        else:
            drive_epath = entities_path + ".drive.json"
            if os.path.exists(drive_epath):
                try:
                    with open(drive_epath) as df:
                        dmeta = json.load(df)
                        file_id = dmeta.get("id")
                    if file_id:
                        content = download_from_drive(file_id)
                        data = json.loads(content.decode("utf-8"))
                except Exception:
                    pass
        if isinstance(data, dict):
            for idx, (k, v) in enumerate(data.items(), 1):
                entities.append({
                    "id": str(idx),
                    "type": k,
                    "value": v,
                    "confidence": 1.0,
                })
        elif isinstance(data, list):
            for idx, ent in enumerate(data, 1):
                entities.append({
                    "id": str(idx),
                    "type": ent.get("type") or ent.get("entità") or "",
                    "value": ent.get("value") or ent.get("valore") or "",
                    "confidence": ent.get("confidence", 1.0),
                })

        # Leggi meta.json per recuperare il nome file originale
        filename = pdf_file
        meta_path = os.path.join(folder, pdf_file + ".meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                    filename = meta.get("filename", pdf_file)
            except Exception:
                pass

        return {
            "id": document_id,
            "patient_id": patient_id,
            "document_type": document_type,
            "filename": filename,
            "drive_id": drive_id,
            "drive_link": drive_link,
            "entities": entities,
        }

    def update_document_entities(self, document_id, entities):
        """
        Aggiorna entities.json per un documento esistente.
        Parsing robusto di document_id per estrarre patient_id e document_type,
        anche se il tipo contiene underscore.
        """
        import os, json, logging
        try:
            # Verifica prefisso
            if not document_id.startswith("doc_"):
                logging.error(f"ID documento non valido: {document_id}")
                return False
            rest = document_id[len("doc_"):]
            # Estrai patient_id e resto
            parts = rest.split("_", 1)
            if len(parts) < 2:
                logging.error(f"Formato document_id inaspettato: {document_id}")
                return False
            patient_id, remainder = parts
            # Lista tipi documenti supportati
            possible_types = [
                "lettera_dimissione",
                "coronarografia",
                "intervento",
                "eco_preoperatorio",
                "eco_postoperatorio",
                "tc_cuore",
                "altro"
            ]
            # Individua il document_type più lungo che sia prefisso di remainder
            document_type = None
            for t in sorted(possible_types, key=lambda x: -len(x)):
                if remainder.startswith(t + "_") or remainder == t:
                    document_type = t
                    break
            if not document_type:
                logging.error(f"Impossibile determinare document_type da: {remainder}")
                return False
            # Percorso cartella e JSON
            folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
            entities_path = os.path.join(folder, "entities.json")
            # Prepara dati
            entities_obj = self._entities_list_to_dict(entities)
            # Scrive il file
            with open(entities_path, "w", encoding="utf-8") as f:
                json.dump(entities_obj, f, indent=2, ensure_ascii=False)

            drive_root_id = os.getenv("DRIVE_FOLDER_ID")
            if drive_root_id:
                try:
                    patient_folder_id = ensure_folder(patient_id, drive_root_id)
                    doc_folder_id = ensure_folder(document_type, patient_folder_id)
                    drive_meta = upload_to_drive(entities_path, doc_folder_id)
                    with open(entities_path + ".drive.json", "w", encoding="utf-8") as md:
                        json.dump(drive_meta, md, indent=2, ensure_ascii=False)
                except Exception as e:
                    logging.warning(f"Drive upload fallito per {entities_path}: {e}")
            return True
        except Exception as e:
            logging.exception(f"Errore in update_document_entities: {e}")
            return False
