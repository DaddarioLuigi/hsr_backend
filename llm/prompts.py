# llm/prompts.py

from typing import Dict, List


class PromptManager:
    """
    Gestisce schemi JSON e prompt testuali per l'estrazione di entità.
    """
    UPLOAD_FOLDER = "./uploads"      # Storage locale
    EXPORT_FOLDER = "./export"       # Excel output

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
                "terapia_alla_dimissione": { "type": "string" },

                "edemi_declivi": { "type": "boolean" },
                "ascite": { "type": "boolean" },

                "intervento_cardiochirurgico_pregresso": { "type": "boolean" },
                "intervento_transcatetere_pregresso": { "type": "boolean" },
                "intervento_pregresso_descrizione": { "type": "string" },
                "altri_diuretici": { "type": "boolean" },
                
                "statine": { "type": "boolean" },

                "insulina": { "type": "boolean" },
                "metformina": { "type": "boolean" },
                "anti_SGLT2": { "type": "boolean" },

                "ARNI": { "type": "boolean" },
                "Anno_REDO": { "type": "string", "format": "date" },

                "pre_esami_laboratorio": { "type": "string" },
                "post_esami_laboratorio": { "type": "string" },

                "pre_EMOCROMO_Globuli_rossi": { "type": "number" },
                "post_EMOCROMO_Globuli_rossi": { "type": "number" },

                "pre_EMOCROMO_Globuli_bianchi": { "type": "number" },
                "post_EMOCROMO_Globuli_bianchi": { "type": "number" },

                "pre_EMOCROMO_Ematocrito": { "type": "number" },
                "post_EMOCROMO_Ematocrito": { "type": "number" },

                "pre_EMOCROMO_Emoglobina": { "type": "number" },
                "post_EMOCROMO_Emoglobina": { "type": "number" },

                "pre_PIASTRINE_Piastrine": { "type": "number" },
                "post_PIASTRINE_Piastrine": { "type": "number" },

                "pre_S_GLUCOSIO": { "type": "number" },
                "post_S_GLUCOSIO": { "type": "number" },

                "pre_S_UREA": { "type": "number" },
                "post_S_UREA": { "type": "number" },

                "pre_S_CREATININA": { "type": "number" },
                "post_S_CREATININA": { "type": "number" },

                "pre_eGFR_ml_min": { "type": "number" },
                "post_eGFR_ml_min": { "type": "number" },

                "pre_S_SODIO": { "type": "number" },
                "post_S_SODIO": { "type": "number" },

                "pre_S_POTASSIO": { "type": "number" },
                "post_S_POTASSIO": { "type": "number" },

                "pre_S_CALCIO": { "type": "number" },
                "post_S_CALCIO": { "type": "number" },

                "pre_S_BILIRUBINA_TOTALE": { "type": "number" },
                "post_S_BILIRUBINA_TOTALE": { "type": "number" },

                "pre_S_BILIRUBINA_DIRETTA": { "type": "number" },
                "post_S_BILIRUBINA_DIRETTA": { "type": "number" },

                "pre_S_BILIRUBINA_INDIRETTA": { "type": "number" },
                "post_S_BILIRUBINA_INDIRETTA": { "type": "number" },

                "pre_S_ASPARTATO_AMINOTRANSFERASI": { "type": "number" },
                "post_S_ASPARTATO_AMINOTRANSFERASI": { "type": "number" },

                "pre_S_GAMMAGLUTAMILTRANSFERASI": { "type": "number" },
                "post_S_GAMMAGLUTAMILTRANSFERASI": { "type": "number" },

                "pre_S_FOSFATASI_ALCALINA": { "type": "number" },
                "post_S_FOSFATASI_ALCALINA": { "type": "number" },

                "pre_S_LATTICODEIDROGENASI": { "type": "number" },
                "post_S_LATTICODEIDROGENASI": { "type": "number" },

                "pre_S_FERRO": { "type": "number" },
                "post_S_FERRO": { "type": "number" },

                "pre_S_TRANSFERRINA": { "type": "number" },
                "post_S_TRANSFERRINA": { "type": "number" },

                "pre_S_ALBUMINA": { "type": "number" },
                "post_S_ALBUMINA": { "type": "number" },

                "pre_S_PROTEINA_C_REATTIVA": { "type": "number" },
                "post_S_PROTEINA_C_REATTIVA": { "type": "number" },

                "pre_S_TRIGLICERIDI": { "type": "number" },
                "post_S_TRIGLICERIDI": { "type": "number" },

                "pre_S_COLESTEROLO": { "type": "number" },
                "post_S_COLESTEROLO": { "type": "number" },

                "pre_S_TROPONINA_T": { "type": "number" },
                "post_S_TROPONINA_T": { "type": "number" },

                "pre_S_CREATINFOSFOCHINASI": { "type": "number" },
                "post_S_CREATINFOSFOCHINASI": { "type": "number" },

                "pre_PT_INR_International_Normalized_Ratio": { "type": "number" },
                "post_PT_INR_International_Normalized_Ratio": { "type": "number" },

                "pre_PT_Rapporto": { "type": "number" },
                "post_PT_Rapporto": { "type": "number" },

                "pre_APTT_Secondi": { "type": "number" },
                "post_APTT_Secondi": { "type": "number" },

                "pre_S_PROPEPTIDE_NATRIURETICO_NT_proBNP": { "type": "number" },
                "post_S_PROPEPTIDE_NATRIURETICO_NT_proBNP": { "type": "number" }

                
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
                # Testo completo del referto di coronarografia
                # NOTA: in Excel la colonna si chiama 'coronarografia_text'
                "coronarografia_text": { "type": "string" },
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
                "data_esame": { "type": "string", "format": "date" },
                "eco_text": { "type": "string" },         # riassunto referto
                "parametri": { "type": "string" },        # cattura tabellari non mappati singolarmente
                
                #=======================
                #VENTRICOLO SINISTRO (VSX)
                #=======================
                "Ventricolo_sinistro_GLS": { "type": "number" },
                "Ventricolo_sinistro_diametro_telediastolico": { "type": "number" },
                "Ventricolo_sinistro_setto_interventricolare_spessore_TD": { "type": "number" },
                "Ventricolo_sinistro_parete_posteriore_spessore_TD": { "type": "number" },
                "Ventricolo_sinistro_massa_indicizzata": { "type": "number" },
                "Ventricolo_sinistro_relative_wall_thickness": { "type": "number" },
                "Ventricolo_sinistro_volume_telediastolico_Simpson": { "type": "number" },
                "Ventricolo_sinistro_volume_telediastolico_ind_Simpson": { "type": "number" },
                "Ventricolo_sinistro_volume_telesistolico_Simpson": { "type": "number" },
                "Ventricolo_sinistro_volume_telesistolico_ind_Simpson": { "type": "number" },
                "Ventricolo_sinistro_FE": { "type": "number" },
                "Ventricolo_sinistro_frazione_eiezione_Simpson": { "type": "number" },
                "Ventricolo_sinistro_fractional_area_change": { "type": "number" },

                #=======================
                #VENTRICOLO DESTRO (VDX)
                #=======================
                "Ventricolo_destro_TAPSE": { "type": "number" },
                "Ventricolo_destro_velocita_S_TDI": { "type": "number" },
                "Ventricolo_destro_diametro_basale": { "type": "number" },
                "Ventricolo_destro_diametro_medio": { "type": "number" },
                "Ventricolo_destro_frac_wall_LS": { "type": "number" },
                "Ventricolo_destro_PAPs": { "type": "number" },

                #=======================
                #ATRIO SINISTRO (ASX)
                #======================= */
                "Atrio_sinistro_volume_telesistolico": { "type": "number" },
                "Atrio_sinistro_volume_telesistolico_indicizzato": { "type": "number" },

                #=======================
                #AORTA
                #=======================
                "Aorta_diametro_seni_Valsalva": { "type": "number" },
                "Aorta_diametro_giunzione_seno_tubulare": { "type": "number" },
                "Aorta_diametro_tratto_tubulare": { "type": "number" },
                "Aorta_diametro_arco": { "type": "number" },

                #=======================
                #VALVOLA AORTICA
                #=======================
                "Valvola_aortica_insufficienza": { "type": "boolean" },
                "Valvola_aortica_stenosi": { "type": "boolean" },
                "Valvola_aortica_protesi_in_sede": { "type": "boolean" },
                "Valvola_aortica_protesi_degenerata": { "type": "boolean" },
                "Valvola_aortica_velocita_massima": { "type": "number" },
                "Valvola_aortica_gradiente_massimo": { "type": "number" },
                "Valvola_aortica_gradiente_medio": { "type": "number" },
                "Valvola_aortica_AVA": { "type": "number" },
                "Valvola_aortica_AVAi": { "type": "number" },
                "Valvola_aortica_DVI": { "type": "number" },
                "Valvola_aortica_bicuspide": { "type": "boolean" },
                "Valvola_aortica_PVL": { "type": "boolean" },

                #=======================
                #VALVOLA MITRALE
                #=======================
                "Valvola_mitrale_insufficienza": { "type": "boolean" },
                "Valvola_mitrale_stenosi": { "type": "boolean" },
                "Valvola_mitrale_gradiente_medio": { "type": "number" },
                "Valvola_mitrale_area_valvolare": { "type": "number" },
                "Valvola_mitrale_annulus_AP": { "type": "number" },
                "Valvola_mitrale_annulus_IC": { "type": "number" },
                "Valvola_mitrale_distanza_SIV_C": { "type": "number" },
                "Valvola_mitrale_angolo_MA": { "type": "number" },
                "Valvola_mitrale_lunghezza_lembo_anteriore": { "type": "number" },
                "Valvola_mitrale_lunghezza_lembo_posteriore": { "type": "number" },
                "Valvola_mitrale_rapporto_LAM_LP": { "type": "number" },

                "Valvola_mitrale_protesi_in_sede": { "type": "boolean" },
                "Valvola_mitrale_protesi_degenerata": { "type": "boolean" },
                "Valvola_mitrale_PVL": { "type": "boolean" },

                "Valvola_mitrale_lesione_bilembo": { "type": "boolean" },
                "Valvola_mitrale_lesione_anteriore": { "type": "boolean" },
                "Valvola_mitrale_lesione_posteriore": { "type": "boolean" },

                "Valvola_mitrale_scallop_A1": { "type": "boolean" },
                "Valvola_mitrale_scallop_A2": { "type": "boolean" },
                "Valvola_mitrale_scallop_A3": { "type": "boolean" },
                "Valvola_mitrale_scallop_P1": { "type": "boolean" },
                "Valvola_mitrale_scallop_P2": { "type": "boolean" },
                "Valvola_mitrale_scallop_P3": { "type": "boolean" },

                "Valvola_mitrale_tipo_lesione": {
                    "type": "string",
                    "enum": [
                    "Ventricolare",
                    "Atriale",
                    "Mista",
                    "Prolasso",
                    "Flail",
                    "Endocardite",
                    "Interferenza elettrocatetere"
                    ]
                },
                "Valvola_mitrale_eziologia": { "type": "string" },
                "Valvola_mitrale_calcificazione_anello": { "type": "boolean" },
                "Valvola_mitrale_calcificazione_lembi": { "type": "boolean" },
                "Valvola_mitrale_presenza_cleft": { "type": "boolean" },
                "Valvola_mitrale_localizzazione_cleft": { "type": "string" },

                #=======================
                #VALVOLA TRICUSPIDE
                #=======================
                "Valvola_tricuspide_diametro_setto_laterale": { "type": "number" },
                "Valvola_tricuspide_diametro_setto_laterale_indicizzato": { "type": "number" },
                "Valvola_tricuspide_insufficienza": { "type": "boolean" },
                "Valvola_tricuspide_stenosi": { "type": "boolean" },
                "Valvola_tricuspide_eziologia": { "type": "string" },

                #=======================
                #VALVOLA POLMONARE
                #=======================
                "Valvola_polmonare_insufficienza": { "type": "boolean" },
                "Valvola_polmonare_stenosi": { "type": "boolean" }
                },
                "required": ["n_cartella", "nome", "cognome"],
                "additionalProperties":True

        },

        "eco_postoperatorio": {
            "name": "eco_postoperatorio",
    "title": "Scheda Ecocardiogramma Postoperatorio",
    "type": "object",
    "properties": {
      "data_esame": { "type": "string", "format": "date" },
      "eco_text": { "type": "string" },
      "parametri": { "type": "string" },
      "VSX_FE": { "type": "string" },
      
      "Valvola_aortica_insufficienza": { "type": "string" },
      "Valvola_aortica_stenosi": { "type": "string" },
      "Valvola_aortica_velocita_max": { "type": "string" },
      "Valvola_aortica_gradiente_max": { "type": "string" },
      "Valvola_aortica_gradiente_med": { "type": "string" },
      "Valvola_aortica_PVL": { "type": "string" },
      
      "Valvola_mitrale_insufficienza": { "type": "string" },
      "Valvola_mitrale_stenosi": { "type": "string" },
      "Valvola_mitrale_gradiente_med": { "type": "string" },
      "Valvola_mitrale_PVL": { "type": "string" },
      
      "Valvola_tricuspidalica_insufficienza": { "type": "string" },
      "Valvola_tricuspidalica_stenosi": { "type": "string" },
      "Valvola_tricuspidalica_gradiente_med": { "type": "string" },
      
      "Valvola_polmonare_insufficienza": { "type": "string" },
      "Valvola_polmonare_stenosi": { "type": "string" },
      "Valvola_polmonare_gradiente_med": { "type": "string" }
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
                # Testo completo del referto TC Cuore
                # NOTA: in Excel la colonna si chiama 'tac_text'
                "tac_text": { "type": "string" },
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
                "n_cartella": { "type": "number" },
                "nome": { "type": "string" },
                "cognome": { "type": "string" },
                "data_di_nascita": { "type": "string", "format": "date" },  # (CSV: 'dob')
                "data_intervento": { "type": "string", "format": "date" },
                "Percorso": { "type": "string" },                           # Chirurgico / Transcatetere
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

                "primo operatore cognome": { "type": "string" },
                "primo operatore nome": { "type": "string" },

                "num_interventi": { "type": "number" },

                # Primo intervento dettagliato (aderente al CSV di esempio)
                "intervento 1": { "type": "string" },
                "protesi 1": { "type": "string" },          # Biologica/Meccanica/Anello
                "modello 1": { "type": "string" },
                "numero 1": { "type": "number" },
                "eziologia_valvolare 1": { "type": "string" },

                # Testo libero (riassunto verbale operatorio)
                "intervento text": { "type": "string" },
                "edemi_declivi": {"type": "boolean"},
                "ascite": {"type": "boolean"},
                "intervento_cardiochirurgico_pregresso": {"type": "boolean"},
                "intervento_transcatetere_pregresso": {"type": "boolean"},
                "intervento_pregresso_descrizione": {"type": "string"},
                "Anno_REDO": {"type": "string","format": "date"},
                "altri_diuretici": {"type": "boolean"},
                "statine": {"type": "boolean"},
                "insulina": {"type": "boolean"},
                "metformina": {"type": "boolean"},
                "anti_SGLT2": {"type": "boolean"},
                "ARNI": {"type": "boolean"}
            },
            "required": ["n_cartella", "nome", "cognome", "data_intervento"]
        },
            "anamnesi": {
        "name": "anamnesi",
        "title": "Scheda Anamnesi",
        "type": "object",
        "properties": {
            "n_cartella": { "type": "number" },
            "nome": { "type": "string" },
            "cognome": { "type": "string" },
            "data_di_nascita": { "type": "string", "format": "date" },

            "Terapia": { "type": "string" },            # terapia in atto all'ingresso
            "Allergie": { "type": "string" },           # farmacoallergie/intolleranze
            "Abitudini": { "type": "string" },          # fumo/alcol/altro se riportati
            "Comorbidita": { "type": "string" },        # elenco/riassunto comorbidità
            "esami_all_ingresso": { "type": "string" }, # labs/strumentali all'ingresso
            "parametri": { "type": "string" }           # key:value; key:value; da tabelle/elenco
        },
        "required": ["n_cartella", "nome", "cognome"],
        "additionalProperties": True
    },

    "epicrisi_ti": {
        "name": "epicrisi_ti",
        "title": "Epicrisi Terapia Intensiva",
        "type": "object",
        "properties": {
            "n_cartella": { "type": "number" },
            "nome": { "type": "string" },
            "cognome": { "type": "string" },
            "data_intervento": { "type": "string", "format": "date" },
            "Decorso_post_operatorio": { "type": "string" },   # ventilazione, emodinamica, complicanze, etc.
            "IABP_ECMO_IMPELLA": { "type": "boolean" },
            "Inotropi": { "type": "boolean" },
            "eventi_avversi_TI": { "type": "string" },         # lista/riassunto eventi ICU
            "data_dimissione_cch": { "type": "string", "format": "date" },
            "parametri": { "type": "string" }                  # tabellari/elenco "chiave: valore; ..."
        },
        "required": ["n_cartella", "nome", "cognome"],
        "additionalProperties": True
    },


    "cartellino_anestesiologico": {
        "name": "cartellino_anestesiologico",
        "title": "Scheda Anestesiologica Intraoperatoria",
        "type": "object",
        "properties": {

            "n_cartella": { "type": "number" },
            "nome": { "type": "string" },
            "cognome": { "type": "string" },
            "data_di_nascita": { "type": "string", "format": "date" },
            "data_intervento": { "type": "string", "format": "date" },

            "INGRESSO_IN_SALA": { "type": "string", "format": "time" },
            "INIZIO_TEMPO_CHIRURGICO": { "type": "string", "format": "time" },
            "TEMPI_CCH_Inizio_CEC": { "type": "string", "format": "time" },
            "TEMPI_CCH_Clamp_Ao": { "type": "string", "format": "time" },
            "TEMPI_CCH_Declamp_Ao": { "type": "string", "format": "time" },
            "TEMPI_CCH_fine_CEC": { "type": "string", "format": "time" },
            "FINE_TEMPO_CHIRURGICO": { "type": "string", "format": "time" },
            "USCITA_DI_SALA": { "type": "string", "format": "time" },

            "cec": { "type": "boolean" },

            "Cardioplegia": { "type": "string" },
            "Tipo_plegia": { "type": "string" },

            "anestesia": { "type": "string" },
            "farmaci_intraop": { "type": "string" },
            "eventi_intraop": { "type": "string" },
            "parametri": { "type": "string" }

        },
        "required": ["n_cartella", "nome", "cognome", "data_intervento"],
        "additionalProperties": True
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
| numero_di_telefono                         | Text              | Recapito telefonico del paziente o di un contatto di riferimento.                                                                              |
| eta_al_momento_dell_intervento            | Number            | Età del paziente calcolata alla data dell’intervento chirurgico.                                                                               |
| data_di_nascita                            | Date              | Data di nascita del paziente.                                                                                                                   |
| Diagnosi                                   | Text              | Diagnosi principale alla base dell'indicazione chirurgica.                                                                                      |
| Anamnesi                                   | Text              | Anamnesi patologica remota e prossima, utile per la valutazione del rischio operatorio.                                                        |
| Motivo_ricovero                            | Text              | Indicazione clinica per il ricovero in Cardiochirurgia.                                                                                         |
| classe_nyha                                | Categorical_1234  | Classe funzionale NYHA per scompenso cardiaco (I-IV), definisce la gravità dei sintomi.                                                        |
| angor                                      | Boolean           | Presenza di angina pectoris (dolore toracico di origine ischemica).                                                                            |
| STEMI_NSTEMI                               | Boolean           | Presenza di infarto miocardico acuto con/senza sopraslivellamento del tratto ST.                                                               |
| scompenso_cardiaco_nei_3_mesi_precedenti   | Boolean           | Episodi di scompenso cardiaco documentati nei 3 mesi precedenti l’intervento.                                                                  |
| fumo                                       | Categorical_012   | Abitudine al fumo (0 = mai fumato, 1 = ex-fumatore, 2 = fumatore attivo).                                                                      |
| diabete                                    | Boolean           | Presenza di diabete mellito noto. Oltre al testo esplicito, imposta `diabete = true` se la terapia comprende farmaci specifici per il diabete (es. insulina, metformina, anti-SGLT2, ARNI), anche in assenza di una frase che menzioni esplicitamente “diabete”. |
| ipertensione                               | Boolean           | Presenza di ipertensione arteriosa. Oltre al testo, se la terapia comprende ACE-inibitori (`aceinib`), sartani (`sartanici`) o calcio-antagonisti (`caantag`), imposta `ipertensione = true` anche in assenza di una dicitura esplicita. |
| dislipidemia                               | Boolean           | Presenza di dislipidemia (colesterolo e/o trigliceridi elevati). Inoltre, se i valori di colesterolo o trigliceridi negli esami di laboratorio risultano alterati, oppure se è presente una terapia con **statine**, imposta `dislipidemia = true`. |
| BPCO                                       | Boolean           | Presenza di broncopneumopatia cronica ostruttiva.                                                                                               |
| stroke_pregresso                           | Boolean           | Precedente episodio di ictus cerebrale ischemico o emorragico.                                                                                  |
| TIA_pregresso                              | Boolean           | Episodio pregresso di attacco ischemico transitorio (TIA).                                                                                      |
| vasculopatiaperif                          | Boolean           | Malattia vascolare periferica documentata (es. arteriopatia arti inferiori).                                                                   |
| neoplasia_pregressa                        | Boolean           | Presenza di neoplasie trattate in passato.                                                                                                      |
| irradiazionetoracica                       | Boolean           | Pregressa radioterapia al torace, rilevante per effetti tardivi su cuore e vasi.                                                               |
| insufficienza_renale_cronica               | Boolean           | Presenza di insufficienza renale cronica diagnosticata. Inoltre, se è riportato un valore di **eGFR ml/min** < 60, imposta `insufficienza_renale_cronica = true` anche senza frase esplicita. |
| familiarita_cardiovascolare                | Boolean           | Familiarità per malattie cardiovascolari premature (prima dei 55 anni per uomini, 65 per donne).                                                |
| limitazione_mobilita                       | Boolean           | Presenza di limitazioni significative alla mobilità (es. pazienti allettati).                                                                  |
| endocardite                                | Boolean           | Pregressa o attiva endocardite infettiva, rilevante per indicazione chirurgica.                                                                |
| ritmo_all_ingresso                         | Categorical_012   | Ritmo cardiaco al momento del ricovero (0 = ritmo sinusale, 1 = FA, 2 = altro).                                                                 |
| fibrillazione_atriale                      | Categorical_012   | Presenza di fibrillazione atriale (0 = mai, 1 = parossistica, 2 = permanente/persistente).                                                     |
| dialisi                                    | Boolean           | Paziente in trattamento emodialitico o peritoneale.                                                                                             |
| elettivo_urgenza_emergenza                 | Categorical_012   | Tipo di intervento (0 = elettivo, 1 = urgente, 2 = emergenza).                                                                                  |
| pm                                         | Boolean           | Presenza di pacemaker.                                                                                                                          |
| crt                                        | Boolean           | Presenza di terapia di resincronizzazione cardiaca (CRT).                                                                                       |
| icd                                        | Boolean           | Presenza di defibrillatore impiantabile (ICD).                                                                                                  |
| pci_pregressa                              | Boolean           | Precedente angioplastica coronarica percutanea (PCI).                                                                                           |
| REDO                                       | Boolean           | Intervento cardiochirurgico di revisione (non prima chirurgia).                                                                                |
| Anno_REDO                                  | Date              | Anno in cui è stato eseguito l'intervento REDO precedente.                                                                                      |
| Tipo_di_REDO                               | Text              | Descrizione del tipo di intervento REDO eseguito.                                                                                               |
| Terapia                                    | Text              | Terapia farmacologica in atto al momento del ricovero. Deve riferirsi alla situazione **pre-operatoria**, quindi utilizza le date per escludere terapia chiaramente introdotta solo alla dimissione. |
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
| esami_laboratorio                         | Text              | Risultati di laboratorio e strumentali. Quando possibile, indica se si riferiscono al periodo **pre-operatorio** o **alla dimissione**, sfruttando la data degli esami rispetto a `data_intervento` e `data_dimissione_cch`. |
| Decorso_post_operatorio                    | Text              | Descrizione del decorso clinico successivo all’intervento chirurgico.                                                                          |
| IABP_ECMO_IMPELLA                          | Boolean           | Necessità di supporto meccanico circolatorio (IABP, ECMO o Impella).                                                                           |
| Inotropi                                   | Boolean           | Necessità di farmaci inotropi positivi nel post-operatorio.                                                                                     |
| secondo_intervento                         | Boolean           | Esecuzione di un secondo intervento durante la degenza attuale.                                                                                |
| Tipo_secondo_intervento                    | Text              | Tipo e motivazione del secondo intervento chirurgico.                                                                                           |
| II_Run_CEC                                 | Boolean           | Presenza di secondo passaggio in circolazione extracorporea (CEC).                                                                             |
| Causa_II_Run_CEC                           | Text              | Motivazione per il secondo utilizzo della CEC.                                                                                                  |
| LCOS                                       | Boolean           | Sindrome da bassa portata cardiaca (Low Cardiac Output Syndrome) post-operatoria. Imposta `LCOS = true` se il testo descrive chiaramente bassa portata o se sono presenti inotropi ad alte dosi e/o IABP/ECMO/IMPELLA. |
| Impianto_PM_post_intervento                | Boolean           | Necessità di impianto di pacemaker dopo l’intervento.                                                                                           |
| Stroke_TIA_post_op                         | Boolean           | Evento neurologico ischemico (TIA/stroke) avvenuto dopo l’intervento.                                                                          |
| Necessita_di_trasfusioni                   | Boolean           | Necessità di trasfusioni ematiche post-intervento.                                                                                              |
| IRA                                        | Boolean           | Insufficienza renale acuta insorta nel post-operatorio.                                                                                         |
| Insufficienza_respiratoria                 | Boolean           | Insorgenza di insufficienza respiratoria nel post-operatorio.                                                                                   |
| FA_di_nuova_insorgenza                     | Boolean           | Fibrillazione atriale di nuova insorgenza nel post-operatorio.                                                                                  |
| Ritmo_alla_dimissione                      | Categorical_012   | Ritmo cardiaco documentato alla dimissione (0 = sinusale, 1 = FA, 2 = altro).                                                                   |
| H_Stay_giorni_da_intervento_a_dimissione   | Number            | Durata della degenza in giorni, calcolata dall’intervento alla dimissione.                                                                      |
| Morte                                      | Boolean           | Evento di decesso durante la degenza cardiochirurgica.                                                                                          |
| Causa_morte                                | Text              | Causa clinica del decesso (es. sepsi, shock cardiogeno, ecc.).                                                                                  |
| data_morte                                 | Date              | Data del decesso, se avvenuto.                                                                                                                  |
| esami_laboratorio_dimissione              | Text              | Risultati di laboratorio e strumentali prima della dimissione (usa solo esami con data successiva all’intervento e prossima alla dimissione).  |
| Terapia_dimissione                        | Text              | Terapia farmacologica prescritta alla dimissione (usa solo la terapia associata temporalmente alla dimissione, non quella pre-operatoria).     |
| edemi_declivi                         | Boolean | Presenza di edemi declivi (arti inferiori). Imposta `true` se nel testo compaiono termini come *edemi declivi*, *edemi periferici*, *edema malleolare*, *edemi agli arti inferiori*. In assenza di menzione o se negati, imposta `false`. |
| ascite                                | Boolean | Presenza di ascite clinicamente rilevante. Imposta `true` se nel testo sono riportati *ascite*, *versamento ascitico*, *liquido in addome*. Imposta `false` se assente o negata.                                                          |
| intervento_cardiochirurgico_pregresso | Boolean | Presenza di **precedente intervento cardiochirurgico** prima dell’intervento attuale. Imposta `true` se riportato in anamnesi o lettera di dimissione (es. *pregresso bypass*, *pregressa sostituzione valvolare*).                       |
| intervento_transcatetere_pregresso    | Boolean | Presenza di **precedente intervento transcatetere** (es. TAVI, MitraClip, PCI strutturale) prima dell’intervento attuale. Imposta `true` se riportato esplicitamente nel testo.                                                           |
| intervento_pregresso_descrizione      | Text    | Descrizione libera dell’intervento pregresso (cardiochirurgico e/o transcatetere). Deve riferirsi **solo a procedure precedenti all’intervento attuale**. Può essere estratta sia da anamnesi che da lettera di dimissione.               |
| altri_diuretici                       | Boolean | Uso di diuretici **diversi dalla furosemide** (es. tiazidici, spironolattone, canrenoato). Imposta `true` se presenti in terapia pre-operatoria.                                                                                          |
| statine                               | Boolean | Terapia con statine (es. atorvastatina, rosuvastatina, simvastatina). Imposta `true` se presenti in terapia. **Regola derivata**: se `statine = true`, allora `dislipidemia = true`.                                                      |
| insulina                              | Boolean | Terapia insulinica in corso prima dell’intervento. **Regola derivata**: se `insulina = true`, allora `diabete = true`, anche in assenza di menzione testuale di diabete.                                                                  |
| metformina                            | Boolean | Terapia con metformina prima dell’intervento. **Regola derivata**: se `metformina = true`, allora `diabete = true`.                                                                                                                       |
| anti_SGLT2                            | Boolean | Terapia con inibitori SGLT2 (gliflozine: dapagliflozin, empagliflozin, ecc.). **Regola derivata**: se `anti_SGLT2 = true`, allora `diabete = true`.                                                                                       |
| ARNI                                  | Boolean | Terapia con ARNI (sacubitril/valsartan – Entresto). Imposta `true` se presente in terapia pre-operatoria.                                                                                                                                 |
| Anno_REDO                             | Date    | Anno/data di un **intervento cardiochirurgico o transcatetere pregresso** (REDO). Deve riferirsi **a interventi precedenti a quello attuale**, non all’intervento in corso.                                                               |
                        | Text              | Terapia farmacologica prescritta alla dimissione (usa solo la terapia associata temporalmente alla dimissione, non quella pre-operatoria).     |
|   pre_esami_laboratorio                    | Text              | Testo degli esami di laboratorio pre-intervento.
| post_esami_laboratorio                    | Text              | Testo degli esami di laboratorio post-intervento.
| pre_EMOCROMO_Globuli_rossi                 | Number | Globuli rossi pre-intervento.         |
| post_EMOCROMO_Globuli_rossi                | Number | Globuli rossi post-intervento.        |
| pre_EMOCROMO_Globuli_bianchi               | Number | Globuli bianchi pre-intervento.       |
| post_EMOCROMO_Globuli_bianchi              | Number | Globuli bianchi post-intervento.      |
| pre_EMOCROMO_Ematocrito                    | Number | Ematocrito pre-intervento.            |
| post_EMOCROMO_Ematocrito                   | Number | Ematocrito post-intervento.           |
| pre_EMOCROMO_Emoglobina                    | Number | Emoglobina pre-intervento.            |
| post_EMOCROMO_Emoglobina                   | Number | Emoglobina post-intervento.           |
| pre_PIASTRINE_Piastrine                    | Number | Piastrine pre-intervento.             |
| post_PIASTRINE_Piastrine                   | Number | Piastrine post-intervento.            |
| pre_S_GLUCOSIO                             | Number | Glicemia pre-intervento.              |
| post_S_GLUCOSIO                            | Number | Glicemia post-intervento.             |
| pre_S_UREA                                 | Number | Urea pre-intervento.                  |
| post_S_UREA                                | Number | Urea post-intervento.                 |
| pre_S_CREATININA                           | Number | Creatinina pre-intervento.            |
| post_S_CREATININA                          | Number | Creatinina post-intervento.           |
| pre_eGFR_ml_min                            | Number | eGFR pre-intervento.                  |
| post_eGFR_ml_min                           | Number | eGFR post-intervento.                 |
| pre_S_SODIO                                | Number | Sodio pre-intervento.                 |
| post_S_SODIO                               | Number | Sodio post-intervento.                |
| pre_S_POTASSIO                             | Number | Potassio pre-intervento.              |
| post_S_POTASSIO                            | Number | Potassio post-intervento.             |
| pre_S_CALCIO                               | Number | Calcio pre-intervento.                |
| post_S_CALCIO                              | Number | Calcio post-intervento.               |
| pre_S_BILIRUBINA_TOTALE                    | Number | Bilirubina totale pre-intervento.     |
| post_S_BILIRUBINA_TOTALE                   | Number | Bilirubina totale post-intervento.    |
| pre_S_BILIRUBINA_DIRETTA                   | Number | Bilirubina diretta pre-intervento.    |
| post_S_BILIRUBINA_DIRETTA                  | Number | Bilirubina diretta post-intervento.   |
| pre_S_BILIRUBINA_INDIRETTA                 | Number | Bilirubina indiretta pre-intervento.  |
| post_S_BILIRUBINA_INDIRETTA                | Number | Bilirubina indiretta post-intervento. |
| pre_S_ASPARTATO_AMINOTRANSFERASI           | Number | AST pre-intervento.                   |
| post_S_ASPARTATO_AMINOTRANSFERASI          | Number | AST post-intervento.                  |
| pre_S_GAMMAGLUTAMILTRANSFERASI             | Number | GGT pre-intervento.                   |
| post_S_GAMMAGLUTAMILTRANSFERASI            | Number | GGT post-intervento.                  |
| pre_S_FOSFATASI_ALCALINA                   | Number | Fosfatasi alcalina pre-intervento.    |
| post_S_FOSFATASI_ALCALINA                  | Number | Fosfatasi alcalina post-intervento.   |
| pre_S_LATTICODEIDROGENASI                  | Number | LDH pre-intervento.                   |
| post_S_LATTICODEIDROGENASI                 | Number | LDH post-intervento.                  |
| pre_S_FERRO                                | Number | Ferro pre-intervento.                 |
| post_S_FERRO                               | Number | Ferro post-intervento.                |
| pre_S_TRANSFERRINA                         | Number | Transferrina pre-intervento.          |
| post_S_TRANSFERRINA                        | Number | Transferrina post-intervento.         |
| pre_S_ALBUMINA                             | Number | Albumina pre-intervento.              |
| post_S_ALBUMINA                            | Number | Albumina post-intervento.             |
| pre_S_PROTEINA_C_REATTIVA                  | Number | PCR pre-intervento.                   |
| post_S_PROTEINA_C_REATTIVA                 | Number | PCR post-intervento.                  |
| pre_S_TRIGLICERIDI                         | Number | Trigliceridi pre-intervento.          |
| post_S_TRIGLICERIDI                        | Number | Trigliceridi post-intervento.         |
| pre_S_COLESTEROLO                          | Number | Colesterolo pre-intervento.           |
| post_S_COLESTEROLO                         | Number | Colesterolo post-intervento.          |
| pre_S_TROPONINA_T                          | Number | Troponina T pre-intervento.           |
| post_S_TROPONINA_T                         | Number | Troponina T post-intervento.          |
| pre_S_CREATINFOSFOCHINASI                  | Number | CPK pre-intervento.                   |
| post_S_CREATINFOSFOCHINASI                 | Number | CPK post-intervento.                  |
| pre_PT_INR_International_Normalized_Ratio  | Number | INR pre-intervento.                   |
| post_PT_INR_International_Normalized_Ratio | Number | INR post-intervento.                  |
| pre_PT_Rapporto                            | Number | Rapporto PT pre-intervento.           |
| post_PT_Rapporto                           | Number | Rapporto PT post-intervento.          |
| pre_APTT_Secondi                           | Number | aPTT pre-intervento (secondi).        |
| post_APTT_Secondi                          | Number | aPTT post-intervento (secondi).       |
| pre_S_PROPEPTIDE_NATRIURETICO_NT_proBNP    | Number | NT-proBNP pre-intervento.             |
| post_S_PROPEPTIDE_NATRIURETICO_NT_proBNP   | Number | NT-proBNP post-intervento.            |

---

### **Istruzioni IMPORTANTI:**

- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- Usa le regole derivate da esami e terapia come indicato sopra (per `diabete`, `dislipidemia`, `insufficienza_renale_cronica`, `ipertensione`, `LCOS`, ecc.), ma **non** impostare mai un valore se mancano completamente dati coerenti nel testo o nei parametri.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
-Se la data accanto al valore è < data_intervento → campo pre_
-Se la data accanto al valore è ≥ data_intervento → campo post_
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

### Entità da estrarre:

### Mappa delle entità e tipi
| Entità              | Tipo    | Descrizione                                                                    |
| ------------------- | ------- | ------------------------------------------------------------------------------ |
| n_cartella          | Number  | Numero identificativo univoco della cartella clinica del paziente              |
| nome                | Text    | Nome del paziente                                                              |
| cognome             | Text    | Cognome del paziente                                                           |
| data_di_nascita     | Date    | Data di nascita del paziente                                                   |
| data_esame          | Date    | Data di esecuzione della coronarografia                                        |
| coronarografia_text | Text    | Testo completo del referto di coronarografia (in Excel: `coronarografia_text`) |
| coro_tc_stenosi50   | Boolean | Presenza di stenosi ≥50% del tronco comune                                     |
| coro_iva_stenosi50  | Boolean | Presenza di stenosi ≥50% dell’arteria interventricolare anteriore (IVA)        |
| coro_cx_stenosi50   | Boolean | Presenza di stenosi ≥50% dell’arteria circonflessa (CX)                        |
| coro_mo1_stenosi50  | Boolean | Presenza di stenosi ≥50% del primo ramo marginale ottuso (MO1)                 |
| coro_mo2_stenosi50  | Boolean | Presenza di stenosi ≥50% del secondo ramo marginale ottuso (MO2)               |
| coro_mo3_stenosi50  | Boolean | Presenza di stenosi ≥50% del terzo ramo marginale ottuso (MO3)                 |
| coro_int_stenosi50  | Boolean | Presenza di stenosi ≥50% del ramo intermedio                                   |
| coro_plcx_stenosi50 | Boolean | Presenza di stenosi ≥50% del ramo posterolaterale della circonflessa           |
| coro_dx_stenosi50   | Boolean | Presenza di stenosi ≥50% dell’arteria coronaria destra                         |
| coro_pl_stenosi50   | Boolean | Presenza di stenosi ≥50% del ramo posterolaterale                              |
| coro_ivp_stenosi50  | Boolean | Presenza di stenosi ≥50% dell’arteria interventricolare posteriore             |


---

- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
**NON** aggiungere commenti, spiegazioni, note, intestazioni o altro: **solo** la lista JSON.
-Se trovi **tabelle**, **elenchi** o **parametri** , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura).
-Se trovi **esami** o **strumentali** (ad esempio esami di laboratorio) , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura). 

