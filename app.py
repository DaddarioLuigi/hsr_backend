import logging
from flask import Flask, request, jsonify, send_file, abort, redirect
from werkzeug.utils import secure_filename, safe_join
import os
from controller.controller import DocumentController
from flask_cors import CORS
import io
import json
import pdfplumber
from datetime import datetime
from threading import Thread

# Configura logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
# Abilita CORS per tutte le rotte e supporta le credenziali
origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,https://v0-vercel-frontend-development-weld.vercel.app").split(",") if o.strip()]
CORS(app, origins=origins, supports_credentials=True)

EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", "./export")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")

os.makedirs(EXPORT_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config.update({
    "UPLOAD_FOLDER": UPLOAD_FOLDER,
    "EXPORT_FOLDER": EXPORT_FOLDER
})

document_controller = DocumentController(
    upload_folder=UPLOAD_FOLDER,
    export_folder=EXPORT_FOLDER
)

def log_route(route_name):
    app.logger.info(f"Endpoint chiamato: {route_name}")

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

@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # Evita cache su JSON per prevenire dati stantii sul frontend
    if response.mimetype == 'application/json':
        response.headers["Cache-Control"] = "no-store"
    return response

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

@app.route("/api/document/<document_id>", methods=["DELETE"])
def delete_document(document_id):
    log_route("delete_document")
    result = document_controller.delete_document(document_id)
    status = 200 if result.get("success") else 404
    return jsonify(result), status

@app.route("/api/upload-document", methods=["POST"])
def upload_document():
    log_route("upload_document")
    try:
        files = request.files.getlist("file")
        app.logger.debug(f"Numero di file ricevuti: {len(files)}")
        if not files:
            return jsonify({"error": "Almeno un file è obbligatorio"}), 400
        # Limita dimensione totale e tipi: accetta solo PDF
        max_total_mb = float(os.getenv("MAX_UPLOAD_MB", "25"))
        total_size = 0
        for f in files:
            f.stream.seek(0, os.SEEK_END)
            total_size += f.stream.tell()
            f.stream.seek(0)
            if not f.filename.lower().endswith('.pdf'):
                return jsonify({"error": "Sono consentiti solo file PDF"}), 400
        if total_size > max_total_mb * 1024 * 1024:
            return jsonify({"error": f"Dimensione totale upload supera {max_total_mb}MB"}), 413

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

            # Estrazione testo (se serve in futuro); evitare chiamate LLM sincrone qui
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            app.logger.debug(f"Testo estratto lunghezza: {len(text)}")

            # Determina patient_id_final
            if document_type == "lettera_dimissione":
                # Se l'utente ha fornito un patient_id, usalo direttamente evitando LLM nella richiesta
                if user_id:
                    patient_id_final = str(user_id)
                else:
                    # In assenza di patient_id, tenta una singola estrazione LLM per n_cartella
                    try:
                        resp = document_controller.llm.get_response_from_document(
                            text, document_type, model=document_controller.model_name
                        )
                        extracted_json = json.loads(resp)
                        extracted_id = extracted_json.get("n_cartella")
                    except Exception:
                        extracted_id = None

                    if extracted_id:
                        patient_id_final = str(extracted_id)
                    else:
                        results.append({"filename": filename, "error": "Non è stato trovato il numero di cartella; inserisci patient_id"})
                        continue
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

            # Salvataggio su disco e upload su Drive
            filepath, _ = document_controller.file_manager.save_file(
                patient_id_final,
                document_type,
                filename,
                file
            )
            app.logger.info(f"File salvato in: {filepath}")

            # Lettura anagrafica iniziale
            provided_anagraphic = document_controller.file_manager.read_existing_entities(patient_id_final, "lettera_dimissione") if document_type != "lettera_dimissione" else None

            # Processing in background per evitare timeout del worker
            Thread(
                target=document_controller.process_document_and_entities,
                args=(filepath, patient_id_final, document_type, provided_anagraphic),
                daemon=True,
            ).start()

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
    try:
        fullpath = safe_join(UPLOAD_FOLDER, filename)
    except Exception:
        abort(400)
    # Enforce path inside UPLOAD_FOLDER
    if not os.path.realpath(fullpath).startswith(os.path.realpath(UPLOAD_FOLDER)):
        abort(403)
    if os.path.isfile(fullpath):
        return send_file(fullpath, conditional=True)
    app.logger.warning(f"File non trovato: {fullpath}")
    abort(404)

@app.route("/")
def index():
    log_route("index")
    return "Hello from Railway!"

if __name__ == "__main__":
    logging.info("Avvio app in locale su porta 8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
