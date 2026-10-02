# APPFL readiness plan demo

Zilinghan suggested an AIDRIN-APPFL connection. I started with the handoff between a plan and APPFL's existing checks.

I still write the plan in `example_plan.json` by hand, but the program checks the requested metrics and shows the plan before anything runs. Once approved, four fake hospitals run APPFL's sample-size and class-imbalance checks and get an HTML report. Hospital C has only 4 positive outcomes among 80 patients. Its imbalance stands out.

With Python 3.10 and APPFL installed (`pip install appfl`), run:

```bash
python -X utf8 demo.py
python -X utf8 demo.py --approve
python -X utf8 -m unittest -v
```

The first command only displays the plan. To try the AIDRIN part, [install its CLI](https://aidrin.readthedocs.io/en/latest/cli_installation.html) (`pip install aidrin`) and run:

```bash
python -X utf8 demo.py --approve --aidrin
```

For each fake hospital, the script makes a temporary CSV, runs AIDRIN's class-imbalance check locally, and deletes the CSV after the check finishes. AIDRIN runs only if `class_imbalance` was approved. In my run, hospital C scored 0.90 in AIDRIN and 0.64 in APPFL. Different scales. I show both results separately, and `--aidrin-command` lets you point to AIDRIN if it's installed in another environment.

Everything here runs on one computer with synthetic data. AIDRIN checks class imbalance, but its agent does not choose the plan yet. I wrote down how I would try that in the [project plan](PLAN.md), including what I would test before proposing any change to APPFL.
