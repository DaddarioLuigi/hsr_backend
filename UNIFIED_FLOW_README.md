# Flusso Unificato per Upload Documenti Clinici

## Panoramica

Il sistema ora supporta un **flusso unificato** che tratta ogni documento PDF come un potenziale pacchetto clinico completo da segmentare automaticamente. Questo garantisce parità di comportamento tra l'upload di singoli documenti e l'upload di cartelle cliniche complete.

## Workflow

### 1. Upload & OCR
- L'utente carica un PDF contenente l'intera cartella clinica
- Il testo viene estratto via **OCR Mistral AI** (saltando pdfplumber)
- Il testo OCR completo viene salvato come file standalone

### 2. Segmentazione Automatica
- Il testo viene suddiviso in sezioni basandosi su frasi d'inizio predefinite
- Tipi di sezione supportati:
  - `lettera_dimissione`
  - `anamnesi`
  - `epicrisi_ti`
  - `cartellino_anestesiologico`
  - `intervento`
  - `coronarografia`
  - `eco_preoperatorio`
  - `eco_postoperatorio`
  - `tc_cuore`

### 3. Trattamento per Sezione
Ogni sezione identificata viene trattata come documento autonomo:
- **Creazione cartella**: `uploads/{patient_id}/{doc_type}/`
- **Salvataggio PDF**: Copia del PDF originale nella cartella della sezione
- **Salvataggio testo**: Testo della sezione come file `.txt`
- **Estrazione entità**: Usando il prompt dedicato al tipo di documento
- **Persistenza**: JSON + Excel come per i singoli documenti

### 4. Dashboard
- Appare come se l'utente avesse caricato più file separati
- Ogni sezione è visibile come documento indipendente
- Stessi stati e artefatti previsti per i singoli documenti

## Utilizzo

### Attivazione del Flusso Unificato

Per attivare il nuovo flusso, aggiungi il parametro `process_as_packet=true` all'upload:

```bash
curl -X POST http://localhost:5000/api/upload-document \
  -F "file=@cartella_clinica.pdf" \
  -F "patient_id=12345" \
  -F "process_as_packet=true"
```

### Parametri

- `file`: File PDF da caricare (obbligatorio)
- `patient_id`: ID paziente (opzionale se non specificato viene generato automaticamente)
- `process_as_packet`: 
  - `"true"`: Attiva il flusso unificato
  - `"false"`: Usa il flusso originale (default)

## Nuovi Endpoint

### 1. Stato Processing Pacchetto
```bash
GET /api/document-packet-status/{patient_id}
```

Risposta:
```json
{
  "patient_id": "12345",
  "status": "completed",
  "message": "Elaborazione completata. Sezioni trovate: 5, mancanti: 2",
  "progress": 100,
  "filename": "cartella_clinica.pdf",
  "sections_found": ["lettera_dimissione", "intervento", "coronarografia", "eco_preoperatorio", "eco_postoperatorio"],
  "sections_missing": ["anamnesi", "epicrisi_ti"],
  "documents_created": [
    {
      "document_id": "doc_12345_lettera_dimissione_cartella_clinica",
      "document_type": "lettera_dimissione",
      "filename": "cartella_clinica_lettera_dimissione.pdf",
      "status": "processed",
      "entities_count": 45
    }
  ],
  "errors": []
}
```

### 2. Testo OCR Estratto
```bash
GET /api/document-ocr-text/{patient_id}
```

Risposta:
```json
{
  "patient_id": "12345",
  "filename": "cartella_clinica_ocr_text.txt",
  "ocr_text": "Testo completo estratto via OCR...",
  "metadata": {
    "original_filename": "cartella_clinica.pdf",
    "upload_date": "2024-01-15",
    "content_type": "ocr_text"
  }
}
```

## Struttura File Generata

```
uploads/
└── {patient_id}/
    ├── temp_processing/
    │   ├── cartella_clinica.pdf
    │   └── processing_status.json
    ├── ocr_text/
    │   ├── cartella_clinica_ocr_text.txt
    │   └── cartella_clinica_ocr_text.txt.meta.json
    ├── lettera_dimissione/
    │   ├── cartella_clinica_lettera_dimissione.pdf
    │   ├── cartella_clinica_lettera_dimissione_section.txt
    │   ├── entities.json
    │   └── cartella_clinica_lettera_dimissione.pdf.meta.json
    ├── intervento/
    │   ├── cartella_clinica_intervento.pdf
    │   ├── cartella_clinica_intervento_section.txt
    │   ├── entities.json
    │   └── cartella_clinica_intervento.pdf.meta.json
    └── ... (altre sezioni)
```

## Stati del Processing

- `ocr_start`: OCR in esecuzione
- `segmenting`: Segmentazione in corso
- `processing_sections`: Elaborazione sezioni
- `completed`: Elaborazione completata con successo
- `completed_with_errors`: Completata con alcuni errori
- `failed`: Elaborazione fallita

## Notifiche Sezioni Mancanti

Il sistema identifica automaticamente le sezioni attese ma non trovate nel documento e le riporta nel campo `sections_missing`. Questo permette all'utente di:

1. **Verificare completezza**: Controllare se il documento contiene tutte le sezioni attese
2. **Identificare problemi**: Capire se ci sono sezioni mancanti o non riconosciute
3. **Pianificare azioni**: Decidere se caricare documenti aggiuntivi

## Vantaggi

1. **Consistenza**: Stesso comportamento per singoli documenti e pacchetti
2. **Automazione**: Segmentazione automatica senza intervento manuale
3. **Trasparenza**: Visibilità completa su sezioni trovate e mancanti
4. **Flessibilità**: Supporto per documenti parziali o incompleti
5. **Tracciabilità**: Salvataggio del testo OCR per audit e debug

## Test

Usa il file `test_unified_flow.py` per testare il nuovo flusso:

```bash
python test_unified_flow.py
```

Il test verifica:
- Upload con `process_as_packet=true`
- Monitoraggio stato processing
- Recupero testo OCR
- Verifica documenti creati nella dashboard

## Note Tecniche

- **OCR Primario**: Il testo OCR è la fonte primaria, saltando pdfplumber
- **Processing Asincrono**: Tutto il processing avviene in background
- **Gestione Errori**: Errori per sezione non bloccano il processing delle altre
- **Compatibilità**: Il flusso originale rimane invariato e disponibile 