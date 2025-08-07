# app.py
import logging
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
from controller.controller import DocumentController
from flask_cors import CORS
import io
import json
import pdfplumber
from datetime import datetime

# Configura logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
# Abilita CORS per tutte le rotte e supporta le credenziali
CORS(app, origins=[
    "https://v0-vercel-frontend-development-weld.vercel.app",
    "http://localhost:3000"
], supports_credentials=True)

# Cartella per upload
#UPLOAD_FOLDER = "uploads"
#os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

document_controller = DocumentController()

# Funzione per logging route

def log_route(route_name):
    app.logger.info(f"Endpoint chiamato: {route_name}")

# Funzione per determinare tipo di documento

def guess_document_type(filename):
    name = filename.lower()
    if "dimissione" in name:
        return "lettera_dimissione"
    if "coronaro" in name:
        return "coronarografia"
    if "intervento" in name or "verbale" in name:
        return "intervento"
    if "eco" in name and "pre" in name:
        return "eco_preoperatorio"
    if "eco" in name and "post" in name:
        return "eco_postoperatorio"
    if "tc" in name or "tac" in name:
        return "tc_cuore"
    return "altro"

@app.route("/preview-entities/<patient_id>/<document_type>/<filename>", methods=["GET"])
def preview_entities(patient_id, document_type, filename):
    log_route("preview_entities")
    result = document_controller.update_entities_for_document(
        patient_id, document_type, filename, preview=True
    )
    app.logger.debug(f"Risultato preview: {result}")
    return jsonify(result)

@app.route("/update-entities", methods=["POST"])
def update_entities():
    log_route("update_entities")
    data = request.json
    app.logger.debug(f"Payload update_entities: {data}")
    response = document_controller.update_entities_for_document(
        data.get("patient_id"),
        data.get("document_type"),
        data.get("filename"),
        updated_entities=data.get("updated_entities")
    )
    app.logger.debug(f"Risposta update_entities: {response}")
    return jsonify(response)

@app.route("/api/export-excel", methods=["GET"])
def export_excel():
    log_route("export_excel")
    path = document_controller.excel_manager.export_excel_file()
    app.logger.info(f"Excel scritto in: {path}")
    return send_file(path, as_attachment=True, download_name="dati_clinici.xlsx")

@app.route("/api/patients", methods=["GET"])
def get_patients():
    log_route("get_patients")
    patients = document_controller.list_existing_patients()
    app.logger.debug(f"Pazienti trovati: {patients}")
    return jsonify(patients)

@app.route("/api/patient/<patient_id>", methods=["GET"])
def get_patient_detail(patient_id):
    log_route("get_patient_detail")
    detail = document_controller.get_patient_detail(patient_id)
    app.logger.debug(f"Dettaglio paziente {patient_id}: {detail}")
    if detail is None:
        app.logger.warning(f"Paziente non trovato: {patient_id}")
        return jsonify({"error": "Paziente non trovato"}), 404
    return jsonify(detail)

@app.route("/api/document/<document_id>", methods=["GET"])
def get_document_detail(document_id):
    log_route("get_document_detail")
    detail = document_controller.get_document_detail(document_id)
    app.logger.debug(f"Dettaglio documento {document_id}: {detail}")
    if detail is None:
        app.logger.warning(f"Documento non trovato: {document_id}")
        return jsonify({"error": "Documento non trovato"}), 404
    return jsonify(detail)

@app.route("/api/document/<document_id>", methods=["PUT"])
def update_document_entities_route(document_id):
    log_route("update_document_entities_route")
    data = request.get_json()
    app.logger.debug(f"Payload PUT entities per {document_id}: {data}")
    entities = data.get("entities")
    if not isinstance(entities, list):
        app.logger.error("Formato entità non valido")
        return jsonify({"success": False, "message": "Formato entità non valido"}), 400
    ok = document_controller.update_document_entities(document_id, entities)
    if not ok:
        app.logger.error(f"Errore salvataggio entità documento {document_id}")
        return jsonify({"success": False, "message": "Errore durante il salvataggio"}), 500
    return jsonify({"success": True, "document_id": document_id, "message": "Entità aggiornate con successo."})

