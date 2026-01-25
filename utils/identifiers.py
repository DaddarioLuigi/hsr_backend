import re
import secrets
from datetime import datetime


_CARTELLA_REGEX = re.compile(
    r"(?:numero\s+cartella|n\.?\s*cartella)\s*[:\-]?\s*(\d{7,12})",
    re.IGNORECASE,
)


def extract_clinical_record_number(text: str | None) -> str | None:
    if not text:
        return None

    match = _CARTELLA_REGEX.search(text)
    if not match:
        return None

    return match.group(1)


def generate_patient_id(existing_patient_ids: set[str] | None = None) -> str:
    existing_patient_ids = existing_patient_ids or set()

    for _ in range(100):
        patient_id = f"P_{secrets.token_hex(6).upper()}"
        if patient_id not in existing_patient_ids:
            return patient_id

    raise RuntimeError("Impossibile generare un patient_id univoco")


def generate_clinical_record_number(
    existing_numbers: set[str] | None = None,
    now: datetime | None = None,
) -> str:
    """
    Formato dedotto da esempi reali:
    - Numero cartella a 10 cifre: YYYY + 6 cifre (con zeri a sinistra)
    """
    existing_numbers = existing_numbers or set()
    now = now or datetime.now()

    year_prefix = f"{now.year}"
    for _ in range(1000):
        suffix = secrets.randbelow(1_000_000)
        value = f"{year_prefix}{suffix:06d}"
        if value not in existing_numbers:
            return value

    raise RuntimeError("Impossibile generare un n_cartella univoco")

import re
import secrets
from datetime import datetime


_CARTELLA_REGEX = re.compile(
    r"(?:numero\s+cartella|n\.?\s*cartella)\s*[:\-]?\s*(\d{7,12})",
    re.IGNORECASE,
)


def extract_clinical_record_number(text: str | None) -> str | None:
    if not text:
        return None

    match = _CARTELLA_REGEX.search(text)
    if not match:
        return None

    return match.group(1)


def generate_patient_id(existing_patient_ids: set[str] | None = None) -> str:
    existing_patient_ids = existing_patient_ids or set()

    # Formato osservato in uploads/: P_ + 12 hex maiuscoli
    for _ in range(100):
        patient_id = f"P_{secrets.token_hex(6).upper()}"
        if patient_id not in existing_patient_ids:
            return patient_id

    raise RuntimeError("Impossibile generare un patient_id univoco")


def generate_clinical_record_number(
    existing_numbers: set[str] | None = None,
    now: datetime | None = None,
) -> str:
    """
    Formato dedotto da esempi reali in `esempi/`:
    - Numero Cartella a 10 cifre: YYYY + 6 cifre (con zeri a sinistra)
    """
    existing_numbers = existing_numbers or set()
    now = now or datetime.now()

    year_prefix = f"{now.year}"
    for _ in range(1000):
        suffix = secrets.randbelow(1_000_000)
        value = f"{year_prefix}{suffix:06d}"
        if value not in existing_numbers:
            return value

    raise RuntimeError("Impossibile generare un n_cartella univoco")

