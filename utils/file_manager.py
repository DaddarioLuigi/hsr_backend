import os
import json
import shutil
import re

class FileManager:
    UPLOAD_FOLDER = "uploads"

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
        with open(output_path, "w") as f:
            json.dump(entities_obj, f, indent=2, ensure_ascii=False)

    def read_existing_entities(self, patient_id: str, document_type: str):
        json_path = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type, "entities.json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                return json.load(f) 
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
                    # id documento: doc_{patient_id}_{doc_type}_{filename senza estensione}
                    doc_id = f"doc_{patient_id}_{doc_type}_{os.path.splitext(filename)[0]}"
                    documents.append({
                        "id": doc_id,
                        "filename": filename,
                        "document_type": doc_type,
                        "upload_date": upload_date,
                        "entities_count": entities_count,
                        "status": status
                    })
        return {
            "id": patient_id,
            "name": name or patient_id,
            "documents": documents
        }

    def get_document_detail(self, document_id):
        # document_id: doc_{patient_id}_{document_type}_{filename senza estensione}
        def normalize(s):
            return re.sub(r'[^a-z0-9]', '', s.lower())
        try:
            parts = document_id.split('_')
            if len(parts) < 4: 
                return None
            patient_id = parts[1]
            # document_type può contenere underscore, quindi prendi tutto tranne il primo, il secondo e l'ultimo pezzo
            document_type = '_'.join(parts[2:-1])
            filename_noext = parts[-1]
            folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
            # Cerca il PDF in modo case-insensitive e ignorando underscore/spazi
            pdf_file = None
            normalized_target = normalize(filename_noext)
            print("DEBUG: folder=", folder)
            print("DEBUG: filename_noext=", filename_noext)
            print("DEBUG: files in folder:", os.listdir(folder))
            for f in os.listdir(folder):
                if f.lower().endswith('.pdf') and normalize(os.path.splitext(f)[0]) == normalized_target:
                    pdf_file = f
                    break
            if not pdf_file:
                print("DEBUG: Nessun file PDF trovato che corrisponde a", filename_noext)
                return None
            pdf_path = f"/uploads/{patient_id}/{document_type}/{pdf_file}"
            # Leggi entities.json
            entities_path = os.path.join(folder, "entities.json")
            entities = []
            if os.path.exists(entities_path):
                with open(entities_path) as f:
                    data = json.load(f)
                    # Se dict, converti in lista
                    if isinstance(data, dict):
                        for idx, (k, v) in enumerate(data.items(), 1):
                            entities.append({
                                "id": str(idx),
                                "type": k,
                                "value": v,
                                "confidence": 1.0
                            })
                    elif isinstance(data, list):
                        for idx, ent in enumerate(data, 1):
                            entities.append({
                                "id": str(idx),
                                "type": ent.get("type") or ent.get("entità") or "",
                                "value": ent.get("value") or ent.get("valore") or "",
                                "confidence": ent.get("confidence", 1.0)
                            })
            # Leggi meta.json per filename
            meta_path = os.path.join(folder, pdf_file + ".meta.json")
            filename = pdf_file
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
                "pdf_path": pdf_path,
                "entities": entities
            }
        except Exception:
            return None

    def update_document_entities(self, document_id, entities):
        try:
            parts = document_id.split('_', 3)
            if len(parts) < 4:
                return False
            _, patient_id, document_type, _ = parts
            folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
            entities_path = os.path.join(folder, "entities.json")
            entities_obj = self._entities_list_to_dict(entities)
            with open(entities_path, "w") as f:
                json.dump(entities_obj, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
