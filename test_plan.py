import csv
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from demo import aidrin_check, main, should_run_aidrin
from plan import appfl_config, load_plan, validate_plan

GOOD = {
    "task": "binary_classification",
    "target": "outcome",
    "checks": ["sample_size", "class_imbalance"],
}
AIDRIN_RESULT = {"Imbalance degree": {"Imbalance Degree score": 0.0}}


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
            validate_plan(
                {**GOOD, "checks": ["sample_size", "sample_size"]}, {"outcome"}
            )

    def test_reject_invalid_plan_shapes(self):
        for plan in (None, [], {}, {**GOOD, "extra": True}):
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                validate_plan(plan, {"outcome"})

    def test_reject_invalid_checks(self):
        for checks in ([], "sample_size", None, [1], ["sample_size", None]):
            with self.subTest(checks=checks), self.assertRaises(ValueError):
                validate_plan({**GOOD, "checks": checks}, {"outcome"})

    def test_reject_other_tasks(self):
        with self.assertRaises(ValueError):
            validate_plan({**GOOD, "task": "regression"}, {"outcome"})

    def test_validated_checks_are_a_copy(self):
        source = {**GOOD, "checks": list(GOOD["checks"])}
        validated = validate_plan(source, {"outcome"})
        source["checks"].append("unknown")
        self.assertEqual(validated["checks"], GOOD["checks"])

    def test_config_rejects_invalid_client_counts(self):
        for count in (0, -1, True, 1.5, "4"):
            with self.subTest(count=count), self.assertRaises(ValueError):
                appfl_config(GOOD, "output", count)

    def test_config_rejects_unvalidated_checks(self):
        with self.assertRaises(ValueError):
            appfl_config({**GOOD, "checks": ["unknown"]}, "output", 4)

    def test_load_plan_rejects_duplicate_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(
                '{"task":"binary_classification","target":"age",'
                '"target":"outcome","checks":["sample_size"]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate plan field"):
                load_plan(path, {"outcome"})

    @patch("demo.run")
    def test_preview_does_not_execute_or_create_output(self, run):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with redirect_stdout(io.StringIO()):
                code = main(["--aidrin", "--output-dir", str(output)])
            self.assertEqual(code, 0)
            run.assert_not_called()
            self.assertFalse(output.exists())

    @patch("demo.run")
    def test_approved_plan_is_passed_to_runner(self, run):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--approve", "--aidrin"]), 0)
        self.assertEqual(run.call_args.args[0], GOOD)
        self.assertTrue(run.call_args.args[2])

    @patch("demo.run")
    def test_invalid_plan_never_executes(self, run):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            for text in ("{", json.dumps({**GOOD, "checks": ["unknown"]})):
                path.write_text(text, encoding="utf-8")
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(main(["--approve", "--plan", str(path)]), 2)
        run.assert_not_called()

    @patch("demo.run")
    def test_missing_plan_never_executes(self, run):
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(["--approve", "--plan", str(Path(directory) / "missing")]), 2
                )
        run.assert_not_called()

    @patch("demo.run", side_effect=RuntimeError("metric failed"))
    def test_execution_failure_returns_nonzero(self, run):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["--approve"]), 2)
        self.assertIn("metric failed", errors.getvalue())

    @patch("demo.subprocess.run")
    def test_aidrin_command_uses_local_csv(self, run):
        run.return_value.stdout = json.dumps(AIDRIN_RESULT)
        result = aidrin_check([0, 1], "outcome")
        self.assertEqual(result, AIDRIN_RESULT)
        args = run.call_args.args[0]
        self.assertEqual(args[:3], ["aidrin", "run", "class-imbalance"])
        self.assertEqual(args[-1], "outcome")
        self.assertEqual(run.call_args.kwargs["timeout"], 60)
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")

    @patch("demo.subprocess.run")
    def test_aidrin_temporary_csv_is_removed(self, run):
        paths = []

        def check_csv(command, **kwargs):
            path = Path(command[3])
            paths.append(path)
            with path.open(encoding="utf-8", newline="") as file:
                self.assertEqual(list(csv.reader(file)), [["outcome"], ["0"], ["1"]])
            return subprocess.CompletedProcess(
                command, 0, stdout=json.dumps(AIDRIN_RESULT)
            )

        run.side_effect = check_csv
        aidrin_check([0, 1], "outcome")
        self.assertFalse(paths[0].exists())

    @patch("demo.subprocess.run")
    def test_aidrin_failures_are_clear_and_remove_csv(self, run):
        for error, message in (
            (FileNotFoundError(), "CLI not found"),
            (subprocess.TimeoutExpired("aidrin", 60), "60 seconds"),
            (subprocess.CalledProcessError(1, "aidrin"), "exit 1"),
        ):
            with self.subTest(message=message):
                run.side_effect = error
                with self.assertRaisesRegex(RuntimeError, message):
                    aidrin_check([0, 1], "outcome")
                self.assertFalse(Path(run.call_args.args[0][3]).exists())

    @patch("demo.subprocess.run")
    def test_aidrin_rejects_unexpected_responses(self, run):
        for text in (
            "not JSON",
            "[]",
            "null",
            "{}",
            '{"error":"failed"}',
            '{"Error":"failed"}',
            '{"Imbalance degree":{"Error":"failed"}}',
        ):
            with self.subTest(text=text), self.assertRaises(RuntimeError):
                run.return_value.stdout = text
                aidrin_check([0, 1], "outcome")

    @patch("demo.subprocess.run")
    def test_aidrin_rejects_invalid_scores(self, run):
        for score in (None, True, "0.9", -1, float("nan"), float("inf")):
            with self.subTest(score=score), self.assertRaises(RuntimeError):
                run.return_value.stdout = json.dumps(
                    {"Imbalance degree": {"Imbalance Degree score": score}}
                )
                aidrin_check([0, 1], "outcome")

    def test_aidrin_follows_approved_checks(self):
        self.assertTrue(should_run_aidrin(GOOD, True))
        self.assertFalse(should_run_aidrin(GOOD, False))
        self.assertFalse(should_run_aidrin({**GOOD, "checks": ["sample_size"]}, True))


if __name__ == "__main__":
    unittest.main()
