import unittest

from plan import appfl_config, validate_plan


GOOD = {"task": "binary_classification", "target": "outcome",
        "checks": ["sample_size", "class_imbalance"]}


class PlanTests(unittest.TestCase):
    def test_accepted_checks_become_appfl_settings(self):
        plan = validate_plan(GOOD, {"outcome"})
        config = appfl_config(plan, "output", 4)
        checks = config["client_configs"]["data_readiness_configs"]["dr_metrics"]
        self.assertEqual(checks, {"sample_size": True, "class_imbalance": True})
        self.assertEqual(config["server_configs"]["num_clients"], 4)

    def test_reject_unknown_check(self):
        with self.assertRaises(ValueError):
            validate_plan({**GOOD, "checks": ["send_patient_rows"]}, {"outcome"})

    def test_reject_missing_target(self):
        with self.assertRaises(ValueError):
            validate_plan(GOOD, {"age"})

    def test_reject_duplicate_check(self):
        with self.assertRaises(ValueError):
            validate_plan({**GOOD, "checks": ["sample_size", "sample_size"]}, {"outcome"})


if __name__ == "__main__":
    unittest.main()
