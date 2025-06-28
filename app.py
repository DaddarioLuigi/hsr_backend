# app.py
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from controller.controller import (
    process_document_and_entities,
    update_entities_for_document,
    export_excel_file,
    list_existing_patients
)

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload-document", methods=["POST"])
def upload_document():
    #check this
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

    response = process_document_and_entities(filepath, patient_id, document_type)
    return jsonify(response)

@app.route("/preview-entities/<patient_id>/<document_type>/<filename>", methods=["GET"])
def preview_entities(patient_id, document_type, filename):
    return jsonify(update_entities_for_document(patient_id, document_type, filename, preview=True))

@app.route("/update-entities", methods=["POST"])
def update_entities():
    data = request.json
    return jsonify(update_entities_for_document(
        data["patient_id"],
        data["document_type"],
        data["filename"],
        updated_entities=data["updated_entities"]
    ))

@app.route("/export-excel", methods=["GET"])
def export_excel():
    path = export_excel_file()
    return send_file(path, as_attachment=True)

@app.route("/patients", methods=["GET"])
def list_patients():
    return jsonify(list_existing_patients())

if __name__ == "__main__":
    app.run(debug=True)
