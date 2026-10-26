"""Compare harnesses on every split: the table each improvement lab ends with."""

from pathlib import Path

from . import course, evaluate, improve, bench


def product(run):
    best = (Path(run) / "BEST").read_text(encoding="utf-8").strip()
    return Path(run) / best / "harness", best


def splits_table(harnesses, base=course.H0, replicas=(0, 1, 2, 3), splits=("evolve", "heldout", "ood")):
    """harnesses: {label: dir}. Prints norm per split and the paired difference against base."""
    base_res = {s: evaluate.evaluate(base, bench.SPLITS[s], replicas) for s in splits}
    rows = [["h0 (start)"] + [f"{base_res[s].score:.3f}" for s in splits] + ["", f"{base_res['evolve'].cost:,.0f}"]]
    diffs = {}
    for label, hdir in harnesses.items():
        res = {s: evaluate.evaluate(hdir, bench.SPLITS[s], replicas) for s in splits}
        diffs[label] = {s: evaluate.paired_diff(res[s], base_res[s]) for s in splits}
        rows.append([label] + [f"{res[s].score:.3f} ({diffs[label][s]['mean']:+.3f})" for s in splits]
                    + [f"{res['evolve'].score - res['ood'].score:+.3f}", f"{res['evolve'].cost:,.0f}"])
    course.table(rows, ["harness"] + [f"{s} norm (vs h0)" for s in splits] + ["evolve - ood", "cost/attempt"])
    for label, d in diffs.items():
        for s in splits:
            print(f"  {label:24s} {s:8s} {evaluate.fmt_diff(d[s])}")
    print()
    return diffs


def lineage_table(run):
    best = (Path(run) / "BEST").read_text(encoding="utf-8").strip()
    rows = []
    for c in improve.lineage(run, best):
        m = c["meta"]
        rows.append([c["id"], m.get("round", 0), f"{c.get('result', {}).get('score', float('nan')):.3f}",
                     "; ".join(m.get("edit_summary", [])) or "(start)"])
    course.table(rows, ["candidate", "round", "evolve norm", "edits that were kept"])


def decisions(run):
    counts = {}
    for c in improve.candidates(run)[1:]:
        d = c["meta"].get("decision", "?")
        key = ("rejected by critic" if "mentions" in d else
               "accepted" if d == "accepted" else
               "rejected: lost the round" if "another candidate" in d else
               "rejected by acceptance rule" if d == "rejected" else d[:40])
        counts[key] = counts.get(key, 0) + 1
    return counts
