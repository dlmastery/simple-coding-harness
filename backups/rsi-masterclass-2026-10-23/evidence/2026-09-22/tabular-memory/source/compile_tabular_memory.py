"""Compile verified development experience and replay bounded selectors without new fits."""
import hashlib
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PREFIX = {
    "classification": ["base:linear", "base:extra-trees", "base:rbf-1", "base:hist-boost"],
    "regression": ["one:median-reference", "base:linear", "base:random-forest", "base:rbf-1"],
}


def profile(schema, train, kind):
    fields = schema[schema.role == "feature"]
    target, = schema[schema.role == "target"].column.tolist()
    return np.array([
        2 * float((fields.kind == "categorical").mean()),
        np.log1p(len(fields)) / np.log(66),
        .5 * np.log1p(len(train)) / np.log(2401),
        2 * float((train[target] == 0).mean()) if kind == "regression" else 0.,
    ])


def ranked_candidates(scores, profiles, kind, query, alpha, exclude_task=None):
    peers = profiles[(profiles.kind == kind) & (profiles.task != exclude_task)].copy()
    if len(peers) == 0:
        raise ValueError("No development peers")
    dimensions = ["categorical", "features", "rows", "zero_target"]
    distance = np.linalg.norm(peers[dimensions].to_numpy() - query, axis=1)
    local = 1 / (.1 + distance)
    local /= local.sum()
    weights = (1-alpha) / len(peers) + alpha * local
    memory = scores[scores.task.isin(peers.task)].copy()
    memory["rank"] = memory.groupby("task").selection_loss.rank(method="average", ascending=True)
    memory["weight"] = memory.task.map(dict(zip(peers.task, weights)))
    memory["weighted_rank"] = memory["rank"] * memory.weight
    ordered = memory.groupby("candidate", as_index=False).weighted_rank.sum().sort_values(["weighted_rank", "candidate"])
    return ordered.candidate.tolist()


