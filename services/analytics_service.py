from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from utils.file_manager import FileManager


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


class AnalyticsService:
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    def query(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        group_by: str = "day",
        metrics: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from_date = _parse_date(date_from)
        to_date = _parse_date(date_to)
        metrics = metrics or ["documents"]
        filters = filters or {}

        document_types_filter = filters.get("document_types")
        patient_ids_filter = filters.get("patient_ids")

        patients = self.file_manager.get_patients_summary() or []
        all_docs: list[dict[str, Any]] = []

        for p in patients:
            patient_id = (p or {}).get("id")
            if not patient_id:
                continue
            if patient_ids_filter and patient_id not in patient_ids_filter:
                continue

            detail = self.file_manager.get_patient_detail(patient_id) or {}
            for doc in detail.get("documents") or []:
                doc_type = doc.get("type")
                if document_types_filter and doc_type not in document_types_filter:
                    continue

                upload_date = doc.get("upload_date")
                if upload_date:
                    d = _parse_date(upload_date)
                    if from_date and d and d < from_date:
                        continue
                    if to_date and d and d > to_date:
                        continue

                status = doc.get("status", "unknown")
                all_docs.append(
                    {
                        "patient_id": patient_id,
                        "document_type": doc_type,
                        "upload_date": upload_date,
                        "status": status,
                    }
                )

        grouped: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))

        for doc in all_docs:
            if group_by == "day":
                key = doc.get("upload_date") or "unknown"
            elif group_by == "document_type":
                key = doc.get("document_type") or "unknown"
            elif group_by == "status":
                key = doc.get("status") or "unknown"
            elif group_by == "patient":
                key = doc.get("patient_id") or "unknown"
            else:
                key = "unknown"

            grouped[key]["documents"] += 1

            if doc.get("status") == "processed":
                grouped[key]["processed"] += 1
            elif doc.get("status") == "processing":
                grouped[key]["processing"] += 1
            elif doc.get("status") == "error":
                grouped[key]["errors"] += 1

        rows = []
        for key in sorted(grouped.keys()):
            row: dict[str, Any] = {"key": key}
            for metric in metrics:
                row[metric] = grouped[key].get(metric, 0)
            rows.append(row)

        totals: dict[str, Any] = {}
        for metric in metrics:
            totals[metric] = sum(r.get(metric, 0) for r in rows)

        return {
            "group_by": group_by,
            "metrics": metrics,
            "filters": filters,
            "date_from": date_from,
            "date_to": date_to,
            "rows": rows,
            "totals": totals,
        }
