# HSR Backend - Sistema di Gestione Documenti Clinici

Un sistema backend Flask per l'elaborazione automatica di documenti clinici cardiologici utilizzando Large Language Models (LLM) per l'estrazione di entità strutturate.

## 🏥 Panoramica

Il sistema è progettato per processare documenti clinici PDF e estrarre automaticamente informazioni strutturate utilizzando modelli di linguaggio avanzati. Supporta diversi tipi di documenti cardiologici e mantiene la coerenza dei dati tra documenti dello stesso paziente.

### Tipi di Documenti Supportati

- **Lettera di Dimissione** - Documento principale con dati anagrafici
- **Coronarografia** - Esami diagnostici invasivi
- **Interventi** - Verbali di interventi chirurgici
- **Ecocardiogrammi** - Pre e post-operatori
- **TC Cuore** - Tomografie computerizzate
- **Altri documenti** - Documenti generici

## 🏗️ Architettura del Sistema

### Componenti Principali

```
hsr_backend/
├── app.py                    # Applicazione Flask principale
├── controller/
│   └── controller.py         # Controller per la logica di business
├── llm/
│   ├── extractor.py          # Interfaccia con LLM (Together AI)
│   └── prompts.py            # Gestione prompt e schemi JSON
├── utils/
│   ├── file_manager.py       # Gestione file e storage
│   ├── excel_manager.py      # Esportazione dati Excel
│   ├── entity_extractor.py   # Parsing risposte LLM
│   ├── table_parser.py       # Estrazione tabelle da PDF
│   ├── metadata_coherence_manager.py  # Verifica coerenza dati
│   └── progress.py           # Tracking progresso elaborazione
└── docs/                     # Documentazione
    ├── unused/               # Codice non utilizzato (S3)
    └── *.md                  # Guide e documentazione
```

### Flusso di Elaborazione

1. **Upload Documento** - Caricamento PDF con validazione
2. **Estrazione Testo** - Parsing PDF con pdfplumber
3. **Elaborazione LLM** - Estrazione entità con Together AI
4. **Verifica Coerenza** - Controllo consistenza dati paziente
5. **Storage** - Salvataggio file e metadati
6. **Aggiornamento Excel** - Esportazione dati strutturati

## 🚀 Installazione e Configurazione

### Prerequisiti

- Python 3.8+
- Together AI API Key
- Flask e dipendenze (vedi `requirements.txt`)

### Setup

1. **Clona il repository**
```bash
git clone <repository-url>
cd hsr_backend
```

2. **Installa dipendenze**
```bash
pip install -r requirements.txt
```

3. **Configura variabili d'ambiente**
```bash
# Crea file .env
TOGETHER_API_KEY=your_together_api_key_here
UPLOAD_FOLDER=./uploads
EXPORT_FOLDER=./export
FRONTEND_ORIGINS=http://localhost:3000
MAX_UPLOAD_MB=25
MAX_TOTAL_UPLOAD_MB=100
```

4. **Avvia l'applicazione**
```bash
python app.py
# oppure
python run.py
```

L'applicazione sarà disponibile su `http://localhost:8080`

## 📡 API Endpoints

### Gestione Pazienti
- `GET /api/patients` - Lista tutti i pazienti
- `GET /api/patient/<patient_id>` - Dettagli paziente specifico

### Gestione Documenti
- `POST /api/upload-document` - Carica nuovo documento
- `GET /api/document/<document_id>` - Dettagli documento
- `PUT /api/document/<document_id>` - Aggiorna entità documento
- `DELETE /api/document/<document_id>` - Elimina documento

### Elaborazione e Coerenza
- `GET /preview-entities/<patient_id>/<document_type>/<filename>` - Anteprima entità
- `POST /update-entities` - Aggiorna entità documento
- `GET /api/coherence-status/<patient_id>` - Stato coerenza metadati
- `POST /api/check-document-coherence` - Verifica coerenza pre-upload

### Esportazione e Utilità
- `GET /api/export-excel` - Esporta dati in Excel
- `POST /api/cleanup-temp-files/<patient_id>` - Pulisce file temporanei
- `GET /health` - Health check sistema

## 🔧 Configurazione Avanzata

### Modelli LLM Supportati

Il sistema supporta diversi modelli tramite Together AI:
- `deepseek-ai/DeepSeek-V3` (default)
- `openai/gpt-oss-120b`
- Altri modelli compatibili con Together AI

### Validazione e Sicurezza

- **Validazione File**: Solo PDF, dimensione massima configurabile
- **Validazione Patient ID**: Normalizzazione e pulizia input
- **Coerenza Metadati**: Verifica automatica consistenza tra documenti
- **CORS**: Configurabile per frontend specifici
- **Headers Sicurezza**: X-Content-Type-Options, X-Frame-Options

### Storage

- **File System**: Storage locale in cartelle organizzate per paziente/tipo
- **Metadati**: JSON con informazioni upload e processing
- **Backup**: Struttura cartelle per backup e recovery

## 📊 Struttura Dati

### Organizzazione File
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

### Schema Entità (Esempio Lettera Dimissione)
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

## 🔍 Monitoraggio e Debug

### Logging
- Log strutturati con timestamp e livelli
- Tracciamento errori LLM e processing
- Monitoraggio performance API

### Health Check
Endpoint `/health` fornisce:
- Stato configurazione API keys
- Verifica cartelle e permessi
- Warnings per configurazioni mancanti

### Gestione Errori
- Retry automatico per errori LLM
- Cleanup automatico file temporanei
- Rollback in caso di errori di coerenza

## 🚀 Deployment

### Produzione
- **Gunicorn**: Server WSGI per produzione
- **Railway**: Configurazione per deployment cloud
- **Nixpacks**: Buildpack per containerizzazione

### Variabili Ambiente Produzione
```bash
TOGETHER_API_KEY=your_production_key
UPLOAD_FOLDER=/data/uploads
EXPORT_FOLDER=/data/export
FRONTEND_ORIGINS=https://your-frontend-domain.com
```

## 📚 Documentazione Aggiuntiva

Vedi la cartella `docs/` per documentazione dettagliata:
- `DEPLOYMENT_GUIDE.md` - Guida deployment
- `ENV_VARIABLES.md` - Variabili ambiente
- `CHANGELOG.md` - Cronologia modifiche
- `IMPROVEMENTS_README.md` - Roadmap miglioramenti

## 🤝 Contributi

1. Fork del repository
2. Crea branch feature (`git checkout -b feature/nuova-funzionalita`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova funzionalità'`)
4. Push branch (`git push origin feature/nuova-funzionalita`)
5. Crea Pull Request

## 📄 Licenza

Vedi file `LICENSE` per dettagli sulla licenza.

## 🆘 Supporto

Per problemi o domande:
1. Controlla la documentazione in `docs/`
2. Verifica i log dell'applicazione
3. Controlla lo stato con `/health`
4. Apri una issue su GitHub

---

**Versione**: 1.0.0  
**Ultimo aggiornamento**: 2025