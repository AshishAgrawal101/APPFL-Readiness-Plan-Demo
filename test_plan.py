import unittest
from unittest.mock import patch

from demo import aidrin_check, should_run_aidrin
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

    @patch("demo.subprocess.run")
    def test_aidrin_command_uses_local_csv(self, run):
        run.return_value.stdout = '{"metric": "class-imbalance"}'
        result = aidrin_check([0, 1], "outcome")
        self.assertEqual(result["metric"], "class-imbalance")
        args = run.call_args.args[0]
        self.assertEqual(args[:3], ["aidrin", "run", "class-imbalance"])
        self.assertEqual(args[-1], "outcome")

    def test_aidrin_follows_approved_checks(self):
        self.assertTrue(should_run_aidrin(GOOD, True))
        self.assertFalse(should_run_aidrin(GOOD, False))
        self.assertFalse(should_run_aidrin({**GOOD, "checks": ["sample_size"]}, True))


if __name__ == "__main__":
    unittest.main()
