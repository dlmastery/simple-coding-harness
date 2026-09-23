"""Summarize checked native scores, behavior changes, uncertainty and all fit costs."""
import argparse
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from run_nested_research import ARMS, workspace


def report(phase):
    work = workspace(phase)
    checks = pd.read_csv(work / "FINAL-CHECKS.csv")
    if checks.empty or not checks.passed.all():
        raise ValueError("Complete final checks required")
    scores = pd.read_csv(work / "SCORES.csv")
    ledger = pd.read_csv(work / "SEARCH-LEDGER.csv")
    panel = pd.read_csv(work / "PANEL.csv").set_index("task")
    require_arms = ARMS[phase]
    native = scores.pivot(index="task", columns="arm", values="final_score")[require_arms]
    native.insert(0, "name", panel.loc[native.index, "name"])
    native.insert(1, "metric", ["balanced_accuracy" if panel.loc[task, "kind"] == "classification" else "MAE" for task in native.index])
    native.to_csv(work / "NATIVE-SCORES.csv")
    losses = scores.pivot(index="task", columns="arm", values="final_loss")
    contrasts = [("i0", "parent"), ("i1", "parent")] if phase == "development" else [("i1", "i0"), ("i1", "parent"), ("i1", "fixed"), ("i1", "random")]
    summaries = []
    for child, parent in contrasts:
        differences = losses[child]-losses[parent]
        rng = np.random.default_rng(7342)
        draws = []
        for kind in ("classification", "regression"):
            ids = panel[panel.kind == kind].index
            values = differences.loc[ids].to_numpy()
            draws.append(rng.choice(values, size=(10000, len(values)), replace=True))
        bootstrap = np.concatenate(draws, axis=1).mean(axis=1)
        low, high = np.percentile(bootstrap, [2.5, 97.5])
        summaries.append(dict(child=child, parent=parent, mean_loss_change=differences.mean(),
                              interval_low=low, interval_high=high, better=int((differences < -1e-12).sum()),
                              tied=int((np.abs(differences) <= 1e-12).sum()), worse=int((differences > 1e-12).sum())))
    pd.DataFrame(summaries).to_csv(work / "CONTRASTS.csv", index=False)
    behavior = []
    for task in panel.index:
        parent = ledger[(ledger.task == task) & (ledger.arm == "parent")].sort_values("step")
        for arm in ("i0", "i1"):
            child = ledger[(ledger.task == task) & (ledger.arm == arm)].sort_values("step")
            behavior.append(dict(task=task, researcher=arm,
                                 differing_model_choices=sum(a != b for a, b in zip(parent.constructor_sha256, child.constructor_sha256)),
                                 parent_choice=int(scores[(scores.task == task) & (scores.arm == "parent")].selected_step.iloc[0]),
                                 child_choice=int(scores[(scores.task == task) & (scores.arm == arm)].selected_step.iloc[0])))
    pd.DataFrame(behavior).to_csv(work / "BEHAVIOR-CHANGES.csv", index=False)
    costs = []
    for label, records in (("search", ledger), ("scoring", scores)):
        for arm, group in records.groupby("arm"):
            costs.append(dict(phase=label, arm=arm, attempts=len(group), success=int(group.status.eq("success").sum()),
                              failed=int((~group.status.eq("success")).sum()), worker_seconds=group.worker_seconds.sum()))
    pd.DataFrame(costs).to_csv(work / "COSTS.csv", index=False)
    lines = [f"# Checked {phase} comparison", "", "Balanced accuracy is better when higher; MAE is better when lower.", "",
             "| Task | Metric | " + " | ".join(require_arms) + " |", "|---|---|" + "---:|"*len(require_arms)]
    for task, row in native.iterrows():
        lines.append(f"| {task}: {row['name']} | {row['metric']} | " + " | ".join(f"{row[arm]:.6f}" for arm in require_arms) + " |")
    lines += ["", "Normalized paired loss differences below are better when negative.", "",
              "| Comparison | Mean change | 95% task-bootstrap interval | Better / tied / worse |", "|---|---:|---|---|"]
    for row in summaries:
        lines.append(f"| {row['child']} minus {row['parent']} | {row['mean_loss_change']:+.6f} | [{row['interval_low']:+.6f}, {row['interval_high']:+.6f}] | {row['better']} / {row['tied']} / {row['worse']} |")
    lines += ["", "Six public tasks, one model seed, 10,000 task bootstrap draws stratified by kind.",
              "Intervals are exploratory and unadjusted for multiple comparisons. A source", "rewrite is not proof of changed behavior or improved quality.", "",
              f"This phase executed {len(ledger)} search attempts and {len(scores)} scoring refits.",
              f"Recorded worker-process time: {ledger.worker_seconds.sum()+scores.worker_seconds.sum():.3f} seconds.",
              "This excludes coding-agent inference and cannot establish total research-cost savings.", "",
              "Inspect BEHAVIOR-CHANGES.csv for actual differing constructed models and COSTS.csv", "for all researcher costs. Losing searches remain charged."]
    if phase == "development":
        lines += ["", "These tasks were already exposed in prior work. Their former final rows are", "development evaluation here. Do not describe these as fresh transfer results.", "The fixed promotion rule is evaluated separately in VERDICTS.csv."]
    else:
        lines += ["", "The primary comparison is I1's generated researcher versus I0's generated", "researcher. Fixed and random controls remain visible. This is a bounded", "programmatic adaptation, not a frontier-system reproduction or weight update.",
                  "Add the separate 234-attempt development phase when reporting the full study cost."]
    (work / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    source = work / "analysis-source"
    source.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__), source / Path(__file__).name)
    print(pd.DataFrame(summaries).to_string(index=False))
    print(f"Reported {len(ledger)+len(scores)} charged attempts; no new fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=list(ARMS))
    report(parser.parse_args().phase)
