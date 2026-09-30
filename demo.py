"""Run an approved plan on synthetic hospital data with APPFL."""

import argparse
import json
from pathlib import Path

from plan import appfl_config, validate_plan


SITES = (("hospital_a", 200, 100), ("hospital_b", 120, 60),
         ("hospital_c", 80, 4), ("hospital_d", 40, 12))


def run(plan, output_dir):
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
    clients = []
    try:
        for name, count, positives in SITES:
            client = ClientAgent(OmegaConf.create({
                "client_id": name,
                "train_configs": {"logging_output_dirname": str(output_dir)},
            }))
            clients.append(client)
            client.train_dataset = HospitalData(count, positives)
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
    parser.add_argument("--plan", type=Path, default=Path(__file__).with_name("example_plan.json"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    plan = validate_plan(json.loads(args.plan.read_text(encoding="utf-8")), {"outcome"})
    print("Proposed plan:")
    print(json.dumps(plan, indent=2))
    if not args.approve:
        print("No client checks ran. Review the plan, then rerun with --approve.")
        return
    run(plan, args.output_dir)


if __name__ == "__main__":
    main()
