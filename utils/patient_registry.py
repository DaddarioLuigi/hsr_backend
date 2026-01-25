import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from utils.identifiers import generate_clinical_record_number, generate_patient_id


@dataclass(frozen=True)
class PatientContext:
    patient_id: str
    hospitalization_id: str
    clinical_record_number: str | None = None


class PatientRegistry:
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        self.patient_index_path = os.path.join(upload_folder, "patient_index.json")

    def _load_patient_index(self) -> dict[str, str]:
        if not os.path.exists(self.patient_index_path):
            return {}
        try:
            with open(self.patient_index_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_patient_index(self, index: dict[str, str]) -> None:
        os.makedirs(self.upload_folder, exist_ok=True)
        tmp_path = self.patient_index_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(tmp_path, self.patient_index_path)

    def list_existing_patient_ids(self) -> set[str]:
        if not os.path.exists(self.upload_folder):
            return set()
        return {
            d
            for d in os.listdir(self.upload_folder)
            if os.path.isdir(os.path.join(self.upload_folder, d))
        }

    def list_existing_clinical_record_numbers(self) -> set[str]:
        existing: set[str] = set()
        if not os.path.exists(self.upload_folder):
            return existing

        for entry in os.listdir(self.upload_folder):
            if entry.isdigit():
                existing.add(entry)

            if not entry.startswith("P_"):
                continue

            patient_path = os.path.join(self.upload_folder, entry)
            if not os.path.isdir(patient_path):
                continue

            for hosp in os.listdir(patient_path):
                if not hosp.startswith("H_"):
                    continue
                clinical = hosp[2:]
                if clinical.isdigit():
                    existing.add(clinical)

        return existing

    def find_patient_by_hospitalization_id(self, hospitalization_id: str) -> str | None:
        if not hospitalization_id:
            return None
        if not os.path.exists(self.upload_folder):
            return None

        for entry in os.listdir(self.upload_folder):
            if not entry.startswith("P_"):
                continue
            hosp_path = os.path.join(self.upload_folder, entry, hospitalization_id)
            if os.path.isdir(hosp_path):
                return entry
        return None

    def find_patient_by_display_name(self, normalized_display_name: str) -> str | None:
        if not normalized_display_name:
            return None
        index = self._load_patient_index()
        for pid, name in index.items():
            if (name or "").strip().lower().replace(" ", "") == normalized_display_name:
                return pid
        return None

    def create_patient(self, display_name: str | None = None) -> str:
        existing = self.list_existing_patient_ids()
        patient_id = generate_patient_id(existing_patient_ids=existing)

        patient_path = os.path.join(self.upload_folder, patient_id)
        os.makedirs(patient_path, exist_ok=True)

        patient_json_path = os.path.join(patient_path, "patient.json")
        if not os.path.exists(patient_json_path):
            payload = {
                "patient_id": patient_id,
                "display_name": display_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(patient_json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

        if display_name:
            index = self._load_patient_index()
            index[patient_id] = display_name
            self._save_patient_index(index)

        return patient_id

    def ensure_hospitalization(
        self,
        patient_id: str,
        clinical_record_number: str | None = None,
    ) -> PatientContext:
        existing_numbers = self.list_existing_clinical_record_numbers()
        clinical_record_number = clinical_record_number or generate_clinical_record_number(
            existing_numbers=existing_numbers
        )
        hospitalization_id = f"H_{clinical_record_number}"

        hosp_path = os.path.join(self.upload_folder, patient_id, hospitalization_id)
        os.makedirs(hosp_path, exist_ok=True)

        return PatientContext(
            patient_id=patient_id,
            hospitalization_id=hospitalization_id,
            clinical_record_number=clinical_record_number,
        )

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from utils.identifiers import (
    generate_clinical_record_number,
    generate_patient_id,
)


@dataclass(frozen=True)
class PatientContext:
    patient_id: str
    hospitalization_id: str
    clinical_record_number: str | None = None


class PatientRegistry:
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        self.patient_index_path = os.path.join(upload_folder, "patient_index.json")

    def _load_patient_index(self) -> dict[str, str]:
        if not os.path.exists(self.patient_index_path):
            return {}
        try:
            with open(self.patient_index_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_patient_index(self, index: dict[str, str]) -> None:
        os.makedirs(self.upload_folder, exist_ok=True)
        tmp_path = self.patient_index_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(tmp_path, self.patient_index_path)

    def list_existing_patient_ids(self) -> set[str]:
        if not os.path.exists(self.upload_folder):
            return set()
        return {
            d
            for d in os.listdir(self.upload_folder)
            if os.path.isdir(os.path.join(self.upload_folder, d))
        }

    def list_existing_clinical_record_numbers(self) -> set[str]:
        existing = set()
        if not os.path.exists(self.upload_folder):
            return existing

        for entry in os.listdir(self.upload_folder):
            # Legacy: cartella clinica usata come patient folder
            if entry.isdigit():
                existing.add(entry)

            if not entry.startswith("P_"):
                continue

            patient_path = os.path.join(self.upload_folder, entry)
            if not os.path.isdir(patient_path):
                continue

            for hosp in os.listdir(patient_path):
                if not hosp.startswith("H_"):
                    continue
                clinical = hosp.removeprefix("H_")
                if clinical.isdigit():
                    existing.add(clinical)

        return existing

    def find_patient_by_hospitalization_id(self, hospitalization_id: str) -> str | None:
        if not hospitalization_id:
            return None

        if not os.path.exists(self.upload_folder):
            return None

        for entry in os.listdir(self.upload_folder):
            if not entry.startswith("P_"):
                continue
            hosp_path = os.path.join(self.upload_folder, entry, hospitalization_id)
            if os.path.isdir(hosp_path):
                return entry

        return None

    def create_patient(self, display_name: str | None = None) -> str:
        existing = self.list_existing_patient_ids()
        patient_id = generate_patient_id(existing_patient_ids=existing)

        patient_path = os.path.join(self.upload_folder, patient_id)
        os.makedirs(patient_path, exist_ok=True)

        patient_json_path = os.path.join(patient_path, "patient.json")
        if not os.path.exists(patient_json_path):
            payload = {
                "patient_id": patient_id,
                "display_name": display_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(patient_json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

        if display_name:
            index = self._load_patient_index()
            index[patient_id] = display_name
            self._save_patient_index(index)

        return patient_id

    def ensure_hospitalization(
        self,
        patient_id: str,
        clinical_record_number: str | None = None,
    ) -> PatientContext:
        existing_numbers = self.list_existing_clinical_record_numbers()
        clinical_record_number = clinical_record_number or generate_clinical_record_number(
            existing_numbers=existing_numbers
        )
        hospitalization_id = f"H_{clinical_record_number}"

        hosp_path = os.path.join(self.upload_folder, patient_id, hospitalization_id)
        os.makedirs(hosp_path, exist_ok=True)

        return PatientContext(
            patient_id=patient_id,
            hospitalization_id=hospitalization_id,
            clinical_record_number=clinical_record_number,
        )

