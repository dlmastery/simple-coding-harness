"""Author walkthrough of shared execution paths; no learner responses invented."""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("walkthrough_lab", REPO / "rsi/tools/lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
OUT = REPO / "rsi/evidence/2026-09-20/walkthrough"


def run():
    if OUT.exists():
        raise RuntimeError("Preserve prior evidence. Use a new dated output path for another run.")
    results = []
    for label, task, recipes in [
        ("02-01-model-change", "bike", [("constant", "calendar"), ("linear", "calendar")]),
        ("02-03-feature-change", "bike", [("linear", "calendar"), ("linear", "all")]),
        ("02-02-bounded-loop", "bike", [("constant", "calendar"), ("linear", "calendar"), ("tree", "calendar")]),
        ("05-02-classification", "wine", [("constant", "all"), ("linear", "all")]),
    ]:
        workspace = OUT / label
        for model, features in recipes:
            row = lab.experiment(workspace, task, model, features, 17,
                                 f"Author walkthrough: compare {model} with {features} under the frozen {task} contract.")
            results.append((label, row["candidate"], row["score"], row["seconds"]))
        lab.compare(workspace)
        lab.write(workspace / "PROGRESS.md", "# Author walkthrough\n\nExecuted the declared fits and comparison. No student prediction, quiz, or teach-back was collected. Final data was not used for selection.\n")

    domain = OUT / "04-04-domain"
    bad = "| Subject | Relation | Object |\n|---|---|---|\n| model | uses feature | total_users |\n| total_users | derived from | target |\n| scaler | fit on | final |\n| search | selects on | final |\n"
    good = "| Subject | Relation | Object |\n|---|---|---|\n| model | uses feature | hr |\n| scaler | fit on | train |\n| search | selects on | selection |\n"
    lab.write(domain / "ORIGINAL.md", bad)
    errors = lab.audit_domain(domain / "ORIGINAL.md", domain / "ORIGINAL-CHECK.md")
    assert len(errors) == 3
    lab.write(domain / "CORRECTED.md", good)
    assert not lab.audit_domain(domain / "CORRECTED.md", domain / "CORRECTED-CHECK.md")

    final_workspace = OUT / "02-02-bounded-loop"
    selected = lab.compare(final_workspace)
    final_score = lab.final_evaluation(final_workspace, selected)
    try:
        lab.experiment(final_workspace, "bike", "forest", "calendar", 17, "Attempt after final exposure")
    except lab.Refusal as error:
        lab.write(final_workspace / "POST-FINAL-REFUSAL.md", f"# Actual refusal\n\n{error}\n\nNo extra fit started.\n")
    else:
        raise AssertionError("Post-final fit was not rejected")
    summary = "# Controlled author walkthrough\n\n| Path | Candidate | Selection score | Fit seconds |\n|---|---|---:|---:|\n"
    summary += "\n".join(f"| {label} | {candidate} | {score:.6f} | {seconds:.6f} |" for label, candidate, score, seconds in results)
    summary += f"\n\nThe bounded-loop retained recipe {selected} received final public-data MAE {final_score:.6f}. Post-final search was refused.\n\n"
    summary += "These are actual tool executions by the authoring agent. The report does not establish independent evaluator secrecy, native skill discovery in other agents, all 101 learner workflows, or teaching effectiveness. Nine model fits plus one final refit ran. Domain checks rejected three violations and accepted the corrected facts. Costs shown exclude agent inference and process startup.\n"
    lab.write(OUT / "README.md", summary)
    print(summary)


if __name__ == "__main__":
    run()
