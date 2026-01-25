import unittest

from utils.patient_registry import PatientRegistry


class TestPatientRegistry(unittest.TestCase):
    def test_create_patient_and_hospitalization(self):
        registry = PatientRegistry(upload_folder="/tmp/hsr_backend_test_uploads")
        patient_id = registry.create_patient(display_name="Mario Rossi")
        ctx = registry.ensure_hospitalization(patient_id)
        self.assertTrue(patient_id.startswith("P_"))
        self.assertTrue(ctx.hospitalization_id.startswith("H_"))

import os
import tempfile
import unittest

from utils.patient_registry import PatientRegistry


class TestPatientRegistry(unittest.TestCase):
    def test_create_patient_and_hospitalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = PatientRegistry(tmp)
            patient_id = registry.create_patient(display_name="Mario Rossi")
            self.assertTrue(patient_id.startswith("P_"))

            ctx = registry.ensure_hospitalization(patient_id, clinical_record_number="2026000001")
            self.assertEqual(ctx.patient_id, patient_id)
            self.assertEqual(ctx.hospitalization_id, "H_2026000001")

            self.assertTrue(os.path.isdir(os.path.join(tmp, patient_id)))
            self.assertTrue(os.path.isdir(os.path.join(tmp, patient_id, "H_2026000001")))

            found = registry.find_patient_by_hospitalization_id("H_2026000001")
            self.assertEqual(found, patient_id)


if __name__ == "__main__":
    unittest.main()

