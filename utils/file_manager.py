import os
import json
import shutil
import re
import logging
from datetime import datetime
from .s3_manager import S3Manager



class FileManager:

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

    def __init__(self):
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        self.s3_manager = S3Manager()
    
    def cleanup_temp_files(self, patient_id: str, document_type: str = None):
        """
        Pulisce i file temporanei per un paziente o un tipo di documento specifico.
        
        Args:
            patient_id: ID del paziente
            document_type: Tipo di documento specifico (opzionale)
        """
        try:
            if document_type:
                # Pulisce solo il tipo di documento specifico
                folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
                if os.path.exists(folder):
                    # Rimuovi solo i file temporanei
                    for filename in os.listdir(folder):
                        if filename.startswith("temp_") or filename.endswith(".tmp"):
                            filepath = os.path.join(folder, filename)
                            try:
                                if os.path.isfile(filepath):
                                    os.remove(filepath)
                                elif os.path.isdir(filepath):
                                    shutil.rmtree(filepath)
                                logging.info(f"Rimosso file temporaneo: {filepath}")
                            except Exception as e:
                                logging.warning(f"Errore rimozione file temporaneo {filepath}: {e}")
            else:
                # Pulisce tutti i file temporanei del paziente
                patient_folder = os.path.join(self.UPLOAD_FOLDER, patient_id)
                if os.path.exists(patient_folder):
                    for root, dirs, files in os.walk(patient_folder):
                        # Rimuovi file temporanei
                        for filename in files:
                            if filename.startswith("temp_") or filename.endswith(".tmp"):
                                filepath = os.path.join(root, filename)
                                try:
                                    os.remove(filepath)
                                    logging.info(f"Rimosso file temporaneo: {filepath}")
                                except Exception as e:
                                    logging.warning(f"Errore rimozione file temporaneo {filepath}: {e}")
                        
                        # Rimuovi cartelle temporanee
                        for dirname in dirs:
                            if dirname.startswith("temp_") or dirname == "temp_processing":
                                dirpath = os.path.join(root, dirname)
                                try:
                                    shutil.rmtree(dirpath)
                                    logging.info(f"Rimossa cartella temporanea: {dirpath}")
                                except Exception as e:
                                    logging.warning(f"Errore rimozione cartella temporanea {dirpath}: {e}")
        except Exception as e:
            logging.error(f"Errore durante la pulizia dei file temporanei per {patient_id}: {e}")

    def validate_patient_id(self, patient_id: str) -> tuple[bool, str]:
        """
        Valida e normalizza un patient_id.
        
        Returns:
            tuple[bool, str]: (is_valid, normalized_id)
        """
        if not patient_id:
            return False, ""
        
        # Normalizza il patient_id
        normalized = str(patient_id).strip()
        
        # Rimuovi caratteri non validi (solo numeri e lettere)
        import re
        normalized = re.sub(r'[^a-zA-Z0-9]', '', normalized)
        
        # Verifica che non sia vuoto dopo la normalizzazione
        if not normalized:
            return False, ""
        
        # Verifica che non sia un ID temporaneo
        if (normalized.startswith("pending") or 
            normalized.startswith("extract") or 
            normalized.startswith("unknown") or
            normalized.startswith("temp")):
            return False, ""
        
        return True, normalized

    def save_file(self, patient_id: str, document_type: str, filename: str, file_stream) -> tuple[str, dict | None]:
        # Validazione input
        if not patient_id or not document_type or not filename or not file_stream:
            raise ValueError("Tutti i parametri sono obbligatori")
        
        # Valida e normalizza patient_id
        is_valid, normalized_patient_id = self.validate_patient_id(patient_id)
        if not is_valid:
            raise ValueError(f"Patient ID non valido: {patient_id}")
        
        # Normalizza document_type
        document_type = str(document_type).strip().lower()
        if not document_type:
            raise ValueError("Document type non può essere vuoto")
        
        # Normalizza filename
        filename = str(filename).strip()
        if not filename:
            raise ValueError("Filename non può essere vuoto")
        
        # 1) crea cartella locale
        folder = os.path.join(self.UPLOAD_FOLDER, normalized_patient_id, document_type)
        os.makedirs(folder, exist_ok=True)

        # 2) scrivi su disco
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(file_stream.read())
        except Exception as e:
            # Cleanup in caso di errore
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            raise Exception(f"Errore nel salvataggio del file: {str(e)}")

        # 3) metadati locali
        meta = {"filename": filename, "upload_date": datetime.now().strftime("%Y-%m-%d")}
        meta_path = filepath + ".meta.json"
        try:
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(meta, mf, indent=2, ensure_ascii=False)
        except Exception as e:
            # Cleanup in caso di errore
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            raise Exception(f"Errore nel salvataggio dei metadati: {str(e)}")

        # 4) Upload su S3 (se configurato)
        s3_result = None
        if self.s3_manager.s3_client:
            s3_key = f"patients/{normalized_patient_id}/{document_type}/{filename}"
            s3_result = self.s3_manager.upload_file(filepath, s3_key)
            if s3_result.get("success"):
                # Aggiungi URL S3 ai metadati
                meta["s3_url"] = s3_result.get("url")
                meta["s3_key"] = s3_key
                try:
                    with open(meta_path, "w", encoding="utf-8") as mf:
                        json.dump(meta, mf, indent=2, ensure_ascii=False)
                except Exception as e:
                    logging.warning(f"Errore nell'aggiornamento dei metadati con URL S3: {e}")
                logging.info(f"File caricato su S3: {s3_key}")
            else:
                logging.warning(f"Errore upload S3: {s3_result.get('error')}")

        return filepath, s3_result

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
        
        # Upload entities.json su S3 (se configurato)
        if self.s3_manager.s3_client:
            s3_key = f"patients/{patient_id}/{document_type}/entities.json"
            s3_result = self.s3_manager.upload_file(output_path, s3_key)
            if s3_result.get("success"):
                logging.info(f"Entities JSON caricato su S3: {s3_key}")
            else:
                logging.warning(f"Errore upload entities JSON su S3: {s3_result.get('error')}")


    def read_existing_entities(self, patient_id: str, document_type: str):
        json_path = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type, "entities.json")
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)

        return []

    def list_existing_patients(self):
        patients = []
        if os.path.exists(self.UPLOAD_FOLDER):
            for patient_id in os.listdir(self.UPLOAD_FOLDER):
                # Filtra pazienti con ID temporanei o pending
                if (patient_id.startswith("_pending_") or 
                    patient_id.startswith("_extract_") or 
                    patient_id.startswith("unknown_")):
                    continue
                
                # Per i pazienti che iniziano con "patient_", verifica se hanno documenti processati
                if patient_id.startswith("patient_"):
                    # Controlla se ci sono documenti processati (non solo temp_processing)
                    patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
                    if not os.path.isdir(patient_path):
                        continue
                    
                    # Cerca documenti processati (cartelle con entities.json)
                    has_processed_docs = False
                    for doc_type in os.listdir(patient_path):
                        doc_type_path = os.path.join(patient_path, doc_type)
                        if os.path.isdir(doc_type_path) and doc_type != "temp_processing":
                            entities_path = os.path.join(doc_type_path, "entities.json")
                            if os.path.exists(entities_path):
                                has_processed_docs = True
                                break
                    
                    # Se non ci sono documenti processati, salta questo paziente
                    if not has_processed_docs:
                        continue
                    
                patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
                if os.path.isdir(patient_path):
                    patients.append(patient_id)
        if patients:
            return patients
        return []

    def get_patients_summary(self):
        patients = []
        if os.path.exists(self.UPLOAD_FOLDER):
            for patient_id in os.listdir(self.UPLOAD_FOLDER):
                # Filtra pazienti con ID temporanei o pending
                if (patient_id.startswith("_pending_") or 
                    patient_id.startswith("_extract_") or 
                    patient_id.startswith("unknown_")):
                    continue
                
                # Per i pazienti che iniziano con "patient_", verifica se hanno documenti processati
                if patient_id.startswith("patient_"):
                    # Controlla se ci sono documenti processati (non solo temp_processing)
                    patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
                    if not os.path.isdir(patient_path):
                        continue
                    
                    # Cerca documenti processati (cartelle con entities.json)
                    has_processed_docs = False
                    for doc_type in os.listdir(patient_path):
                        doc_type_path = os.path.join(patient_path, doc_type)
                        if os.path.isdir(doc_type_path) and doc_type != "temp_processing":
                            entities_path = os.path.join(doc_type_path, "entities.json")
                            if os.path.exists(entities_path):
                                has_processed_docs = True
                                break
                    
                    # Se non ci sono documenti processati, salta questo paziente
                    if not has_processed_docs:
                        continue
                    
                patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
                if not os.path.isdir(patient_path):
                    continue
                name = None
                document_count = 0
                last_document_date = None
                for doc_type in os.listdir(patient_path):
                    doc_type_path = os.path.join(patient_path, doc_type)
                    if not os.path.isdir(doc_type_path):
                        continue
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
        if patients:
            return patients
        return []

    def get_patient_detail(self, patient_id):
        patient_path = os.path.join(self.UPLOAD_FOLDER, patient_id)
        if os.path.isdir(patient_path):
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
                        
                        # Costruisci document_id - gestisci documenti del flusso unificato
                        file_noext = os.path.splitext(filename)[0]
                        if file_noext.endswith(f"_{doc_type}"):
                            # Documento del flusso unificato: estrai nome originale
                            original_filename = file_noext.replace(f"_{doc_type}", "")
                            doc_id = f"doc_{patient_id}_{doc_type}_{original_filename}"
                        else:
                            # Documento singolo: usa il filename così com'è
                            doc_id = f"doc_{patient_id}_{doc_type}_{file_noext}"
                        
                        documents.append({
                            "id": doc_id,
                            "filename": filename,
                            "document_type": doc_type,
                            "upload_date": upload_date,
                            "entities_count": entities_count,
                            "status": status,
                        })
            return {
                "id": patient_id,
                "name": name or patient_id,
                "documents": documents
            }
        return None

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
            "anamnesi",
            "epicrisi_ti",
            "cartellino_anestesiologico",
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
                if f.lower().endswith('.pdf'):
                    # Per i documenti del flusso unificato, il file è nel formato {original}_{doc_type}.pdf
                    # Per i documenti singoli, il file è nel formato originale
                    file_noext = os.path.splitext(f)[0]
                    
                    # Controlla se è un documento del flusso unificato
                    if file_noext.endswith(f"_{document_type}"):
                        # Estrai il nome originale dal file del flusso unificato
                        original_name = file_noext.replace(f"_{document_type}", "")
                        if normalize(original_name) == normalized_target:
                            pdf_file = f
                            break
                    else:
                        # Documento singolo - confronta direttamente
                        if normalize(file_noext) == normalized_target:
                            pdf_file = f
                            break
        except FileNotFoundError:
            return None

        if not pdf_file:
            return None


        # Leggi entities.json
        entities = []
        entities_path = os.path.join(folder, "entities.json")
        data = None
        if os.path.exists(entities_path):
            with open(entities_path) as f:
                data = json.load(f)
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
            if not document_id.startswith("doc_"):
                logging.error(f"ID documento non valido: {document_id}")
                return False
            rest = document_id[len("doc_"):]
            parts = rest.split("_", 1)
            if len(parts) < 2:
                logging.error(f"Formato document_id inaspettato: {document_id}")
                return False
            patient_id, remainder = parts
            possible_types = [
                "lettera_dimissione",
                "anamnesi",
                "epicrisi_ti",
                "cartellino_anestesiologico",
                "coronarografia",
                "intervento",
                "eco_preoperatorio",
                "eco_postoperatorio",
                "tc_cuore",
                "altro"
            ]
            document_type = None
            for t in sorted(possible_types, key=lambda x: -len(x)):
                if remainder.startswith(t + "_") or remainder == t:
                    document_type = t
                    break
            if not document_type:
                logging.error(f"Impossibile determinare document_type da: {remainder}")
                return False
            folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
            entities_path = os.path.join(folder, "entities.json")
            entities_obj = self._entities_list_to_dict(entities)
            with open(entities_path, "w", encoding="utf-8") as f:
                json.dump(entities_obj, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logging.exception(f"Errore in update_document_entities: {e}")
            return False

    def delete_document(self, document_id: str) -> dict:
        """
        Cancella un documento identificato da document_id (formato: doc_{patient_id}_{document_type}_{filenameNoExt}).
        Rimuove PDF, meta.json, entities.json associato al document_type e ripulisce le cartelle vuote.
        Se il paziente rimane senza documenti, rimuove anche la cartella del paziente.
        Ritorna un dict con esito e flag su cartelle rimosse.
        """
        import logging
        # Parsing robusto, simile a get_document_detail
        if not isinstance(document_id, str) or not document_id.startswith("doc_"):
            return {"success": False, "error": "document_id non valido"}
        rest = document_id[len("doc_"):]
        try:
            patient_id, remainder = rest.split("_", 1)
        except ValueError:
            return {"success": False, "error": "Formato document_id non valido"}
        possible_types = [
            "lettera_dimissione",
            "anamnesi",
            "epicrisi_ti",
            "cartellino_anestesiologico",
            "coronarografia",
            "intervento",
            "eco_preoperatorio",
            "eco_postoperatorio",
            "tc_cuore",
            "altro"
        ]
        document_type = next((t for t in possible_types if remainder.startswith(t + "_") or remainder == t), None)
        if not document_type:
            return {"success": False, "error": "Impossibile determinare document_type"}
        filename_noext = remainder[len(document_type) + 1:] if remainder != document_type else ""

        import re
        def normalize(s: str) -> str:
            return re.sub(r'[^a-z0-9]', '', (s or '').lower())

        import os, shutil, json
        folder = os.path.join(self.UPLOAD_FOLDER, patient_id, document_type)
        if not os.path.isdir(folder):
            return {"success": False, "error": "Cartella documento non trovata"}

        # Identifica il PDF da cancellare (case-insensitive, filename normalizzato)
        target_pdf = None
        normalized_target = normalize(filename_noext) if filename_noext else None
        for f in os.listdir(folder):
            if f.lower().endswith('.pdf'):
                file_noext = os.path.splitext(f)[0]
                
                # Per i documenti del flusso unificato, il file è nel formato {original}_{doc_type}.pdf
                # Per i documenti singoli, il file è nel formato originale
                if file_noext.endswith(f"_{document_type}"):
                    # Estrai il nome originale dal file del flusso unificato
                    original_name = file_noext.replace(f"_{document_type}", "")
                    if normalized_target is None or normalize(original_name) == normalized_target:
                        target_pdf = f
                        break
                else:
                    # Documento singolo - confronta direttamente
                    if normalized_target is None or normalize(file_noext) == normalized_target:
                        target_pdf = f
                        break
        if not target_pdf:
            return {"success": False, "error": "PDF non trovato"}

        # Cancella PDF e meta
        pdf_path = os.path.join(folder, target_pdf)
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            logging.warning(f"Impossibile rimuovere {pdf_path}: {e}")
        meta_path = pdf_path + ".meta.json"
        try:
            if os.path.exists(meta_path):
                os.remove(meta_path)
        except Exception as e:
            logging.warning(f"Impossibile rimuovere {meta_path}: {e}")

        # Cancella entities.json del document_type (poiché 1 documento per tipo)
        entities_path = os.path.join(folder, "entities.json")
        try:
            if os.path.exists(entities_path):
                os.remove(entities_path)
        except Exception as e:
            logging.warning(f"Impossibile rimuovere {entities_path}: {e}")

        # Cancella file da S3 (se configurato)
        if self.s3_manager.s3_client:
            # Cancella PDF da S3
            s3_pdf_key = f"patients/{patient_id}/{document_type}/{target_pdf}"
            s3_result = self.s3_manager.delete_file(s3_pdf_key)
            if s3_result.get("success"):
                logging.info(f"PDF rimosso da S3: {s3_pdf_key}")
            else:
                logging.warning(f"Errore rimozione PDF da S3: {s3_result.get('error')}")
            
            # Cancella entities.json da S3
            s3_entities_key = f"patients/{patient_id}/{document_type}/entities.json"
            s3_result = self.s3_manager.delete_file(s3_entities_key)
            if s3_result.get("success"):
                logging.info(f"Entities JSON rimosso da S3: {s3_entities_key}")
            else:
                logging.warning(f"Errore rimozione entities JSON da S3: {s3_result.get('error')}")



        # Se cartella del document_type è vuota, rimuovila
        document_type_deleted = False
        try:
            if os.path.isdir(folder) and not os.listdir(folder):
                shutil.rmtree(folder)
                document_type_deleted = True
        except Exception as e:
            logging.warning(f"Impossibile rimuovere cartella {folder}: {e}")

        # Se il paziente non ha più alcuna sottocartella, rimuovi anche il paziente
        patient_folder = os.path.join(self.UPLOAD_FOLDER, patient_id)
        patient_deleted = False
        try:
            if os.path.isdir(patient_folder):
                remaining = [d for d in os.listdir(patient_folder) if os.path.isdir(os.path.join(patient_folder, d))]
                if not remaining:
                    shutil.rmtree(patient_folder)
                    patient_deleted = True
        except Exception as e:
            logging.warning(f"Impossibile rimuovere cartella paziente {patient_folder}: {e}")

        return {"success": True, "patient_deleted": patient_deleted, "document_type_deleted": document_type_deleted}

    def move_patient_folder(self, src_patient_id: str, dst_patient_id: str) -> bool:
        src = os.path.join(self.UPLOAD_FOLDER, str(src_patient_id))
        dst = os.path.join(self.UPLOAD_FOLDER, str(dst_patient_id))
        if not os.path.isdir(src):
            return False
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        if os.path.exists(dst):
            # merge: sposta i contenuti singolarmente
            for name in os.listdir(src):
                shutil.move(os.path.join(src, name), os.path.join(dst, name))
            shutil.rmtree(src, ignore_errors=True)
        else:
            shutil.move(src, dst)
        return True
