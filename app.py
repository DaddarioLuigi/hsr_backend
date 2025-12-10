import logging
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename, safe_join
import os
from controller.controller import DocumentController
from flask_cors import CORS
from datetime import datetime
from utils.progress import ProgressStore
from services.document_upload_service import DocumentUploadService
from extension import db
from models.response import Response



# Configura logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)


app = Flask(__name__)
# Abilita CORS per tutte le rotte e supporta le credenziali
origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,https://v0-vercel-frontend-development-weld.vercel.app").split(",") if o.strip()]
CORS(app, origins=origins, supports_credentials=True)

# Configurazione database PostgreSQL
# Usa variabile d'ambiente o default per Docker Compose
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/ALFIERI"
)
   

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", "./export")
UPLOAD_FOLDER = os.path.abspath(os.getenv("UPLOAD_FOLDER", "./uploads"))

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

progress_store = ProgressStore(document_controller.file_manager.UPLOAD_FOLDER)
upload_service = DocumentUploadService(document_controller, UPLOAD_FOLDER)

def log_route(route_name):
    app.logger.info(f"Endpoint chiamato: {route_name}")

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

@app.route("/api/coherence-status/<patient_id>", methods=["GET"])
def get_coherence_status(patient_id):
    """Ottiene lo stato di coerenza dei metadati per un paziente."""
    log_route("get_coherence_status")
    try:
        status = document_controller.coherence_manager.get_coherence_status(patient_id)
        return jsonify(status)
    except Exception as e:
        app.logger.exception("Errore nel recupero dello stato di coerenza")
        return jsonify({"error": str(e)}), 500

@app.route("/api/cleanup-temp-files/<patient_id>", methods=["POST"])
def cleanup_temp_files(patient_id):
    """Pulisce i file temporanei per un paziente."""
    log_route("cleanup_temp_files")
    try:
        document_type = request.json.get("document_type") if request.json else None
        document_controller.file_manager.cleanup_temp_files(patient_id, document_type)
        return jsonify({"success": True, "message": "File temporanei puliti con successo"})
    except Exception as e:
        app.logger.exception("Errore nella pulizia dei file temporanei")
        return jsonify({"error": str(e)}), 500

@app.route("/api/list-volume-files", methods=["GET"])
def list_volume_files():
    """Endpoint temporaneo per listare i file nel volume montato"""
    log_route("list_volume_files")
    volume_path = "/data/uploads"
    
    try:
        if not os.path.exists(volume_path):
            return jsonify({
                "error": f"Volume path {volume_path} does not exist",
                "current_working_dir": os.getcwd(),
                "available_dirs": os.listdir("/data") if os.path.exists("/data") else []
            }), 404
        
        files = []
        for root, dirs, filenames in os.walk(volume_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, volume_path)
                file_size = os.path.getsize(file_path)
                files.append({
                    "name": filename,
                    "path": rel_path,
                    "size": file_size,
                    "full_path": file_path
                })
        
        return jsonify({
            "volume_path": volume_path,
            "total_files": len(files),
            "files": files
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "volume_path": volume_path
        }), 500

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

    response_obj=Response.update_response(document_id, detail.get("entities"))
    app.logger.debug(f"Risposta db: {response_obj}")

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

    try:
        entities_count = len(entities) if entities else 0
        update_obj = Response.increment_correction(document_id, increment_by=entities_count)
        app.logger.debug(f"Risposta increment_correction: {update_obj}")
    except Exception as e:
        app.logger.exception(
            f"Errore durante l'incremento delle correzioni per {document_id}: {e}"
        )
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
        
        user_id = request.form.get("patient_id")
        
        # Validazione della richiesta
        is_valid, error_message, validated_files = document_controller.validate_upload_request(
            files, user_id, False
        )
        
        if not is_valid:
            return jsonify({"error": error_message}), 400
        
        # Processa ogni file usando il servizio
        results = []
        for file in validated_files:
            # Usa secure_filename per sanitizzare il nome file
            file.filename = secure_filename(file.filename)
            result = upload_service.process_upload(file, user_id)
            results.append(result.to_dict())

            #Popoliamo il db con le response
            response_db=Response.add_response(
                id_document=result.document_id,
            )
            app.logger.debug(f"Risposta db: {response_db}")

        return jsonify(results[0] if len(results) == 1 else results)
    except Exception as e:
        app.logger.exception("Errore in upload_document")
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<path:filename>', methods=['GET', 'HEAD'])
def uploaded_file(filename):
    log_route("uploaded_file")
    try:
        filename = filename.lstrip('/')
        fullpath = safe_join(UPLOAD_FOLDER, filename)
        fullpath = os.path.abspath(fullpath)
    except Exception as e:
        app.logger.error(f"Errore safe_join per {filename}: {e}")
        abort(400)
    if not fullpath.startswith(os.path.abspath(UPLOAD_FOLDER)):
        abort(403)
    if os.path.isfile(fullpath):
        return send_file(fullpath, conditional=True, mimetype='application/pdf')
    # Cerca case-insensitive nella cartella
    dir_path = os.path.dirname(fullpath)
    expected_name = os.path.basename(fullpath)
    if os.path.isdir(dir_path):
        for f in os.listdir(dir_path):
            if f.lower() == expected_name.lower() and f.lower().endswith('.pdf'):
                return send_file(os.path.join(dir_path, f), conditional=True, mimetype='application/pdf')
    app.logger.warning(f"File non trovato: {fullpath}")
    abort(404)

















