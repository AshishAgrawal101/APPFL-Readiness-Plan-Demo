"""Run an approved plan on synthetic hospital data with APPFL."""

import argparse
import csv
import json
import subprocess
import tempfile
from pathlib import Path

from plan import appfl_config, validate_plan


SITES = (("hospital_a", 200, 100), ("hospital_b", 120, 60),
         ("hospital_c", 80, 4), ("hospital_d", 40, 12))


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
                capture_output=True, text=True, check=True, timeout=60,
            )
        except FileNotFoundError as error:
            raise RuntimeError("AIDRIN CLI not found; install AIDRIN or omit --aidrin") from error
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"AIDRIN failed: {error.stderr.strip()}") from error
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("AIDRIN returned output that was not JSON") from error


def run(plan, output_dir, use_aidrin=False, aidrin_command="aidrin"):
    import torch
    from omegaconf import OmegaConf
    from appfl.agent import ClientAgent, ServerAgent

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
            client = ClientAgent(OmegaConf.create({
                "client_id": name,
                "train_configs": {"logging_output_dirname": str(output_dir)},
            }))
            clients.append(client)
            client.train_dataset = HospitalData(count, positives)
            if should_run_aidrin(plan, use_aidrin):
                aidrin_results[name] = aidrin_check(
                    client.train_dataset.data_label.tolist(), plan["target"], aidrin_command
                )
            client_config = server.get_client_configs()
            client.load_config(client_config)
            report = client.generate_readiness_report(client_config)
            for key, value in report.items():
                reports.setdefault(key, {})[name] = value
        server.data_readiness_report(reports)
        print(json.dumps({
            "approved_checks": plan["checks"],
            "client_results": {
                name: {key: reports[key][name] for key in plan["checks"]}
                for name, _, _ in SITES
            },
            "aidrin_results": aidrin_results or "not run",
        }, indent=2))
        print(f"APPFL report: {output_dir.resolve()}")
    finally:
        for agent in [*clients, server]:
            for handler in list(agent.logger.logger.handlers):
                handler.close()
                agent.logger.logger.removeHandler(handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--aidrin", action="store_true")
    parser.add_argument("--aidrin-command", default="aidrin")
    parser.add_argument("--plan", type=Path, default=Path(__file__).with_name("example_plan.json"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    plan = validate_plan(json.loads(args.plan.read_text(encoding="utf-8")), {"outcome"})
    print("Proposed plan:")
    print(json.dumps(plan, indent=2))
    if not args.approve:
        print("No client checks ran. Review the plan, then rerun with --approve.")
        return
    run(plan, args.output_dir, args.aidrin, args.aidrin_command)


if __name__ == "__main__":
    main()
