"""Report all frozen procedure outcomes and prespecified paired contrasts after checks."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"
ARMS = ["fixed", "random", "memory", "parent", "harness", "updater"]
CONTRASTS = [("harness", "parent"), ("updater", "harness"), ("memory", "fixed"), ("memory", "random")]


def main():
    if not pd.read_csv(WORK / "FINAL-CHECKS.csv").passed.all():
        raise ValueError("Final checks must pass before reporting")
    scores = pd.read_csv(WORK / "SCORES.csv")
    search = pd.read_csv(WORK / "SEARCH-LEDGER.csv")
    panel = pd.read_csv(WORK / "PANEL.csv").set_index("task")
    summaries = []
    for arm in ARMS:
        outcomes = scores[scores.arm == arm]
        attempts = search[search.arm == arm]
        successful = outcomes[outcomes.status == "success"]
        summaries.append(dict(arm=arm, search_attempts=len(attempts), search_failures=int((attempts.status != "success").sum()),
                              scoring_attempts=len(outcomes), scoring_failures=int((outcomes.status != "success").sum()),
                              mean_final_loss=successful.final_loss.mean(), successful_tasks=len(successful),
                              search_worker_seconds=attempts.worker_seconds.sum(), scoring_worker_seconds=outcomes.worker_seconds.sum()))
    summary = pd.DataFrame(summaries)
    summary.to_csv(WORK / "SUMMARY.csv", index=False)
    paired, contrasts = [], []
    for child, parent in CONTRASTS:
        left = scores[scores.arm == child].set_index("task")
        right = scores[scores.arm == parent].set_index("task")
        valid = left.index[(left.status == "success") & (right.status == "success")]
        differences = left.loc[valid, "final_loss"] - right.loc[valid, "final_loss"]
        for task in left.index:
            paired.append(dict(contrast=f"{child}-minus-{parent}", task=task, kind=panel.loc[task, "kind"],
                               child_status=left.loc[task, "status"], parent_status=right.loc[task, "status"],
                               child_native_score=left.loc[task, "final_score"] if left.loc[task, "status"] == "success" else np.nan,
                               parent_native_score=right.loc[task, "final_score"] if right.loc[task, "status"] == "success" else np.nan,
                               loss_difference=differences.get(task, np.nan)))
        lower = upper = np.nan
        if len(valid) == 6:
            rng = np.random.default_rng(7342)
            classification = differences.loc[panel.loc[valid].query("kind == 'classification'").index].to_numpy()
            regression = differences.loc[panel.loc[valid].query("kind == 'regression'").index].to_numpy()
            draws = (rng.choice(classification, (10000, 3), replace=True).sum(axis=1) +
                     rng.choice(regression, (10000, 3), replace=True).sum(axis=1))/6
            lower, upper = np.quantile(draws, [.025, .975])
        contrasts.append(dict(contrast=f"{child}-minus-{parent}", paired_tasks=len(valid), mean_loss_difference=differences.mean(),
                              ci_lower=lower, ci_upper=upper, quality_better=int((differences < -1e-12).sum()),
                              quality_tied=int((differences.abs() <= 1e-12).sum()), quality_worse=int((differences > 1e-12).sum())))
    pd.DataFrame(paired).to_csv(WORK / "PAIRED-TASKS.csv", index=False)
    contrasts = pd.DataFrame(contrasts)
    contrasts.to_csv(WORK / "CONTRASTS.csv", index=False)
    display_scores = scores.copy()
    display_scores.loc[display_scores.status != "success", "final_score"] = np.nan
    native = display_scores.pivot(index="task", columns="arm", values="final_score").reindex(columns=ARMS)
    native.insert(0, "metric", ["balanced_accuracy" if panel.loc[t, "kind"] == "classification" else "MAE" for t in native.index])
    native.insert(0, "task_name", [panel.loc[t, "name"] for t in native.index])
    native.to_csv(WORK / "NATIVE-SCORES.csv")
    lines = ["# Matched procedure comparison on six reserved tasks", "",
             "All procedures received the same four starting probes and eight search attempts. "
             "The source and choices were frozen before final scoring. Lower normalized loss is better; "
             "the native classification metric is balanced accuracy and the regression metric is MAE.", "",
             "## Final task scores", "", "| Task | Metric | Fixed | Random | Memory | Parent | Harness | Updater |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for task, row in native.iterrows():
        values = [f"{row[arm]:.6f}" if pd.notna(row[arm]) else "Missing" for arm in ARMS]
        lines.append(f"| {task}: {row.task_name} | {row.metric} | " + " | ".join(values) + " |")
    lines.extend(["", "## Prespecified comparisons", "",
                  "Differences below are child minus parent normalized final loss. Negative favors the child. "
                  "Intervals use a stratified task bootstrap and are exploratory with only three tasks of each kind. "
                  "They do not correct for multiple comparisons or establish general superiority.", "",
                  "| Contrast | Mean difference | Descriptive 95% interval | Better / tied / worse |", "|---|---:|---|---|"])
    for row in contrasts.itertuples():
        interval = f"[{row.ci_lower:+.6f}, {row.ci_upper:+.6f}]" if row.paired_tasks == 6 else f"Not reported; {row.paired_tasks}/6 complete pairs"
        lines.append(f"| {row.contrast} | {row.mean_loss_difference:+.6f} | {interval} | {row.quality_better} / {row.quality_tied} / {row.quality_worse} |")
    lines.extend(["", "## Actual work and scope", "",
                  f"Search: {len(search)} admitted attempts, {(search.status != 'success').sum()} failures or invalid outcomes, {search.worker_seconds.sum():.3f} worker-process seconds. "
                  f"Final scoring: {len(scores)} charged refits, {(scores.status != 'success').sum()} failures or invalid outcomes, {scores.worker_seconds.sum():.3f} worker-process seconds.", "",
                  "Each procedure actually spent eight search fits per task. This study cannot claim fewer fits. "
                  "The preceding 96 development fits, replay work and unmetered coding-agent inference are additional. "
                  "Worker time excludes the complete research and orchestration cost.", "",
                  "The root coding agent authored the harness and updater revisions; a bounded program generated "
                  "the inner proposals. Later skill use and source inheritance are observable. The study does not "
                  "establish autonomous invention, post-promotion deployment, sustained acceleration or a reproduction "
                  "of each named research system. The six public tasks are classroom adaptations.", ""])
    (WORK / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(contrasts.to_string(index=False))
    print(f"All {len(search)+len(scores)} admitted search/scoring attempts included")


if __name__ == "__main__":
    main()
