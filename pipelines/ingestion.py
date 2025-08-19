# pipelines/ingestion.py
# -*- coding: utf-8 -*-
"""
Pipeline di ingestione del 'pacchetto clinico' (PDF unico):
1) OCR (Mistral) -> markdown completo
2) Segmentazione in sezioni per tipologia documento
3) Estrazione entità per sezione (PromptManager + LLMExtractor + EntityExtractor)
4) Cross-document resolver: build mappa globale e backfill
5) Persistenza (entities.json per tipo + aggiornamento Excel)

Dipendenze interne:
- ocr.mistral_ocr.MistralOCR, ocr_response_to_markdown
- utils.document_segmenter.find_document_sections
- pipelines.router.SectionExtractor, normalize_doc_type
- utils.cross_doc_resolver.build_global_map, backfill_entities_for_doc
- FileManager, ExcelManager (propri del progetto)

Nota:
- Sono gestiti alias di tipo (es. 'verbale_operatorio' -> 'intervento') nel router.
- Se una sezione ha un tipo non supportato dal PromptManager, viene saltata con warning.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
import shutil
import re
from utils.progress import ProgressStore

# --- OCR ---
try:
    # --- OCR ---
    from ocr.mistral_ocr import MistralOCR, ocr_response_to_markdown
except ImportError as e:
    raise ImportError(
        "Impossibile importare 'MistralOCR' da ocr.mistral_ocr. "
        "Assicurati di aver aggiunto il file 'ocr/mistral_ocr.py' come da istruzioni."
    ) from e

# --- Segmentazione ---
from utils.document_segmenter import find_document_sections, Section

# --- Router LLM + alias normalize ---
from pipelines.router import SectionExtractor, normalize_doc_type

# --- Cross-document resolver ---
from utils.cross_doc_resolver import build_global_map, backfill_entities_for_doc

# --- Persistenza (gestione file/Excel) ---
try:
    from utils.file_manager import FileManager
except ImportError:
    from file_manager import FileManager  # fallback al root

try:
    from utils.excel_manager import ExcelManager
except ImportError:
    from excel_manager import ExcelManager  # fallback al root


# Tipologie riconosciute/persistite
SUPPORTED_TYPES = {
    "lettera_dimissione",
    "anamnesi",
    "epicrisi_ti",
    "cartellino_anestesiologico",
    "intervento",         # canonical (alias: verbale/referto operatorio)
    "coronarografia",
    "eco_preoperatorio",
    "eco_postoperatorio",
    "tc_cuore",
    "altro",
}


@dataclass
class IngestionSummary:
    patient_id: str
    sections_found: List[str]
    documents_processed: List[str]
    global_map: Dict[str, Any]


class ClinicalPacketIngestion:
    """
    Orchestratore end-to-end del flusso PDF unico -> estrazioni per tipologia.
    """

    def __init__(
        self,
        model_name: str = "deepseek-ai/DeepSeek-V3",
        ocr_api_key: Optional[str] = None,
        upload_folder: Optional[str] = None,
    ):
        self.ocr = MistralOCR(api_key=ocr_api_key)  # usa env MISTRAL_API_KEY se None
        self.extractor = SectionExtractor(model_name=model_name)

        # Manager di progetto
        self.fm = FileManager()
        self.progress = ProgressStore(self.fm.UPLOAD_FOLDER)
        self.excel = ExcelManager()
        # opzionale: override cartella upload (se supportato dal tuo FileManager)
        if upload_folder:
            # se FileManager espone UPLOAD_FOLDER, lo aggiorniamo
            if hasattr(self.fm, "UPLOAD_FOLDER"):
                self.fm.UPLOAD_FOLDER = upload_folder

    # ----------------------------------------
    # Utility
    # ----------------------------------------

    def _merge_entities_fill_empty(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge 'new' dentro 'base' riempiendo solo i campi vuoti/assenti.
        Non sovrascrive valori già presenti e non-vuoti.
        """
        merged = dict(base or {})
        for k, v in (new or {}).items():
            if (k not in merged) or (merged[k] in (None, "", [], {})):
                merged[k] = v
        return merged

    def _save_raw_artifacts(self, patient_id: str, doc_type: str, pdf_path: str, markdown_text: Optional[str] = None) -> None:
        """
        Salva opzionalmente:
        - una copia del PDF originale sotto UPLOAD_FOLDER/patient_id/doc_type/
        - un file .md con il testo OCR della sezione (se fornito)
        """
        # Se FileManager non gestisce upload folder, esci silenziosamente
        upload_folder = getattr(self.fm, "UPLOAD_FOLDER", None)
        if not upload_folder:
            return

        # crea cartelle
        base_dir = os.path.join(upload_folder, str(patient_id), str(doc_type))
        os.makedirs(base_dir, exist_ok=True)

        # copia pdf (se non già presente con stesso nome)
        try:
            basename = os.path.basename(pdf_path)
            dst_pdf = os.path.join(base_dir, basename)
            if os.path.abspath(pdf_path) != os.path.abspath(dst_pdf):
                with open(pdf_path, "rb") as src, open(dst_pdf, "wb") as dst:
                    dst.write(src.read())

            # salva metadata minimi
            meta_path = os.path.join(base_dir, basename + ".meta.json")
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(
                    {"filename": basename},
                    mf,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception:
            # non bloccare la pipeline se fallisce la copia
            pass

        # salva markdown della sezione (se c'è)
        if markdown_text:
            try:
                md_path = os.path.join(base_dir, "ocr_section.md")
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(markdown_text)
            except Exception:
                pass

    def _persist_entities(self, patient_id: str, doc_type: str, entities: Dict[str, Any]) -> None:
        """
        Persistenza entità per documento:
        - JSON per tipo (via FileManager)
        - aggiornamento Excel (via ExcelManager)
        """
        try:
            # Salvataggio JSON (l'implementazione del tuo FileManager gestisce path/folder)
            self.fm.save_entities_json(patient_id, doc_type, entities)
        except Exception as e:
            # Non fermare la pipeline: log minimo su console
            print(f"[WARN] save_entities_json fallita per {doc_type}: {e}")

        try:
            # Aggiornamento Excel
            self.excel.update_excel(patient_id, doc_type, entities)
        except Exception as e:
            print(f"[WARN] update_excel fallita per {doc_type}: {e}")

    # ----------------------------------------
    # Entry point principale
    # ----------------------------------------


    def ingest_pdf_packet(self, pdf_path: Optional[str], patient_id: Optional[str] = None) -> Dict[str, Any]:
        """
        OCR (Mistral) → sanitizzazione → segmentazione → estrazione per tipologia →
        consolidamento cross-doc → backfill → persistenza (JSON + Excel) con progressi.
        Ritorna: dict con patient_id finale, sezioni trovate, tipi processati, global_map.
        """
        # --- helpers -------------------------------------------------------------
        def _sanitize_for_llm(txt: str) -> str:
            s = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', txt or '')  # immagini markdown
            s = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+', '', s)  # data-uri
            s = re.sub(r'[ \t]+', ' ', s)
            s = re.sub(r'\n{3,}', '\n\n', s)
            return s.strip()

        def _norm_id(s: Optional[str]) -> str:
            return str(s).strip().replace(" ", "") if s is not None else ""

        PER_SECTION_MAX_CHARS = 30000   # limite difensivo per input LLM
        MAX_DOC_CHARS_FALLBACK = 30000  # limite fallback

        # --- inizio --------------------------------------------------------------
        working_id = _norm_id(patient_id) or f"_pending_{uuid4().hex}"

        try:
            # 0) Upload OK
            try:
                self.progress.update(working_id, "upload_ok", 5, "File ricevuto")
            except Exception:
                pass

            # 1) OCR
            try:
                self.progress.update(working_id, "ocr_start", 10, "OCR in esecuzione")
            except Exception:
                pass
            ocr_resp = self.ocr.process_pdf(pdf_path)
            full_md = ocr_response_to_markdown(ocr_resp)
            full_md = _sanitize_for_llm(full_md)
            try:
                self.progress.update(working_id, "ocr_done", 30, "OCR completato")
            except Exception:
                pass

            if not full_md:
                try:
                    self.progress.update(working_id, "failed", 100, "OCR ha restituito testo vuoto")
                except Exception:
                    pass
                return {
                    "patient_id": working_id,
                    "sections_found": [],
                    "documents_processed": [],
                    "global_map": {},
                }

            # 2) Segmentazione
            try:
                self.progress.update(working_id, "segmenting", 35, "Segmentazione in corso")
            except Exception:
                pass

            sections: List[Section] = find_document_sections(full_md)
            normalized_sections: List[Tuple[str, str]] = []
            for s in (sections or []):
                doc_type = normalize_doc_type(getattr(s, "doc_type", "") or "altro")
                text = getattr(s, "text", "") or ""
                normalized_sections.append((doc_type, text))

            try:
                self.progress.update(working_id, "segmented", 40, f"Sezioni trovate: {len(normalized_sections)}")
            except Exception:
                pass

            extractable: List[Tuple[str, str]] = [
                (t, txt) for (t, txt) in normalized_sections
                if t in SUPPORTED_TYPES and t != "altro" and (txt or "").strip()
            ]

            # 3) Estrazione per sezioni
            per_doc_entities: Dict[str, Dict[str, Any]] = {}
            if extractable:
                total = len(extractable)
                for idx, (canonical_type, sec_text) in enumerate(extractable, start=1):
                    try:
                        self.progress.update(
                            working_id, "extracting",
                            40 + int(45 * idx / max(1, total)),
                            f"Estrazione {idx}/{total}: {canonical_type}"
                        )
                    except Exception:
                        pass

                    # salva raw + limita input per LLM
                    self._save_raw_artifacts(working_id, canonical_type, pdf_path, markdown_text=sec_text)
                    sec_text_slice = (sec_text or "")[:PER_SECTION_MAX_CHARS]

                    # verifica che esista lo schema/prompt
                    try:
                        _ = self.prompts.get_spec_for(canonical_type)
                    except Exception:
                        print(f"[INFO] Tipo senza schema/prompt: {canonical_type} → skip")
                        continue

                    try:
                        ents = self.extractor.extract(sec_text_slice, canonical_type) or {}
                    except Exception as e:
                        print(f"[WARN] estrazione fallita per {canonical_type}: {e}")
                        continue

                    current = per_doc_entities.get(canonical_type, {})
                    per_doc_entities[canonical_type] = self._merge_entities_fill_empty(current, ents)

            # 3b) FALLBACK se nulla estratto
            if not per_doc_entities:
                try:
                    self.progress.update(working_id, "no_sections", 45, "Nessuna sezione riconosciuta, avvio fallback")
                except Exception:
                    pass

                available = set(getattr(self.prompts, "SCHEMAS", {}).keys())
                priority_order = [
                    "lettera_dimissione",
                    "intervento",
                    "cartellino_anestesiologico",
                    "epicrisi_ti",
                    "eco_preoperatorio",
                    "eco_postoperatorio",
                    "tc_cuore",
                    "coronarografia",
                    "anamnesi",
                ]
                candidate_types = [t for t in priority_order if t in available]
                candidate_types += [t for t in available if t not in candidate_types]

                doc_slice = full_md[:MAX_DOC_CHARS_FALLBACK]
                total_fb = len(candidate_types) or 1

                for idx, t in enumerate(candidate_types, start=1):
                    try:
                        self.progress.update(
                            working_id, "fallback_extract",
                            45 + int(40 * idx / total_fb),
                            f"Fallback {idx}/{total_fb}: {t}"
                        )
                    except Exception:
                        pass

                    try:
                        _ = self.prompts.get_spec_for(t)
                    except Exception:
                        continue

                    try:
                        ents = self.extractor.extract(doc_slice, t) or {}
                        if ents:
                            current = per_doc_entities.get(t, {})
                            per_doc_entities[t] = self._merge_entities_fill_empty(current, ents)
                    except Exception as e:
                        print(f"[WARN] fallback estrazione fallita per {t}: {e}")
                        continue

            # 4) Cross-doc
            try:
                self.progress.update(working_id, "consolidating", 90, "Consolidamento dati")
            except Exception:
                pass

            global_map = build_global_map(per_doc_entities)

            # 5) ID finale e move cartella se necessario
            final_id = _norm_id(global_map.get("n_cartella")) or _norm_id(patient_id) or working_id
            if final_id != working_id:
                try:
                    if hasattr(self.fm, "move_patient_folder"):
                        self.fm.move_patient_folder(working_id, final_id)
                except Exception as e:
                    print(f"[WARN] Move patient folder {working_id} -> {final_id} fallito: {e}")

            # 6) Backfill + persistenza
            documents_processed: List[str] = []
            for doc_type, ents in per_doc_entities.items():
                bf = backfill_entities_for_doc(doc_type, ents, global_map)
                self._persist_entities(final_id, doc_type, bf)
                documents_processed.append(doc_type)

            # 7) Completed
            try:
                self.progress.update(
                    final_id, "completed", 100, "Elaborazione completata",
                    extra={
                        "final_patient_id": final_id,
                        "sections_found": [t for (t, _) in normalized_sections],
                        "documents_processed": documents_processed,
                    }
                )
            except Exception:
                pass

            return {
                "patient_id": final_id,
                "sections_found": [t for (t, _) in normalized_sections],
                "documents_processed": documents_processed,
                "global_map": global_map,
            }

        except Exception as e:
            try:
                self.progress.update(working_id, "failed", 100, f"Errore: {e!s}")
            except Exception:
                pass
            raise
