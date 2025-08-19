# config/type_phrases.py
# -*- coding: utf-8 -*-
"""
Frasi/regex di inizio documento per segmentare la cartella clinica in sezioni.
Derivate dal documento di specifica che mi hai inviato.
Usare sempre con re.IGNORECASE.
"""

from typing import Dict, List

# Nota implementativa:
# - Ancoriamo all'inizio riga o subito dopo un newline: (?:^|\n)\s*
# - Gestiamo diversi tipi di trattino: [-–—]
# - Manteniamo pattern specifici prima di quelli generici
# - “Verbale/Referto operatorio” sono alias di **intervento** (unico tipo canonico)

TYPE_START_PHRASES: Dict[str, List[str]] = {
    # 1) Lettera di dimissione
    "lettera_dimissione": [
        r"(?:^|\n)\s*relazione\s+clinica\s+alla\s+dimissione\s*[-–—]\s*definitiva\b",
        r"(?:^|\n)\s*relazione\s+clinica\s+alla\s+dimissione\b",
        r"(?:^|\n)\s*lettera\s+di\s+dimissione\b",
        r"(?:^|\n)\s*si\s+dimette\s+in\s+data\b",
    ],

    # 2) Anamnesi
    "anamnesi": [
        r"(?:^|\n)\s*anamnesi\b",
        r"(?:^|\n)\s*cenni\s+anamnestici\b",
    ],

    # 3) Epicrisi terapia intensiva (TICCH)
    "epicrisi_ti": [
        r"(?:^|\n)\s*epicrisi\s+terapia\s+intensiva(?:\s*/?\s*TICCH)?\b",
        r"(?:^|\n)\s*epicrisi\s+ticch\b",
    ],

    # 4) Cartellino/Scheda anestesiologica intraoperatoria
    "cartellino_anestesiologico": [
        r"(?:^|\n)\s*scheda\s+anestesiologica\s+intraoperatoria\b",
        r"(?:^|\n)\s*cartellino\s+anestesiologico\b",
        r"(?:^|\n)\s*scheda\s+anestesiologica\b",
    ],

    # 5) Intervento cardiochirurgico (include alias Verbale/Referto operatorio)
    "intervento": [
        r"(?:^|\n)\s*intervento\s+cardiochirurgico\b",
        r"(?:^|\n)\s*verbale\s+operatorio\b",
        r"(?:^|\n)\s*referto\s+operatorio\b",
    ],

    # 6) Coronarografia / Emodinamica / Cateterismo cardiaco
    "coronarografia": [
        r"(?:^|\n)\s*laboratorio\s+di\s+emodinamica\s+e\s+cardiologia\s+interventistica\b",
        r"(?:^|\n)\s*coronarografia\b",
        r"(?:^|\n)\s*cateterismo\s+cardiaco\b",
        r"(?:^|\n)\s*angiografia\s+coronarica\b",
    ],

    # 7) Ecocardiogramma preoperatorio
    # (La distinzione fra pre/post avviene a valle usando la cronologia: pre < intervento < post)
    "eco_preoperatorio": [
        r"(?:^|\n)\s*laborator[io]i?\s+di\s+ecocardiografia\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transtoracico\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transesofageo\b",
    ],

    # 8) Ecocardiogramma postoperatorio (stessi header di pre; disambiguazione temporale)
    "eco_postoperatorio": [
        r"(?:^|\n)\s*laborator[io]i?\s+di\s+ecocardiografia\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transtoracico\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transesofageo\b",
    ],

    # 9) TC cuore/coronarie
    "tc_cuore": [
        r"(?:^|\n)\s*tc\s+cuore\b",
        r"(?:^|\n)\s*tac\s+cuore\b",
        r"(?:^|\n)\s*tc\s+coronaric[ae]\b",
        r"(?:^|\n)\s*angio[-–—]?tc\s+cardiac[ae]\b",
        r"(?:^|\n)\s*tc\s+cardiac[ae]\b",
    ],
}

# Priorità generale per risoluzione conflitti (opzionale, usata dal segmenter se serve)
TYPE_PRIORITY: List[str] = [
    "lettera_dimissione",
    "intervento",
    "cartellino_anestesiologico",
    "epicrisi_ti",
    "coronarografia",
    "tc_cuore",
    "eco_preoperatorio",
    "eco_postoperatorio",
    "anamnesi",
]