---
 Questo è un esempio di input per capire il formato di output:
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
]

''',
        "eco_preoperatorio": '''
Sei un medico specializzato in cardiochirurgia.
Estrai le seguenti entità dall’ecocardiogramma **preoperatorio**:
### Entità da estrarre:

### Mappa delle entità e tipi
| Entità                                                  | Tipo    | Descrizione                                                                                                                                  |
| ------------------------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| n_cartella                                              | Number  | Numero identificativo univoco della cartella clinica del paziente                                                                            |
| nome                                                    | Text    | Nome del paziente                                                                                                                            |
| cognome                                                 | Text    | Cognome del paziente                                                                                                                         |
| data_di_nascita                                         | Date    | Data di nascita del paziente                                                                                                                 |
| altezza                                                 | Number  | Altezza del paziente in centimetri                                                                                                           |
| peso                                                    | Number  | Peso del paziente in chilogrammi                                                                                                             |
| bmi                                                     | Number  | Body Mass Index                                                                                                                              |
| bsa                                                     | Number  | Body Surface Area                                                                                                                            |
| data_esame                                              | Date    | Data di esecuzione dell’ecocardiogramma                                                                                                      |
| eco_text                                                | Text    | Riassunto testuale del referto ecocardiografico                                                                                              |
| parametri                                               | Text    | Parametri tabellari non mappati singolarmente                                                                                                |
| Ventricolo_sinistro_GLS                                 | Number  | Global Longitudinal Strain del ventricolo sinistro                                                                                           |
| Ventricolo_sinistro_diametro_telediastolico             | Number  | Diametro telediastolico del ventricolo sinistro                                                                                              |
| Ventricolo_sinistro_setto_interventricolare_spessore_TD | Number  | Spessore telediastolico del setto interventricolare                                                                                          |
| Ventricolo_sinistro_parete_posteriore_spessore_TD       | Number  | Spessore telediastolico della parete posteriore                                                                                              |
| Ventricolo_sinistro_massa_indicizzata                   | Number  | Massa ventricolare sinistra indicizzata                                                                                                      |
| Ventricolo_sinistro_relative_wall_thickness             | Number  | Relative Wall Thickness                                                                                                                      |
| Ventricolo_sinistro_volume_telediastolico_Simpson       | Number  | Volume telediastolico secondo Simpson                                                                                                        |
| Ventricolo_sinistro_volume_telediastolico_ind_Simpson   | Number  | Volume telediastolico indicizzato secondo Simpson                                                                                            |
| Ventricolo_sinistro_volume_telesistolico_Simpson        | Number  | Volume telesistolico secondo Simpson                                                                                                         |
| Ventricolo_sinistro_volume_telesistolico_ind_Simpson    | Number  | Volume telesistolico indicizzato secondo Simpson                                                                                             |
| Ventricolo_sinistro_FE                                  | Number  | Frazione di eiezione del ventricolo sinistro                                                                                                 |
| Ventricolo_sinistro_frazione_eiezione_Simpson           | Number  | Frazione di eiezione calcolata con metodo Simpson                                                                                            |
| Ventricolo_sinistro_fractional_area_change              | Number  | Fractional Area Change                                                                                                                       |
| Ventricolo_destro_TAPSE                                 | Number  | TAPSE del ventricolo destro                                                                                                                  |
| Ventricolo_destro_velocita_S_TDI                        | Number  | Velocità S al TDI del ventricolo destro                                                                                                      |
| Ventricolo_destro_diametro_basale                       | Number  | Diametro basale del ventricolo destro                                                                                                        |
| Ventricolo_destro_diametro_medio                        | Number  | Diametro medio del ventricolo destro                                                                                                         |
| Ventricolo_destro_frac_wall_LS                          | Number  | Longitudinal strain della parete libera del ventricolo destro                                                                                |
| Ventricolo_destro_PAPs                                  | Number  | Pressione arteriosa polmonare sistolica                                                                                                      |
| Atrio_sinistro_volume_telesistolico                     | Number  | Volume telesistolico dell’atrio sinistro                                                                                                     |
| Atrio_sinistro_volume_telesistolico_indicizzato         | Number  | Volume telesistolico indicizzato dell’atrio sinistro                                                                                         |
| Aorta_diametro_seni_Valsalva                            | Number  | Diametro dei seni di Valsalva                                                                                                                |
| Aorta_diametro_giunzione_seno_tubulare                  | Number  | Diametro della giunzione seno-tubulare                                                                                                       |
| Aorta_diametro_tratto_tubulare                          | Number  | Diametro del tratto tubulare dell’aorta                                                                                                      |
| Aorta_diametro_arco                                     | Number  | Diametro dell’arco aortico                                                                                                                   |
| Valvola_aortica_insufficienza                           | Boolean | Presenza di insufficienza aortica                                                                                                            |
| Valvola_aortica_stenosi                                 | Boolean | Presenza di stenosi aortica                                                                                                                  |
| Valvola_aortica_protesi_in_sede                         | Boolean | Presenza di protesi valvolare aortica                                                                                                        |
| Valvola_aortica_protesi_degenerata                      | Boolean | Segni di degenerazione della protesi aortica                                                                                                 |
| Valvola_aortica_velocita_massima                        | Number  | Velocità massima transvalvolare aortica                                                                                                      |
| Valvola_aortica_gradiente_massimo                       | Number  | Gradiente massimo transaortico                                                                                                               |
| Valvola_aortica_gradiente_medio                         | Number  | Gradiente medio transaortico                                                                                                                 |
| Valvola_aortica_AVA                                     | Number  | Area valvolare aortica                                                                                                                       |
| Valvola_aortica_AVAi                                    | Number  | Area valvolare aortica indicizzata                                                                                                           |
| Valvola_aortica_DVI                                     | Number  | Doppler Velocity Index                                                                                                                       |
| Valvola_aortica_bicuspide                               | Boolean | Valvola aortica bicuspide                                                                                                                    |
| Valvola_aortica_PVL                                     | Boolean | Leak perivalvolare aortico                                                                                                                   |
| Valvola_mitrale_insufficienza                           | Boolean | Presenza di insufficienza mitralica                                                                                                          |
| Valvola_mitrale_stenosi                                 | Boolean | Presenza di stenosi mitralica                                                                                                                |
| Valvola_mitrale_gradiente_medio                         | Number  | Gradiente medio trans-mitralico                                                                                                              |
| Valvola_mitrale_area_valvolare                          | Number  | Area valvolare mitralica                                                                                                                     |
| Valvola_mitrale_annulus_AP                              | Number  | Diametro antero-posteriore dell’anulus mitralico                                                                                             |
| Valvola_mitrale_annulus_IC                              | Number  | Diametro inter-commissurale dell’anulus mitralico                                                                                            |
| Valvola_mitrale_distanza_SIV_C                          | Number  | Distanza setto interventricolare–coaptazione                                                                                                 |
| Valvola_mitrale_angolo_MA                               | Number  | Angolo mitro-aortico                                                                                                                         |
| Valvola_mitrale_lunghezza_lembo_anteriore               | Number  | Lunghezza del lembo anteriore mitralico                                                                                                      |
| Valvola_mitrale_lunghezza_lembo_posteriore              | Number  | Lunghezza del lembo posteriore mitralico                                                                                                     |
| Valvola_mitrale_rapporto_LAM_LP                         | Number  | Rapporto tra lembo anteriore e posteriore                                                                                                    |
| Valvola_mitrale_protesi_in_sede                         | Boolean | Presenza di protesi mitralica                                                                                                                |
| Valvola_mitrale_protesi_degenerata                      | Boolean | Degenerazione della protesi mitralica                                                                                                        |
| Valvola_mitrale_PVL                                     | Boolean | Leak perivalvolare mitralico                                                                                                                 |
| Valvola_mitrale_lesione_bilembo                         | Boolean | Coinvolgimento di entrambi i lembi                                                                                                           |
| Valvola_mitrale_lesione_anteriore                       | Boolean | Coinvolgimento del lembo anteriore                                                                                                           |
| Valvola_mitrale_lesione_posteriore                      | Boolean | Coinvolgimento del lembo posteriore                                                                                                          |
| Valvola_mitrale_scallop_A1                              | Boolean | Coinvolgimento scallop A1                                                                                                                    |
| Valvola_mitrale_scallop_A2                              | Boolean | Coinvolgimento scallop A2                                                                                                                    |
| Valvola_mitrale_scallop_A3                              | Boolean | Coinvolgimento scallop A3                                                                                                                    |
| Valvola_mitrale_scallop_P1                              | Boolean | Coinvolgimento scallop P1                                                                                                                    |
| Valvola_mitrale_scallop_P2                              | Boolean | Coinvolgimento scallop P2                                                                                                                    |
| Valvola_mitrale_scallop_P3                              | Boolean | Coinvolgimento scallop P3                                                                                                                    |
| Valvola_mitrale_tipo_lesione                            | Enum    | **Tipo di lesione mitralica da cercare nel testo**: Ventricolare, Atriale, Mista, Prolasso, Flail, Endocardite, Interferenza elettrocatetere |
| Valvola_mitrale_eziologia                               | Text    | Eziologia clinica dell’insufficienza mitralica (degenerativa, funzionale, ischemica, reumatica, ecc.)                                        |
| Valvola_mitrale_calcificazione_anello                   | Boolean | Presenza di calcificazione dell’anello mitralico                                                                                             |
| Valvola_mitrale_calcificazione_lembi                    | Boolean | Presenza di calcificazione dei lembi                                                                                                         |
| Valvola_mitrale_presenza_cleft                          | Boolean | Presenza di cleft mitralico                                                                                                                  |
| Valvola_mitrale_localizzazione_cleft                    | Text    | Localizzazione del cleft                                                                                                                     |
| Valvola_tricuspide_diametro_setto_laterale              | Number  | Diametro setto-laterale dell’anulus tricuspide                                                                                               |
| Valvola_tricuspide_diametro_setto_laterale_indicizzato  | Number  | Diametro setto-laterale indicizzato                                                                                                          |
| Valvola_tricuspide_insufficienza                        | Boolean | Presenza di insufficienza tricuspide                                                                                                         |
| Valvola_tricuspide_stenosi                              | Boolean | Presenza di stenosi tricuspide                                                                                                               |
| Valvola_tricuspide_eziologia                            | Text    | Eziologia della patologia tricuspide                                                                                                         |
| Valvola_polmonare_insufficienza                         | Boolean | Presenza di insufficienza polmonare                                                                                                          |
| Valvola_polmonare_stenosi                               | Boolean | Presenza di stenosi polmonare                                                                                                                |



