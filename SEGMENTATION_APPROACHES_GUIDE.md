# Guida agli Approcci di Segmentazione

## Panoramica

Abbiamo implementato **4 approcci diversi** per la segmentazione dei pacchetti clinici, ognuno con vantaggi e svantaggi specifici. Questa guida ti aiuta a scegliere l'approccio migliore per le tue esigenze.

## Approcci Disponibili

### 1. **Regex-Only (Originale)**
**File**: `utils/document_segmenter.py`

**Caratteristiche**:
- ⚡ **Molto veloce** (pochi millisecondi)
- 🎯 **Accuratezza media** (70-80%)
- 🔧 **Pattern fissi** basati su regex precise
- 💰 **Costo zero** (nessuna chiamata LLM)

**Quando usarlo**:
- Documenti con formattazione standard
- Testi puliti senza artefatti OCR
- Quando la velocità è prioritaria
- Budget limitato per chiamate LLM

**Limitazioni**:
- Non gestisce variazioni formattazione
- Non distingue eco pre/post automaticamente
- Pattern rigidi che potrebbero fallire

### 2. **Advanced Hybrid (Migliorato)**
**File**: `utils/advanced_segmenter.py`

**Caratteristiche**:
- ⚡ **Velocità media** (1-3 secondi)
- 🎯 **Alta accuratezza** (85-90%)
- 🔧 **Regex + LLM enhancement**
- 💰 **Costo basso** (poche chiamate LLM)

**Quando usarlo**:
- Documenti con leggere variazioni formattazione
- Quando serve distinzione eco pre/post
- Bilanciamento tra velocità e accuratezza
- Budget moderato per LLM

**Miglioramenti**:
- Pattern più flessibili per OCR
- Confidenza dinamica basata su keyword
- Validazione LLM per sezioni ambigue
- Permette sezioni multiple dello stesso tipo

### 3. **LLM-First (Innovativo)**
**File**: `utils/llm_segmenter.py`

**Caratteristiche**:
- ⚡ **Lento** (5-15 secondi)
- 🎯 **Massima accuratezza** (90-95%)
- 🔧 **Completamente LLM-driven**
- 💰 **Costo alto** (multiple chiamate LLM)

**Quando usarlo**:
- Documenti con artefatti OCR significativi
- Formattazioni molto variabili
- Quando l'accuratezza è prioritaria
- Budget elevato per LLM

**Vantaggi**:
- Massima flessibilità e adattabilità
- Gestione intelligente di casi ambigui
- Spiegazioni per ogni classificazione
- Distinzione automatica eco pre/post

### 4. **Adaptive (Raccomandato)**
**File**: `utils/adaptive_segmenter.py`

**Caratteristiche**:
- ⚡ **Velocità adattiva** (0.1-10 secondi)
- 🎯 **Accuratezza adattiva** (75-95%)
- 🔧 **Selezione automatica della strategia**
- 💰 **Costo ottimizzato**

**Quando usarlo**:
- **Raccomandato per uso generale**
- Quando non sei sicuro dell'approccio migliore
- Ottimizzazione automatica costi/prestazioni
- Gestione di documenti eterogenei

**Strategie di Selezione**:
- **Regex-Only**: Testi corti e puliti
- **Hybrid**: Caso generale
- **LLM-First**: Problemi OCR o ambiguità

## Configurazione e Utilizzo

### Configurazione Base

```python
from utils.adaptive_segmenter import AdaptiveSegmenter, SegmentationStrategy

# Approccio adattivo (raccomandato)
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.ADAPTIVE)

# Approccio specifico
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.LLM_FIRST)
```

### Livelli di Confidenza

```python
# Bassa confidenza: accetta quasi tutto
sections = segmenter.segment_document(text, confidence_level="low")

# Media confidenza: bilanciato (default)
sections = segmenter.segment_document(text, confidence_level="medium")

# Alta confidenza: solo sezioni molto sicure
sections = segmenter.segment_document(text, confidence_level="high")
```

### Configurazione Personalizzata

```python
# Imposta soglie personalizzate
segmenter.set_confidence_threshold("low", 0.3)
segmenter.set_confidence_threshold("medium", 0.6)
segmenter.set_confidence_threshold("high", 0.8)

# Permetti sezioni multiple dello stesso tipo
segmenter.set_allow_multiple_sections(True)
```

## Test e Confronto

### Esecuzione Test

