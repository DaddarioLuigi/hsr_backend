# Flusso Unificato - Gestione ID Cartella Clinica

## Panoramica

Il sistema ora gestisce in modo unificato l'estrazione e la gestione dell'ID della cartella clinica tra il flusso di caricamento di documenti singoli e il flusso di caricamento di cartelle cliniche complete.

## Problemi Risolti

### 1. Inconsistenza tra Flussi
**Problema**: Il flusso unificato (`process_single_document_as_packet`) usava regex per estrarre l'ID della cartella clinica, mentre il flusso singolo usava LLM.

**Soluzione**: Entrambi i flussi ora usano LLM per estrarre l'ID dalla lettera di dimissione, garantendo consistenza e affidabilità.

### 2. Gestione Errori
**Problema**: Il flusso unificato non gestiva correttamente il caso in cui non c'è lettera di dimissione.

**Soluzione**: 
- Se non c'è lettera di dimissione, il sistema restituisce un errore chiaro
- Se l'LLM non riesce a estrarre l'ID, viene richiesto l'inserimento manuale
- Messaggi di errore più chiari e informativi

### 3. Fallback e Recovery
**Problema**: Non c'era modo di recuperare da errori di estrazione ID.

**Soluzione**: 
- Nuovi endpoint per gestire manualmente l'ID
- Possibilità di riavviare il processing con ID specifico
- Spostamento automatico delle cartelle quando necessario

## Modifiche Implementate

### 1. Controller (`controller/controller.py`)

#### `process_single_document_as_packet()`
- **Estrazione ID con LLM**: Usa la stessa logica del flusso singolo
- **Controllo lettera di dimissione**: Verifica presenza prima dell'estrazione
- **Gestione errori robusta**: Messaggi chiari e fallback appropriati
- **Logging dettagliato**: Tracciamento completo del processo

```python
# Estrazione automatica dell'ID dalla lettera di dimissione usando LLM
if lettera_section:
    resp = self.llm.get_response_from_document(
        lettera_section.text, "lettera_dimissione", model=self.model_name
    )
    extracted_json = json.loads(resp)
    extracted_id = extracted_json.get("n_cartella")
    
    if extracted_id:
        final_patient_id = str(extracted_id)
    else:
        # Richiedi inserimento manuale
        results["errors"].append("Non è stato trovato il numero di cartella nella lettera di dimissione; inserisci patient_id manualmente")
```

### 2. Pipeline di Ingestion (`pipelines/ingestion.py`)

#### `ingest_pdf_packet()`
- **Logica unificata**: Stessa priorità di estrazione ID
- **Fallback intelligente**: Cross-doc resolver come backup
- **Priorità chiare**: LLM > Cross-doc > Fornito > Temporaneo

```python
# PRIORITÀ: LLM estratto > cross-doc > fornito > temporaneo
final_id_from_cross_doc = _norm_id(global_map.get("n_cartella"))

if final_id_from_cross_doc and final_id_from_cross_doc != final_id:
    # Se l'LLM non ha trovato nulla ma il cross-doc sì, usa quello del cross-doc
    if final_id.startswith("_pending_") or final_id.startswith("_extract_"):
        final_id = final_id_from_cross_doc
```

### 3. API Endpoints (`app.py`)

#### Nuovi Endpoint

**`/api/set-patient-id/{patient_id}` (POST)**
- Imposta manualmente l'ID della cartella clinica
- Sposta automaticamente la cartella del paziente
- Aggiorna i file di stato

**`/api/restart-processing/{patient_id}` (POST)**
- Riavvia il processing con un ID specifico
- Utile quando il processing automatico fallisce

#### Endpoint Aggiornati

**`/api/document-packet-status/{patient_id}` (GET)**
- Aggiunti warnings quando manca la lettera di dimissione
- Messaggi più informativi per l'utente

**`/api/upload-document` (POST)**
- Messaggio aggiornato per informare sulla possibile richiesta manuale dell'ID

### 4. Documentazione OpenAPI (`openapi.yaml`)

- Documentazione completa dei nuovi endpoint
- Schema aggiornato per includere warnings
- Esempi di utilizzo e gestione errori

## Flusso di Utilizzo

### Scenario 1: Lettera di Dimissione Presente
1. Carica documento con `process_as_packet=true`
2. Sistema estrae automaticamente l'ID con LLM
3. Processing continua normalmente
4. Risultato: Documento processato con ID corretto

### Scenario 2: Lettera di Dimissione Assente
1. Carica documento con `process_as_packet=true`
2. Sistema rileva assenza lettera di dimissione
3. Processing fallisce con messaggio chiaro
4. Utente può:
   - Usare `/api/set-patient-id/{patient_id}` per impostare ID manualmente
   - Usare `/api/restart-processing/{patient_id}` per riavviare con ID specifico

### Scenario 3: Estrazione LLM Fallisce
1. Carica documento con `process_as_packet=true`
2. Sistema trova lettera di dimissione ma LLM non estrae ID
3. Processing fallisce con messaggio chiaro
4. Utente può usare gli endpoint di recovery

## Vantaggi

1. **Consistenza**: Entrambi i flussi usano la stessa logica
2. **Affidabilità**: LLM è più affidabile delle regex
3. **Recovery**: Possibilità di recuperare da errori
4. **UX**: Messaggi chiari e azioni concrete per l'utente
5. **Manutenibilità**: Codice più pulito e logica centralizzata

## Compatibilità

- **Backward Compatible**: I flussi esistenti continuano a funzionare
- **Gradual Rollout**: Le modifiche sono additive
- **Fallback**: Il sistema mantiene la robustezza con fallback appropriati

## Testing

Per testare le modifiche:

1. **Test con lettera di dimissione**: Verifica estrazione automatica
2. **Test senza lettera di dimissione**: Verifica gestione errori
3. **Test con ID manuale**: Verifica endpoint di recovery
4. **Test cross-doc**: Verifica fallback con cross-doc resolver

## Monitoraggio

Il sistema ora fornisce:
- Log dettagliati per ogni fase del processing
- Stati di progresso aggiornati
- Messaggi di errore specifici
- Warnings informativi per l'utente 