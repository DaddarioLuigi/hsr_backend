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
    # 1) Lettera di dimissione (pag 8-11) - Documento principale
    "lettera_dimissione": [
        r"(?:^|\n)\s*RELAZIONE\s+CLINICA\s+ALLA\s+DIMISSIONE\s*[-–—]\s*DEFINITIVA\b",
        r"(?:^|\n)\s*relazione\s+clinica\s+alla\s+dimissione\b",
        r"(?:^|\n)\s*lettera\s+di\s+dimissione\b",
        r"(?:^|\n)\s*si\s+dimette\s+in\s+data\b",
    ],

    # 2) Anamnesi (pag 35) - Storia del paziente
    "anamnesi": [
        r"(?:^|\n)\s*anamnesi\b",
        r"(?:^|\n)\s*cenni\s+anamnestici\b",
    ],

    # 3) Epicrisi terapia intensiva (pag 44) - TICCH
    "epicrisi_ti": [
        r"(?:^|\n)\s*epicrisi\s+terapia\s+intensiva(?:\s*/?\s*TICCH)?\b",
        r"(?:^|\n)\s*epicrisi\s+ticch\b",
    ],

    # 4) Cartellino anestesiologico (pag 120) - Dati fissi con orari
    "cartellino_anestesiologico": [
        r"(?:^|\n)\s*scheda\s+anestesiologica\s+intraoperatoria\b",
        r"(?:^|\n)\s*cartellino\s+anestesiologico\b",
        r"(?:^|\n)\s*scheda\s+anestesiologica\b",
    ],

    # 5) Verbale operatorio (pag 125) - Relazione dell'intervento
    "intervento": [
        r"(?:^|\n)\s*verbale\s+operatorio\b",
        r"(?:^|\n)\s*intervento\s+cardiochirurgico\b",
        r"(?:^|\n)\s*referto\s+operatorio\b",
    ],

    # 6) Coronarografia (pag 135) - Stato delle coronarie
    "coronarografia": [
        r"(?:^|\n)\s*laboratorio\s+di\s+emodinamica\s+e\s+cardiologia\s+interventistica\b",
        r"(?:^|\n)\s*coronarografia\b",
        r"(?:^|\n)\s*cateterismo\s+cardiaco\b",
        r"(?:^|\n)\s*angiografia\s+coronarica\b",
    ],

    # 7) Ecocardiogramma preoperatorio (pag 137-138) - PRIMA dell'intervento
    "eco_preoperatorio": [
        r"(?:^|\n)\s*laborator[io]i?\s+di\s+ecocardiografia\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transtoracico\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transesofageo\b",
    ],

    # 8) Ecocardiogramma postoperatorio (pag 139) - DOPO l'intervento
    "eco_postoperatorio": [
        r"(?:^|\n)\s*laborator[io]i?\s+di\s+ecocardiografia\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transtoracico\b",
        r"(?:^|\n)\s*ecocardiogramma\s+transesofageo\b",
    ],

    # 9) TC cuore/coronarie - Alternativa a coronarografia
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
