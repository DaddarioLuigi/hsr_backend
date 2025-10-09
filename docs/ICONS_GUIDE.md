# Guida Icone Professionali

Questo documento descrive le icone professionali utilizzate nel frontend, sostituendo le emoticon precedenti.

## Icone Importate da Lucide React

```typescript
import { 
  Upload,           // Caricamento file
  FileText,         // Documenti di testo
  AlertCircle,      // Errori e avvisi
  CheckCircle,      // Successo/completato
  XCircle,          // Errore/fallimento
  Info,             // Informazioni generali
  Eye,              // Visualizzazione
  FolderOpen,       // Cartelle e documenti
  ArrowRight,       // Navigazione
  Clock,            // Tempo/attesa
  User,             // Utenti/pazienti
  File,             // File generici
  HardDrive,        // Spazio/disco
  Database,         // Dati/entità
  Settings,         // Configurazione/processing
  Search,           // Ricerca
  Download,         // Download/esportazione
  Trash2,           // Eliminazione
  Edit,             // Modifica
  Plus,             // Aggiunta
  Minus,            // Rimozione
  AlertTriangle,    // Avvisi importanti
  HelpCircle        // Aiuto/documentazione
} from "lucide-react";
```

## Mappatura Sostituzioni

### Prima (Emoticon) → Dopo (Icone Professionali)

| Contesto | Emoticon | Icona Sostitutiva | Descrizione |
|----------|----------|-------------------|-------------|
| Paziente identificato | ✓ | `CheckCircle` | Conferma successo |
| Nome file | 📄 | `File` | File generico |
| Dimensione file | 📏 | `HardDrive` | Spazio/disco |
| Testo OCR | 📄 | `FileText` | Documento di testo |
| Documenti processati | 📁 | `FolderOpen` | Cartella aperta |
| Stato processing | 🔄 | `Settings` | Configurazione/elaborazione |
| Debug status | - | `Info` | Informazioni di debug |

## Utilizzo nel Codice

### Esempio di Sostituzione

```tsx
// Prima
<p className="text-sm text-green-600">
  ✓ Paziente identificato: {currentPatientName}
</p>

// Dopo
<p className="text-sm text-green-600 flex items-center gap-1">
  <CheckCircle className="h-3 w-3" />
  Paziente identificato: {currentPatientName}
</p>
```

### Esempio di File Info

```tsx
// Prima
<div className="text-sm text-gray-600">
  <p>📄 {file.name}</p>
  <p>📏 {(file.size / 1024 / 1024).toFixed(2)} MB</p>
</div>

// Dopo
<div className="text-sm text-gray-600 space-y-1">
  <p className="flex items-center gap-2">
    <File className="h-4 w-4" />
    {file.name}
  </p>
  <p className="flex items-center gap-2">
    <HardDrive className="h-4 w-4" />
    {(file.size / 1024 / 1024).toFixed(2)} MB
  </p>
</div>
```

## Vantaggi delle Icone Professionali

1. **Consistenza**: Tutte le icone provengono dalla stessa libreria (Lucide React)
2. **Scalabilità**: Icone vettoriali che si adattano a qualsiasi dimensione
3. **Accessibilità**: Migliore supporto per screen reader
4. **Professionalità**: Aspetto più pulito e professionale
5. **Personalizzazione**: Possibilità di modificare colore, dimensione e stile
6. **Performance**: Icone ottimizzate e leggere

## Dimensioni Standard

- **Piccole**: `h-3 w-3` (12px) - per indicatori e badge
- **Medie**: `h-4 w-4` (16px) - per icone nei pulsanti
- **Grandi**: `h-5 w-5` (20px) - per icone nei titoli
- **Extra grandi**: `h-6 w-6` (24px) - per icone principali

## Colori Standard

- **Successo**: `text-green-600`
- **Errore**: `text-red-600`
- **Avviso**: `text-yellow-600`
- **Info**: `text-blue-600`
- **Neutro**: `text-gray-600`

## Best Practices

1. **Sempre usare icone con testo**: Le icone da sole non sono sufficienti per l'accessibilità
2. **Mantenere consistenza**: Usare le stesse icone per le stesse azioni
3. **Dimensioni appropriate**: Scegliere la dimensione in base al contesto
4. **Colori semantici**: Usare colori che riflettono il significato dell'azione
5. **Spaziatura**: Usare `gap-1` o `gap-2` per spaziatura consistente 