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

    def ingest_pdf_packet(self, pdf_path: str, patient_id: str) -> Dict[str, Any]:
        """
        Esegue l'intero flusso su un PDF di cartella clinica completa.

        Returns:
            dict serializzabile con:
                - patient_id
                - sections_found: lista tipi riconosciuti in ordine di apparizione
                - documents_processed: tipi per cui è stato salvato entities.json
                - global_map: mappa chiave->valore consolidata
        """
        # 1) OCR -> markdown
        ocr_resp = self.ocr.process_pdf(pdf_path)
        full_md = ocr_response_to_markdown(ocr_resp)

        # 2) Segmentazione
        sections: List[Section] = find_document_sections(full_md)
        sections_found = [s.doc_type for s in sections]

        # 3) Estrazione
        per_doc_entities: Dict[str, Dict[str, Any]] = {}

        for sec in sections:
            raw_type = sec.doc_type
            canonical_type = normalize_doc_type(raw_type)

            # Skip se il tipo non è previsto dal nostro set (salvo 'altro')
            if canonical_type not in SUPPORTED_TYPES:
                print(f"[INFO] Tipo non supportato: {canonical_type}. Skippato.")
                continue

            # Se è 'altro', non abbiamo prompt/schema -> salviamo solo artefatti e saltiamo estrazione
            if canonical_type == "altro":
                self._save_raw_artifacts(patient_id, canonical_type, pdf_path, markdown_text=sec.text)
                continue

            # Chiamata LLM tramite router
            try:
                entities = self.extractor.extract(sec.text, canonical_type)
            except Exception as e:
                print(f"[WARN] Estrazione fallita per {canonical_type}: {e}")
                # salviamo almeno la sezione raw per audit
                self._save_raw_artifacts(patient_id, canonical_type, pdf_path, markdown_text=sec.text)
                continue

            # merge con eventuale sezione precedente dello stesso tipo (riempie solo vuoti)
            existing = per_doc_entities.get(canonical_type, {})
            per_doc_entities[canonical_type] = self._merge_entities_fill_empty(existing, entities)

            # salva artefatti raw (opzionale, utile per QA)
            self._save_raw_artifacts(patient_id, canonical_type, pdf_path, markdown_text=sec.text)

        # 4) Cross-doc: build mappa globale & backfill
        global_map = build_global_map(per_doc_entities)
        backfilled: Dict[str, Dict[str, Any]] = {}
        for doc_type, ents in per_doc_entities.items():
            backfilled[doc_type] = backfill_entities_for_doc(doc_type, ents, global_map)

        # 5) Persistenza per ogni doc_type
        documents_processed: List[str] = []
        for doc_type, ents in backfilled.items():
            try:
                self._persist_entities(patient_id, doc_type, ents)
                documents_processed.append(doc_type)
            except Exception as e:
                print(f"[WARN] Persistenza fallita per {doc_type}: {e}")

        # 6) Riepilogo
        summary = IngestionSummary(
            patient_id=patient_id,
            sections_found=sections_found,
            documents_processed=documents_processed,
            global_map=global_map,
        )

        # Restituiamo un dict plain (più comodo da serializzare)
        return {
            "patient_id": summary.patient_id,
            "sections_found": summary.sections_found,
            "documents_processed": summary.documents_processed,
            "global_map": summary.global_map,
        }
