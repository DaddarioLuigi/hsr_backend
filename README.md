# HSR Backend - Clinical Document Management System

A Flask backend system for automatic processing of clinical cardiology documents using Large Language Models (LLM) for structured entity extraction.

## 🏥 Overview

The system is designed to process clinical PDF documents and automatically extract structured information using advanced language models. It supports various types of cardiology documents and maintains data consistency between documents from the same patient.

### Supported Document Types

- **Discharge Letter** - Main document with demographic data
- **Coronary Angiography** - Invasive diagnostic exams
- **Surgical Procedures** - Surgical procedure reports
- **Echocardiograms** - Pre and post-operative
- **Cardiac CT** - Computed tomography scans
- **Other Documents** - Generic documents

## 🏗️ System Architecture

### Main Components

```
hsr_backend/
├── app.py                    # Main Flask application
├── controller/
│   └── controller.py         # Business logic controller
├── llm/
│   ├── extractor.py          # LLM interface (Together AI)
│   └── prompts.py            # Prompt and JSON schema management
├── utils/
│   ├── file_manager.py       # File management and storage
│   ├── excel_manager.py      # Excel data export
│   ├── entity_extractor.py   # LLM response parsing
│   ├── table_parser.py       # PDF table extraction
│   ├── metadata_coherence_manager.py  # Data consistency verification
│   └── progress.py           # Processing progress tracking
└── docs/                     # Documentation
    ├── unused/               # Unused code (S3)
    └── *.md                  # Guides and documentation
```

### Processing Flow

1. **Document Upload** - PDF upload with validation
2. **Text Extraction** - PDF parsing with pdfplumber
3. **LLM Processing** - Entity extraction with Together AI
4. **Consistency Check** - Patient data consistency verification
5. **Storage** - File and metadata saving
6. **Excel Update** - Structured data export

## 🚀 Installation and Configuration

### Prerequisites

- Python 3.8+
- Together AI API Key
- Flask and dependencies (see `requirements.txt`)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd hsr_backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Create .env file
TOGETHER_API_KEY=your_together_api_key_here
UPLOAD_FOLDER=./uploads
EXPORT_FOLDER=./export
FRONTEND_ORIGINS=http://localhost:3000
MAX_UPLOAD_MB=25
MAX_TOTAL_UPLOAD_MB=100
```

4. **Start the application**
```bash
python app.py
# or
python run.py
```

The application will be available at `http://localhost:8080`

## 📡 API Endpoints

### Patient Management
- `GET /api/patients` - List all patients
- `GET /api/patient/<patient_id>` - Specific patient details

### Document Management
- `POST /api/upload-document` - Upload new document
- `GET /api/document/<document_id>` - Document details
- `PUT /api/document/<document_id>` - Update document entities
- `DELETE /api/document/<document_id>` - Delete document

### Processing and Consistency
- `GET /preview-entities/<patient_id>/<document_type>/<filename>` - Entity preview
- `POST /update-entities` - Update document entities
- `GET /api/coherence-status/<patient_id>` - Metadata consistency status
- `POST /api/check-document-coherence` - Pre-upload consistency check

### Export and Utilities
- `GET /api/export-excel` - Export data to Excel
- `POST /api/cleanup-temp-files/<patient_id>` - Clean temporary files
- `GET /health` - System health check

## 🔧 Advanced Configuration

### Supported LLM Models

The system supports various models via Together AI:
- `deepseek-ai/DeepSeek-V3` (default)
- `openai/gpt-oss-120b`
- Other Together AI compatible models

### Validation and Security

- **File Validation**: PDF only, configurable maximum size
- **Patient ID Validation**: Input normalization and cleaning
- **Metadata Consistency**: Automatic consistency verification between documents
- **CORS**: Configurable for specific frontends
- **Security Headers**: X-Content-Type-Options, X-Frame-Options

### Storage

- **File System**: Local storage in organized folders by patient/type
- **Metadata**: JSON with upload and processing information
- **Backup**: Folder structure for backup and recovery

## 📊 Data Structure

### File Organization
```
uploads/
├── {patient_id}/
│   ├── lettera_dimissione/
│   │   ├── documento.pdf
│   │   ├── documento.pdf.meta.json
│   │   └── entities.json
│   ├── coronarografia/
│   └── ...
```

### Entity Schema (Discharge Letter Example)
```json
{
  "n_cartella": 12345,
  "nome": "Mario",
  "cognome": "Rossi",
  "sesso": "M",
  "eta_al_momento_dell_intervento": 65,
  "data_di_nascita": "1958-03-15",
  "Diagnosi": "Stenosi aortica severa",
  "classe_nyha": "III",
  "diabete": true,
  "ipertensione": true
}
```

## 🔍 Monitoring and Debug

### Logging
- Structured logs with timestamps and levels
- LLM and processing error tracking
- API performance monitoring

### Health Check
The `/health` endpoint provides:
- API key configuration status
- Folder and permission verification
- Warnings for missing configurations

### Error Management
- Automatic retry for LLM errors
- Automatic cleanup of temporary files
- Rollback in case of consistency errors

## 🚀 Deployment

### Production
- **Gunicorn**: WSGI server for production
- **Railway**: Cloud deployment configuration
- **Nixpacks**: Buildpack for containerization

### Production Environment Variables
```bash
TOGETHER_API_KEY=your_production_key
UPLOAD_FOLDER=/data/uploads
EXPORT_FOLDER=/data/export
FRONTEND_ORIGINS=https://your-frontend-domain.com
```

## 📚 Additional Documentation

See the `docs/` folder for detailed documentation:
- `DEPLOYMENT_GUIDE.md` - Deployment guide
- `ENV_VARIABLES.md` - Environment variables
- `CHANGELOG.md` - Change history
- `IMPROVEMENTS_README.md` - Improvement roadmap

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📄 License

See `LICENSE` file for license details.

## 🆘 Support

For issues or questions:
1. Check documentation in `docs/`
2. Verify application logs
3. Check status with `/health`
4. Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: 2025