# APPFL readiness plan demo

Mr. Li suggested exploring whether AIDRIN could help APPFL choose data-readiness checks for new datasets. This repo is an early test of that idea. It runs two existing checks on synthetic data, but it does not use an agent to choose them yet.

The checks are listed in `example_plan.json`. The script validates the plan and shows it to the user. Nothing runs until the user adds `--approve`. APPFL then runs sample-size and class-imbalance checks for four simulated hospitals and saves an HTML report. One hospital has 4 positive outcomes among 80 patients, so it provides a clear example of class imbalance.

To run the demo, use Python 3.10 with APPFL installed (`pip install appfl`):

```bash
python -X utf8 demo.py
python -X utf8 demo.py --approve
python -X utf8 -m unittest -v
```

The first command displays the plan without running any checks. To test the optional AIDRIN connection, [install its CLI](https://aidrin.readthedocs.io/en/latest/cli_installation.html) (`pip install aidrin`) and run:

```bash
python -X utf8 demo.py --approve --aidrin
```

The script runs AIDRIN's class-imbalance check for each simulated hospital using a temporary local CSV, which it deletes afterward. It calls AIDRIN only when class imbalance is included in the approved plan. In one run, the most imbalanced hospital scored 0.90 with AIDRIN and 0.64 with APPFL. These scores use different scales, so the demo reports them separately. Use `--aidrin-command` if the AIDRIN executable is in another environment.

All four hospitals run on one computer, and the data is synthetic. The agent-guided part is still planned work. I explain the broader idea and what I would test in [PLAN.md](PLAN.md).
