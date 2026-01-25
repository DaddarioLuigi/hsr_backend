import json
import os
import shutil
from datetime import datetime


UPLOADS_DIR = os.path.abspath(os.getenv("UPLOAD_FOLDER", "./uploads"))


def _read_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _find_ld_cartella(patient_dir: str, hosp_id: str) -> str | None:
    ld_entities = os.path.join(patient_dir, hosp_id, "lettera_dimissione", "entities.json")
    data = _read_json(ld_entities)
    if not data:
        return None
    n_cartella = data.get("n_cartella")
    if n_cartella is None:
        return None
    value = str(n_cartella).strip()
    return value if value.isdigit() else None


def normalize_patient(patient_id: str) -> dict:
    patient_dir = os.path.join(UPLOADS_DIR, patient_id)
    hosp_ids = sorted(
        d
        for d in os.listdir(patient_dir)
        if d.startswith("H_") and os.path.isdir(os.path.join(patient_dir, d))
    )
    if not hosp_ids:
        return {"patient_id": patient_id, "status": "skipped_no_hospitalizations"}

    ld_hosps = []
    for h in hosp_ids:
        cartella = _find_ld_cartella(patient_dir, h)
        if not cartella:
            continue
        ld_hosps.append({"hosp_id": h, "cartella": cartella})

    if not ld_hosps:
        return {"patient_id": patient_id, "status": "skipped_no_ld"}

    chosen = ld_hosps[0]
    target_hosp = f"H_{chosen['cartella']}"

    archived_root = os.path.join(patient_dir, "_archived_hospitalizations")
    _ensure_dir(archived_root)

    chosen_path = os.path.join(patient_dir, chosen["hosp_id"])
    target_path = os.path.join(patient_dir, target_hosp)
    if chosen["hosp_id"] != target_hosp and not os.path.exists(target_path):
        os.rename(chosen_path, target_path)

    if not os.path.isdir(target_path):
        return {"patient_id": patient_id, "status": "failed_no_target", "target": target_hosp}

    archived = 0
    for h in hosp_ids:
        if h == target_hosp:
            continue
        if h == chosen["hosp_id"] and chosen["hosp_id"] != target_hosp:
            continue

        src = os.path.join(patient_dir, h)
        if not os.path.isdir(src):
            continue

        dst_archive = os.path.join(archived_root, h)
        if os.path.exists(dst_archive):
            suffix = datetime.now().strftime("%Y%m%d%H%M%S")
            dst_archive = os.path.join(archived_root, f"{h}_{suffix}")
        os.rename(src, dst_archive)
        archived += 1

        for doc_type in os.listdir(dst_archive):
            doc_src = os.path.join(dst_archive, doc_type)
            if not os.path.isdir(doc_src):
                continue
            doc_dst = os.path.join(target_path, doc_type)
            if os.path.exists(doc_dst):
                continue
            shutil.move(doc_src, doc_dst)

    return {
        "patient_id": patient_id,
        "status": "ok",
        "target_hospitalization_id": target_hosp,
        "archived_hospitalizations": archived,
    }


def main() -> None:
    if not os.path.isdir(UPLOADS_DIR):
        raise SystemExit(f"uploads dir not found: {UPLOADS_DIR}")

    patients = sorted(
        d
        for d in os.listdir(UPLOADS_DIR)
        if d.startswith("P_") and os.path.isdir(os.path.join(UPLOADS_DIR, d))
    )
    print(f"Uploads dir: {UPLOADS_DIR}")
    print(f"Patients found: {len(patients)}")

    results = []
    for p in patients:
        result = normalize_patient(p)
        results.append(result)
        print(result)

    out = os.path.join(UPLOADS_DIR, "_normalize_hospitalizations_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Report written: {out}")


if __name__ == "__main__":
    main()

import json
import os
import shutil
from datetime import datetime


UPLOADS_DIR = os.path.abspath(os.getenv("UPLOAD_FOLDER", "./uploads"))


def _read_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _find_ld_cartella(patient_dir: str, hosp_id: str) -> str | None:
    ld_entities = os.path.join(patient_dir, hosp_id, "lettera_dimissione", "entities.json")
    data = _read_json(ld_entities)
    if not data:
        return None
    n_cartella = data.get("n_cartella")
    if n_cartella is None:
        return None
    value = str(n_cartella).strip()
    return value if value.isdigit() else None


