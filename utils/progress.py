# utils/progress.py
# -*- coding: utf-8 -*-
import os, json, time
from typing import Any, Dict, Optional

class ProgressStore:
    """
    Salva/legge lo stato in:
    <UPLOAD_FOLDER>/<pending_id>/packet_ocr/status.json
    """
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder

    def _folder(self, pending_id: str) -> str:
        return os.path.join(self.upload_folder, str(pending_id), "packet_ocr")

    def _path(self, pending_id: str) -> str:
        os.makedirs(self._folder(pending_id), exist_ok=True)
        return os.path.join(self._folder(pending_id), "status.json")

    def update(self, pending_id: str, stage: str, percent: int,
               message: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        data: Dict[str, Any] = {
            "pending_id": pending_id,
            "stage": stage,         # es. upload_ok, ocr_start, extracting, completed, failed
            "percent": max(0, min(100, int(percent))),
            "message": message or "",
            "timestamp": now,
        }
        if extra:
            data.update(extra)
        with open(self._path(pending_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return data

    def read(self, pending_id: str) -> Dict[str, Any]:
        p = self._path(pending_id)
        if not os.path.exists(p):
            return { "pending_id": pending_id, "stage": "unknown", "percent": 0, "message": "" }
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
