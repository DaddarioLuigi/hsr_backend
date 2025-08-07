import os
import logging
import pandas as pd
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ExcelManager:
    EXPORT_DIR = "export"
    EXPORT_PATH = os.path.join(EXPORT_DIR, "output.xlsx")

    @staticmethod
    def normalize_key(key: str) -> str:
        """
        Trasforma chiavi con spazi, slash, parentesi in underscore e minuscole.
        """
        return (key.strip()
                .replace("/", "_")
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("-", "_")
                .lower())

    def _create_template(self):
        """
        Crea il file Excel vuoto se non esiste, con almeno un foglio temporaneo.
        """
        os.makedirs(self.EXPORT_DIR, exist_ok=True)
        if not os.path.exists(self.EXPORT_PATH):
            with pd.ExcelWriter(self.EXPORT_PATH, engine='openpyxl') as writer:
                # Crea un foglio temporaneo per evitare errori openpyxl
                pd.DataFrame({"temp": [None]}).to_excel(writer, sheet_name="temp", index=False)
        logging.info(f"Created new Excel template at {self.EXPORT_PATH}")

    def update_excel(self, patient_id: str, document_type: str, estratti: dict):
        """
        Aggiunge o aggiorna i dati estratti per un paziente sul foglio relativo a document_type.
        Le colonne vengono aggiunte dinamicamente in base alle entità trovate.
        """
        os.makedirs(self.EXPORT_DIR, exist_ok=True)
        # Normalizza tutte le chiavi in estratti
        normalized = {self.normalize_key(k): v for k, v in estratti.items()}
        sheet = document_type
        # Se il file non esiste, crea il template vuoto
        if not os.path.exists(self.EXPORT_PATH):
            self._create_template()
        # Leggi tutti i fogli esistenti
        try:
            all_sheets = pd.read_excel(self.EXPORT_PATH, sheet_name=None, dtype=object)
        except Exception:
            all_sheets = {}
        # Prendi il foglio se esiste, altrimenti crealo
        if sheet in all_sheets:
            df = all_sheets[sheet]
        else:
            df = pd.DataFrame()
        # Aggiungi nuove colonne se necessario
        for col in normalized.keys():
            if col not in df.columns:
                df[col] = None
        # Prepara i dati per la riga
        row_data = {col: normalized.get(col, None) for col in df.columns}
        # Cerca se esiste già una riga con lo stesso n_cartella (o patient_id)
        id_col = self.normalize_key("n_cartella")
        if id_col in df.columns:
            mask = df[id_col].astype(str) == str(patient_id)
        else:
            mask = pd.Series([False]*len(df))
        if mask.any():  # Aggiorna riga esistente
            for col, val in row_data.items():
                df.loc[mask, col] = val
            logging.debug(f"Updated {sheet} for patient {patient_id}")
        else:  # Aggiunge nuova riga
            df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
            logging.debug(f"Appended new row to {sheet} for patient {patient_id}")
        # Aggiorna la mappa dei fogli
        all_sheets[sheet] = df
        # Rimuovi il foglio 'temp' se ci sono altri fogli reali
        if 'temp' in all_sheets and len(all_sheets) > 1:
            del all_sheets['temp']
        # Scrivi tutti i fogli
        with pd.ExcelWriter(self.EXPORT_PATH, engine='openpyxl') as writer:
            for sname, sdf in all_sheets.items():
                sdf.to_excel(writer, sheet_name=sname, index=False)

    def build_excel_from_uploads(self, uploads_dir="uploads"):
        """
        Scansiona la cartella uploads e crea un file Excel dinamico:
        - Un foglio per ogni tipo documento (nome sottocartella)
        - Colonne = unione di tutte le chiavi trovate nei vari entities.json di quel tipo
        - Ogni riga = un entities.json
        """
        os.makedirs(self.EXPORT_DIR, exist_ok=True)
        # Mappa: tipo_doc -> lista di dict (ogni dict = entities.json normalizzato)
        doc_data = {}
        # Mappa: tipo_doc -> set di tutte le chiavi trovate
        doc_keys = {}
        for paziente in os.listdir(uploads_dir):
            paz_path = os.path.join(uploads_dir, paziente)
            if not os.path.isdir(paz_path):
                continue
            for tipo_doc in os.listdir(paz_path):
                tipo_path = os.path.join(paz_path, tipo_doc)
                if not os.path.isdir(tipo_path):
                    continue
                entities_path = os.path.join(tipo_path, "entities.json")
                if not os.path.exists(entities_path):
                    continue
                try:
                    with open(entities_path, "r") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Errore lettura {entities_path}: {e}")
                    continue
                # Normalizza chiavi
                norm_data = {self.normalize_key(k): v for k, v in data.items()}
                doc_data.setdefault(tipo_doc, []).append(norm_data)
                doc_keys.setdefault(tipo_doc, set()).update(norm_data.keys())
        # Crea un DataFrame per ogni tipo_doc
        with pd.ExcelWriter(self.EXPORT_PATH, engine='openpyxl') as writer:
            for tipo_doc, rows in doc_data.items():
                columns = sorted(doc_keys[tipo_doc])
                df = pd.DataFrame(rows, columns=columns)
                df.to_excel(writer, sheet_name=tipo_doc, index=False)
        print(f"Creato Excel dinamico in {self.EXPORT_PATH}")

    def export_excel_file(self) -> str:
        """
        Ritorna il path del file Excel pronto per il download.
        """
        return self.EXPORT_PATH
