"""Apply the fixed development gate, then invoke each inherited improver again."""
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from run_nested_research import generate, sha, support, workspace


def main():
    work = workspace("development")
    helper = support(work)
    helper.verify_manifest(work, work / "STUDY-FREEZE.csv")
    helper.verify_manifest(work, work / "CHOICE-FREEZE.csv")
    checks = pd.read_csv(work / "FINAL-CHECKS.csv")
    if checks.empty or not checks.passed.all() or not (work / "SCORING-COMPLETE.md").exists():
        raise ValueError("Complete independently checked development required")
    if (work / "VERDICTS.csv").exists() or (work / "generations/2").exists():
        raise ValueError("Later generation already exists; preserve it")
    scores = pd.read_csv(work / "SCORES.csv")
    if len(scores) != 18 or not scores.status.eq("success").all():
        raise ValueError("Every declared researcher must have a valid outer score")
    table = scores.pivot(index="task", columns="arm", values="final_loss")
    decisions = []
    for version in ("i0", "i1"):
        delta = table[version]-table.parent
        gain = float(delta.mean())
        nonworse = int((delta <= 1e-12).sum())
        promote = gain <= -.002 and nonworse >= 4
        decisions.append(dict(improver=version, mean_loss_change=gain, nonworse=nonworse,
                              better=int((delta < -1e-12).sum()), worse=int((delta > 1e-12).sum()),
                              promote=promote, retained=version if promote else "parent"))
    pd.DataFrame(decisions).to_csv(work / "VERDICTS.csv", index=False)
    descendants = []
    for decision in decisions:
        parent = work / "researchers" / decision["retained"] / "researcher.py"
        child = generate(work, decision["improver"], 2, parent, work / "SEARCH-LEDGER.csv", not decision["promote"])
        descendants.append(dict(improver=decision["improver"], parent_sha256=sha(parent), child_sha256=sha(child),
                                changed=sha(parent) != sha(child), source=child.relative_to(work).as_posix()))
    pd.DataFrame(descendants).to_csv(work / "GENERATION-TWO.csv", index=False)
    source = work / "analysis-source"
    source.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__), source / Path(__file__).name)
    paths = [work / name for name in ("SEARCH-LEDGER.csv", "SCORES.csv", "FINAL-CHECKS.csv", "VERDICTS.csv", "GENERATION-TWO.csv")]
    paths += sorted(path for path in (work / "generations/2").rglob("*") if path.is_file())
    helper.manifest(work, work / "GENERATION-TWO-FREEZE.csv", paths)
    print(pd.DataFrame(decisions).to_string(index=False))
    print("Both inherited improvers generated a later complete researcher; zero new fits")


if __name__ == "__main__":
    main()