### **Istruzioni IMPORTANTI:**

- Considera che molti parametri ecocardiografici appartengono a **sezioni** specifiche (es. Ventricolo sinistro, Ventricolo destro, Valvola aortica, Valvola mitrale, Valvola tricuspide, Valvola polmonare).
- Quando riporti coppie chiave‑valore in **parametri**, anteponi sempre il nome della sezione alla variabile, in forma `Sezione_nome_variabile`.
  - Esempi: `Ventricolo_sinistro_GLS: -18`, `Ventricolo_sinistro_FE: 45`, `Valvola_aortica_gradiente_max_aortica: 40`, `Valvola_mitralica_TAPSE: 17`.
- Se trovi tabelle/elenco parametri (es. "FE: 45 %", "TAPSE: 17 mm"), estrai ciascuna coppia nel campo **parametri** come testo strutturato `"Sezione_nome_variabile: valore"` separati da **punto e virgola**.
- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
**NON** aggiungere commenti, spiegazioni, note, intestazioni o altro: **solo** la lista JSON.
-Se trovi **tabelle**, **elenchi** o **parametri** , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura).
-Se trovi **esami** o **strumentali** (ad esempio esami di laboratorio) , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura). - Output = **solo** una lista JSON di oggetti `{"entità": <nome>, "valore": <valore>}`. Nessun altro testo.

