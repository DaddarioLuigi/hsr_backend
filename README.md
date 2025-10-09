# HSR Backend API

Backend Flask per la gestione di pazienti, documenti clinici, entità estratte ed esportazione dati in Excel.

## Requisiti

- Python 3.9+
- pip
- **TOGETHER_API_KEY** - API key per Together AI (obbligatoria)
- **MISTRAL_API_KEY** - API key per Mistral AI (obbligatoria)

## Installazione

1. Clona il repository o copia tutti i file backend in una cartella.
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configura le variabili d'ambiente** (vedi [ENV_VARIABLES.md](./ENV_VARIABLES.md)):
   ```bash
   # Crea un file .env nella root del progetto
   TOGETHER_API_KEY=your_together_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```
4. (Opzionale) Crea la cartella `uploads/` nella root del progetto se non esiste:
   ```bash
   mkdir uploads
   ```

## Avvio del server

```bash
python app.py
```

Il server sarà disponibile su [http://localhost:8080](http://localhost:8080)

## Verifica Configurazione

Per verificare che l'applicazione sia configurata correttamente:

```bash
curl http://localhost:8080/health
```

Questo endpoint restituisce lo stato di:
- API keys configurate (TOGETHER_API_KEY, MISTRAL_API_KEY)
- Cartelle di upload ed export
- Permessi di scrittura

**Esempio risposta OK:**
```json
{
  "status": "healthy",
  "checks": {
    "together_api_key": { "configured": true, "status": "ok" },
    "mistral_api_key": { "configured": true, "status": "ok" },
    "upload_folder": { "exists": true, "writable": true, "status": "ok" },
    "export_folder": { "exists": true, "writable": true, "status": "ok" }
  }
}
```

**Esempio risposta con errori:**
```json
{
  "status": "degraded",
  "warnings": [
    "TOGETHER_API_KEY non configurata - l'elaborazione dei documenti fallirà"
  ],
  "checks": {
    "together_api_key": { "configured": false, "status": "missing" },
    ...
  }
}
```

## Documentazione API

La documentazione OpenAPI è disponibile nel file [`openapi.yaml`](./openapi.yaml).

- Puoi visualizzarla e testarla su [Swagger Editor](https://editor.swagger.io/) copiando/incollando il contenuto del file.
- Tutte le specifiche degli endpoint, parametri e risposte sono descritte lì.

## Endpoints principali

- `GET    /api/patients` — Elenco pazienti
- `GET    /api/patient/{patient_id}` — Dettaglio paziente e lista documenti
- `POST   /api/upload-document` — Caricamento documento PDF
- `GET    /api/document/{document_id}` — Dati per l'editor di entità
- `PUT    /api/document/{document_id}` — Aggiorna le entità di un documento
- `GET    /api/export-excel` — Esporta tutti i dati in Excel

## Struttura delle cartelle

- `app.py` — Entry point Flask
- `controller/` — Logica di business
- `utils/` — Utility per file, Excel, ecc.
- `uploads/` — Cartelle e file dei pazienti e documenti
- `openapi.yaml` — Documentazione OpenAPI

## Configurazione AWS S3

Variabili d'ambiente per l'integrazione con AWS S3:

- `AWS_ACCESS_KEY_ID`: Access key ID per AWS
- `AWS_SECRET_ACCESS_KEY`: Secret access key per AWS
- `AWS_REGION`: Regione AWS (es. us-east-1)
- `S3_BUCKET_NAME`: Nome del bucket S3 per i file
- `S3_BUCKET_EXPORT`: Nome del bucket S3 per i file Excel (opzionale)

## Note per il frontend developer

- Tutte le risposte e i parametri sono documentati in `openapi.yaml`.
- Per testare upload e download file, usa strumenti come Postman o Swagger UI.
- Il backend salva i PDF e i dati associati nella cartella `uploads/`.

## Persistenza su Railway

Il backend salva i PDF e i dati associati nella cartella `uploads/`.
Su Railway abilita la persistenza con un Volume:

- Crea un Volume e montalo su `/data`
- Imposta le variabili d'ambiente del servizio:
  - `UPLOAD_FOLDER=/data/uploads`
  - `EXPORT_FOLDER=/data/export`

Opzionali:
- `MAX_UPLOAD_MB` (default `25`) per limitare la dimensione totale dell'upload

Gli upload accettano solo PDF.

Endpoint per cancellazione documenti:
- `DELETE /api/document/{document_id}` — elimina il documento; se il paziente rimane senza documenti, rimuove anche la cartella del paziente.

## Supporto

Per domande tecniche o bug, contatta il maintainer del backend.
