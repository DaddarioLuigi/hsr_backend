# utils/document_segmenter.py
# -*- coding: utf-8 -*-
"""
Segmentazione del markdown OCR della cartella clinica in sezioni omogenee.

Logica:
- Scandisce il testo con le regex in config/type_phrases.TYPE_START_PHRASES
- Se più tipologie matchano esattamente allo stesso offset (es. eco pre/post),
  sceglie UNA sola tipologia in base a TYPE_PRIORITY (la più prioritaria vince).
- Crea sezioni [start, end) ordinate e rimuove rumore (chunk troppo piccoli).
- Unisce consecutivi dello stesso tipo se separati da pochissimo testo.

Nota:
- La distinzione temporale ECO pre vs post è demandata a valle (resolver/cronologia).
  Qui rispettiamo TYPE_PRIORITY per scegliere un solo anchor quando le intestazioni coincidono.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Iterable, Tuple
import re

from config.type_phrases import TYPE_START_PHRASES, TYPE_PRIORITY

# --- Parametri euristici ---
_MIN_SECTION_CHARS = 30       # scarta spezzoni troppo corti
_MERGE_GAP_CHARS   = 20       # gap massimo per unire sezioni adiacenti stesso tipo


@dataclass
class Section:
    doc_type: str
    start: int
    end: int
    text: str


def _priority_index(doc_type: str) -> int:
    """Indice di priorità (più basso = più prioritario)."""
    try:
        return TYPE_PRIORITY.index(doc_type)
    except ValueError:
        # Se non è in lista, metti in coda
        return len(TYPE_PRIORITY) + 999


def _iter_raw_matches(text: str) -> Iterable[Tuple[str, int]]:
    """
    Genera tuple (doc_type, start_index) per OGNI match di OGNI pattern.
    """
    flags = re.IGNORECASE
    for doc_type, patterns in TYPE_START_PHRASES.items():
        for pat in patterns:
            for m in re.finditer(pat, text, flags=flags):
                yield (doc_type, m.start())


def _dedup_anchors_by_start(raw: Iterable[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """
    Quando più doc_type matchano allo stesso identico offset, sceglie il doc_type
    con priorità più alta (TYPE_PRIORITY). Restituisce una lista di ancore uniche.
    """
    by_start: Dict[int, List[str]] = {}
    for doc_type, pos in raw:
        by_start.setdefault(pos, []).append(doc_type)

    anchors: List[Tuple[str, int]] = []
    for pos, types in by_start.items():
        if len(types) == 1:
            anchors.append((types[0], pos))
        else:
            # scegli il tipo con priorità migliore
            winner = sorted(types, key=_priority_index)[0]
            anchors.append((winner, pos))

    # ordina per posizione di inizio
    anchors.sort(key=lambda t: t[1])
    return anchors


def _merge_small_or_duplicate(sections: List[Section]) -> List[Section]:
    """
    Unisce sezioni adiacenti dello stesso tipo se separate da gap minimo
    oppure se il testo è troppo piccolo per avere senso da solo.
    """
    if not sections:
        return sections

    merged: List[Section] = []
    cur = sections[0]
    for nxt in sections[1:]:
        same_type = (nxt.doc_type == cur.doc_type)
        small_next = (len(nxt.text) < _MIN_SECTION_CHARS)
        tiny_gap = (nxt.start - cur.end) <= _MERGE_GAP_CHARS

        if same_type and (tiny_gap or small_next):
            # Fondere
            cur = Section(
                doc_type=cur.doc_type,
                start=cur.start,
                end=nxt.end,
                text=(cur.text + "\n\n" + nxt.text).strip(),
            )
        else:
            # Chiudi cur e passa oltre
            if len(cur.text) >= _MIN_SECTION_CHARS:
                merged.append(cur)
            cur = nxt

    # chiudi l'ultimo
    if len(cur.text) >= _MIN_SECTION_CHARS:
        merged.append(cur)

    return merged


def find_document_sections(full_md_text: str) -> List[Section]:
    """
    Trova le sezioni del documento basandosi su frasi d'inizio predefinite.

    Ritorna:
        List[Section] ordinate per 'start'. Se nessun match, ritorna una singola sezione 'altro'.
    """
    # 1) trova tutti i match grezzi
    raw = list(_iter_raw_matches(full_md_text))

    # 2) deduplica per posizione, scegliendo il tipo con priorità migliore
    anchors = _dedup_anchors_by_start(raw)

    # 3) nessuna ancora? restituisci tutto come 'altro'
    if not anchors:
        return [Section("altro", 0, len(full_md_text), full_md_text)]

    # 4) costruisci sezioni [start, end)
    sections: List[Section] = []
    for idx, (doc_type, start) in enumerate(anchors):
        end = anchors[idx + 1][1] if (idx + 1) < len(anchors) else len(full_md_text)
        chunk = full_md_text[start:end].strip()
        if chunk:
            sections.append(Section(doc_type=doc_type, start=start, end=end, text=chunk))

    # 5) pulizia/merge
    sections = _merge_small_or_duplicate(sections)

    return sections
