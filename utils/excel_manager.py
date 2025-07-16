import os
import pandas as pd

EXPORT_PATH = "export/output.xlsx"

SHEET_ENTITIES = {
    "lettera_dimissione": [
        "n_cartella",
        "data_ingresso_cch",
        "data_dimissione_cch",
        "nome",
        "cognome",
        "sesso",
        "numero di telefono",
        "età al momento dell'intervento",
        "data_di_nascita",
        "Diagnosi",
        "Anamnesi",
        "Motivo ricovero",
        "classe_nyha",
        "angor",
        "STEMI/NSTEMI",
        "scompenso_cardiaco_nei_3_mesi_precedenti",
        "fumo",
        "diabete",
        "ipertensione",
        "dislipidemia",
        "BPCO",
        "stroke_pregresso",
        "TIA_pregresso",
        "vasculopatiaperif",
        "neoplasia_pregressa",
        "irradiazionetoracica",
        "insufficienza_renale_cronica",
        "familiarita_cardiovascolare",
        "limitazione_mobilita",
        "endocardite",
        "ritmo_all_ingresso",
        "fibrillazione_atriale",
        "dialisi",
        "elettivo_urgenza_emergenza",
        "pm",
        "crt",
        "icd",
        "pci_pregressa",
        "REDO",
        "Anno REDO",
        "Tipo di REDO",
        "Terapia",
        "lasix",
        "lasix_dosaggio",
        "nitrati",
        "antiaggregante",
        "dapt",
        "anticoagorali",
        "aceinib",
        "betabloc",
        "sartanici",
        "caantag",
        "esami_all_ingresso",
        "Decorso_post_operatorio",
        "IABP/ECMO/IMPELLA",
        "Inotropi",
        "secondo_intervento",
        "Tipo_secondo_intervento",
        "II_Run",
        "Causa_II_Run_CEC",
        "LCOS",
        "Impianto_PM_post_intervento",
        "Stroke_TIA_post_op",
        "Necessità_di_trasfusioni",
        "IRA",
        "Insufficienza_respiratoria",
        "FA_di_nuova_insorgenza",
        "Ritmo_alla_dimissione",
        "H_Stay_giorni (da intervento a dimissione)",
        "Morte",
        "Causa_morte",
        "data_morte",
        "esami_alla_dimissione",
        "terapia_alla_dimissione"
    ],
    "coronarografia": [
        "n_cartella",
        "nome",
        "cognome",
        "data_di_nascita",
        "data_esame",
        "coronarografia text",
        "coro_tc_stenosi50",
        "coro_iva_stenosi50",
        "coro_cx_stenosi50",
        "coro_mo1_stenosi50",
        "coro_mo2_stenosi50",
        "coro_mo3_stenosi50",
        "coro_int_stenosi50",
        "coro_plcx_stenosi50",
        "coro_dx_stenosi50",
        "coro_pl_stenosi50",
        "coro_ivp_stenosi50"
    ],
    "intervento": [
        "n_cartella",
        "data_intervento",
        "intervento text",
        "primo operatore",
        "redo",
        "cec",
        "cannulazionearteriosa",
        "statopaz",
        "cardioplegia",
        "approcciochirurgico",
        "entratainsala",
        "iniziointervento",
        "iniziocec",
        "inizioclamp",
        "inizioacc",
        "fineacc",
        "fineclamp",
        "finecec",
        "fineintervento",
        "uscitasala",
        "intervento",
        "protesi",
        "modello",
        "numero"
    ]
}



def update_excel(patient_id: str, document_type: str, estratti: dict):
    if not os.path.exists(EXPORT_PATH):
        os.makedirs("export", exist_ok=True)
        with pd.ExcelWriter(EXPORT_PATH, engine='openpyxl') as writer:
            for sheet, columns in SHEET_ENTITIES.items():
                pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet, index=False)

    excel_file = pd.ExcelFile(EXPORT_PATH)
    writer = pd.ExcelWriter(EXPORT_PATH, engine='openpyxl', mode='a', if_sheet_exists='overlay')

    for sheet in excel_file.sheet_names:
        df = pd.read_excel(EXPORT_PATH, sheet_name=sheet)
        columns = SHEET_ENTITIES.get(sheet, [])
        row_data = {key: estratti.get(key, "") for key in columns}
        if str(patient_id) in df.get("n_cartella", []).astype(str).values:
            for key, value in row_data.items():
                if key in df.columns:
                    if pd.isna(value):
                        value = ""  # o np.nan se preferisci
                    df.loc[df["n_cartella"].astype(str) == str(patient_id), key] = value
        else:
            df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        df.to_excel(writer, sheet_name=sheet, index=False)

    writer.close()


def export_excel_file():
    return EXPORT_PATH
