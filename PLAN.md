# Plan for connecting AIDRIN and APPFL

I write `example_plan.json` myself right now. The next question is whether AIDRIN's existing skill can suggest useful checks from a dataset description, which a person could review before APPFL asks its clients to run anything. Patient rows stay at each client.

The proposed path is `dataset description -> AIDRIN suggestion -> validation -> human approval -> APPFL client checks -> report`.

## Start with the information AIDRIN needs

I'd start with a few synthetic binary-classification datasets. The planner would get the task, column names and types, and an outcome column confirmed by a person. No patient rows. AIDRIN's usual workflow also looks at sample statistics, so I'd test whether this shorter description is enough. If the suggestions are poor, I would check what extra information it needs and review that information before sharing it.

## Turn the suggestion into an APPFL plan

I'd ask AIDRIN's skill for checks and short reasons, then convert its answer into the JSON format used here and validate it against APPFL's supported checks and required column roles. The validator would also catch duplicates and conflicting settings. A person could change or reject the plan before any client runs, and suggested text would never be run as code or a shell command.

I'd start with `sample_size` and `class_imbalance`, the two checks already in this demo, and leave AIDRIN's literature-search and code-generation features for later.

## Run and report

After approval, APPFL would give every client the same data-readiness settings so each one can calculate checks on its own data, with AIDRIN running a local metric where useful, as it does here. The report should name the tool behind each number and show which sites finished or failed. It must keep unlike scores separate. APPFL's and AIDRIN's imbalance scores, for example, have different scales.

## Test before proposing an APPFL change

I'd try balanced and imbalanced data, a renamed outcome column, and a dataset where the outcome is unclear. I'd also propose an unsupported check and deliberately fail one client. Nothing runs before approval. Every client must get the same plan, with failures visible in the report and patient rows absent from both the planning request and server report. After that, I'd try a local networked APPFL run.

I would compare AIDRIN's suggestions against plans chosen by a person for several synthetic datasets, and the program would stop with an explanation if the assistant chose the wrong outcome or an unsupported check. One successful demo would not tell me much about that.

This separate repo is where I'd keep the experiments while asking the APPFL and AIDRIN teams for feedback. The subgroup-calibration PR is separate. Once the plan is tested, I could propose the smallest useful change to APPFL.

I want to ask them which dataset details AIDRIN can safely use and whether this approval step fits APPFL. I also want their view on AIDRIN's role: should it run checks at each client, help select APPFL's existing checks, or both?