def _find_ld_upload_date(patient_dir: str, hosp_id: str) -> str | None:
    ld_dir = os.path.join(patient_dir, hosp_id, "lettera_dimissione")
    if not os.path.isdir(ld_dir):
        return None

    for name in os.listdir(ld_dir):
        if not name.lower().endswith(".pdf"):
            continue
        meta = _read_json(os.path.join(ld_dir, name + ".meta.json")) or {}
        date_str = meta.get("upload_date")
        return str(date_str) if date_str else None

    return None


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def normalize_patient(patient_id: str) -> dict:
    patient_dir = os.path.join(UPLOADS_DIR, patient_id)
    hosp_ids = sorted(
        d
        for d in os.listdir(patient_dir)
        if d.startswith("H_") and os.path.isdir(os.path.join(patient_dir, d))
    )
    if not hosp_ids:
        return {"patient_id": patient_id, "status": "skipped_no_hospitalizations"}

    ld_hosps = []
    for h in hosp_ids:
        cartella = _find_ld_cartella(patient_dir, h)
        if not cartella:
            continue
        ld_hosps.append(
            {
                "hosp_id": h,
                "cartella": cartella,
                "upload_date": _parse_date(_find_ld_upload_date(patient_dir, h)),
            }
        )

    if not ld_hosps:
        return {"patient_id": patient_id, "status": "skipped_no_ld"}

    ld_hosps.sort(key=lambda x: x["upload_date"] or datetime.min, reverse=True)
    chosen = ld_hosps[0]
    target_hosp = f"H_{chosen['cartella']}"

    archived_root = os.path.join(patient_dir, "_archived_hospitalizations")
    _ensure_dir(archived_root)

    # Se la cartella target non esiste ma abbiamo una diversa hosp_id, rinominiamo
    chosen_path = os.path.join(patient_dir, chosen["hosp_id"])
    target_path = os.path.join(patient_dir, target_hosp)
    if chosen["hosp_id"] != target_hosp:
        if os.path.exists(target_path):
            # merge rinominando la chosen in archivio e poi spostando contenuti
            pass
        else:
            os.rename(chosen_path, target_path)

    # Ora target_path esiste
    if not os.path.isdir(target_path):
        return {"patient_id": patient_id, "status": "failed_no_target", "target": target_hosp}

    moved = 0
    archived = 0

    for h in hosp_ids:
        if h == target_hosp:
            continue
        if h == chosen["hosp_id"] and chosen["hosp_id"] != target_hosp:
            # era rinominato al target
            continue

        src = os.path.join(patient_dir, h)
        if not os.path.isdir(src):
            continue

        # Prima archiviamo l'intero ricovero sotto _archived_hospitalizations
        dst_archive = os.path.join(archived_root, h)
        if os.path.exists(dst_archive):
            suffix = datetime.now().strftime("%Y%m%d%H%M%S")
            dst_archive = os.path.join(archived_root, f"{h}_{suffix}")
        os.rename(src, dst_archive)
        archived += 1

        # Poi proviamo a fondere i documenti nel target (solo se non confliggono)
        for doc_type in os.listdir(dst_archive):
            doc_src = os.path.join(dst_archive, doc_type)
            if not os.path.isdir(doc_src):
                continue
            doc_dst = os.path.join(target_path, doc_type)
            if os.path.exists(doc_dst):
                # conflitto: lasciamo in archivio
                continue
            shutil.move(doc_src, doc_dst)
            moved += 1

    return {
        "patient_id": patient_id,
        "status": "ok",
        "target_hospitalization_id": target_hosp,
        "archived_hospitalizations": archived,
        "moved_document_types": moved,
    }


def main() -> None:
    if not os.path.isdir(UPLOADS_DIR):
        raise SystemExit(f"uploads dir not found: {UPLOADS_DIR}")

    patients = sorted(
        d
        for d in os.listdir(UPLOADS_DIR)
        if d.startswith("P_") and os.path.isdir(os.path.join(UPLOADS_DIR, d))
    )
    print(f"Uploads dir: {UPLOADS_DIR}")
    print(f"Patients found: {len(patients)}")

    results = []
    for p in patients:
        result = normalize_patient(p)
        results.append(result)
        print(result)

    out = os.path.join(UPLOADS_DIR, "_normalize_hospitalizations_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Report written: {out}")


if __name__ == "__main__":
    main()

