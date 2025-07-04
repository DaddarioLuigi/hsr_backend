# llm/prompts.py

#mettere prompt corretto 
PROMPTS = {
    "lettera_dimissione": '''
Sei un medico specializzato in cardiochirurgia. Il tuo compito è estrarre **esclusivamente** le seguenti entità dalla **lettera di dimissione** riportata qui sotto.

###**Entità da estrarre (solo queste):**

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
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
**NON** aggiungere commenti, spiegazioni, note, intestazioni o altro: **solo** la lista JSON.

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
  { "entità": "familiarita cardiovascolare", "valore": true }
]

'''
}
def get_prompt_for(document_type: str) -> str:
    return PROMPTS[document_type]

