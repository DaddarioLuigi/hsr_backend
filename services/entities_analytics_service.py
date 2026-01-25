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


def _is_numeric(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, bool):
        return False
    s = str(value).strip()
    if not s:
        return False
    try:
        float(s.replace(",", "."))
        return True
    except Exception:
        return False


def _to_numeric(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _load_all_entities(file_manager: FileManager) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    patients = file_manager.get_patients_summary() or []
    for p in patients:
        patient_id = (p or {}).get("id")
        if not patient_id:
            continue
        detail = file_manager.get_patient_detail(patient_id) or {}
        for doc in detail.get("documents") or []:
            doc_id = doc.get("id")
            if not doc_id:
                continue
            parsed = file_manager._parse_document_id(doc_id)
            if not parsed:
                continue
            folder = file_manager._build_document_folder(
                parsed["patient_id"],
                parsed["document_type"],
                hospitalization_id=parsed.get("hospitalization_id"),
            )
            entities_path = os.path.join(folder, "entities.json")
            if not os.path.exists(entities_path):
                continue
            try:
                with open(entities_path, encoding="utf-8") as f:
                    entities_data = json.load(f)
                if not isinstance(entities_data, dict):
                    continue
                out.append(
                    {
                        "document_id": doc_id,
                        "patient_id": parsed["patient_id"],
                        "document_type": parsed["document_type"],
                        "upload_date": doc.get("upload_date"),
                        "entities": entities_data,
                    }
                )
            except Exception:
                continue
    return out


def _filter_entities(
    *,
    items: list[dict[str, Any]],
    from_date: date | None,
    to_date: date | None,
    document_types: list[str] | None,
    patient_ids: list[str] | None,
    entity_filters: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    allowed_types = set(document_types or [])
    allowed_patients = set(patient_ids or [])
    entity_filters = entity_filters or {}

    for item in items:
        upload_date = item.get("upload_date")
        if upload_date:
            d = _parse_date(upload_date)
            if from_date and d and d < from_date:
                continue
            if to_date and d and d > to_date:
                continue

        doc_type = item.get("document_type")
        if allowed_types and doc_type not in allowed_types:
            continue

        patient_id = item.get("patient_id")
        if allowed_patients and patient_id not in allowed_patients:
            continue

        entities = item.get("entities") or {}
        matches = True
        for entity_name, filter_value in entity_filters.items():
            entity_value = entities.get(entity_name)
            if filter_value is None:
                if entity_value is not None:
                    matches = False
                    break
            elif isinstance(filter_value, dict):
                op = filter_value.get("op", "eq")
                val = filter_value.get("value")
                if op == "eq" and entity_value != val:
                    matches = False
                    break
                elif op == "ne" and entity_value == val:
                    matches = False
                    break
                elif op == "contains" and val not in str(entity_value or ""):
                    matches = False
                    break
                elif op == "gt" and _to_numeric(entity_value) <= _to_numeric(val):
                    matches = False
                    break
                elif op == "lt" and _to_numeric(entity_value) >= _to_numeric(val):
                    matches = False
                    break
            else:
                if str(entity_value or "").lower() != str(filter_value).lower():
                    matches = False
                    break

        if matches:
            out.append(item)

    return out


class EntitiesAnalyticsService:
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    def analyze_entities(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        document_types: list[str] | None = None,
        patient_ids: list[str] | None = None,
        entity_filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from_date = _parse_date(date_from)
        to_date = _parse_date(date_to)

        all_items = _load_all_entities(self.file_manager)
        filtered = _filter_entities(
            items=all_items,
            from_date=from_date,
            to_date=to_date,
            document_types=document_types,
            patient_ids=patient_ids,
            entity_filters=entity_filters,
        )

        entity_stats: dict[str, dict[str, Any]] = {}
        entity_values: dict[str, list[Any]] = defaultdict(list)

        for item in filtered:
            entities = item.get("entities") or {}
            for entity_name, entity_value in entities.items():
                if entity_name not in entity_stats:
                    entity_stats[entity_name] = {
                        "name": entity_name,
                        "total_count": 0,
                        "non_null_count": 0,
                        "null_count": 0,
                        "unique_values": set(),
                        "is_numeric": False,
                        "numeric_values": [],
                    }
                stat = entity_stats[entity_name]
                stat["total_count"] += 1
                if entity_value is not None and entity_value != "":
                    stat["non_null_count"] += 1
                    stat["unique_values"].add(str(entity_value))
                    entity_values[entity_name].append(entity_value)
                    if _is_numeric(entity_value):
                        stat["is_numeric"] = True
                        num_val = _to_numeric(entity_value)
                        if num_val is not None:
                            stat["numeric_values"].append(num_val)
                else:
                    stat["null_count"] += 1

        result_stats = []
        for name, stat in entity_stats.items():
            numeric_vals = stat["numeric_values"]
            result_stat: dict[str, Any] = {
                "name": name,
                "total_count": stat["total_count"],
                "non_null_count": stat["non_null_count"],
                "null_count": stat["null_count"],
                "unique_count": len(stat["unique_values"]),
                "is_numeric": stat["is_numeric"],
            }
            if stat["is_numeric"] and numeric_vals:
                result_stat["min"] = min(numeric_vals)
                result_stat["max"] = max(numeric_vals)
                result_stat["mean"] = sum(numeric_vals) / len(numeric_vals)
                result_stat["median"] = sorted(numeric_vals)[len(numeric_vals) // 2]
            else:
                top_values = defaultdict(int)
                for v in entity_values[name]:
                    if v is not None:
                        top_values[str(v)] += 1
                result_stat["top_values"] = sorted(
                    top_values.items(), key=lambda x: -x[1]
                )[:10]
            result_stats.append(result_stat)

        return {
            "total_documents": len(filtered),
            "entities": sorted(result_stats, key=lambda x: -x["total_count"]),
        }

    def get_correlations(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        document_types: list[str] | None = None,
        patient_ids: list[str] | None = None,
        entity_names: list[str] | None = None,
    ) -> dict[str, Any]:
        from_date = _parse_date(date_from)
        to_date = _parse_date(date_to)

        all_items = _load_all_entities(self.file_manager)
        filtered = _filter_entities(
            items=all_items,
            from_date=from_date,
            to_date=to_date,
            document_types=document_types,
            patient_ids=patient_ids,
            entity_filters=None,
        )

        if entity_names:
            target_entities = set(entity_names)
        else:
            target_entities = set()
            for item in filtered:
                target_entities.update((item.get("entities") or {}).keys())
            target_entities = sorted(target_entities)[:20]

        correlations: list[dict[str, Any]] = []
        pairs = []
        entity_list = sorted(target_entities)
        for i, e1 in enumerate(entity_list):
            for e2 in entity_list[i + 1 :]:
                pairs.append((e1, e2))

        for e1, e2 in pairs:
            co_occurrences = 0
            e1_only = 0
            e2_only = 0
            neither = 0
            e1_numeric = []
            e2_numeric = []

            for item in filtered:
                entities = item.get("entities") or {}
                has_e1 = e1 in entities and entities[e1] is not None
                has_e2 = e2 in entities and entities[e2] is not None

                if has_e1 and has_e2:
                    co_occurrences += 1
                    if _is_numeric(entities[e1]) and _is_numeric(entities[e2]):
                        n1 = _to_numeric(entities[e1])
                        n2 = _to_numeric(entities[e2])
                        if n1 is not None and n2 is not None:
                            e1_numeric.append(n1)
                            e2_numeric.append(n2)
                elif has_e1:
                    e1_only += 1
                elif has_e2:
                    e2_only += 1
                else:
                    neither += 1

            if co_occurrences > 0:
                corr_data: dict[str, Any] = {
                    "entity1": e1,
                    "entity2": e2,
                    "co_occurrences": co_occurrences,
                    "e1_only": e1_only,
                    "e2_only": e2_only,
                    "neither": neither,
                }
                if len(e1_numeric) == len(e2_numeric) and len(e1_numeric) >= 3:
                    mean1 = sum(e1_numeric) / len(e1_numeric)
                    mean2 = sum(e2_numeric) / len(e2_numeric)
                    numerator = sum(
                        (e1_numeric[i] - mean1) * (e2_numeric[i] - mean2)
                        for i in range(len(e1_numeric))
                    )
                    denom1 = sum((x - mean1) ** 2 for x in e1_numeric) ** 0.5
                    denom2 = sum((x - mean2) ** 2 for x in e2_numeric) ** 0.5
                    if denom1 > 0 and denom2 > 0:
                        corr_coef = numerator / (denom1 * denom2)
                        corr_data["correlation_coefficient"] = corr_coef
                correlations.append(corr_data)

        return {
            "total_documents": len(filtered),
            "correlations": sorted(
                correlations, key=lambda x: -x.get("co_occurrences", 0)
            ),
        }

    def search_entities(
        self,
        *,
        query: str,
        date_from: str | None = None,
        date_to: str | None = None,
        document_types: list[str] | None = None,
        patient_ids: list[str] | None = None,
        entity_names: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        from_date = _parse_date(date_from)
        to_date = _parse_date(date_to)

        all_items = _load_all_entities(self.file_manager)
        filtered = _filter_entities(
            items=all_items,
            from_date=from_date,
            to_date=to_date,
            document_types=document_types,
            patient_ids=patient_ids,
            entity_filters=None,
        )

        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        for item in filtered:
            entities = item.get("entities") or {}
            matches: list[dict[str, str]] = []

            for entity_name, entity_value in entities.items():
                if entity_names and entity_name not in entity_names:
                    continue
                if entity_value is None:
                    continue
                value_str = str(entity_value).lower()
                if query_lower in value_str or query_lower in entity_name.lower():
                    matches.append({"entity": entity_name, "value": str(entity_value)})

            if matches:
                results.append(
                    {
                        "document_id": item.get("document_id"),
                        "patient_id": item.get("patient_id"),
                        "document_type": item.get("document_type"),
                        "upload_date": item.get("upload_date"),
                        "matches": matches,
                    }
                )
                if len(results) >= limit:
                    break

        return {
            "query": query,
            "total_results": len(results),
            "results": results,
        }
