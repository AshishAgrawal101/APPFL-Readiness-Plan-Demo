# APPFL and AIDRIN readiness demo

Mr. Li proposed an interesting idea about using AIDRIN to help APPFL decide on data-readiness checks for new datasets. This repository is an initial experiment with this idea. It tests two existing checks on synthetic data, but without using an agent to choose between them yet.

The checks under consideration are described in `example_plan.json`. The script validates the plan and displays it to the user; nothing is executed until `--approve` is given. Then, sample-size and class-imbalance checks are performed for four simulated hospitals and an HTML summary is generated. The third hospital has 4 positive outcomes out of 80 patients, to illustrate a case with class imbalance.

To run the demo, Python 3.10 is needed with APPFL installed (`pip install appfl`):

```bash
python -X utf8 demo.py
python -X utf8 demo.py --approve
python -X utf8 -m unittest -v
```

The first command simply displays the plan, without actually performing any checks. To test the optional connection to AIDRIN, one should first install its command-line interface (`pip install aidrin`) and then try:

```bash
python -X utf8 demo.py --approve --aidrin
```

This will run the class-imbalance check from AIDRIN for each of the four simulated hospitals, using a temporary local CSV file, which is then deleted. The AIDRIN check is called only for hospitals for which class imbalance was included in the approved plan. In the example, the most imbalanced hospital scored 0.90 with AIDRIN and 0.64 with APPFL, but these scores are not directly comparable as they are on different scales, and are reported separately in the demo. Alternatively, one can use `--aidrin-command` if the AIDRIN executable is not in the system's PATH.

In this demo, all four hospitals are run on a single computer, using synthetic data only. The agent-guided part of the process is left for future work; here, I illustrate the general idea and describe what specific tests I would perform in [PLAN.md](PLAN.md).
