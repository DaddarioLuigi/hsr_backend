# app.py
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from controller.controller import DocumentController

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

document_controller = DocumentController()

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

@app.route("/api/upload-document", methods=["POST"])
def upload_document():
    if "file" not in request.files or "patient_id" not in request.form:
        return jsonify({"error": "file e patient_id sono obbligatori"}), 400

    file = request.files["file"]
    patient_id = request.form["patient_id"]
    filename = secure_filename(file.filename)

    # Funzione semplice per auto-determinare il tipo documento
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

    document_type = guess_document_type(filename)
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

    # Avvia processing (ma la risposta è subito processing)
    # document_controller.process_document_and_entities(filepath, patient_id, document_type)

    # document_id: doc_{patient_id}_{document_type}_{filename senza estensione}
    doc_id = f"doc_{patient_id}_{document_type}_{os.path.splitext(filename)[0]}"
    return jsonify({
        "document_id": doc_id,
        "patient_id": patient_id,
        "document_type": document_type,
        "filename": filename,
        "status": "processing"
    })

if __name__ == "__main__":
    app.run(debug=True)
