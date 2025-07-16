# llm/prompts.py

class PromptManager:
    SCHEMAS = {
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
                "Ritmo_alla_dimissione": { "type": "number", "enum": [0, 1, 2] },
                "H_Stay_giorni_da_intervento_a_dimissione": { "type": "number" },
                "Morte": { "type": "boolean" },
                "Causa_morte": { "type": "string" },
                "data_morte": { "type": "string", "format": "date" },
                "esami_alla_dimissione": { "type": "string" },
                "terapia_alla_dimissione": { "type": "string" }
            },
            "required": ["n_cartella", "nome", "cognome"]
        }
    }

    PROMPTS = {
        "lettera_dimissione": "Il tuo prompt qui..."
        # Aggiungi qui gli altri prompt
    }

    def get_prompt_for(self, document_type: str) -> str:
        """
        Restituisce il prompt associato al document_type.
        """
        if document_type not in self.PROMPTS:
            raise ValueError(f"Prompt non definito per {document_type}")
        return self.PROMPTS[document_type]

    def get_schema_for(self, document_type: str) -> dict:
        """
        Restituisce lo schema JSON associato al document_type.
        """
        if document_type not in self.SCHEMAS:
            raise ValueError(f"Schema non definito per {document_type}")
        return self.SCHEMAS[document_type]
