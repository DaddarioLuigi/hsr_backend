# Guida Configurazione AWS S3

Questa guida ti aiuterà a configurare l'integrazione con AWS S3 per sostituire Google Drive.

## 1. Prerequisiti

- Account AWS attivo
- Accesso alla console AWS
- Permessi per creare bucket S3 e utenti IAM

## 2. Configurazione AWS S3

### 2.1 Creazione del Bucket S3

1. Accedi alla [Console AWS S3](https://console.aws.amazon.com/s3/)
2. Clicca su "Create bucket"
3. Configura il bucket:
   - **Bucket name**: `hsr-backend-files` (o un nome univoco)
   - **Region**: Scegli la regione più vicina (es. `eu-west-1` per l'Europa)
   - **Block Public Access**: Mantieni tutte le opzioni attivate per sicurezza
   - **Bucket Versioning**: Disabilitato (opzionale)
   - **Default encryption**: Abilita la crittografia server-side
4. Clicca "Create bucket"

### 2.2 Creazione Utente IAM

1. Vai alla [Console IAM](https://console.aws.amazon.com/iam/)
2. Clicca su "Users" → "Create user"
3. Configura l'utente:
   - **User name**: `hsr-backend-s3-user`
   - **Access type**: Programmatic access
4. Clicca "Next: Permissions"

### 2.3 Assegnazione Permessi

1. Clicca "Attach existing policies directly"
2. Cerca e seleziona `AmazonS3FullAccess` (o crea una policy personalizzata più restrittiva)
3. Clicca "Next: Tags" → "Next: Review" → "Create user"
4. **IMPORTANTE**: Salva l'Access Key ID e Secret Access Key

### 2.4 Policy Personalizzata (Opzionale, Raccomandato)

Per maggiore sicurezza, crea una policy personalizzata:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::hsr-backend-files",
                "arn:aws:s3:::hsr-backend-files/*"
            ]
        }
    ]
}
```

## 3. Configurazione Variabili d'Ambiente

Aggiungi le seguenti variabili al tuo file `.env` o configurazione:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=eu-west-1
S3_BUCKET_NAME=hsr-backend-files
S3_BUCKET_EXPORT=hsr-backend-exports  # Opzionale, per file Excel
```

## 4. Struttura File S3

I file verranno organizzati automaticamente in S3 con questa struttura:

```
hsr-backend-files/
├── patients/
│   ├── patient_123/
│   │   ├── lettera_dimissione/
│   │   │   ├── documento.pdf
│   │   │   ├── entities.json
│   │   │   └── documento.pdf.meta.json
│   │   ├── anamnesi/
│   │   │   ├── documento.pdf
│   │   │   └── entities.json
│   │   └── ...
│   └── ...
└── exports/
    └── excel_files/
        └── patient_123_summary.xlsx
```

## 5. Test dell'Integrazione

Esegui lo script di test per verificare la configurazione:

```bash
python s3_example.py
```

## 6. Funzionalità Disponibili

### 6.1 Upload Automatico
- I file PDF vengono caricati automaticamente su S3 quando salvati localmente
- I file `entities.json` vengono sincronizzati con S3
- I metadati includono gli URL S3 per accesso diretto

### 6.2 Gestione File
- **Upload**: `s3_manager.upload_file(file_path, s3_key)`
- **Download**: `s3_manager.download_file(s3_key, local_path)`
- **Delete**: `s3_manager.delete_file(s3_key)`
- **URL temporaneo**: `s3_manager.get_file_url(s3_key, expires_in=3600)`

### 6.3 Integrazione FileManager
Il `FileManager` ora include automaticamente:
- Upload su S3 durante il salvataggio
- Sincronizzazione dei metadati
- Rimozione da S3 durante la cancellazione

## 7. Sicurezza

### 7.1 Best Practices
- Usa sempre HTTPS per le connessioni
- Non committare mai le credenziali AWS nel codice
- Usa policy IAM con permessi minimi necessari
- Abilita la crittografia server-side sui bucket

### 7.2 Rotazione Credenziali
- Cambia regolarmente le credenziali AWS
- Usa AWS Secrets Manager per applicazioni in produzione
- Monitora l'uso delle credenziali tramite CloudTrail

## 8. Monitoraggio e Logging

### 8.1 CloudWatch
Configura CloudWatch per monitorare:
- Operazioni S3 (Get, Put, Delete)
- Errori di accesso
- Utilizzo dello spazio

### 8.2 Logging Applicativo
L'applicazione registra automaticamente:
- Upload riusciti/falliti
- Errori di connessione
- Operazioni di sincronizzazione

## 9. Troubleshooting

### 9.1 Errori Comuni

**"Client S3 non inizializzato"**
- Verifica le variabili d'ambiente
- Controlla le credenziali AWS

**"Access Denied"**
- Verifica i permessi IAM
- Controlla che il bucket esista
- Verifica la regione AWS

**"NoCredentialsError"**
- Le credenziali AWS non sono configurate
- Verifica il formato delle credenziali

### 9.2 Debug
Abilita il logging dettagliato:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 10. Migrazione da Google Drive

### 10.1 Backup
Prima di rimuovere Google Drive:
1. Esporta tutti i file da Google Drive
2. Verifica che tutti i file siano stati caricati su S3
3. Testa l'accesso ai file tramite S3

### 10.2 Rollback
Se necessario, puoi temporaneamente disabilitare S3:
- Rimuovi le variabili d'ambiente AWS
- L'applicazione continuerà a funzionare solo con storage locale

## 11. Costi

### 11.1 Stima Costi S3
- **Storage**: ~$0.023/GB/mese
- **Transfer**: ~$0.09/GB (outbound)
- **Requests**: ~$0.0004 per 1000 GET requests

### 11.2 Ottimizzazione
- Usa la compressione per i file JSON
- Implementa lifecycle policies per archiviare file vecchi
- Considera S3 Intelligent Tiering per costi ottimali

## 12. Supporto

Per problemi o domande:
1. Controlla i log dell'applicazione
2. Verifica la configurazione AWS
3. Consulta la documentazione AWS S3
4. Contatta il team di sviluppo 