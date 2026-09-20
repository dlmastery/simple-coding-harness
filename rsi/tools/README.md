# Tools the agent runs

Students use the course skills and the prompts in each lesson. They do not type the commands below. These notes let an agent or maintainer inspect the supplied implementation.

Use Python 3.12 in a project-local environment. Install [requirements.txt](requirements.txt). From the repository root, run `rsi/tools/lab.py` through that environment's Python. Give it an absolute learner workspace outside the course source.

| Action | Agent command arguments | Result |
|---|---|---|
| Inspect data | `inspect --task bike --workspace PATH` | Data report, sample rows, measured chart |
| Fit one candidate | `run --task bike --workspace PATH --model constant --features all --hypothesis "Use the training median as a baseline"` | Proposal, predictions, result, trial ledger |
| Compare candidates | `compare --workspace PATH` | Selection report and chosen candidate ID |
| Evaluate final recipe once | `final --workspace PATH --candidate trial-001` | Final predictions and a closed workspace |
| Check meaning rules | `audit-domain --input DOMAIN.md --output CHECK.md` | Concrete rule violations; nonzero exit on failure |

Task names: `bike` and `wine`. Model names: `constant`, `linear`, `tree`, `forest`. Bike feature groups: `calendar`, `weather`, `all`. Wine uses `all`. Seeds are explicit; default 17. On the first fit, the agent supplies `--attempt-limit N` using the lesson's total budget for that workspace. Later run, compare, and final commands recover that frozen limit automatically. A request to change it is refused. An optional `--policy PATH` retains the policy used by the agent. It records provenance, not proof of compliance.

For an existing successful selection candidate, run `rsi/tools/check_result.py CANDIDATE_PATH --report CHECK_PATH` through the same environment. It recomputes the metric from saved predictions and pinned source targets, checks row identities, and compares the ledger and report. Exit 0 means agreement; exit 1 reports a failed check. This is a separate calculation within the same local trust boundary. It cannot prove that predictions came from a claimed model or that the evaluator is secret.

## Scope and limits

The small model menu keeps early comparisons understandable. The tool does not propose improvements. The coding agent follows a skill to choose a hypothesis and invoke a tool. Later labs ask the agent to generate a new harness where the research mechanism needs different operations.

The tool pins data, its own source, task, budget, and evaluation rules in the workspace contract. A checksum detects an accidentally changed contract; it is not an independent security boundary. Tool edits require a new workspace. Keep the original source checkout to continue an older experiment; do not rewrite its hash or budget to make a newer tool accept it. Failed fit attempts count. A stale running record stops continuation until inspected. Final evaluation closes selection before reading final results.

The 120-second limit is a check on cumulative recorded fit time before another attempt. It is not a hard operating-system deadline. The agent must also apply a 60-second command timeout and stop the current process if it runs too long. Maximum attempts: 12. Keep early labs below their smaller stated limits. Agent inference and tool startup costs are additional.

These checks prevent common mistakes by cooperative agents. An agent that can edit this tool, its ledger, or its data can bypass them. Use an independently controlled evaluator and immutable records for claims that require an adversarial boundary.

## Recovery

If `.running` exists, read its process ID and confirm whether that process is active. Never delete a live lock. If the process has stopped, preserve the interrupted trial, mark its state `interrupted` in the generated ledger, record the reason, and remove the stale lock. Do not reuse its candidate ID or refund its attempt.

If a final evaluation fails, preserve the locked workspace. Investigate in a separate diagnostic copy. Reopening the original would allow unnoticed test-driven selection. Record any revised evaluation protocol as a new experiment.

Reset means creating a new sibling learner workspace. Do not delete course files, raw data, or prior evidence.
