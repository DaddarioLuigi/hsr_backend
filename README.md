# HSR Backend API

Backend Flask per la gestione di pazienti, documenti clinici, entità estratte ed esportazione dati in Excel.

## Requisiti

- Python 3.9+
- pip

## Installazione

1. Clona il repository o copia tutti i file backend in una cartella.
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
3. (Opzionale) Crea la cartella `uploads/` nella root del progetto se non esiste:
   ```bash
   mkdir uploads
   ```

## Avvio del server

```bash
python app.py
```

Il server sarà disponibile su [http://localhost:5000](http://localhost:5000)

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

## Configurazione Google Drive

Variabili d'ambiente per l'integrazione con Google Drive:

- `GOOGLE_APPLICATION_CREDENTIALS`: path al file JSON del service account.
- `DRIVE_FOLDER_ID`: ID della cartella principale per i PDF.
- `DRIVE_EXPORT_FOLDER_ID`: ID della cartella per i file Excel.

Le cartelle devono essere condivise con l'account del service account.

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
