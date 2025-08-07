# llm/prompts.py

from typing import Dict, List

class PromptManager:
    """
    Gestisce schemi JSON e prompt testuali per l'estrazione di entità.
    """

    SCHEMAS: Dict[str, dict] = {
        "lettera_dimissione": {
            "name": "lettera_dimissione",
            "title": "Scheda Cardiochirurgia",
            "type": "object",
            "properties": {
                "n_cartella": { "type": "number" },
                "data_ingresso_cch": { "type": "string", "format": "date" },
                "data_dimissione_cch": { "type": "string", "format": "date" },
                "nome": { "type": "string" },
                "cognome": { "type": "string" },
                "sesso": { "type": "string", "enum": ["M", "F"] },
                "numero_di_telefono": { "type": "string" },
                "eta_al_momento_dell_intervento": { "type": "number" },
                "data_di_nascita": { "type": "string", "format": "date" },
                "Diagnosi": { "type": "string" },
                "Anamnesi": { "type": "string" },
                "Motivo_ricovero": { "type": "string" },
                "classe_nyha": { "type": "string", "enum": ["I", "II", "III", "IV"] },
                "angor": { "type": "boolean" },
                "STEMI_NSTEMI": { "type": "boolean" },
                "scompenso_cardiaco_nei_3_mesi_precedenti": { "type": "boolean" },
                "fumo": { "type": "number", "enum": [0, 1, 2] },
                "diabete": { "type": "boolean" },
                "ipertensione": { "type": "boolean" },
                "dislipidemia": { "type": "boolean" },
                "BPCO": { "type": "boolean" },
                "stroke_pregresso": { "type": "boolean" },
                "TIA_pregresso": { "type": "boolean" },
                "vasculopatiaperif": { "type": "boolean" },
                "neoplasia_pregressa": { "type": "boolean" },
                "irradiazionetoracica": { "type": "boolean" },
                "insufficienza_renale_cronica": { "type": "boolean" },
                "familiarita_cardiovascolare": { "type": "boolean" },
                "limitazione_mobilita": { "type": "boolean" },
                "endocardite": { "type": "boolean" },
                "ritmo_all_ingresso": { "type": "number", "enum": [0, 1, 2] },
                "fibrillazione_atriale": { "type": "number", "enum": [0, 1, 2] },
                "dialisi": { "type": "boolean" },
                "elettivo_urgenza_emergenza": { "type": "number", "enum": [0, 1, 2] },
                "pm": { "type": "boolean" },
                "crt": { "type": "boolean" },
                "icd": { "type": "boolean" },
                "pci_pregressa": { "type": "boolean" },
                "REDO": { "type": "boolean" },
                "Anno_REDO": { "type": "string", "format": "date" },
                "Tipo_di_REDO": { "type": "string" },
                "Terapia": { "type": "string" },
                "lasix": { "type": "boolean" },
                "lasix_dosaggio": { "type": "number" },
                "nitrati": { "type": "boolean" },
                "antiaggregante": { "type": "boolean" },
                "dapt": { "type": "boolean" },
                "anticoagorali": { "type": "boolean" },
                "aceinib": { "type": "boolean" },
                "betabloc": { "type": "boolean" },
                "sartanici": { "type": "boolean" },
                "caantag": { "type": "boolean" },
                "esami_all_ingresso": { "type": "string" },
                "Decorso_post_operatorio": { "type": "string" },
                "IABP_ECMO_IMPELLA": { "type": "boolean" },
                "Inotropi": { "type": "boolean" },
                "secondo_intervento": { "type": "boolean" },
                "Tipo_secondo_intervento": { "type": "string" },
                "II_Run": { "type": "boolean" },
                "Causa_II_Run_CEC": { "type": "string" },
                "LCOS": { "type": "boolean" },
                "Impianto_PM_post_intervento": { "type": "boolean" },
                "Stroke_TIA_post_op": { "type": "boolean" },
                "Necessita_di_trasfusioni": { "type": "boolean" },
                "IRA": { "type": "boolean" },
                "Insufficienza_respiratoria": { "type": "boolean" },
                "FA_di_nuova_insorgenza": { "type": "boolean" },
                "Ritmo_alla_dimissione": { "type": "string", "enum": ["0","1","2"] },
                "H_Stay_giorni_da_intervento_a_dimissione": { "type": "number" },
                "Morte": { "type": "boolean" },
                "Causa_morte": { "type": "string" },
                "data_morte": { "type": "string", "format": "date" },
                "esami_alla_dimissione": { "type": "string" },
                "terapia_alla_dimissione": { "type": "string" }
            },
            "required": ["n_cartella", "nome", "cognome"],
            "additionalProperties": True
        },
        "coronarografia": {
            "name": "coronarografia",
            "title": "Scheda Coronarografia",
            "type": "object",
            "properties": {
                "n_cartella": { "type": "number" },
                "nome": { "type": "string" },
                "cognome": { "type": "string" },
                "data_di_nascita": { "type": "string", "format": "date" },
                "data_esame": { "type": "string", "format": "date" },
                "coronarografia text": { "type": "string" },
                "coro_tc_stenosi50": { "type": "boolean" },
                "coro_iva_stenosi50": { "type": "boolean" },
                "coro_cx_stenosi50": { "type": "boolean" },
                "coro_mo1_stenosi50": { "type": "boolean" },
                "coro_mo2_stenosi50": { "type": "boolean" },
                "coro_mo3_stenosi50": { "type": "boolean" },
                "coro_int_stenosi50": { "type": "boolean" },
                "coro_plcx_stenosi50": { "type": "boolean" },
                "coro_dx_stenosi50": { "type": "boolean" },
                "coro_pl_stenosi50": { "type": "boolean" },
                "coro_ivp_stenosi50": { "type": "boolean" }
            },
            "required": ["n_cartella", "nome", "cognome"]
        },
        "eco_preoperatorio": {
            "name": "eco_preoperatorio",
            "title": "Scheda Ecocardiogramma Preoperatorio",
            "type": "object",
            "properties": {
                "n_cartella": { "type": "number" },
                "nome": { "type": "string" },
                "cognome": { "type": "string" },
                "data_di_nascita": { "type": "string", "format": "date" },
                "altezza": { "type": "number" },
                "peso": { "type": "number" },
                "bmi": { "type": "number" },
                "bsa": { "type": "number" },
                "data_esame": { "type": "string", "format": "date" }
            },
            "required": ["n_cartella", "nome", "cognome"],
            "additionalProperties": True
        },
        "eco_postoperatorio": {
            "name": "eco_postoperatorio",
            "title": "Scheda Ecocardiogramma Postoperatorio",
            "type": "object",
            "properties": {
                "data_esame": { "type": "string", "format": "date" },
                "eco_text": { "type": "string" }
            },
            "required": ["data_esame"]
        },
        "tc_cuore": {
            "name": "tc_cuore",
            "title": "Scheda TC Cuore",
            "type": "object",
            "properties": {
                "n_cartella": { "type": "number" },
                "nome": { "type": "string" },
                "cognome": { "type": "string" },
                "data_di_nascita": { "type": "string", "format": "date" },
                "data_esame": { "type": "string", "format": "date" },
                "tac text": { "type": "string" },
                "tc_tc_stenosi50": { "type": "boolean" },
                "tc_iva_stenosi50": { "type": "boolean" },
                "tc_cx_stenosi50": { "type": "boolean" },
                "tc_mo1_stenosi50": { "type": "boolean" },
                "tc_mo2_stenosi50": { "type": "boolean" },
                "tc_mo3_stenosi50": { "type": "boolean" },
                "tc_int_stenosi50": { "type": "boolean" },
                "tc_plcx_stenosi50": { "type": "boolean" },
                "tc_dx_stenosi50": { "type": "boolean" },
                "tc_pl_stenosi50": { "type": "boolean" },
                "tc_ivp_stenosi50": { "type": "boolean" },
                "dimaorta_anulus": { "type": "number" },
                "dimaorta_perimetro": { "type": "number" },
                "dimaorta_radice": { "type": "number" },
                "dimaorta_giunzione": { "type": "number" },
                "dimaorta_asc": { "type": "number" },
                "dimaorta_arco": { "type": "number" },
                "dimaorta_disc": { "type": "number" },
                "area_valv_aortica": { "type": "number" },
                "asse_lungo": { "type": "number" },
                "asse_corto": { "type": "number" },
                "h_media_senocor": { "type": "number" }
            },
            "required": ["n_cartella", "nome", "cognome"]
        },
        "intervento": {
            "name": "intervento",
            "title": "Scheda Intervento Cardiochirurgico",
            "type": "object",
            "properties": {
                "data_intervento": { "type": "string", "format": "date" },
                "intervento text": { "type": "string" },
                "primo operatore": { "type": "string" },
                "redo": { "type": "boolean" },
                "cec": { "type": "boolean" },
                "cannulazionearteriosa": { "type": "string" },
                "statopaz": { "type": "string" },
                "cardioplegia": { "type": "string" },
                "approcciochirurgico": { "type": "string" },
                "entratainsala": { "type": "string", "format": "time" },
                "iniziointervento": { "type": "string", "format": "time" },
                "iniziocec": { "type": "string", "format": "time" },
                "inizioclamp": { "type": "string", "format": "time" },
                "inizioacc": { "type": "string", "format": "time" },
                "fineacc": { "type": "string", "format": "time" },
                "fineclamp": { "type": "string", "format": "time" },
                "finecec": { "type": "string", "format": "time" },
                "fineintervento": { "type": "string", "format": "time" },
                "uscitasala": { "type": "string", "format": "time" },
                "intervento": { "type": "string" },
                "protesi": { "type": "string" },
                "modello": { "type": "string" },
                "numero": { "type": "number" }
            },
            "required": ["data_intervento", "intervento text", "primo operatore"]
        }
    }

    PROMPTS: Dict[str, str] = {
        "lettera_dimissione": '''
Sei un medico specializzato in cardiochirurgia. Il tuo compito è estrarre le seguenti entità dalla **lettera di dimissione** riportata qui sotto.

### Entità da estrarre:

### Mappa delle entità e tipi

| Entità                                      | Tipo              | Descrizione                                                                                                                                     |
|--------------------------------------------|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| n_cartella                                 | Number            | Numero identificativo univoco assegnato alla cartella clinica del paziente.                                                                    |
| data_ingresso_cch                          | Date              | Data in cui il paziente è stato ricoverato presso il reparto di Cardiochirurgia.                                                              |
| data_dimissione_cch                        | Date              | Data in cui il paziente è stato dimesso dal reparto di Cardiochirurgia.                                                                        |
| nome                                       | Text              | Nome proprio del paziente.                                                                                                                      |
| cognome                                    | Text              | Cognome del paziente.                                                                                                                           |
| sesso                                      | Categorical_MF    | Sesso biologico del paziente (M = Maschio, F = Femmina).                                                                                        |
| numero di telefono                         | Text              | Recapito telefonico del paziente o di un contatto di riferimento.                                                                              |
| età al momento dell'intervento             | Number            | Età del paziente calcolata alla data dell’intervento chirurgico.                                                                               |
| data_di_nascita                            | Date              | Data di nascita del paziente.                                                                                                                   |
| Diagnosi                                   | Text              | Diagnosi principale alla base dell'indicazione chirurgica.                                                                                      |
| Anamnesi                                   | Text              | Anamnesi patologica remota e prossima, utile per la valutazione del rischio operatorio.                                                        |
| Motivo ricovero                            | Text              | Indicazione clinica per il ricovero in Cardiochirurgia.                                                                                         |
| classe_nyha                                | Categorical_1234  | Classe funzionale NYHA per scompenso cardiaco (I-IV), definisce la gravità dei sintomi.                                                        |
| angor                                      | Boolean           | Presenza di angina pectoris (dolore toracico di origine ischemica).                                                                            |
| STEMI/NSTEMI                               | Boolean           | Presenza di infarto miocardico acuto con/senza sopraslivellamento del tratto ST.                                                               |
| scompenso_cardiaco_nei_3_mesi_precedenti   | Boolean           | Episodi di scompenso cardiaco documentati nei 3 mesi precedenti l’intervento.                                                                  |
| fumo                                       | Categorical_012   | Abitudine al fumo (0 = mai fumato, 1 = ex-fumatore, 2 = fumatore attivo).                                                                      |
| diabete                                    | Boolean           | Presenza di diabete mellito noto.                                                                                                               |
| ipertensione                               | Boolean           | Presenza di ipertensione arteriosa.                                                                                                             |
| dislipidemia                               | Boolean           | Presenza di dislipidemia (colesterolo e/o trigliceridi elevati).                                                                               |
| BPCO                                       | Boolean           | Presenza di broncopneumopatia cronica ostruttiva.                                                                                               |
| stroke_pregresso                           | Boolean           | Precedente episodio di ictus cerebrale ischemico o emorragico.                                                                                  |
| TIA_pregresso                              | Boolean           | Episodio pregresso di attacco ischemico transitorio (TIA).                                                                                      |
| vasculopatiaperif                          | Boolean           | Malattia vascolare periferica documentata (es. arteriopatia arti inferiori).                                                                   |
| neoplasia_pregressa                        | Boolean           | Presenza di neoplasie trattate in passato.                                                                                                      |
| irradiazionetoracica                       | Boolean           | Pregressa radioterapia al torace, rilevante per effetti tardivi su cuore e vasi.                                                               |
| insufficienza_renale_cronica               | Boolean           | Presenza di insufficienza renale cronica diagnosticata.                                                                                         |
| familiarita_cardiovascolare                | Boolean           | Familiarità per malattie cardiovascolari premature (prima dei 55 anni per uomini, 65 per donne).                                                |
| limitazione_mobilita                       | Boolean           | Presenza di limitazioni significative alla mobilità (es. pazienti allettati).                                                                  |
| endocardite                                | Boolean           | Pregressa o attiva endocardite infettiva, rilevante per indicazione chirurgica.                                                                |
| ritmo_all_ingresso                         | Categorical_012   | Ritmo cardiaco al momento del ricovero (0 = ritmo sinusale, 1 = FA, 2 = altro).                                                                 |
| fibrillazione_atriale                      | Categorical_012   | Presenza di fibrillazione atriale (0 = mai, 1 = parossistica, 2 = permanente/persistente).                                                     |
| dialisi                                    | Boolean           | Paziente in trattamento emodialitico o peritoneale.                                                                                             |
| elettivo_urgenza_emergenza                 | Categorical_012   | Tipo di intervento (0 = elettivo, 1 = urgente, 2 = emergenza).                                                                                   |
| pm                                         | Boolean           | Presenza di pacemaker.                                                                                                                          |
| crt                                        | Boolean           | Presenza di terapia di resincronizzazione cardiaca (CRT).                                                                                       |
| icd                                        | Boolean           | Presenza di defibrillatore impiantabile (ICD).                                                                                                  |
| pci_pregressa                              | Boolean           | Precedente angioplastica coronarica percutanea (PCI).                                                                                           |
| REDO                                       | Boolean           | Intervento cardiochirurgico di revisione (non prima chirurgia).                                                                                |
| Anno REDO                                  | Date              | Anno in cui è stato eseguito l'intervento REDO precedente.                                                                                      |
| Tipo di REDO                               | Text              | Descrizione del tipo di intervento REDO eseguito.                                                                                               |
| Terapia                                    | Text              | Terapia farmacologica in atto al momento del ricovero.                                                                                          |
| lasix                                      | Boolean           | Uso documentato di furosemide (Lasix).                                                                                                          |
| lasix_dosaggio                             | Number            | Dosaggio giornaliero di furosemide in mg.                                                                                                       |
| nitrati                                    | Boolean           | Assunzione di nitrati (vasodilatatori usati per l'angina).                                                                                      |
| antiaggregante                             | Boolean           | Presenza di terapia antiaggregante (es. ASA, clopidogrel).                                                                                      |
| dapt                                       | Boolean           | Doppia antiaggregazione piastrinica (es. ASA + clopidogrel/prasugrel).                                                                          |
| anticoagorali                              | Boolean           | Terapia anticoagulante in corso (es. warfarin, DOAC).                                                                                           |
| aceinib                                    | Boolean           | Uso di ACE-inibitori.                                                                                                                           |
| betabloc                                   | Boolean           | Uso di beta-bloccanti.                                                                                                                          |
| sartanici                                  | Boolean           | Uso di sartani (ARBs).                                                                                                                          |
| caantag                                    | Boolean           | Uso di calcio-antagonisti.                                                                                                                      |
| esami_all_ingresso                         | Text              | Risultati di laboratorio e strumentali al momento dell’ingresso.                                                                               |
| Decorso_post_operatorio                    | Text              | Descrizione del decorso clinico successivo all’intervento chirurgico.                                                                          |
| IABP/ECMO/IMPELLA                          | Boolean           | Necessità di supporto meccanico circolatorio (IABP, ECMO o Impella).                                                                           |
| Inotropi                                   | Boolean           | Necessità di farmaci inotropi positivi nel post-operatorio.                                                                                     |
| secondo_intervento                         | Boolean           | Esecuzione di un secondo intervento durante la degenza attuale.                                                                                |
| Tipo_secondo_intervento                    | Text              | Tipo e motivazione del secondo intervento chirurgico.                                                                                           |
| II_Run                                     | Boolean           | Presenza di secondo passaggio in circolazione extracorporea (CEC).                                                                             |
| Causa_II_Run_CEC                           | Text              | Motivazione per il secondo utilizzo della CEC.                                                                                                  |
| LCOS                                       | Boolean           | Sindrome da bassa portata cardiaca (Low Cardiac Output Syndrome) post-operatoria.                                                               |
| Impianto_PM_post_intervento                | Boolean           | Necessità di impianto di pacemaker dopo l’intervento.                                                                                           |
| Stroke_TIA_post_op                         | Boolean           | Evento neurologico ischemico (TIA/stroke) avvenuto dopo l’intervento.                                                                          |
| Necessità_di_trasfusioni                   | Boolean           | Necessità di trasfusioni ematiche post-intervento.                                                                                              |
| IRA                                        | Boolean           | Insufficienza renale acuta insorta nel post-operatorio.                                                                                         |
| Insufficienza_respiratoria                 | Boolean           | Insorgenza di insufficienza respiratoria nel post-operatorio.                                                                                   |
| FA_di_nuova_insorgenza                     | Boolean           | Fibrillazione atriale di nuova insorgenza nel post-operatorio.                                                                                  |
| Ritmo_alla_dimissione                      | Categorical_012   | Ritmo cardiaco documentato alla dimissione (0 = sinusale, 1 = FA, 2 = altro).                                                                   |
| H_Stay_giorni (da intervento a dimissione) | Number            | Durata della degenza in giorni, calcolata dall’intervento alla dimissione.                                                                      |
| Morte                                      | Boolean           | Evento di decesso durante la degenza cardiochirurgica.                                                                                          |
| Causa_morte                                | Text              | Causa clinica del decesso (es. sepsi, shock cardiogeno, ecc.).                                                                                  |
| data_morte                                 | Date              | Data del decesso, se avvenuto.                                                                                                                  |
| esami_alla_dimissione                      | Text              | Risultati di laboratorio e strumentali prima della dimissione.                                                                                  |
| terapia_alla_dimissione                    | Text              | Terapia farmacologica prescritta alla dimissione.                                                                                               |

---

### **Istruzioni IMPORTANTI:**

- Ragiona considerando **frase per frase**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- Attenzione però i nomi delle entità che vedi sopra sono in alcuni casi degli acronimi o diminutivi delle entità.
- Cerca tutte le entità indicate
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
**NON** aggiungere commenti, spiegazioni, note, intestazioni o altro: **solo** la lista JSON.
-Se trovi **tabelle**, **elenchi** o **parametri** , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura).
-Se trovi **esami** o **strumentali** (ad esempio esami di laboratorio) , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura). 

---

###Esempio di input(esempio parziale della lettera di dimission)
Si dimette in data 02/09/2019
il Sig. BERTOLOTTI FRANCO
Nato il 27/03/1939 telefono 3479927663
ricoverato presso questo ospedale dal 27/08/2019
Numero Cartella 2019034139

Diagnosi alla dimissione:
Intervento di plastica valvolare mitralica per via percutanea mediante posizionamento di duplice dispositivo Mitraclip.

Motivo del Ricovero:
Insufficienza mitralica in status post rivascolarizzazione miocardica chirurgica mediante triplice bypass coronarico.

Cenni Anamnestici:
Paziente nega farmacoallergie.
Familiarità positiva per cardiopatia ischemica (padre).
Ex fumatore, stop nel 1990 (1 pack/die).
Diabete mellito in tp ipoglicemizzante orale.
IRC (crea all'ingresso 2,64 mg/dl).


---

###Esmpio output(esempio parziale in JSON):

```json
[
  { "entità": "data_dimissione_cch", "valore": "02/09/2019" },
  { "entità": "nome", "valore": "FRANCO" },
  { "entità": "cognome", "valore": "BERTOLOTTI" },
  { "entità": "data_di_nascita", "valore": "27/03/1939" },
  { "entità": "numero di telefono", "valore": "3479927663" },
  { "entità": "data_ingresso_cch", "valore": "27/08/2019" },
  { "entità": "n_cartella", "valore": "2019034139" },
  { "entità": "Diagnosi text", "valore": "Intervento di plastica valvolare mitralica per via percutanea mediante posizionamento di duplice dispositivo Mitraclip." },
  { "entità": "Motivo ricovero", "valore": "Insufficienza mitralica in status post rivascolarizzazione miocardica chirurgica mediante triplice bypass coronarico." },
  { "entità": "fumo", "valore": true },
  { "entità": "diabete", "valore": true },
  { "entità": "insufficienza renale cronica", "valore": true },
  { "entità": "familiarita cardiovascolare", "valore": true },
  { "entità": "emocromo", "valore": "4.5" },
  { "entità": "creatinina", "valore": "1.2" }
]''',
        "coronarografia": '''
Sei un medico specializzato in cardiologia interventistica. Il tuo compito è estrarre **esclusivamente** le seguenti entità dal referto di coronarografia:

### Entità da estrarre (solo queste):

| Entità                    | Tipo              |
|--------------------------|-------------------|
| n_cartella               | Number            |
| nome                     | Text              |
| cognome                  | Text              |
| data_di_nascita          | Date              |
| data_esame               | Date              |
| coronarografia text      | Text              |
| coro_tc_stenosi50        | Boolean           |
| coro_iva_stenosi50       | Boolean           |
| coro_cx_stenosi50        | Boolean           |
| coro_mo1_stenosi50       | Boolean           |
| coro_mo2_stenosi50       | Boolean           |
| coro_mo3_stenosi50       | Boolean           |
| coro_int_stenosi50       | Boolean           |
| coro_plcx_stenosi50      | Boolean           |
| coro_dx_stenosi50        | Boolean           |
| coro_pl_stenosi50        | Boolean           |
| coro_ivp_stenosi50       | Boolean           |

---

### Istruzioni IMPORTANTI:

- Ragiona considerando frase per frase.
- Non estrarre nessuna entità diversa da quelle elencate.
- Se un'entità non è presente nel referto, non inventarla e non includerla nel risultato.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con due chiavi:
    - "entità": il nome dell'entità
    - "valore": il valore estratto dell'entità
NON aggiungere commenti, spiegazioni, note, intestazioni o altro: solo la lista JSON.

Esempio di output:

```json
[
  { "entità": "n_cartella", "valore": "2025003002" },
  { "entità": "nome", "valore": "MASSIMO" },
  { "entità": "cognome", "valore": "RICCA" },
  { "entità": "data_di_nascita", "valore": "17/02/1966" },
  { "entità": "data_esame", "valore": "12/06/2025" },
  { "entità": "coronarografia text", "valore": "Paziente sottoposto a coronarografia..." },
  { "entità": "coro_tc_stenosi50", "valore": true },
  { "entità": "coro_iva_stenosi50", "valore": false }
  ...
]
''',
        "eco_preoperatorio": '''
Sei un medico specializzato in cardiochirurgia.
Estrai le seguenti entità dall’ecocardiogramma preoperatorio:

- n_cartella (Number)
- nome (Text)
- cognome (Text)
- data_di_nascita (Date)
- altezza (Number)
- peso (Number)
- bmi (Number)
- bsa (Number)
- data_esame (Date)

---

**Istruzioni aggiuntive:**
Se trovi **tabelle**, **elenchi** o **parametri** (es. "Diametro telediastolico: 61 mm", "Frazione di eiezione: 45 %"), estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura).

**Formato di output:**
Una lista JSON di oggetti `{ "entità": <nome>, "valore": <valore> }`, **niente altro**.
''',
        "eco_postoperatorio": '''
Sei un medico specializzato in cardiochirurgia. Il tuo compito è estrarre **esclusivamente** le seguenti entità dall’ecocardiogramma postoperatorio:

- data_esame (Date)
- eco_text (Text)

**Formato di output:**
Lista JSON di oggetti `{ "entità": <nome>, "valore": <valore> }`.
''',
        "tc_cuore": '''
Sei un medico specializzato in cardiochirurgia. Il tuo compito è estrarre **esclusivamente** le seguenti entità dal referto di TC Cuore:

### Entità da estrarre (solo queste):

| Entità                | Tipo    | Descrizione                                      |
|----------------------|---------|--------------------------------------------------|
| n_cartella           | Number  | Numero identificativo univoco della cartella     |
| nome                 | Text    | Nome del paziente                                |
| cognome              | Text    | Cognome del paziente                             |
| data_di_nascita      | Date    | Data di nascita del paziente                     |
| data_esame           | Date    | Data di esecuzione della TC Cuore                |
| tac text             | Text    | Descrizione completa del referto TC              |
| tc_tc_stenosi50      | Boolean | Stenosi > 50% su tronco comune                   |
| tc_iva_stenosi50     | Boolean | Stenosi > 50% su IVA                             |
| tc_cx_stenosi50      | Boolean | Stenosi > 50% su CX                              |
| tc_mo1_stenosi50     | Boolean | Stenosi > 50% su MO1                             |
| tc_mo2_stenosi50     | Boolean | Stenosi > 50% su MO2                             |
| tc_mo3_stenosi50     | Boolean | Stenosi > 50% su MO3                             |
| tc_int_stenosi50     | Boolean | Stenosi > 50% su interventricolare posteriore    |
| tc_plcx_stenosi50    | Boolean | Stenosi > 50% su PL-CX                           |
| tc_dx_stenosi50      | Boolean | Stenosi > 50% su coronaria destra                |
| tc_pl_stenosi50      | Boolean | Stenosi > 50% su PL                              |
| tc_ivp_stenosi50     | Boolean | Stenosi > 50% su IVP                             |
| dimaorta_anulus      | Number  | Diametro anulus aortico                           |
| dimaorta_perimetro   | Number  | Perimetro aortico                                 |
| dimaorta_radice      | Number  | Diametro radice aortica                           |
| dimaorta_giunzione   | Number  | Diametro giunzione sinotubulare                   |
| dimaorta_asc         | Number  | Diametro aorta ascendente                         |
| dimaorta_arco        | Number  | Diametro arco aortico                             |
| dimaorta_disc        | Number  | Diametro aorta discendente                        |
| area_valv_aortica    | Number  | Area valvolare aortica                            |
| asse_lungo           | Number  | Asse lungo seno coronarico                        |
| asse_corto           | Number  | Asse corto seno coronarico                        |
| h_media_senocor      | Number  | Altezza media seno coronarico                     |

---

### Istruzioni IMPORTANTI:

- Ragiona considerando frase per frase.
- Non estrarre nessuna entità diversa da quelle elencate.
- Se un'entità non è presente, non inventarla.
- Il formato di output deve essere una lista JSON con:
    - "entità": nome dell'entità
    - "valore": valore estratto
Nessun commento o testo aggiuntivo.
''',
        "intervento": '''
Sei un medico cardiochirurgo. Il tuo compito è estrarre **esclusivamente** le seguenti entità dal referto di intervento cardiochirurgico:

### Entità da estrarre:

| Entità                   | Tipo            | Descrizione                                              |
|-------------------------|-----------------|----------------------------------------------------------|
| n_cartella              | Number          | Numero identificativo della cartella clinica             |
| data_intervento         | Date            | Data dell'intervento eseguito                            |
| intervento text         | Text            | Descrizione completa dell’intervento                     |
| primo operatore         | Text            | Nome del primo operatore                                 |
| redo                    | Boolean         | Se l'intervento è un redo (re-intervento)               |
| cec                     | Boolean         | Uso di circolazione extracorporea (CEC)                 |
| cannulazionearteriosa   | Text            | Tipo di cannulazione arteriosa utilizzata               |
| statopaz                | Text            | Stato del paziente al termine dell’intervento          |
| cardioplegia            | Text            | Tipo di cardioplegia                                     |
| approcciochirurgico     | Text            | Approccio chirurgico adottato                            |
| entratainsala           | Time            | Ora di ingresso in sala operatoria                      |
| iniziointervento        | Time            | Ora di inizio intervento                                 |
| iniziocec               | Time            | Ora di inizio CEC                                        |
| inizioclamp             | Time            | Ora di inizio clampaggio                                 |
| inizioacc               | Time            | Ora di inizio accensione                                 |
| fineacc                 | Time            | Ora di fine accensione                                   |
| fineclamp               | Time            | Ora di fine clampaggio                                   |
| finecec                 | Time            | Ora di fine CEC                                          |
| fineintervento          | Time            | Ora di fine intervento                                   |
| uscitasala              | Time            | Ora di uscita dalla sala operatoria                      |
| intervento              | Text            | Tipo principale di intervento                            |
| protesi                 | Text            | Tipo di protesi utilizzata                               |
| modello                 | Text            | Modello della protesi                                    |
| numero                  | Number          | Numero seriale della protesi                             |

---

### Istruzioni Importanti:

- Non estrarre nessuna entità diversa da quelle elencate.
- Se un’entità non è presente nel documento, non inventarla.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con due chiavi:
    - "entità": il nome dell’entità
    - "valore": il valore estratto
- Nessuna spiegazione, nessun commento, solo la lista JSON.

---
'''
    }

    def get_schema_for(self, document_type: str) -> dict:
        """
        Restituisce lo schema JSON per il tipo di documento.
        """
        if document_type not in self.SCHEMAS:
            raise ValueError(f"Schema non definito per {document_type}")
        return self.SCHEMAS[document_type]

    def get_prompt_for(self, document_type: str) -> str:
        """
        Restituisce il prompt testuale per il tipo di documento.
        """
        if document_type not in self.PROMPTS:
            raise ValueError(f"Prompt non definito per {document_type}")
        return self.PROMPTS[document_type]

    def get_spec_for(self, document_type: str) -> Dict[str, List[str]]:
        """
        Restituisce un dict con:
          - 'entities': lista di chiavi dal JSON schema
        """
        schema = self.get_schema_for(document_type)
        entities = list(schema.get("properties", {}).keys())
        return { "entities": entities }
