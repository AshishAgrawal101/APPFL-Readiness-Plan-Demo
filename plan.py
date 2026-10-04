"""Check a proposed readiness plan before giving it to APPFL."""

import json

ALLOWED_CHECKS = {"sample_size", "class_imbalance"}


def load_plan(path, columns):
    def unique_fields(pairs):
        fields = {}
        for key, value in pairs:
            if key in fields:
                raise ValueError(f"duplicate plan field: {key}")
            fields[key] = value
        return fields

    return validate_plan(
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_fields),
        columns,
    )


def validate_plan(plan, columns):
    if not isinstance(plan, dict) or set(plan) != {"task", "target", "checks"}:
        raise ValueError("plan needs task, target, and checks")
    if plan["task"] != "binary_classification":
        raise ValueError("this demo only handles binary classification")
    if not isinstance(plan["target"], str) or plan["target"] not in columns:
        raise ValueError("target must name an available column")
    checks = plan["checks"]
    if (
        not isinstance(checks, list)
        or not checks
        or any(not isinstance(check, str) for check in checks)
    ):
        raise ValueError("checks must be a nonempty list of names")
    if len(set(checks)) != len(checks) or not set(checks) <= ALLOWED_CHECKS:
        raise ValueError("duplicate or unsupported check")
    return {"task": plan["task"], "target": plan["target"], "checks": list(checks)}


def appfl_config(plan, output_dir, num_clients):
    plan = validate_plan(plan, {"outcome"})
    if type(num_clients) is not int or num_clients < 1:
        raise ValueError("num_clients must be a positive integer")
    return {
        "client_configs": {
            "data_readiness_configs": {
                "generate_dr_report": True,
                "output_dirname": str(output_dir),
                "output_filename": "readiness_report",
                "dr_metrics": {check: True for check in plan["checks"]},
            }
        },
        "server_configs": {
            "num_clients": num_clients,
            "logging_output_dirname": str(output_dir),
        },
    }
