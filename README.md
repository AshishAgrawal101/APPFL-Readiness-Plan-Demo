# APPFL readiness plan demo

This is a small first step toward the idea Zilinghan suggested: letting an assistant propose data-readiness checks for a new dataset, while a person reviews the plan before any hospital runs it.

Right now the plan is written in `example_plan.json`, not produced by AIDRIN. The demo checks that the proposed checks are supported, waits for `--approve`, then gives the same settings to four synthetic hospitals through APPFL. Each hospital runs APPFL's existing sample-size and class-imbalance checks. APPFL saves an HTML report. No real patient data is involved.

Run it with Python 3.10 and APPFL installed (`pip install appfl`):

```bash
python -X utf8 demo.py
python -X utf8 demo.py --approve
python -X utf8 -m unittest -v
```

If you also install the [AIDRIN CLI](https://aidrin.readthedocs.io/en/latest/cli_installation.html) (`pip install aidrin`), you can run its class-imbalance check locally at each synthetic hospital:

```bash
python -X utf8 demo.py --approve --aidrin
```

The script writes a temporary CSV for one hospital at a time, asks AIDRIN to check it, and removes the CSV afterward. It prints AIDRIN's JSON separately from APPFL's results because their imbalance scores use different scales. In my test, hospital C scored 0.90 in AIDRIN and 0.64 in APPFL; both showed it was more imbalanced than the balanced sites. If AIDRIN is in another environment, pass its executable path with `--aidrin-command`.

The first command only shows the plan. The second actually runs the checks. Hospital C has 4 positive outcomes out of 80, so its class imbalance should stand out from the balanced hospitals.

The optional command really calls AIDRIN's metric, but it does **not** use AIDRIN's agent or automatically choose metrics. A next step would be to let an agent suggest the same small JSON plan, keep the validation and approval step, and test it against datasets with different column names and types. It also does not set up a production hospital network or a privacy guarantee.