questi esempi servono per capire il fromato di output
###Esempio di input(esempio parziale della lettera di dimissione)
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
]
''',


        "eco_postoperatorio": '''
Sei un medico specializzato in cardiochirurgia.
Estrai le seguenti entità dall’ecocardiogramma **postoperatorio**
### **Istruzioni IMPORTANTI:**

- Considera che molti parametri ecocardiografici appartengono a **sezioni** specifiche (es. Ventricolo sinistro, Ventricolo destro, Valvola aortica, Valvola mitrale, Valvola tricuspide, Valvola polmonare).
- Quando riporti coppie chiave‑valore in **parametri**, anteponi sempre il nome della sezione alla variabile, in forma `Sezione_nome_variabile`.
  - Esempi: `Ventricolo_sinistro_GLS: -18`, `Ventricolo_sinistro_FE: 45`, `Valvola_aortica_gradiente_max_aortica: 40`, `Valvola_mitralica_TAPSE: 17`.
- Se trovi tabelle/elenco parametri (es. "FE: 45 %", "TAPSE: 17 mm"), estrai ciascuna coppia nel campo **parametri** come testo strutturato `"Sezione_nome_variabile: valore"` separati da **punto e virgola**.
- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
**NON** aggiungere commenti, spiegazioni, note, intestazioni o altro: **solo** la lista JSON.
-Se trovi **tabelle**, **elenchi** o **parametri** , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura).
-Se trovi **esami** o **strumentali** (ad esempio esami di laboratorio) , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura). - Output = **solo** una lista JSON di oggetti `{"entità": <nome>, "valore": <valore>}`. Nessun altro testo.

