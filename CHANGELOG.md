# Changelog - Bug Fixes e Miglioramenti

## 2025-10-09 - Rimozione Flusso Unificato e Pulizia Codice

### 🗑️ Rimozione Flusso Unificato

#### File Rimossi
- ❌ `pipelines/ingestion.py` - Pipeline completa per il flusso unificato
- ❌ `pipelines/router.py` - Router per estrazione sezioni
- ❌ `ocr/mistral_ocr.py` - Wrapper per Mistral OCR
- ❌ `ocr/__init__.py` - Package OCR
- ❌ `config/segmentation_config.py` - Configurazioni segmenter avanzato
- ❌ `config/type_phrases.py` - Pattern regex per identificazione sezioni
- ❌ `utils/document_segmenter.py` - Segmenter base
- ❌ `utils/advanced_segmenter.py` - Segmenter avanzato
- ❌ `utils/adaptive_segmenter.py` - Segmenter adattivo
- ❌ `utils/cross_doc_resolver.py` - Resolver cross-documento
- ❌ `utils/llm_segmenter.py` - Segmenter LLM
- ❌ `test_segmentation_approaches.py` - Test per approcci segmentazione
- ❌ `UNIFIED_FLOW_README.md` - Documentazione flusso unificato
- ❌ `SEGMENTATION_APPROACHES_GUIDE.md` - Guida approcci segmentazione
- ❌ `ADVANCED_SEGMENTATION_README.md` - Documentazione segmenter avanzato

#### Cartelle Rimosse
- ❌ `pipelines/` - Cartella completa
- ❌ `ocr/` - Cartella completa

#### Endpoint Rimossi da `app.py`
- ❌ `/api/upload-packet-ocr`
- ❌ `/api/ingest-packet-ocr-sync`
- ❌ `/api/packet-status/<pending_id>`
- ❌ `/api/document-packet-status/<patient_id>`
- ❌ `/api/document-ocr-text/<patient_id>`
- ❌ `/api/debug-processing-status/<patient_id>`
- ❌ `/api/force-complete-status/<patient_id>`
- ❌ `/api/restart-processing/<patient_id>`
- ❌ `/api/set-patient-id/<patient_id>`
- ❌ `/api/document-packet-files/<patient_id>`

#### Metodi Rimossi da `controller/controller.py`
- ❌ `process_clinical_packet_with_ocr()`
- ❌ `process_single_document_as_packet()` (300+ righe)
- ❌ `_save_ocr_text_file()`
- ❌ `_save_section_as_document()`
- ❌ `_save_packet_processing_status()`

#### Dipendenze Rimosse
- ❌ `mistralai>=1.0.0` da `requirements.txt`

### 🎯 Risultato
L'applicazione ora ha **solo il flusso tradizionale**:
- Upload singolo documento → `pdfplumber` per estrazione testo → `TOGETHER_API_KEY` per LLM
- Nessun OCR esterno - usa solo `pdfplumber` (locale)
- Nessuna segmentazione - ogni documento viene processato come singolo tipo
- Solo una API key richiesta: `TOGETHER_API_KEY`

---

## 2025-10-09 - Fix Critici per Produzione

### 🐛 Bug Fixes

#### 1. **Fix critico: Retry logic in `llm/extractor.py`**
- **Problema**: Se tutte le chiamate all'LLM fallivano, la variabile `response` non veniva mai definita, causando un `NameError`
- **Fix**: 
  - Aggiunto inizializzazione `response = None`
  - Aggiunto controllo finale con messaggio di errore chiaro
  - Aggiunto `time.sleep()` tra i retry (prima la variabile era definita ma non usata)
- **File**: `llm/extractor.py`

#### 2. **Fix: Gestione API keys mancanti**
- **Problema**: Se `TOGETHER_API_KEY` non era configurata, l'errore veniva mostrato solo quando l'LLM falliva
- **Fix**: 
  - Verifica all'inizializzazione di `LLMExtractor`
  - Messaggio di errore chiaro: "TOGETHER_API_KEY non configurata"
- **File**: `llm/extractor.py`

#### 3. **Fix: Errori silenti nei thread in background**
- **Problema**: Quando il processing dei documenti falliva (thread in background), gli errori non venivano loggati
- **Fix**: 
  - Wrapping di tutti i thread con `try/except` e logging esplicito
  - Salvataggio dello stato di errore in `processing_status.json`
  - Salvataggio dettagli errore in `uploads/<patient_id>/errors/`
