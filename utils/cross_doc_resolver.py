# utils/cross_doc_resolver.py
# -*- coding: utf-8 -*-
"""
Cross-document resolver:
- Normalizza alias di tipo documento (es. 'verbale_operatorio' -> 'intervento')
- Costruisce una mappa globale chiave->valore scegliendo la fonte migliore per-chiave
- Esegue il backfill delle entità mancanti in ciascun documento
"""

from __future__ import annotations
from typing import Dict, Any, List

# =========================
# TIPOLOGIE SUPPORTATE
# =========================
DOC_TYPES_ALL: List[str] = [
    "lettera_dimissione",
    "anamnesi",
    "epicrisi_ti",
    "cartellino_anestesiologico",
    "intervento",            # 'verbale/referto operatorio' confluiscono qui
    "coronarografia",
    "eco_preoperatorio",
    "eco_postoperatorio",
    "tc_cuore",
    "altro",
]

# Alias -> tipo canonico
ALIAS_TO_CANONICAL: Dict[str, str] = {
    "verbale_operatorio": "intervento",
    "referto_operatorio": "intervento",
}

def normalize_doc_type(doc_type: str) -> str:
    """Mappa alias su tipo canonico."""
    return ALIAS_TO_CANONICAL.get(doc_type, doc_type)