questi esempi servono per capire il fromato di output

###Esempio di input(esempio parziale della lettera di dimissione)
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
]
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
| tac_text             | Text    | Descrizione completa del referto TC              |
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

### **Istruzioni IMPORTANTI:**
- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
**NON** aggiungere commenti, spiegazioni, note, intestazioni o altro: **solo** la lista JSON.
-Se trovi **tabelle**, **elenchi** o **parametri** , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura).
-Se trovi **esami** o **strumentali** (ad esempio esami di laboratorio) , estrai **ogni** coppia chiave-valore aggiuntiva (senza unità di misura). 
---
 Questo è un esempio di input per capire il formato di output:
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
]

''',
        "intervento": '''
Sei un cardiochirurgo. Estrai le seguenti entità dal referto di intervento/verbale operatorio.

| Entità                                | Tipo    | Descrizione                                                                                                                                       |
| ------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| n_cartella                            | Number  | Numero identificativo univoco della cartella clinica del paziente.                                                                                |
| nome                                  | Text    | Nome del paziente.                                                                                                                                |
| cognome                               | Text    | Cognome del paziente.                                                                                                                             |
| data_di_nascita                       | Date    | Data di nascita del paziente.                                                                                                                     |
| data_intervento                       | Date    | Data in cui è stato eseguito l’intervento cardiochirurgico.                                                                                       |
| Percorso                              | Text    | Tipologia di percorso dell’intervento: **Chirurgico** o **Transcatetere**.                                                                        |
| redo                                  | Boolean | Indica se l’intervento è un REDO. Imposta `true` se è presente un precedente intervento cardiochirurgico o transcatetere sul cuore.               |
| cec                                   | Boolean | Utilizzo della circolazione extracorporea (CEC) durante l’intervento.                                                                             |
| cannulazionearteriosa                 | Text    | Tipo di cannulazione arteriosa utilizzata (es. aortica, femorale).                                                                                |
| statopaz                              | Text    | Stato clinico del paziente al momento dell’intervento (es. stabile, critico).                                                                     |
| cardioplegia                          | Text    | Tipo di cardioplegia utilizzata per la protezione miocardica.                                                                                     |
| approcciochirurgico                   | Text    | Approccio chirurgico utilizzato (es. sternotomia mediana, mini-invasivo).                                                                         |
| entratainsala                         | Time    | Orario di ingresso del paziente in sala operatoria.                                                                                               |
| iniziointervento                      | Time    | Orario di inizio dell’intervento chirurgico.                                                                                                      |
| iniziocec                             | Time    | Orario di inizio della circolazione extracorporea.                                                                                                |
| inizioclamp                           | Time    | Orario di applicazione del clamp aortico.                                                                                                         |
| inizioacc                             | Time    | Orario di inizio arresto cardiaco controllato.                                                                                                    |
| fineacc                               | Time    | Orario di fine arresto cardiaco controllato.                                                                                                      |
| fineclamp                             | Time    | Orario di rimozione del clamp aortico.                                                                                                            |
| finecec                               | Time    | Orario di fine circolazione extracorporea.                                                                                                        |
| fineintervento                        | Time    | Orario di fine dell’intervento chirurgico.                                                                                                        |
| uscitasala                            | Time    | Orario di uscita del paziente dalla sala operatoria.                                                                                              |
| primo operatore cognome               | Text    | Cognome del primo operatore chirurgico responsabile dell’intervento.                                                                              |
| primo operatore nome                  | Text    | Nome del primo operatore chirurgico responsabile dell’intervento.                                                                                 |
| num_interventi                        | Number  | Numero totale di interventi/procedure eseguite nello stesso atto operatorio.                                                                      |
| intervento 1                          | Text    | Descrizione del primo intervento eseguito (aderente alla codifica del CSV).                                                                       |
| protesi 1                             | Text    | Tipo di protesi utilizzata nel primo intervento (Biologica / Meccanica / Anello).                                                                 |
| modello 1                             | Text    | Modello della protesi impiantata.                                                                                                                 |
| numero 1                              | Number  | Numero o misura della protesi impiantata.                                                                                                         |
| eziologia_valvolare 1                 | Text    | Eziologia della patologia valvolare (es. degenerativa, reumatica, infettiva).                                                                     |
| intervento text                       | Text    | Testo libero riassuntivo del verbale operatorio.                                                                                                  |
| edemi_declivi                         | Boolean | Presenza di edemi declivi pre-operatori. Imposta `true` se nel testo sono riportati *edemi declivi*, *edemi periferici*, *edema malleolare*.      |
| ascite                                | Boolean | Presenza di ascite pre-operatoria. Imposta `true` se nel testo compaiono *ascite* o *versamento ascitico*.                                        |
| intervento_cardiochirurgico_pregresso | Boolean | Presenza di precedente intervento cardiochirurgico prima dell’intervento attuale. Imposta `true` se riportato in anamnesi o nel testo operatorio. |
| intervento_transcatetere_pregresso    | Boolean | Presenza di precedente intervento transcatetere (es. TAVI, MitraClip) prima dell’intervento attuale.                                              |
| intervento_pregresso_descrizione      | Text    | Descrizione libera dell’intervento cardiochirurgico o transcatetere pregresso. Deve riferirsi **solo a interventi precedenti** a quello attuale.  |
| Anno_REDO                             | Date    | Anno/data dell’intervento cardiochirurgico o transcatetere pregresso (REDO), non riferito all’intervento attuale.                                 |
| altri_diuretici                       | Boolean | Uso di diuretici diversi dalla furosemide (es. tiazidici, antialdosteronici) nella terapia pre-operatoria.                                        |
| statine                               | Boolean | Terapia con statine. **Regola derivata**: se `statine = true` → `dislipidemia = true`.                                                            |
| insulina                              | Boolean | Terapia insulinica pre-operatoria. **Regola derivata**: se `insulina = true` → `diabete = true`.                                                  |
| metformina                            | Boolean | Terapia con metformina pre-operatoria. **Regola derivata**: se `metformina = true` → `diabete = true`.                                            |
| anti_SGLT2                            | Boolean | Terapia con inibitori SGLT2 (gliflozine). **Regola derivata**: se `anti_SGLT2 = true` → `diabete = true`.                                         |
| ARNI                                  | Boolean | Terapia con ARNI (sacubitril/valsartan – Entresto) in fase pre-operatoria.                                                                        |