@app.route("/api/check-document-coherence", methods=["POST"])
def check_document_coherence():
    """
    Endpoint per verificare la coerenza di un documento prima del caricamento.
    """
    log_route("check_document_coherence")
    try:
        data = request.get_json()
        patient_id = data.get("patient_id")
        document_type = data.get("document_type")
        metadata = data.get("metadata")
        
        if not all([patient_id, document_type, metadata]):
            return jsonify({"error": "Parametri mancanti: patient_id, document_type, metadata"}), 400
        
        result = document_controller.coherence_manager.check_document_coherence(patient_id, document_type, metadata)
        
        return jsonify({
            "status": result.status,
            "reason": result.reason,
            "diff": result.diff,
            "references": result.references,
            "incoerenti": result.incoerenti
        }), 200
        
    except Exception as e:
        app.logger.exception("Errore in check_document_coherence")
        return jsonify({"error": str(e)}), 500





@app.route("/")
def index():
    log_route("index")
    return "Hello from Railway!"

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint per verificare lo stato dell'applicazione e delle configurazioni."""
    log_route("health_check")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Verifica API keys
    together_key = os.getenv("TOGETHER_API_KEY")
    
    health_status["checks"]["together_api_key"] = {
        "configured": bool(together_key),
        "status": "ok" if together_key else "missing"
    }
    
    # Verifica cartelle
    upload_exists = os.path.exists(UPLOAD_FOLDER)
    export_exists = os.path.exists(EXPORT_FOLDER)
    
    health_status["checks"]["upload_folder"] = {
        "path": UPLOAD_FOLDER,
        "exists": upload_exists,
        "writable": os.access(UPLOAD_FOLDER, os.W_OK) if upload_exists else False,
        "status": "ok" if (upload_exists and os.access(UPLOAD_FOLDER, os.W_OK)) else "error"
    }
    
    health_status["checks"]["export_folder"] = {
        "path": EXPORT_FOLDER,
        "exists": export_exists,
        "writable": os.access(EXPORT_FOLDER, os.W_OK) if export_exists else False,
        "status": "ok" if (export_exists and os.access(EXPORT_FOLDER, os.W_OK)) else "error"
    }
    
    # Determina lo stato complessivo
    all_ok = all(
        check.get("status") == "ok" 
        for check in health_status["checks"].values()
    )
    
    health_status["status"] = "healthy" if all_ok else "degraded"
    
    # Se l'API key non è configurata, aggiungi un warning
    if not together_key:
        health_status["warnings"] = [
            "TOGETHER_API_KEY non configurata - l'elaborazione dei documenti fallirà"
        ]
    
    status_code = 200 if all_ok else 503
    return jsonify(health_status), status_code

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        logging.info("Tabelle database create/verificate")
    logging.info("Avvio app in locale su porta 5000")
    app.run(host='0.0.0.0', port=8080, debug=True)