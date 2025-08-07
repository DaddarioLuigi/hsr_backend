# app.py
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
from controller.controller import DocumentController
from flask_cors import CORS
import io 
import json
import pdfplumber
from datetime import datetime

app = Flask(__name__)
# Abilita CORS per tutte le rotte e supporta le credenziali
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# Rimuovo eventuali duplicazioni o override inutili

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

document_controller = DocumentController()

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

'''
@app.route("/upload-document", methods=["POST"])
def upload_document():
    if "file" not in request.files or "patient_id" not in request.form or "document_type" not in request.form:
        return jsonify({"error": "file, patient_id e document_type sono obbligatori"}), 400

    file = request.files["file"]
    patient_id = request.form["patient_id"]
    document_type = request.form["document_type"]
    filename = secure_filename(file.filename)
    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id, document_type)
    os.makedirs(patient_folder, exist_ok=True)
    filepath = os.path.join(patient_folder, filename)
    file.save(filepath)

    # Salva la data di upload in un file meta.json accanto al PDF
    from datetime import datetime
    meta = {
        "filename": filename,
        "upload_date": datetime.now().strftime("%Y-%m-%d")
    }
    meta_path = filepath + ".meta.json"
    with open(meta_path, "w") as f:
        import json
        json.dump(meta, f)

    response = document_controller.process_document_and_entities(filepath, patient_id, document_type)
    return jsonify(response)

'''

@app.route("/preview-entities/<patient_id>/<document_type>/<filename>", methods=["GET"])
def preview_entities(patient_id, document_type, filename):
    return jsonify(document_controller.update_entities_for_document(patient_id, document_type, filename, preview=True))

@app.route("/update-entities", methods=["POST"])
def update_entities():
    data = request.json
    return jsonify(document_controller.update_entities_for_document(
        data["patient_id"],
        data["document_type"],
        data["filename"],
        updated_entities=data["updated_entities"]
    ))

@app.route("/api/export-excel", methods=["GET"])
def export_excel():
    path = document_controller.excel_manager.export_excel_file()
    from flask import send_file
    return send_file(path, as_attachment=True, download_name="dati_clinici.xlsx")

@app.route("/api/patients", methods=["GET"])
def get_patients():
    return jsonify(document_controller.list_existing_patients())

@app.route("/api/patient/<patient_id>", methods=["GET"])
def get_patient_detail(patient_id):
    detail = document_controller.get_patient_detail(patient_id)
    if detail is None:
        return jsonify({"error": "Paziente non trovato"}), 404
    return jsonify(detail)

@app.route("/api/document/<document_id>", methods=["GET"])
def get_document_detail(document_id):
    detail = document_controller.get_document_detail(document_id)
    if detail is None:
        return jsonify({"error": "Documento non trovato"}), 404
    return jsonify(detail)

@app.route("/api/document/<document_id>", methods=["PUT"])
def update_document_entities(document_id):
    data = request.get_json()
    entities = data.get("entities")
    if not isinstance(entities, list):
        return jsonify({"success": False, "message": "Formato entità non valido"}), 400
    ok = document_controller.update_document_entities(document_id, entities)
    if not ok:
        return jsonify({"success": False, "message": "Errore durante il salvataggio"}), 500
    return jsonify({
        "success": True,
        "document_id": document_id,
        "message": "Entità aggiornate con successo."
    })


# app.py
@app.route("/api/upload-document", methods=["POST"])
def upload_document():
    try:
        files = request.files.getlist("file")
        if not files:
            return jsonify({"error": "Almeno un file è obbligatorio"}), 400

        user_id = request.form.get("patient_id")
        results = []

        for file in files:
            filename = secure_filename(file.filename)
            document_type = guess_document_type(filename)

            # --- Leggi file in memoria per analisi preventiva ---
            import io, json
            stream = io.BytesIO(file.read())
            file_bytes = stream.getvalue()
            file.stream.seek(0)

            # Estrai testo dal PDF in memoria
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)

            # Chiamata all’LLM per estrazione entità
            response_json_str = document_controller.llm.get_response_from_document(
                text, document_type, model=document_controller.model_name
            )
            try:
                extracted = json.loads(response_json_str)
            except json.JSONDecodeError:
                results.append({
                    "filename": filename,
                    "error": "Errore durante l’analisi del documento"
                })
                continue

            # Se non estrae nulla, scarta
            if not extracted:
                results.append({
                    "filename": filename,
                    "error": "Nessuna entità estratta; documento non valido"
                })
                continue

            # --- Determina il patient_id finale ---
            if document_type == "lettera_dimissione":
                # estrai n_cartella dal PDF
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
                        results.append({
                            "filename": filename,
                            "error": "Non è stato trovato il numero di cartella; inserisci patient_id"
                        })
                        continue
                    patient_id_final = str(user_id)
                file.stream.seek(0)
            else:
                if not user_id:
                    results.append({
                        "filename": filename,
                        "error": "patient_id è obbligatorio per questo tipo di documento"
                    })
                    continue
                patient_id_final = str(user_id)

            # --- Verifica se esiste già un PDF per questo tipo ---
            patient_folder = os.path.join(UPLOAD_FOLDER, patient_id_final, document_type)
            existing_pdfs = []
            if os.path.isdir(patient_folder):
                existing_pdfs = [
                    f for f in os.listdir(patient_folder)
                    if f.lower().endswith(".pdf")
                ]
            if existing_pdfs:
                results.append({
                    "filename": filename,
                    "error": f"Esiste già un documento di tipo '{document_type}' per il paziente {patient_id_final}"
                })
                continue

            # --- Salvataggio su disco ---
            os.makedirs(patient_folder, exist_ok=True)
            filepath = os.path.join(patient_folder, filename)
            file.save(filepath)

            # --- Lettura anagrafica iniziale per i documenti successivi ---
            if document_type != "lettera_dimissione":
                provided_anagraphic = document_controller.file_manager.read_existing_entities(
                    patient_id_final, "lettera_dimissione"
                )
            else:
                provided_anagraphic = None

            # Salva metadata
            meta = {
                "filename": filename,
                "upload_date": datetime.now().strftime("%Y-%m-%d")
            }
            with open(filepath + ".meta.json", "w", encoding="utf-8") as mf:
                json.dump(meta, mf)

            # Avvia il processing in background
            document_controller.process_document_and_entities(
                filepath, patient_id_final, document_type, provided_anagraphic
            )

            # Prepara risultato
            doc_id = f"doc_{patient_id_final}_{document_type}_{os.path.splitext(filename)[0]}"
            results.append({
                "document_id": doc_id,
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
    fullpath = os.path.join(app.root_path, 'uploads', filename)
    if not os.path.isfile(fullpath):
        abort(404)
    # conditional=True abilita supporto a Range e HEAD
    return send_file(fullpath, conditional=True)

@app.route("/")
def index():
    return "Hello from Railway!"
    
if __name__ == "__main__":
    print("Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.methods} -> {rule}")
    app.run(port=5050, debug=True)