### **Istruzioni IMPORTANTI:**

- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
-Se la data accanto al valore è < data_intervento → campo pre_
-Se la data accanto al valore è ≥ data_intervento → campo post_
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
Questo esempio serve per capire solamente il formato di output
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


    "anamnesi": '''
    Sei un medico. Estrai ESCLUSIVAMENTE le seguenti entità dall'ANAMNESI (periodo **preoperatorio**):
    
    - n_cartella (Number), nome (Text), cognome (Text), data_di_nascita (Date)
    - Terapia (Text)                 # terapia in atto all'ingresso, prima dell'intervento
    - Allergie (Text)                # farmacoallergie/intolleranze
    - Abitudini (Text)               # fumo/alcol/altro, se presenti
    - Comorbidita (Text)             # elenco o riassunto
    - esami_laboratorio (Text)      # labs/strumentali al ricovero preoperatorio
    - parametri (Text)               # se presenti tabelle/elenco parametri: riportali come "chiave: valore" separati da "; "
    
    REGOLE:
    - Considera solo informazioni chiaramente riferite alla fase **preoperatoria** (in base alle date nel documento).
    - Output = LISTA JSON di oggetti: { "entità": "<nome>", "valore": "<valore>" } — niente altro.
    - NON inventare. Se un campo non è presente, omettilo.
    - Se trovi tabelle/elenco (es. "Creatinina: 1.2 mg/dL", "FE: 45 %"), concatenali in **parametri** senza unità, in forma "Creatinina: 1.2; FE: 45".
''',
    "epicrisi_ti": '''
    Sei un medico. Estrai ESCLUSIVAMENTE le seguenti entità dall’EPICRISI di Terapia Intensiva (periodo post‑operatorio immediato):
    
    - n_cartella (Number), nome (Text), cognome (Text)
    - data_intervento (Date)
    - Decorso_post_operatorio (Text)        # ventilazione, emodinamica, complicanze, drenaggi, diuresi, etc.
    - IABP_ECMO_IMPELLA (Boolean), Inotropi (Boolean)
    - eventi_avversi_TI (Text)
    - data_dimissione_cch (Date)
    - parametri (Text)  # se presenti tabelle/elenco parametri, riportali come "chiave: valore" separati da "; "
    
    REGOLE:
    - Output = LISTA JSON di oggetti { "entità": "<nome>", "valore": "<valore>" } — niente altro.
    - NON inventare: ometti i campi assenti.
    - Se trovi misure/tabellari, normalizzale senza unità in **parametri**.
''',

    "cartellino_anestesiologico": '''
    Sei un anestesista. Estrai ESCLUSIVAMENTE le seguenti entità dalla scheda anestesiologica intraoperatoria:
    | Entità                  | Tipo | Descrizione                                                                                               |
| ----------------------- | ---- | --------------------------------------------------------------------------------------------------------- |
| ingresso_in_sala        | Time | Ora di ingresso del paziente in sala operatoria. Cerca nel testo dell’intervento o in “INGRESSO IN SALA”. |
| inizio_tempo_chirurgico | Time | Ora di inizio del tempo chirurgico. Corrisponde a “INIZIO TEMPO CHIRURGICO” o simile nel documento.       |
| tempi_cch_inizio_cec    | Time | Ora di inizio della circolazione extracorporea (CEC). Cerca come “TEMPI CCH: Inizio CEC”.                 |
| tempi_cch_clamp_ao      | Time | Ora del clampaggio aortico (clamp Ao). Cerca “TEMPI CCH: Clamp Ao”.                                       |
| tempi_cch_declamp_ao    | Time | Ora del declampaggio aortico (declamp Ao). Cerca “TEMPI CCH: Declamp Ao”.                                 |
| tempi_cch_fine_cec      | Time | Ora di fine della circolazione extracorporea. Cerca “TEMPI CCH: fine CEC”.                                |
| fine_tempo_chirurgico   | Time | Ora di fine del tempo chirurgico. Corrisponde a “FINE TEMPO CHIRURGICO” o simile.                         |
| uscita_di_sala          | Time | Ora di uscita del paziente dalla sala operatoria. Cerca “USCITA DI SALA”.                                 |
| cardioplegia            | Text | Tipo di soluzione cardioplegica usata. Cerca questa informazione nel testo dell’intervento.               |
| tipo_plegia             | Text | Dettaglio sul tipo di cardioplegia (es. ematica, cristalloide). Cerca nel testo dell’intervento.          |


    ### **Istruzioni IMPORTANTI:**

- Ragiona considerando **frase per frase** e sfrutta sempre le **date** (ingresso, intervento, dimissione, date degli esami) per distinguere ciò che è **pre-operatorio** da ciò che è **post-operatorio/dimissione**.
- Non estrarre **nessuna entità** diversa da quelle elencate.
- Se un'entità non è presente nella lettera, **non inventarla** e **non includerla** nel risultato.
- I nomi delle entità possono essere acronimi o forme abbreviate: mappa sempre correttamente il significato clinico al nome di entità definito nella tabella.
- Cerca tutte le entità indicate.
- Il formato di output deve essere una lista JSON, dove ogni elemento è un oggetto con **due chiavi**:
    - `"entità"`: il nome dell'entità
    - `"valore"`: il valore estratto dell'entità
-Se la data accanto al valore è < data_intervento → campo pre_
-Se la data accanto al valore è ≥ data_intervento → campo post_
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
Questo esempio serve per capire solamente il formato di output
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
]'''

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
