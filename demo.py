"""Run an approved plan on synthetic hospital data with APPFL."""

import argparse
import csv
import json
import math
import platform
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from plan import appfl_config, load_plan, validate_plan

SITES = (
    ("hospital_a", 200, 100),
    ("hospital_b", 120, 60),
    ("hospital_c", 80, 4),
    ("hospital_d", 40, 12),
)


def should_run_aidrin(plan, requested):
    return requested and "class_imbalance" in plan["checks"]


def aidrin_check(labels, target, command="aidrin"):
    with tempfile.TemporaryDirectory() as directory:
        csv_path = Path(directory) / "local_outcomes.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([target])
            writer.writerows((int(label),) for label in labels)
        try:
            result = subprocess.run(
                [command, "run", "class-imbalance", str(csv_path), target],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("AIDRIN did not finish within 60 seconds") from error
        except FileNotFoundError as error:
            raise RuntimeError(
                "AIDRIN CLI not found; install AIDRIN or omit --aidrin"
            ) from error
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"AIDRIN failed (exit {error.returncode})") from error
        try:
            result = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("AIDRIN returned output that was not JSON") from error
        if not isinstance(result, dict):
            raise RuntimeError("AIDRIN returned an unexpected result format")
        if "error" in result or "Error" in result:
            raise RuntimeError("AIDRIN reported a metric error")
        metric = result.get("Imbalance degree")
        score = (
            metric.get("Imbalance Degree score") if isinstance(metric, dict) else None
        )
        if type(score) not in (int, float) or not math.isfinite(score) or score < 0:
            raise RuntimeError("AIDRIN returned no valid class-imbalance score")
        return result


def run(plan, output_dir, use_aidrin=False, aidrin_command="aidrin"):
    plan = validate_plan(plan, {"outcome"})
    output_dir = Path(output_dir)
    import torch
    from appfl.agent import ClientAgent, ServerAgent
    from omegaconf import OmegaConf

    class HospitalData(torch.utils.data.Dataset):
        def __init__(self, count, positives):
            self.data_input = torch.zeros((count, 1), dtype=torch.float32)
            self.data_label = torch.tensor(
                [1] * positives + [0] * (count - positives), dtype=torch.long
            )

        def __len__(self):
            return len(self.data_label)

        def __getitem__(self, index):
            return self.data_input[index], self.data_label[index]

    output_dir.mkdir(parents=True, exist_ok=True)
    config = OmegaConf.create(appfl_config(plan, output_dir, len(SITES)))
    server = ServerAgent(config)
    reports = {}
    aidrin_results = {}
    clients = []
    try:
        for name, count, positives in SITES:
            client = ClientAgent(
                OmegaConf.create(
                    {
                        "client_id": name,
                        "train_configs": {"logging_output_dirname": str(output_dir)},
                    }
                )
            )
            clients.append(client)
            client.train_dataset = HospitalData(count, positives)
            if should_run_aidrin(plan, use_aidrin):
                aidrin_results[name] = aidrin_check(
                    client.train_dataset.data_label.tolist(),
                    plan["target"],
                    aidrin_command,
                )
            client_config = server.get_client_configs()
            client.load_config(client_config)
            report = client.generate_readiness_report(client_config)
            for key, value in report.items():
                reports.setdefault(key, {})[name] = value
        server.data_readiness_report(reports)
        result = {
            "mode": "serial_synthetic",
            "appfl_version": version("appfl"),
            "python_version": platform.python_version(),
            "approved_plan": plan,
            "approved_checks": plan["checks"],
            "client_results": {
                name: {key: reports[key][name] for key in plan["checks"]}
                for name, _, _ in SITES
            },
            "aidrin_results": aidrin_results or "not run",
        }
        results_path = output_dir / "readiness_results.json"
        results_path.write_text(
            json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2, allow_nan=False))
        print(f"APPFL report: {(output_dir / 'readiness_report.html').resolve()}")
        print(f"JSON results: {results_path.resolve()}")
        return result
    finally:
        for agent in [*clients, server]:
            for handler in list(agent.logger.logger.handlers):
                handler.close()
                agent.logger.logger.removeHandler(handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve", action="store_true", help="run the displayed plan")
    parser.add_argument(
        "--aidrin", action="store_true", help="also run AIDRIN class imbalance"
    )
    parser.add_argument(
        "--aidrin-command", default="aidrin", help="path to the AIDRIN executable"
    )
    parser.add_argument(
        "--plan", type=Path, default=Path(__file__).with_name("example_plan.json")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).with_name("output")
    )
    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan, {"outcome"})
    except (OSError, ValueError) as error:
        print(f"Invalid plan: {error}", file=sys.stderr)
        return 2
    print("Proposed plan (checks chosen manually):", flush=True)
    print(json.dumps(plan, indent=2), flush=True)
    if not args.approve:
        print("No client checks ran. Review the plan, then rerun with --approve.")
        return 0
    try:
        run(plan, args.output_dir, args.aidrin, args.aidrin_command)
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f"Demo failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
