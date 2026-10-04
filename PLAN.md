# Proposed AIDRIN and APPFL Integration

The goal is to reduce the manual effort when choosing data-readiness checks to apply to a new federated dataset. AIDRIN would be able to suggest appropriate checks based on a minimal description of the dataset, and only validated and approved checks would run in APPFL.

The current demo is a small proof of concept for this idea. It uses a manually written plan and applies two existing APPFL checks to four synthetic clients. The immediate next step would be to test whether AIDRIN would be able to generate a safe plan similar to the one hard-coded in the demo.

## Proposed workflow

**Describe the dataset.** Start with synthetic tabular data, give the assistant a task, the column names and types, and roles that are confirmed to exist (e.g. outcome column). Avoid including any patient rows in the planning request.

**Generate a readiness plan.** Use the existing AIDRIN metric guidance to choose the most relevant checks and explain the reasoning. Specify what inputs, if any, would be needed to run the suggested check and whether they already exist in APPFL. Identify which of the suggested checks already exist in APPFL.

**Validate the plan.** A small adapter would reject unrecognized checks, missing or invalid column roles, unsupported settings, or conflicting instructions.

**Require manual approval.** A human would be able to edit, approve, or reject the proposed plan before actually doing anything with the clients.

**Run approved checks locally.** The clients would calculate the approved checks on their local data and return whatever summaries or results are needed.

**Report results and failures.** Keep track of which checks actually ran on which clients and what results they returned, or if a client failed to run a check.

**Review metric and privacy assumptions.** Checks with similar names in AIDRIN and APPFL would not be assumed to do the same things unless their formulas and input requirements are known and compatible. Summaries sent from a client would also need a separate privacy review.

## How I would test it

I would compare the assistant's plans to ones I would write myself for a few different datasets. These would include variations in the name of the outcome column, no obvious outcome column, unsupported suggestions, and a client failing a check. I would also make sure that no checks are run before approval and that the planning request and reports do not include patient rows. Once the serial version is working, I would try running a small local networked APPFL.

## What I have so far

The current demo uses a hard-coded plan from `example_plan.json`. The four simulated APPFL clients run `sample_size` and `class_imbalance` checks after manual approval. The demo can also run AIDRIN's class-imbalance metric locally at each client.

AIDRIN does not yet generate the plan, and all four clients currently run on the same computer.

## Where I need feedback

I would appreciate any feedback about this being a reasonable first step for an integration, what capabilities from AIDRIN would be most useful to prioritize, and whether this approach to planning and approval would make sense for APPFL.