@app.route("/api/upload-document", methods=["POST"])
def upload_document():
    log_route("upload_document")
    try:
        files = request.files.getlist("file")
        app.logger.debug(f"Numero di file ricevuti: {len(files)}")
        if not files:
            return jsonify({"error": "Almeno un file è obbligatorio"}), 400

        user_id = request.form.get("patient_id")
        results = []

        for file in files:
            filename = secure_filename(file.filename)
            app.logger.info(f"Processo file: {filename}")
            document_type = guess_document_type(filename)
            app.logger.debug(f"Tipo documento: {document_type}")

            # Lettura PDF in memoria
            stream = io.BytesIO(file.read())
            file_bytes = stream.getvalue()
            file.stream.seek(0)

            # Estrazione testo
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            app.logger.debug(f"Testo estratto lunghezza: {len(text)}")

            # LLM per entità
            response_json_str = document_controller.llm.get_response_from_document(
                text, document_type, model=document_controller.model_name
            )
            app.logger.debug(f"Risposta LLM: {response_json_str}")

            try:
                extracted = json.loads(response_json_str)
            except json.JSONDecodeError:
                app.logger.error("Errore JSONDecode dall'LLM")
                results.append({"filename": filename, "error": "Errore durante l’analisi del documento"})
                continue

            if not extracted:
                app.logger.warning(f"Nessuna entità estratta per: {filename}")
                results.append({"filename": filename, "error": "Nessuna entità estratta; documento non valido"})
                continue

            # Determina patient_id_final
            if document_type == "lettera_dimissione":
                stream = io.BytesIO(file_bytes)
                with pdfplumber.open(stream) as pdf:
                    text_full = "\n".join(p.extract_text() or "" for p in pdf.pages)
                try:
                    resp = document_controller.llm.get_response_from_document(
                        text_full, document_type, model=document_controller.model_name
                    )
                    extracted_json = json.loads(resp)
                    extracted_id = extracted_json.get("n_cartella")
                except Exception:
                    extracted_id = None

                if extracted_id:
                    if user_id and str(user_id) != str(extracted_id):
                        results.append({
                            "filename": filename,
                            "error": "Patient ID nel documento diverso da quello inserito"
                        })
                        continue
                    patient_id_final = str(extracted_id)
                else:
                    if not user_id:
                        results.append({"filename": filename, "error": "Non è stato trovato il numero di cartella; inserisci patient_id"})
                        continue
                    patient_id_final = str(user_id)
                file.stream.seek(0)
            else:
                if not user_id:
                    results.append({"filename": filename, "error": "patient_id è obbligatorio per questo tipo di documento"})
                    continue
                patient_id_final = str(user_id)

            # Verifica esistenza PDF
            patient_folder = os.path.join(UPLOAD_FOLDER, patient_id_final, document_type)
            existing_pdfs = [f for f in os.listdir(patient_folder) if f.lower().endswith(".pdf")] if os.path.isdir(patient_folder) else []
            if existing_pdfs:
                results.append({"filename": filename, "error": f"Esiste già un documento di tipo '{document_type}' per il paziente {patient_id_final}"})
                continue

            # Salvataggio su disco
            os.makedirs(patient_folder, exist_ok=True)
            filepath = os.path.join(patient_folder, filename)
            file.save(filepath)
            app.logger.info(f"File salvato in: {filepath}")

            # Lettura anagrafica iniziale
            provided_anagraphic = document_controller.file_manager.read_existing_entities(patient_id_final, "lettera_dimissione") if document_type != "lettera_dimissione" else None

            # Metadata
            meta = {"filename": filename, "upload_date": datetime.now().strftime("%Y-%m-%d")}  
            with open(filepath + ".meta.json", "w", encoding="utf-8") as mf:
                json.dump(meta, mf)
            app.logger.info(f"Metadata salvato per: {filename}")

            # Processing async
            document_controller.process_document_and_entities(
                filepath, patient_id_final, document_type, provided_anagraphic
            )

            results.append({
                "document_id": f"doc_{patient_id_final}_{document_type}_{os.path.splitext(filename)[0]}",
                "patient_id": patient_id_final,
                "document_type": document_type,
                "filename": filename,
                "status": "processing"
            })

        return jsonify(results[0] if len(results) == 1 else results)
    except Exception as e:
        app.logger.exception("Errore in upload_document")
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<path:filename>', methods=['GET', 'HEAD'])
def uploaded_file(filename):
    log_route("uploaded_file")
    fullpath = os.path.join(app.root_path, 'uploads', filename)
    if not os.path.isfile(fullpath):
        app.logger.warning(f"File non trovato: {fullpath}")
        abort(404)
    return send_file(fullpath, conditional=True)

@app.route("/")
def index():
    log_route("index")
    return "Hello from Railway!"

if __name__ == "__main__":
    logging.info("Avvio app in locale su porta 8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
