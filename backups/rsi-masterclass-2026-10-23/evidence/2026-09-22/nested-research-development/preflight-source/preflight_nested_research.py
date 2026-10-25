"""Exercise complete researcher control flow with labelled synthetic outcomes; zero fits."""
import argparse
from pathlib import Path
import shutil

import pandas as pd

from run_nested_research import ARMS, load, sha, support, workspace


def check(phase):
    work = workspace(phase)
    support(work).verify_manifest(work, work / "STUDY-FREEZE.csv")
    engine = load("preflight_engine", work / "source/refinement_engine.py")
    checks, trace = [], []
    completed = False

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    try:
        for task in pd.read_csv(work / "PANEL.csv").itertuples():
            schema = pd.read_csv(work / "public" / str(task.task) / "SCHEMA.csv")
            for arm in ARMS[phase]:
                module = load("preflight_researcher", work / "researchers" / arm / "researcher.py")
                for favored in ("kernel", "forest", "linear", "reference"):
                    label = f"{task.task}/{arm}/{favored}"
                    seen, actual, rejections = set(), [], []

                    def execute(plan, serial, step):
                        candidate = engine.build_recipe(schema, task.kind, plan["template"], plan["factor"])
                        signature = engine.constructor_signature(candidate)
                        if signature in seen:
                            return dict(status="duplicate-constructor", constructor_sha256=signature)
                        seen.add(signature)
                        # Synthetic scores test control flow only, never empirical efficacy.
                        loss = (.1 if module.family(plan["template"]) == favored else .4) + step*.0001
                        result = dict(step=step, status="success", train_loss=loss-.2, selection_loss=loss,
                                      task=task.task, kind=task.kind, arm=arm, serial=serial, **plan)
                        actual.append(result)
                        return result

                    history, chosen = module.research(task.task, task.kind, False, execute,
                                                       lambda plan, serial, result: rejections.append((plan, serial, result)))
                    require(label + "/twelve_attempts", len(history) == 12 and history == actual)
                    require(label + "/selection", chosen == min(history, key=lambda row: (row["selection_loss"], row["step"])))
                    require(label + "/bounded_proposals", len(history) + len(rejections) <= 128)
                    require(label + "/constructor_uniqueness", len(seen) == 12)
                    require(label + "/common_coverage", [row["template"] for row in history[:8]] == module.PREFIX[task.kind])
                    require(label + "/parent_order", all(0 <= row["parent_step"] < row["step"] for row in history))
                    require(label + "/applicability", not any(row["template"] in {"two:log-boost", "two:log-svr"} for row in history))
                    trace.extend(dict(fixture=favored, **row) for row in history)
                failed = []

                def failure(plan, serial, step):
                    result = dict(**plan, serial=serial, step=step, status="timeout")
                    failed.append(result)
                    return result

                try:
                    module.research(task.task, task.kind, False, failure, lambda *_: None)
                    require(f"{task.task}/{arm}/all_failed_refused", False)
                except ValueError:
                    require(f"{task.task}/{arm}/all_failed_refused", 8 <= len(failed) <= 12 and all(row["status"] == "timeout" for row in failed))
        require("distinct_researchers", len({sha(work / 'researchers' / arm / 'researcher.py') for arm in ARMS[phase]}) == len(ARMS[phase]))
        # The later rejection path must emit a full executable loop with four
        # breadth slots, rather than only editing a prose or configuration file.
        if phase == "development":
            output = work / "preflight-generations"
            i1 = load("preflight_i1", work / "source/i1.py")
            child = i1.generate(work / "researchers/i1/researcher.py", work / "prior-comparison/SEARCH-LEDGER.csv", 2, True, output)
            generated = load("preflight_rejected_child", child)
            require("rejected_child_recovery", generated.BREADTH == 4 and callable(generated.research))
        pd.DataFrame(trace).to_csv(work / "PREFLIGHT-FIXTURE-TRACE.csv", index=False)
        source = work / "preflight-source"
        source.mkdir(exist_ok=True)
        shutil.copyfile(Path(__file__), source / Path(__file__).name)
        completed = True
    finally:
        checks.append(dict(check="preflight_completed", passed=completed))
        pd.DataFrame(checks).to_csv(work / "PREFLIGHT-CHECKS.csv", index=False)
        pd.DataFrame(trace).to_csv(work / "PREFLIGHT-FIXTURE-TRACE.csv", index=False)
    (work / "PREFLIGHT-COMPLETE.md").write_text("# Preflight complete\n\nSynthetic outcomes only; zero model fits.\n")
    print(f"{len(checks)} preflight checks passed; fixture outcomes only; zero fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=list(ARMS))
    check(parser.parse_args().phase)
