"""Honest measurement: replicas, paired comparisons, a noise band, and cost.

The unit of evidence is a cell: one competition x one replica. A harness is
scored by the mean, over cells, of `beats`: the fraction of real Kaggle teams
its final submission would have beaten. Every claim in the course goes through
`evaluate` and `paired_diff`.
"""

import json
import random
import statistics
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from . import agent

COST_PER_EXEC_SECOND = 50  # tokens: one CPU-second of training is priced like 50 model tokens


@dataclass
class Result:
    cells: dict                    # "competition/r<k>" -> beats
    tokens: float                  # mean model tokens per attempt
    exec_seconds: float            # mean training seconds per attempt
    above_median: float            # fraction of cells above the Kaggle median
    valid: float                   # fraction of cells with a gradable submission
    attempts: list = field(default_factory=list, repr=False)

    @property
    def score(self):
        return statistics.fmean(self.cells.values())

    @property
    def cost(self):
        return self.tokens + COST_PER_EXEC_SECOND * self.exec_seconds

    def per_competition(self):
        out = {}
        for k, v in self.cells.items():
            out.setdefault(k.split("/")[0], []).append(v)
        return {k: statistics.fmean(v) for k, v in out.items()}

    def __str__(self):
        return (f"beats {self.score:.3f}  above-median {self.above_median:.2f}  valid {self.valid:.2f}  "
                f"tokens {self.tokens:7.0f}  train-s {self.exec_seconds:6.1f}")

    def to_json(self):
        return {"score": self.score, "cost": self.cost, "cells": self.cells, "tokens": self.tokens,
                "exec_seconds": self.exec_seconds, "above_median": self.above_median, "valid": self.valid}


def evaluate(harness, competitions, replicas=(0, 1), jobs=6, workdir=None, progress=None, save_to=None,
             obfuscate=False):
    """Run every (competition, replica) cell once with the harness (a dict or a directory).

    obfuscate=True swaps in MLE-bench's rewritten descriptions: same task, no competition name.
    """
    h = agent.load_harness(harness) if isinstance(harness, (str, Path)) else harness
    if obfuscate:
        h = {**h, "config": {**h["config"], "obfuscate": True}}
    workdir = Path(workdir or tempfile.mkdtemp(prefix="rsi-run-"))
    cells = [(c, r) for c in competitions for r in replicas]
    with ThreadPoolExecutor(jobs) as pool:
        attempts = list(pool.map(lambda cr: agent.solve(h, cr[0], cr[1], workdir, progress), cells))
    res = Result(
        cells={f"{a.competition}/r{a.replica}": a.final["beats"] for a in attempts},
        tokens=statistics.fmean(a.tokens for a in attempts),
        exec_seconds=statistics.fmean(a.exec_seconds for a in attempts),
        above_median=statistics.fmean(bool(a.final["above_median"]) for a in attempts),
        valid=statistics.fmean(bool(a.final["valid"]) for a in attempts),
        attempts=attempts,
    )
    if save_to:
        save_to = Path(save_to)
        (save_to / "attempts").mkdir(parents=True, exist_ok=True)
        (save_to / "result.json").write_text(json.dumps(res.to_json(), indent=1), encoding="utf-8")
        for a in attempts:
            (save_to / "attempts" / f"{a.competition}-r{a.replica}.json").write_text(
                json.dumps(a.to_json(), indent=1), encoding="utf-8")
    return res


def paired_diff(new, old, n_boot=4000, seed=0):
    """Mean cell difference new - old with a 95% bootstrap interval, plus wins/ties/losses."""
    keys = sorted(set(new.cells) & set(old.cells))
    diffs = [new.cells[k] - old.cells[k] for k in keys]
    rng = random.Random(seed)
    boots = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n_boot))
    wins = sum(d > 0.005 for d in diffs)
    losses = sum(d < -0.005 for d in diffs)
    return {"mean": statistics.fmean(diffs), "lo": boots[int(0.025 * n_boot)], "hi": boots[int(0.975 * n_boot) - 1],
            "wins": wins, "ties": len(diffs) - wins - losses, "losses": losses, "n": len(diffs)}


def noise_band(result):
    """Two standard errors of the mean cell score: differences smaller than this are noise."""
    v = list(result.cells.values())
    return 2 * statistics.stdev(v) / len(v) ** 0.5 if len(v) > 1 else 0.0


def verdict(d):
    if d["lo"] > 0:
        return "better (interval above zero)"
    if d["hi"] < 0:
        return "worse (interval below zero)"
    return "not established (interval includes zero)"


def fmt_diff(d):
    return (f"{d['mean']:+.3f}  95% CI [{d['lo']:+.3f}, {d['hi']:+.3f}]  W/T/L {d['wins']}/{d['ties']}/{d['losses']}"
            f"  (n={d['n']} cells) -> {verdict(d)}")
