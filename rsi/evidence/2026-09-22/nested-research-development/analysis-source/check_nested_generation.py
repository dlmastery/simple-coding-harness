"""Independently check the outer verdict and later source inheritance; zero fits."""
import ast
from pathlib import Path
import shutil

import pandas as pd

from run_nested_research import load, sha, support, workspace


def check():
    work = workspace("development")
    support(work).verify_manifest(work, work / "GENERATION-TWO-FREEZE.csv")
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    complete = False
    try:
        scores = pd.read_csv(work / "SCORES.csv").pivot(index="task", columns="arm", values="final_loss")
        ledger = pd.read_csv(work / "SEARCH-LEDGER.csv")
        verdicts = pd.read_csv(work / "VERDICTS.csv").set_index("improver")
        descendants = pd.read_csv(work / "GENERATION-TWO.csv").set_index("improver")
        for version in ("i0", "i1"):
            differences = scores[version]-scores.parent
            promoted = differences.mean() <= -.002 and int((differences <= 1e-12).sum()) >= 4
            record = verdicts.loc[version]
            require(version + "/outer_gate", bool(record.promote) == promoted and record.nonworse == int((differences <= 1e-12).sum()))
            parent = work / "researchers" / (version if promoted else "parent") / "researcher.py"
            directory = work / "generations/2" / version
            require(version + "/retained_parent", sha(directory / "PARENT.py") == sha(parent) == descendants.loc[version, "parent_sha256"])
            child = directory / "researcher.py"
            require(version + "/child_identity", sha(child) == descendants.loc[version, "child_sha256"])
            description = (directory / "GENERATION.md").read_text()
            for label, source in (("Parent", parent), ("Improver", work / "source/improver.py"),
                                  ("Evidence", work / "SEARCH-LEDGER.csv"), ("Invoked version entry", work / "source" / (version + ".py"))):
                require(version + "/" + label, f"{label} SHA256: {sha(source)}" in description)
            module = load("checked_second_generation", child)
            require(version + "/executable_researcher", callable(module.research) and callable(module.adaptive))
            if version == "i0":
                tree = ast.parse(parent.read_text())
                inherited, = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name) and target.id == "FIRST_FACTOR" for target in node.targets)]
                evidence = ledger[(ledger.status == "success") & (ledger.step > 8) & (ledger.factor != 1) & (ledger.parent_step > 0)]
                mean_gap = (evidence.selection_loss-evidence.train_loss).mean()
                expected = max(.125, inherited/2) if mean_gap > .15 else min(8., inherited*2)
                require(version + "/inherited_multiplier", module.FIRST_FACTOR == expected)
            else:
                require(version + "/verdict_changes_rewrite", module.BREADTH == (2 if promoted else 4))
                evidence = ledger[(ledger.status == "success") & (ledger.step > 8)].copy()
                for kind in ("classification", "regression"):
                    subset = evidence[evidence.kind == kind].copy()
                    subset["rank"] = subset.groupby("task").selection_loss.rank(method="average")
                    ranking = subset.groupby("template")["rank"].mean().sort_values(kind="stable").index.tolist()
                    require(version + "/updated_ranking/" + kind, module.RANKING[kind] == ranking)
                require(version + "/changed_proposer", "alternate two checked families" in child.read_text())
        shutil.copyfile(Path(__file__), work / "analysis-source" / Path(__file__).name)
        complete = True
    finally:
        checks.append(dict(check="generation_audit_completed", passed=complete))
        pd.DataFrame(checks).to_csv(work / "GENERATION-CHECKS.csv", index=False)
    print(f"{len(checks)} later-generation checks passed; zero new fits")


if __name__ == "__main__":
    check()
