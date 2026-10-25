"""Independently check experience identities, peer exclusions and replay arithmetic."""
import hashlib
from pathlib import Path
import re
import shutil

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
work = ROOT.parent / "rsi-work-2026-09-22-tabular-memory"
checks = []


def require(name, condition):
    checks.append(dict(check=name, passed=bool(condition)))
    if not condition:
        pd.DataFrame(checks).to_csv(work / "MEMORY-CHECKS.csv", index=False)
        raise AssertionError(name)


experience = pd.read_csv(work / "EXPERIENCE.csv")
profiles = pd.read_csv(work / "PROFILES.csv")
traces = pd.read_csv(work / "REPLAY-TRACE.csv")
outcomes = pd.read_csv(work / "REPLAY-OUTCOMES.csv")
require("development_only", set(experience.task) == {3, 16, 28, 361234, 361236, 361244})
require("all_attempts", len(experience) == 96 and (experience.groupby("task").size() == 16).all())
for item in pd.read_csv(work / "INPUT-IDENTITIES.csv").itertuples():
    directory = ROOT / "rsi/evidence/2026-09-22" / item.archive
    require(f"{item.archive}/identity", hashlib.sha256((directory / "ARCHIVE-MANIFEST.csv").read_bytes()).hexdigest() == item.manifest_sha256)
    prefix = {"real-tabular-baseline": "base", "real-tabular-revision-1": "one", "real-tabular-revision-2": "two"}[item.archive]
    for row in pd.read_csv(directory / "LEDGER.csv").itertuples():
        record = experience[(experience.task == row.task) & (experience.candidate == prefix+":"+row.candidate)]
        require(f"{item.archive}/{row.attempt}/outcome", len(record) == 1 and record.iloc[0].status == row.status and
                np.isclose(record.iloc[0].selection_loss, row.selection_loss, rtol=1e-12, atol=1e-12))
require("lookup_allocation", len(traces) == 144 and set(traces.alpha) == {0., .5, 1.})
dimensions = ["categorical", "features", "rows", "zero_target"]
for (alpha, task), trace in traces.groupby(["alpha", "task"]):
    require(f"{alpha}/{task}/eight_unique", trace.step.tolist() == list(range(1, 9)) and trace.candidate.nunique() == 8)
    profile = profiles[profiles.task == task].iloc[0]
    peers = profiles[(profiles.kind == profile.kind) & (profiles.task != task)]
    require(f"{alpha}/{task}/held_out", len(peers) == 2 and all(set(map(int, value.split("|"))) == set(peers.task) for value in trace.memory_tasks))
    weights = {}
    for peer in peers.itertuples():
        distance = sum((float(getattr(peer, col))-float(profile[col]))**2 for col in dimensions)**.5
        weights[peer.task] = 1/(.1+distance)
    total = sum(weights.values())
    weights = {key: (1-alpha)/len(peers) + alpha*value/total for key,value in weights.items()}
    rankings = {}
    for peer_id in peers.task:
        scores = experience[experience.task == peer_id].set_index("candidate").selection_loss.rank(method="average")
        for candidate, rank in scores.items():
            rankings[candidate] = rankings.get(candidate, 0) + weights[peer_id]*rank
    ordered = sorted(rankings, key=lambda c: (rankings[c], c))
    prefix = (["base:linear", "base:extra-trees", "base:rbf-1", "base:hist-boost"] if profile.kind == "classification"
              else ["one:median-reference", "base:linear", "base:random-forest", "base:rbf-1"])
    expected = prefix + [c for c in ordered if c not in prefix][:4]
    require(f"{alpha}/{task}/selection_without_outcome", trace.candidate.tolist() == expected)
    observed = experience[experience.task == task].set_index("candidate").selection_loss
    values = np.array([observed[c] for c in expected])
    require(f"{alpha}/{task}/revealed_outcomes", np.allclose(trace.loss_revealed, values, rtol=1e-12, atol=1e-12))
    require(f"{alpha}/{task}/best_path", np.allclose(trace.best_loss, np.minimum.accumulate(values), rtol=1e-12, atol=1e-12))
    result = outcomes[(outcomes.alpha == alpha) & (outcomes.task == task)]
    require(f"{alpha}/{task}/result", len(result) == 1 and np.isclose(result.iloc[0].best_loss, min(values), rtol=1e-12, atol=1e-12))
summary = pd.read_csv(work / "REPLAY-SUMMARY.csv")
expected = outcomes.groupby("alpha", as_index=False).best_loss.mean().sort_values(["best_loss", "alpha"])
require("summary", np.allclose(summary, expected, rtol=1e-12, atol=1e-12))
chosen = float(re.search(r"weight alpha: ([0-9.]+)", (work / "SELECTED-POLICY.md").read_text()).group(1))
require("selected_weight", chosen == float(expected.iloc[0].alpha))
require("no_model_outputs", not (work / "attempts").exists() and not list(work.rglob("final.csv")))
pd.DataFrame(checks).to_csv(work / "MEMORY-CHECKS.csv", index=False)
shutil.copyfile(Path(__file__), work / "source" / Path(__file__).name)
print(f"{len(checks)} memory/replay checks passed; 144 lookups; zero new fits")
