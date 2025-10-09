# Guida al Deployment - HSR Backend

Questa guida ti aiuterà a deployare correttamente il backend HSR in produzione.

## 🚨 Problema Comune: Documento Non Viene Elaborato

Se carichi un documento ma non viene elaborato, **molto probabilmente mancano le API keys**.

### Soluzione Rapida

1. Vai alle impostazioni del tuo servizio (Railway, Render, Heroku, etc.)
2. Aggiungi queste variabili d'ambiente:
   ```
   TOGETHER_API_KEY=your_together_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```
3. Riavvia il servizio
4. Verifica la configurazione visitando: `https://tuo-dominio.com/health`

## 📋 Checklist Pre-Deployment

Prima di deployare, assicurati di avere:

- [ ] **TOGETHER_API_KEY** - Ottienila da https://www.together.ai/
- [ ] **MISTRAL_API_KEY** - Ottienila da https://console.mistral.ai/
- [ ] Configurato le variabili d'ambiente nel servizio di hosting
- [ ] Verificato che le cartelle di upload siano writable (o configurato S3)

## 🔧 Configurazione Variabili d'Ambiente

### Railway

1. Vai su Dashboard → Project → Variables
2. Clicca "New Variable"
3. Aggiungi:
   ```
   TOGETHER_API_KEY = your_together_api_key_here
   MISTRAL_API_KEY = your_mistral_api_key_here
   ```
4. Clicca "Deploy" per riavviare

### Render

1. Vai su Dashboard → Service → Environment
2. Clicca "Add Environment Variable"
3. Aggiungi le chiavi sopra elencate
4. Il servizio si riavvierà automaticamente

### Vercel / Netlify Functions

1. Vai su Settings → Environment Variables
2. Aggiungi le variabili
3. Rideploya il servizio

### Docker / Docker Compose

Crea un file `.env` o passa le variabili al container:

```bash
docker run -e TOGETHER_API_KEY=xxx -e MISTRAL_API_KEY=yyy ...
```

O in `docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      - TOGETHER_API_KEY=${TOGETHER_API_KEY}
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
```

## 🏥 Health Check

Dopo il deployment, verifica che tutto funzioni:

```bash
curl https://tuo-dominio.com/health
```

### Risposta Corretta (Tutto OK)

```json
{
  "status": "healthy",
  "checks": {
    "together_api_key": {
      "configured": true,
      "status": "ok"
    },
    "mistral_api_key": {
      "configured": true,
      "status": "ok"
    },
    "upload_folder": {
      "path": "/app/uploads",
      "exists": true,
      "writable": true,
      "status": "ok"
    },
    "export_folder": {
      "path": "/app/export",
      "exists": true,
      "writable": true,
      "status": "ok"
    }
  }
}
```

### Risposta con Errori

```json
{
  "status": "degraded",
  "warnings": [
    "TOGETHER_API_KEY non configurata - l'elaborazione dei documenti fallirà",
    "MISTRAL_API_KEY non configurata - l'OCR dei documenti fallirà"
  ],
  "checks": {
    "together_api_key": {
      "configured": false,
      "status": "missing"
    },
    ...
  }
}
```

**Se vedi questo, configura le API keys mancanti!**

## 🐛 Debug Errori in Produzione

### 1. Controlla i Log

I log mostreranno chiaramente se mancano le API keys:

```
RuntimeError: TOGETHER_API_KEY non configurata. Assicurati di impostare la variabile d'ambiente TOGETHER_API_KEY
```

```
RuntimeError: MISTRAL_API_KEY non configurata
```

### 2. Verifica lo Stato del Processing

L'applicazione ora salva gli errori in modo persistente:

```bash
# Controlla lo stato del processing
curl https://tuo-dominio.com/api/document-packet-status/<patient_id>
```

Se c'è stato un errore, vedrai:
```json
{
  "status": "failed",
  "message": "Errore critico: ...",
  "errors": ["dettaglio errore..."]
}
```

### 3. Controlla la Cartella Errori

Se l'elaborazione fallisce, l'errore viene salvato in:
```
uploads/<patient_id>/errors/<document_type>_error.json
```

## 📦 Storage dei File

### Opzione 1: Storage Locale (Default)

I file vengono salvati nelle cartelle `./uploads` e `./export`.

**Nota**: Su servizi come Railway, Render, Heroku, i file vengono persi al restart se non usi persistent volumes.

### Opzione 2: AWS S3 (Raccomandato per Produzione)

Configura queste variabili aggiuntive:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_BUCKET_EXPORT=your-export-bucket-name  # opzionale
```

Vedi [S3_SETUP_GUIDE.md](./S3_SETUP_GUIDE.md) per maggiori dettagli.

## 🚀 Performance e Scalabilità

### Timeout Worker

L'applicazione usa Gunicorn con timeout di 360 secondi:

```toml
# nixpacks.toml
[start]
cmd = "gunicorn app:app --access-logfile - --error-logfile - --timeout 360"
```

Se i documenti sono molto grandi, potresti dover aumentare questo valore.

### Worker Concorrenti

Per gestire più richieste simultanee:

```toml
[start]
cmd = "gunicorn app:app --workers 4 --timeout 360"
```

**Attenzione**: Più worker = più memoria usata. Verifica i limiti del tuo piano.

## 📞 Supporto

Se hai problemi:

1. Verifica `/health` endpoint
2. Controlla i log del servizio
3. Controlla `uploads/<patient_id>/errors/` per errori specifici
4. Verifica che le API keys siano valide (non scadute, con crediti sufficienti)

## 🔐 Sicurezza

**Non committare mai le API keys nel codice!**

- ✅ Usa variabili d'ambiente
- ✅ Usa `.env` in locale (gitignored)
- ✅ Usa il sistema di secrets del tuo hosting
- ❌ Non mettere le keys in `app.py` o altri file
- ❌ Non pusharle su GitHub/GitLab

## 📝 Log Utili

I log ora mostrano chiaramente:
- Quando viene iniziata l'elaborazione di un documento
- Ogni tentativo di chiamata all'LLM (con retry)
- Errori critici con stack trace completo
- Stato di completamento/fallimento

Esempio log corretto:
```
INFO: Estrazione completata per lettera_dimissione (tentativo 1)
INFO: Stato processing salvato in entrambi i formati per 12345
```

Esempio log con errore:
```
ERROR: Rate limit error tentativo 1/4: ...
WARNING: Retry 2/4 dopo 1s per lettera_dimissione
ERROR: Errore critico nel processing del pacchetto documento.pdf: ...
```

