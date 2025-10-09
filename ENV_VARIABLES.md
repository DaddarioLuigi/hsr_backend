# Variabili d'Ambiente - HSR Backend

Questo documento descrive tutte le variabili d'ambiente necessarie per il funzionamento dell'applicazione.

## 🔴 OBBLIGATORIE

Queste variabili **DEVONO** essere configurate per il corretto funzionamento dell'applicazione:

### `TOGETHER_API_KEY`
- **Descrizione**: API key per Together AI (usata per il modello LLM DeepSeek-V3)
- **Dove ottenerla**: https://www.together.ai/
- **Esempio**: `TOGETHER_API_KEY=abc123def456...`

### `MISTRAL_API_KEY`
- **Descrizione**: API key per Mistral AI (usata per l'OCR dei documenti PDF)
- **Dove ottenerla**: https://console.mistral.ai/
- **Esempio**: `MISTRAL_API_KEY=xyz789ghi012...`

## 🟡 OPZIONALI

### Configurazione Cartelle

#### `UPLOAD_FOLDER`
- **Descrizione**: Cartella dove vengono salvati i file caricati
- **Default**: `./uploads`
- **Esempio**: `UPLOAD_FOLDER=/data/uploads`

#### `EXPORT_FOLDER`
- **Descrizione**: Cartella dove vengono salvati i file esportati (Excel)
- **Default**: `./export`
- **Esempio**: `EXPORT_FOLDER=/data/export`

### CORS - Frontend Origins

#### `FRONTEND_ORIGINS`
- **Descrizione**: Lista di origini frontend separate da virgola (per CORS)
- **Default**: `http://localhost:3000,https://v0-vercel-frontend-development-weld.vercel.app`
- **Esempio**: `FRONTEND_ORIGINS=http://localhost:3000,https://mio-frontend.vercel.app`

### AWS S3 (Opzionale)

Se configurate, i file vengono salvati su AWS S3 invece che localmente.

#### `AWS_ACCESS_KEY_ID`
- **Descrizione**: Access Key ID per AWS
- **Esempio**: `AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE`

#### `AWS_SECRET_ACCESS_KEY`
- **Descrizione**: Secret Access Key per AWS
- **Esempio**: `AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

#### `AWS_REGION`
- **Descrizione**: Regione AWS
- **Default**: `us-east-1`
- **Esempio**: `AWS_REGION=eu-west-1`

#### `S3_BUCKET_NAME`
- **Descrizione**: Nome del bucket S3 per i file
- **Esempio**: `S3_BUCKET_NAME=hsr-backend-uploads`

#### `S3_BUCKET_EXPORT`
- **Descrizione**: Nome del bucket S3 per i file Excel
- **Default**: Usa `S3_BUCKET_NAME`
- **Esempio**: `S3_BUCKET_EXPORT=hsr-backend-exports`

### Limiti Upload

#### `MAX_UPLOAD_MB`
- **Descrizione**: Dimensione massima file singolo in MB
- **Default**: `25`
- **Esempio**: `MAX_UPLOAD_MB=50`

#### `MAX_TOTAL_UPLOAD_MB`
- **Descrizione**: Dimensione massima totale upload in MB
- **Default**: `100`
- **Esempio**: `MAX_TOTAL_UPLOAD_MB=200`

## 📝 Come Configurare

### Sviluppo Locale

1. Crea un file `.env` nella root del progetto
2. Copia le variabili necessarie da questo documento
3. Sostituisci i valori di esempio con i tuoi valori reali

```bash
# .env
TOGETHER_API_KEY=your_together_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Produzione (Railway, Render, etc.)

1. Vai alle impostazioni del tuo servizio
2. Aggiungi le variabili d'ambiente nel pannello di configurazione
3. Riavvia il servizio

### Verifica Configurazione

Per verificare che le variabili siano configurate correttamente, l'applicazione:
- **TOGETHER_API_KEY**: Fallirà all'avvio del `DocumentController` se mancante
- **MISTRAL_API_KEY**: Fallirà al primo processing di un documento se mancante

I log mostreranno chiaramente quale API key manca.

## 🚨 Problemi Comuni

### Documento non viene elaborato
Se carichi un documento ma non viene elaborato:
1. Verifica che `TOGETHER_API_KEY` sia configurata
2. Verifica che `MISTRAL_API_KEY` sia configurata
3. Controlla i log per messaggi di errore
4. Controlla la cartella `uploads/<patient_id>/errors/` per dettagli sull'errore

### Errore "TOGETHER_API_KEY non configurata"
- Configura la variabile `TOGETHER_API_KEY` nelle impostazioni del servizio
- Riavvia l'applicazione

### Errore "MISTRAL_API_KEY non configurata"
- Configura la variabile `MISTRAL_API_KEY` nelle impostazioni del servizio
- Riavvia l'applicazione

