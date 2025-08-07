import camelot
import pandas as pd
import re

class TableParser:
    """
    Estrae e normalizza tabelle da PDF in DataFrame.
    Usa Camelot per l'estrazione e pulisce valori tra parentesi e unità.
    """
    def __init__(self, extraction_engine: str = "camelot"):
        self.engine = extraction_engine

    def extract_tables(self, pdf_path: str) -> list[pd.DataFrame]:
        """
        Estrae tutte le tabelle dal PDF e le normalizza.

        :param pdf_path: percorso al file PDF
        :return: lista di DataFrame normalizzati
        """
        tables = camelot.read_pdf(pdf_path, pages='all').dfs
        return [self.normalize_table(df) for df in tables]

    def normalize_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pulisce il DataFrame:
        - rimuove righe/colonne completamente vuote
        - elimina testo tra parentesi quadre
        - estrae il valore numerico principale, scartando unità e annotazioni
        """
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        # Rimuove testo tra parentesi quadre
        df = df.replace(r"\[.*?\]", "", regex=True)

        def clean_cell(cell):
            text = str(cell).strip()
            m = re.match(r"(?P<num>-?\d+(?:\.\d+)?)", text)
            if m:
                return m.group('num')
            return text

        return df.applymap(clean_cell)
