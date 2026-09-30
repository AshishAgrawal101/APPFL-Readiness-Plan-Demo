"""Check a proposed readiness plan before giving it to APPFL."""

ALLOWED_CHECKS = {"sample_size", "class_imbalance"}


def validate_plan(plan, columns):
    if not isinstance(plan, dict) or set(plan) != {"task", "target", "checks"}:
        raise ValueError("plan needs task, target, and checks")
    if plan["task"] != "binary_classification":
        raise ValueError("this demo only handles binary classification")
    if not isinstance(plan["target"], str) or plan["target"] not in columns:
        raise ValueError("target must name an available column")
    checks = plan["checks"]
    if not isinstance(checks, list) or not checks or any(
        not isinstance(check, str) for check in checks
    ):
        raise ValueError("checks must be a nonempty list of names")
    if len(set(checks)) != len(checks) or not set(checks) <= ALLOWED_CHECKS:
        raise ValueError("duplicate or unsupported check")
    return {"task": plan["task"], "target": plan["target"], "checks": checks}


def appfl_config(plan, output_dir, num_clients):
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