```bash
# Test completo di tutti gli approcci
python test_segmentation_approaches.py
```

### Interpretazione Risultati

Il test confronta:
- **Numero di sezioni trovate**
- **Tempo di esecuzione**
- **Confidenza media**
- **Tipi di documento identificati**

### Esempio di Output

```
============================================================
RISULTATI COMPARATIVI
============================================================
Approccio            Sezioni  Tempo    Confidenza  Successo
------------------------------------------------------------
regex_only           6        0.01     N/A         ✅
advanced_hybrid      8        2.34     0.85        ✅
llm_first            9        8.67     0.92        ✅
adaptive_auto        8        2.45     0.87        ✅
adaptive_low         9        2.67     0.82        ✅
```

## Raccomandazioni per Caso d'Uso

### 🏥 **Ospedale con Documenti Standardizzati**
- **Approccio**: Advanced Hybrid
- **Confidenza**: Medium
- **Motivazione**: Documenti formattati, budget moderato

### 🔬 **Centro di Ricerca con Documenti Variabili**
- **Approccio**: LLM-First
- **Confidenza**: High
- **Motivazione**: Massima accuratezza, budget elevato

### 🏢 **Azienda con Documenti Eterogenei**
- **Approccio**: Adaptive
- **Confidenza**: Medium
- **Motivazione**: Ottimizzazione automatica, gestione variabilità

### 💰 **Startup con Budget Limitato**
- **Approccio**: Regex-Only
- **Confidenza**: Low
- **Motivazione**: Costo zero, velocità massima

## Integrazione nel Sistema

### Modifica del Pipeline

```python
# In pipelines/ingestion.py
from utils.adaptive_segmenter import AdaptiveSegmenter, SegmentationStrategy

# Sostituisci il segmenter esistente
adaptive_segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.ADAPTIVE)
sections = adaptive_segmenter.segment_document(full_md, confidence_level="medium")
```

### Configurazione per Ambiente

```python
# Development: massima flessibilità
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.LLM_FIRST)

# Production: bilanciato
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.ADAPTIVE)

# Testing: veloce
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.REGEX_ONLY)
```

## Monitoraggio e Debug

### Statistiche di Segmentazione

```python
stats = segmenter.get_segmentation_stats(sections)
print(f"Sezioni totali: {stats['total']}")
print(f"Per tipo: {stats['by_type']}")
print(f"Per strategia: {stats['by_strategy']}")
print(f"Confidenza media: {stats['avg_confidence']:.2f}")
```

### Logging Dettagliato

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# I log mostrano:
# - Strategia scelta automaticamente
# - Caratteristiche del testo analizzate
# - Sezioni trovate per ogni fase
# - Confidenza per ogni sezione
```

## Troubleshooting

### Problemi Comuni

1. **Sezioni non trovate**
   - Prova confidenza più bassa
   - Passa a LLM-First
   - Verifica pattern in `config/type_phrases.py`

2. **Performance lente**
   - Usa Regex-Only per testi semplici
   - Riduci livello confidenza
   - Considera caching risultati

3. **Costi LLM elevati**
   - Usa Adaptive con strategia automatica
   - Imposta confidenza alta
   - Considera Regex-Only per documenti standard

### Ottimizzazione

```python
# Per massima copertura
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.ADAPTIVE)
sections = segmenter.segment_document(text, confidence_level="low")

# Per massima accuratezza
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.LLM_FIRST)
sections = segmenter.segment_document(text, confidence_level="high")

# Per massima velocità
segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.REGEX_ONLY)
sections = segmenter.segment_document(text, confidence_level="medium")
```

## Roadmap

### Miglioramenti Futuri

1. **Machine Learning**
   - Training su dataset specifico
   - Predizione automatica strategia ottimale

2. **Caching Intelligente**
   - Cache risultati per documenti simili
   - Riduzione costi LLM

3. **Validazione Umana**
   - Interfaccia per correzione manuale
   - Learning da feedback utente

4. **Metriche Avanzate**
   - Precision/Recall per ogni tipo
   - Analisi errori sistematici

## Conclusione

L'**approccio adattivo** è raccomandato per la maggior parte dei casi d'uso, poiché:
- Sceglie automaticamente la strategia migliore
- Ottimizza costi e prestazioni
- Gestisce documenti eterogenei
- Fornisce statistiche dettagliate

Per casi specifici, usa l'approccio dedicato che meglio si adatta alle tue esigenze di accuratezza, velocità e budget. 