def main():
    work = ROOT.parent / "rsi-work-2026-09-22-tabular-memory"
    if work.exists():
        raise ValueError("Preserve previous memory compilation")
    work.mkdir()
    source = work / "source"
    source.mkdir()
    shutil.copyfile(Path(__file__), source / Path(__file__).name)
    protocol = ROOT / "how-did-i-generate-it/rsi/validation/TABULAR-MEMORY-REPLAY-PROTOCOL.md"
    shutil.copyfile(protocol, source / protocol.name)
    (work / "SOURCE-FREEZE.md").write_text("# Compiler frozen before replay\n\n" + "\n".join(
        f"{p.name}: {hashlib.sha256(p.read_bytes()).hexdigest()}" for p in sorted(source.iterdir())) + "\n")
    base = ROOT / "rsi/evidence/2026-09-22"
    records, provenance = [], []
    for name, prefix, checks in (("real-tabular-baseline", "base", "BASELINE-CHECKS.csv"),
                                  ("real-tabular-revision-1", "one", "REVISION-CHECKS.csv"),
                                  ("real-tabular-revision-2", "two", "REVISION-CHECKS.csv")):
        directory = base / name
        if not pd.read_csv(directory / checks).passed.all():
            raise ValueError("Experience requires passing independent checks")
        for item in pd.read_csv(directory / "ARCHIVE-MANIFEST.csv").itertuples():
            path = directory / item.path
            if hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256:
                raise ValueError(f"Experience archive changed: {path}")
        for row in pd.read_csv(directory / "LEDGER.csv").itertuples():
            loss = float(row.selection_loss) if row.status == "success" else float("inf")
            records.append(dict(task=row.task, kind=row.kind, candidate=prefix+":"+row.candidate,
                                selection_loss=loss, status=row.status, worker_seconds=row.worker_seconds))
        provenance.append(dict(archive=name, manifest_sha256=hashlib.sha256((directory / "ARCHIVE-MANIFEST.csv").read_bytes()).hexdigest(),
                               checks_sha256=hashlib.sha256((directory / checks).read_bytes()).hexdigest()))
    scores = pd.DataFrame(records)
    if len(scores) != 96 or not (scores.groupby("task").size() == 16).all():
        raise ValueError("Expected all 96 charged development attempts")
    if set(scores.task) != {3, 16, 28, 361234, 361236, 361244}:
        raise ValueError("Only declared development tasks may enter memory")
    scores.to_csv(work / "EXPERIENCE.csv", index=False)
    pd.DataFrame(provenance).to_csv(work / "INPUT-IDENTITIES.csv", index=False)
    profiles = []
    for task in pd.read_csv(base / "real-tabular-baseline/PANEL.csv").itertuples():
        directory = base / "real-tabular-baseline/public" / str(task.task)
        schema = pd.read_csv(directory / "SCHEMA.csv")
        train = pd.read_csv(directory / "train.csv")
        vector = profile(schema, train, task.kind)
        profiles.append(dict(task=task.task, kind=task.kind, categorical=vector[0], features=vector[1], rows=vector[2], zero_target=vector[3]))
    profiles = pd.DataFrame(profiles)
    profiles.to_csv(work / "PROFILES.csv", index=False)
    traces, outcomes = [], []
    for alpha in (0., .5, 1.):
        for row in profiles.itertuples():
            query = np.array([row.categorical, row.features, row.rows, row.zero_target])
            choices = PREFIX[row.kind].copy()
            ranked = ranked_candidates(scores, profiles, row.kind, query, alpha, exclude_task=row.task)
            choices.extend(candidate for candidate in ranked if candidate not in choices)
            choices = choices[:8]
            world = scores[scores.task == row.task].set_index("candidate")
            best = float("inf")
            for index, candidate in enumerate(choices, 1):
                if candidate not in world.index:
                    raise ValueError("Replay queried an unrecorded candidate")
                # The held-out development task's outcome is revealed only
                # after its next choice was fixed by other tasks' memory.
                loss = float(world.loc[candidate, "selection_loss"])
                best = min(best, loss)
                traces.append(dict(alpha=alpha, task=row.task, step=index, candidate=candidate, loss_revealed=loss, best_loss=best,
                                   memory_tasks="|".join(str(t) for t in profiles[(profiles.kind == row.kind) & (profiles.task != row.task)].task)))
            outcomes.append(dict(alpha=alpha, task=row.task, kind=row.kind, best_loss=best, lookups=8))
    pd.DataFrame(traces).to_csv(work / "REPLAY-TRACE.csv", index=False)
    outcomes = pd.DataFrame(outcomes)
    outcomes.to_csv(work / "REPLAY-OUTCOMES.csv", index=False)
    means = outcomes.groupby("alpha", as_index=False).best_loss.mean().sort_values(["best_loss", "alpha"])
    means.to_csv(work / "REPLAY-SUMMARY.csv", index=False)
    chosen = float(means.iloc[0].alpha)
    (work / "SELECTED-POLICY.md").write_text(
        "# Retained replay policy\n\n"
        f"Local-memory weight alpha: {chosen:g}\nBudget: eight candidate attempts\n"
        "Tie rule: smaller alpha. Lookup cost is separate from any later fitting cost.\n\n"
        "Four common broad probes precede four ranked candidates. The rank combines "
        "equal-weight experience with feature-profile proximity; it never uses a dataset name. "
        "The chosen weight minimizes mean leave-one-development-task-out normalized selection loss. "
        "Only two same-kind peers support each replay fold. This tiny pool can overfit, and the "
        "weight was itself selected on the six development outcomes. It needs new-task evaluation.\n\n"
        "This is recorded-candidate replay, not a new reproduction of Dream-RSI's simulator "
        "or its full branching discovery process. The course's separately archived tree study "
        "tests those additional mechanisms. No new models were fitted here.\n", encoding="utf-8")
    (work / "MEMORY.md").write_text(
        "# Experience retained after independent outcome checks\n\n"
        "96 attempted development fits are represented, including every source generation. "
        "The root coding agent interprets these checked outcomes; the verifier certifies "
        "numbers and identities, not the truth of a generalized lesson.\n\n"
        "Keep a median reference for regression. Numeric scaling is a model choice, not "
        "a universal improvement. Native categorical masks differ from treating category "
        "codes as numeric distances. Aligning loss can help but did not repair every task. "
        "Target transformations and extra capacity also produced regressions.\n\n"
        "The executable retrieval interface uses task kind, categorical fraction, feature "
        "count, training rows and the training zero-target fraction. No current run budget, "
        "pending action or final labels belong in this store. Freeze this memory when "
        "comparing its later effect. Keep later task working state separately.\n", encoding="utf-8")
    print(means.to_string(index=False))
    print(f"Selected alpha={chosen:g}; 144 replay lookups; zero new fits")


if __name__ == "__main__":
    main()