def _collapse_aliases(per_doc_entities: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Normalizza le chiavi tipo documento e merge dei dizionari entità in caso di alias duplicati.
    Regola di merge: non sovrascrivere valori già presenti e non vuoti.
    """
    collapsed: Dict[str, Dict[str, Any]] = {}
    for raw_type, ents in per_doc_entities.items():
        doc_type = normalize_doc_type(raw_type)
        merged = dict(collapsed.get(doc_type, {}))
        for k, v in (ents or {}).items():
            if k not in merged or merged[k] in (None, "", [], {}):
                merged[k] = v
        collapsed[doc_type] = merged
    return collapsed

# =========================
# GRUPPI DI CHIAVI
# =========================
GLOBAL_ID_KEYS = [
    "n_cartella", "nome", "cognome", "data_di_nascita", "sesso", "numero_di_telefono",
]

GLOBAL_TIMELINE_KEYS = [
    "data_ingresso_cch", "data_dimissione_cch", "data_intervento",
]

GLOBAL_CLINICAL_KEYS = [
    "Diagnosi",
    "Anamnesi",
    "Motivo_ricovero",
    "Terapia",                  # terapia in atto all’ingresso (tipicamente Anamnesi/Lettera)
    "terapia_alla_dimissione",  # Lettera di dimissione
    "esami_all_ingresso",       # Lettera/Anamnesi
    "esami_alla_dimissione",    # Lettera/Epicrisi TI
    "Decorso_post_operatorio",  # Epicrisi TI/Lettera
]

GLOBAL_OR_TIMES = [
    "entratainsala", "iniziointervento", "iniziocec", "inizioclamp",
    "inizioacc", "fineacc", "fineclamp", "finecec", "fineintervento", "uscitasala",
]

ECHO_CORO_KEYS = [
    "data_esame",
]

# =========================
# PRIORITÀ PER-CHIAVE
# =========================
# Default in caso una chiave non abbia una lista specifica
DEFAULT_PRIORITY: List[str] = [
    "lettera_dimissione",
    "intervento",
    "cartellino_anestesiologico",
    "epicrisi_ti",
    "anamnesi",
    "coronarografia",
    "tc_cuore",
    "eco_preoperatorio",
    "eco_postoperatorio",
    "altro",
]

# Mappa chiave -> lista di priorità (prima è fonte preferita)
PER_KEY_PRIORITY: Dict[str, List[str]] = {}

# Identificativi/anagrafiche: lettera è spesso più affidabile/definitiva
for k in GLOBAL_ID_KEYS:
    PER_KEY_PRIORITY[k] = [
        "lettera_dimissione",
        "intervento",
        "anamnesi",
        "epicrisi_ti",
        "coronarografia",
        "tc_cuore",
        "eco_preoperatorio",
        "eco_postoperatorio",
        "altro",
    ]

# Timeline ricovero
PER_KEY_PRIORITY["data_ingresso_cch"]   = ["lettera_dimissione", "anamnesi", "epicrisi_ti", "altro"]
PER_KEY_PRIORITY["data_dimissione_cch"] = ["lettera_dimissione", "epicrisi_ti", "altro"]
# Data intervento: verbale/intervento > cartellino
PER_KEY_PRIORITY["data_intervento"]     = ["intervento", "cartellino_anestesiologico", "lettera_dimissione", "epicrisi_ti", "altro"]

# Clinica
PER_KEY_PRIORITY["Diagnosi"]                 = ["lettera_dimissione", "intervento", "anamnesi", "altro"]
PER_KEY_PRIORITY["Anamnesi"]                 = ["lettera_dimissione", "anamnesi", "altro"]
PER_KEY_PRIORITY["Motivo_ricovero"]          = ["lettera_dimissione", "anamnesi", "altro"]
PER_KEY_PRIORITY["Terapia"]                  = ["anamnesi", "lettera_dimissione", "epicrisi_ti", "altro"]
PER_KEY_PRIORITY["terapia_alla_dimissione"]  = ["lettera_dimissione", "epicrisi_ti", "altro"]
PER_KEY_PRIORITY["esami_all_ingresso"]       = ["lettera_dimissione", "anamnesi", "altro"]
PER_KEY_PRIORITY["esami_alla_dimissione"]    = ["lettera_dimissione", "epicrisi_ti", "altro"]
PER_KEY_PRIORITY["Decorso_post_operatorio"]  = ["epicrisi_ti", "lettera_dimissione", "altro"]

# Tempi sala/CEC: cartellino > intervento
for k in GLOBAL_OR_TIMES:
    PER_KEY_PRIORITY[k] = ["cartellino_anestesiologico", "intervento", "lettera_dimissione", "altro"]

# Eco / Coro: data esame (più recente spesso è post-op eco)
PER_KEY_PRIORITY["data_esame"] = ["eco_postoperatorio", "eco_preoperatorio", "coronarografia", "tc_cuore", "altro"]

# =========================
# CORE LOGIC
# =========================
def _pick_with_priority(per_doc_entities: Dict[str, Dict[str, Any]], key: str) -> Any:
    """
    Restituisce il valore migliore per 'key' in base alla priorità per-chiave.
    """
    priority = PER_KEY_PRIORITY.get(key, DEFAULT_PRIORITY)
    for src in priority:
        val = per_doc_entities.get(src, {}).get(key)
        if val not in (None, "", [], {}):
            return val
    return None

def build_global_map(per_doc_entities: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Costruisce una mappa globale chiave->valore usando priorità per-chiave.
    """
    # 1) Normalizza alias e merge
    per_doc_entities = _collapse_aliases(per_doc_entities)

    # 2) Colleziona l'universo delle chiavi disponibili nei documenti
    keys = set()
    for d in per_doc_entities.values():
        keys.update((d or {}).keys())

    # 3) Picks
    global_map: Dict[str, Any] = {}
    for k in keys:
        picked = _pick_with_priority(per_doc_entities, k)
        if picked not in (None, "", [], {}):
            global_map[k] = picked
    return global_map

def backfill_entities_for_doc(doc_type: str,
                              entities: Dict[str, Any],
                              global_map: Dict[str, Any]) -> Dict[str, Any]:
    """
    Riempie i buchi nelle entità del documento con valori globali, senza sovrascrivere.
    """
    if not entities:
        return entities
    updated = dict(entities)
    for k, v in (global_map or {}).items():
        if k not in updated or updated[k] in (None, "", [], {}):
            updated[k] = v
    return updated