- **File**: `app.py`, `controller/controller.py`

### ✨ Nuove Funzionalità

#### 1. **Health Check Endpoint**
- **Endpoint**: `GET /health`
- **Descrizione**: Verifica lo stato dell'applicazione e delle configurazioni
- **Controlla**:
  - API key configurata (TOGETHER_API_KEY)
  - Esistenza e scrivibilità cartelle upload/export
  - Stato complessivo del sistema
- **File**: `app.py`

#### 2. **Logging Migliorato**
- Aggiunto logging per ogni tentativo di retry LLM
- Logging esplicito per errori critici nei thread
- Salvataggio persistente degli errori per debug
- **File**: `llm/extractor.py`, `app.py`, `controller/controller.py`

#### 3. **Documentazione Variabili d'Ambiente**
- Creato `ENV_VARIABLES.md` con descrizione completa di tutte le variabili
- Aggiornato `README.md` con sezione "Verifica Configurazione"
- Creato `DEPLOYMENT_GUIDE.md` con guida passo-passo per il deployment
- **File**: `ENV_VARIABLES.md`, `README.md`, `DEPLOYMENT_GUIDE.md`

### 📝 Miglioramenti al Codice

#### 1. **Better Error Handling in `process_document_and_entities`**
- Catch esplicito di `RuntimeError` per API keys mancanti
- Salvataggio errori in file JSON per debug
- **File**: `controller/controller.py`

#### 2. **Retry con Backoff Esponenziale**
- Prima: `[1, 2, 4]` senza sleep
- Dopo: `[0, 1, 2, 4]` con sleep effettivo
- **File**: `llm/extractor.py`

### 🔍 Debug e Troubleshooting

#### Nuovi File di Stato/Errore

1. **Processing Status**: `uploads/<patient_id>/processing_status.json`
   - Contiene stato completo del processing
   - Aggiornato in tempo reale
   - Persistente anche dopo il completamento

2. **Error Details**: `uploads/<patient_id>/errors/<document_type>_error.json`
   - Contiene dettagli dell'errore
   - Timestamp dell'errore
   - Tipo di documento che ha fallito

### 📖 Nuova Documentazione

- `ENV_VARIABLES.md` - Guida completa alle variabili d'ambiente
- `DEPLOYMENT_GUIDE.md` - Guida deployment per produzione
- `CHANGELOG.md` - Questo file

### ⚠️ Breaking Changes

Nessuno. Tutte le modifiche sono backward-compatible.

### 🚀 Migration Guide

Se stai aggiornando da una versione precedente:

1. **Configura le API keys** (se non già fatto):
   ```bash
   TOGETHER_API_KEY=your_key_here
   ```

2. **Verifica la configurazione**:
   ```bash
   curl https://tuo-dominio.com/health
   ```

3. **Redeploy** l'applicazione

Non serve migrare dati o database.

### 🎯 Testing

Per testare le fix in locale:

1. Senza API keys:
   ```bash
   # Rimuovi le API keys
   unset TOGETHER_API_KEY
   
   # Avvia l'app
   python app.py
   
   # Verifica health check
   curl http://localhost:8080/health
   # Dovresti vedere status: "degraded" con warnings
   ```

2. Con API keys:
   ```bash
   export TOGETHER_API_KEY=your_key
   
   python app.py
   
   curl http://localhost:8080/health
   # Dovresti vedere status: "healthy"
   ```

3. Test upload documento:
   ```bash
   curl -X POST http://localhost:8080/api/upload-document \
     -F "file=@test.pdf" \
     -F "process_as_packet=true"
   
   # Controlla i log per vedere il processing
   ```

---

## Note per il Futuro

### Possibili Miglioramenti

1. **Retry con Exponential Backoff più aggressivo**
   - Attualmente: 0s, 1s, 2s, 4s
   - Possibile: 0s, 2s, 4s, 8s, 16s

2. **Queue System per Processing**
   - Attualmente: Thread diretti
   - Migliore: Redis/Celery per processing asincrono con retry automatici

3. **Monitoring e Alerting**
   - Aggiungere endpoint `/metrics` per Prometheus
   - Alert quando le API keys sono vicine al limite di rate

4. **Caching delle Risposte LLM**
   - Cachare risposte basate su hash del documento
   - Ridurrebbe costi e tempo di processing per documenti simili

