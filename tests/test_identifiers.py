import re
import unittest

from utils.identifiers import generate_clinical_record_number, generate_patient_id


class TestIdentifiers(unittest.TestCase):
    def test_generate_patient_id(self):
        pid = generate_patient_id()
        self.assertTrue(pid.startswith("P_"))
        self.assertEqual(len(pid), 14)
        self.assertTrue(re.fullmatch(r"P_[A-F0-9]{12}", pid))

    def test_generate_clinical_record_number(self):
        n = generate_clinical_record_number()
        self.assertTrue(n.isdigit())
        self.assertGreaterEqual(len(n), 10)

import unittest
from datetime import datetime

from utils.identifiers import (
    extract_clinical_record_number,
    generate_clinical_record_number,
)


class TestIdentifiers(unittest.TestCase):
    def test_extract_clinical_record_number(self):
        text = "Telefono 3343916166 - Numero Cartella 2020029382 ricoverato presso..."
        self.assertEqual(extract_clinical_record_number(text), "2020029382")

    def test_generate_clinical_record_number_format_and_uniqueness(self):
        now = datetime(2026, 1, 24, 10, 0, 0)
        existing = {"2026000001", "2026999999"}
        value = generate_clinical_record_number(existing_numbers=existing, now=now)
        self.assertTrue(value.startswith("2026"))
        self.assertEqual(len(value), 10)
        self.assertNotIn(value, existing)


if __name__ == "__main__":
    unittest.main()

