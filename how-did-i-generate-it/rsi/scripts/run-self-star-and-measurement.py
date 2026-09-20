"""Agent-written execution and labelled replay for the self-* teaching sequence."""
import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--phase", choices=["all", "correction-replay", "memory"], default="all")
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.workspace.resolve()
    helper_path = repo / "how-did-i-generate-it/rsi/scripts/run-loops-and-systems.py"
    spec = importlib.util.spec_from_file_location("walkthrough_helpers", helper_path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    save, sha, rows, table = helpers.save, helpers.digest, helpers.read_rows, helpers.table
    if args.phase == "correction-replay":
        procedure = (out / "07-01/FIXED-REPORTER.md").read_text(encoding="utf-8")
        assert "Repeat the supplied summary score." in procedure
        save(out / "07-01/LATER-WRONG-REPORT.md", "# Labelled second report fixture\n\nSupplied MAE: 2. The unchanged reporting procedure repeats it without a check.\n")
        save(out / "07-01/LATER-TRACE.md", f"# Separate-process replay\n\nRead unchanged procedure SHA-256 {sha(out / '07-01/FIXED-REPORTER.md')}. Repeated supplied score 2. Earlier output correction was not loaded as a reusable rule. This is a deterministic reporter, not a fresh LLM session.\n")
        return
    if args.phase == "memory":
        memory = (out / "07-03/MEMORY-v1.md").read_text(encoding="utf-8")
        assert "Use the declared metric direction." in memory
        options = rows(out / "07-03/OPTIONS.csv")
        direction = (out / "07-03/TASK.md").read_text()
        assert "Direction: maximize" in direction
        chosen = max(options, key=lambda r: float(r["score"]))
        save(out / "07-03/DECISION.md", f"# Memory-guided choice before lookup\n\nMemory SHA-256: {sha(out / '07-03/MEMORY-v1.md')}\n\nRead the task's maximize direction. Selected candidate: {chosen['candidate']}. This is a decision over cached checked options, not another model fit.\n")
        table(out / "07-03/DECISION.csv", [{"candidate": chosen["candidate"], "score": chosen["score"], "memory_sha256": sha(out / "07-03/MEMORY-v1.md")}])
        return

    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    source = repo / "rsi/evidence/2026-09-20"
    sys.path.insert(0, str(repo / "rsi/tools"))
    import lab
    import check_result
    import numpy as np
    import pandas as pd
    from sklearn.metrics import mean_absolute_error, balanced_accuracy_score
    protocol = repo / "how-did-i-generate-it/rsi/validation/SELF-STAR-AND-MEASUREMENT-PROTOCOL.md"
    for origin, name in [(Path(__file__), "driver.source.py"), (helper_path, "helpers.source.py"),
                         (repo / "rsi/tools/lab.py", "lab.source.py"),
                         (repo / "rsi/tools/check_result.py", "checker.source.py"), (protocol, "PROTOCOL.md")]:
        shutil.copyfile(origin, out / name)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    save(out / "SOURCE.md", f"# Source and execution boundary\n\nGit revision: {revision}\n\nDriver SHA-256: {sha(Path(__file__))}\n\nHelper SHA-256: {sha(helper_path)}\n\n{lab.environment()}\n\nSame author context; new files and child processes. Existing public results were known. No learner participated. All cached choices are labelled replays.\n")
    commands, fits, inputs = [], [], []

    def preserve(origin, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, destination)
        inputs.append({"source": origin.relative_to(repo).as_posix(), "copy": destination.relative_to(out).as_posix(), "sha256": sha(origin)})
        assert sha(origin) == sha(destination)
        table(out / "INPUTS.csv", inputs)

    def execute(label, script, arguments):
        command = [sys.executable, str(script), *map(str, arguments)]
        before = time.perf_counter()
        try:
            result = subprocess.run(command, cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=60)
            status, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            status, stdout, stderr = 124, str(error.stdout or ""), str(error.stderr or "")
        elapsed = time.perf_counter() - before
        commands.append({"action": label, "exit": status, "wall_seconds": elapsed})
        save(out / "commands" / f"{len(commands):02d}-{label}.md", f"# {label}\n\nArguments: {command!r}\n\nExit: {status}. Wall seconds: {elapsed:.6f}.\n\n```text\n{stdout}\n```\n\n```text\n{stderr}\n```\n")
        table(out / "COMMANDS.csv", commands)
        print(f"{label}: exit {status}; {elapsed:.2f}s", flush=True)
        if status:
            save(out / "PROGRESS.md", f"# Stopped\n\nUnexpected exit {status}: {label}. Preserve the attempt; no automatic retry.\n")
            raise RuntimeError(label)

    def fit(relative, task, model, skill):
        work = out / relative
        execute(relative.replace("/", "-") + "-" + model, repo / "rsi/tools/lab.py",
                ["run", "--task", task, "--workspace", work, "--model", model,
                 "--features", "calendar" if task == "bike" else "all", "--seed", 17,
                 "--attempt-limit", 2, "--policy", skill,
                 "--hypothesis", f"Execute predeclared {model} under task skill {sha(skill)}; preserve all outcomes."])
        row = rows(work / "trials.csv")[-1]
        candidate = work / row["candidate"]
        execute(relative.replace("/", "-") + "-check-" + candidate.name, repo / "rsi/tools/check_result.py",
                [candidate, "--report", candidate / "CHECK.md"])
        fits.append({"workspace": relative, **row})
        table(out / "ALL-FITS.csv", fits)
        return candidate, row

    # Correct an output; the procedure remains unchanged.
    baseline = source / "loops-and-systems/02-06/arm-a/trial-001"
    baseline_score = check_result.check(baseline)
    preserve(baseline / "predictions.csv", out / "07-01/predictions.csv")
    save(out / "07-01/FIXED-REPORTER.md", "# Deliberately weak fixed reporter\n\nRepeat the supplied summary score. Do not learn or retain a reporting rule. This is a fixture, not a recommended reporting procedure.\n")
    reporter_hash = sha(out / "07-01/FIXED-REPORTER.md")
    save(out / "07-01/ORIGINAL-WRONG-REPORT.md", "# Labelled altered report\n\nClaimed selection MAE: 1. This number was deliberately changed for the correction exercise.\n")
    p = pd.read_csv(out / "07-01/predictions.csv")
    recomputed = float(np.abs(p.actual - p.predicted).mean())
    assert abs(recomputed - baseline_score) < 1e-9
    save(out / "07-01/CORRECTED-REPORT.md", f"# Corrected current output\n\nSelection MAE: {recomputed:.9f}, from {len(p)} saved predictions. Original claimed value: 1.\n")
    execute("07-01-later-fixed-reporter", Path(__file__), ["--repo", repo, "--workspace", out, "--phase", "correction-replay"])
    assert sha(out / "07-01/FIXED-REPORTER.md") == reporter_hash
    save(out / "07-01/CORRECTION.md", f"# Output changed; procedure did not\n\nThe original and corrected reports remain. Recomputed MAE is {recomputed:.9f}. No reusable instruction was edited. The deliberately weak fixed reporter has the same SHA-256 {reporter_hash} and repeated another wrong supplied score in a later process. This shows why an output correction alone need not prevent recurrence. A fresh coding-agent session was not tested.\n")

    # Two targeted checks of existing synthetic evidence, with no final scores.
    reflection = out / "07-02"
    save(reflection / "REFLECTION.md", "# Reflection before replay checks\n\nObserved in the retained 09.05 trace: an unpruned regression tree reached training MAE 0 but had worse selection MAE than the linear parent. Hypothesis: fitting idiosyncratic training variation can hurt unseen-row prediction. Alternative: this task, sample, feature representation, or capacity choice may favor the parent; the trace alone does not identify a universal cause.\n\nProposed narrow rule: compare valid candidates on the declared selection metric and its direction; do not promote solely on training fit. Scope: same task, data role, and evaluator. Counterexample to an overbroad family ban: the retained nonlinear classification case. Check both replayed cases before retention. This is known evidence, not two fresh validation cases.\n")
    reflection_rows = []
    for task in ("regression", "classification"):
        origin = source / "clean-journey/09-05"
        preserve(origin / f"cases/{task}.csv", reflection / f"inputs/{task}-data.csv")
        raw = pd.read_csv(reflection / f"inputs/{task}-data.csv").set_index("source_row")
        values = {}
        for candidate in ("parent", "child"):
            for partition in ("training", "selection"):
                filename = f"{partition}-predictions.csv"
                destination = reflection / f"inputs/{task}-{candidate}-{filename}"
                preserve(origin / f"rounds/{task}/v1/{candidate}/{filename}", destination)
                predictions = pd.read_csv(destination)
                expected = raw[raw.partition == partition]
                assert list(predictions.source_row) == list(expected.index)
                assert np.array_equal(predictions.target.to_numpy(), expected.target.to_numpy())
                metric = mean_absolute_error if task == "regression" else balanced_accuracy_score
                values[f"{candidate}_{partition}"] = float(metric(predictions.target, predictions.prediction))
        child_better = values["child_selection"] < values["parent_selection"] if task == "regression" else values["child_selection"] > values["parent_selection"]
        reflection_rows.append({"task": task, **values, "narrow_rule_keeps": "tree" if child_better else "linear",
                                "always_tree_keeps": "tree", "always_tree_is_better": child_better})
    table(reflection / "TWO-CHECKS.csv", reflection_rows)
    save(reflection / "RETENTION.md", "# Retain a bounded rule\n\nSelection comparison keeps the linear model in regression and the tree in classification. The two replayed cases refute unconditional tree promotion and an unconditional tree ban. Retain metric-based comparison within scope; do not infer that selection feedback cannot itself be overfit. Both cases and their outcomes were already known. No new fit or final evaluation ran.\n")

    # Retained external memory is read by a separate process on a later task.
    public_wine = source / "author-wine"
    wine_scores = {}
    for candidate in ("trial-001", "trial-002"):
        wine_scores[candidate] = check_result.check(public_wine / candidate)
        preserve(public_wine / candidate / "predictions.csv", out / f"07-03/inputs/{candidate}-predictions.csv")
    save(out / "07-03/MEMORY-v1.md", "# Retained comparison rule\n\nUse the declared metric direction. Compare only candidates for the same task, partition, metric, and validity rules. If any of those differ or are missing, request a comparison contract rather than comparing raw numbers. Selection feedback can overfit; this rule does not prove generalization.\n\nSupporting replay: ../07-02/TWO-CHECKS.csv. A tree wins one case and loses another. Do not retain a model-family slogan.\n")
    save(out / "07-03/TASK.md", "# Later decision task\n\nTask: wine classification. Metric: balanced accuracy. Direction: maximize. Partition: the fixed selection rows. Both options passed the supplied source/row/metric checker. These are cached public predictions, not new fits.\n")
    options = [{"candidate": candidate, "score": score, "metric": "balanced accuracy"} for candidate, score in wine_scores.items()]
    table(out / "07-03/OPTIONS.csv", options)
    no_memory = min(options, key=lambda r: r["score"])
    save(out / "07-03/NO-MEMORY-RULE.md", "# Deliberately weak numerical control\n\nSelect the smaller reported number without consulting metric direction. This is a constructed error, not a measured behavior of an unaided language model.\n")
    execute("07-03-read-retained-memory", Path(__file__), ["--repo", repo, "--workspace", out, "--phase", "memory"])
    memory_choice = rows(out / "07-03/DECISION.csv")[0]
    table(out / "07-03/OUTCOMES.csv", [{"procedure": "weak-no-memory", "candidate": no_memory["candidate"], "cached_balanced_accuracy": no_memory["score"]},
                                       {"procedure": "memory-aware", "candidate": memory_choice["candidate"], "cached_balanced_accuracy": memory_choice["score"]}])
    save(out / "07-03/OUT-OF-SCOPE.md", "# Additional scope fixture\n\nInput A: majority overall accuracy 0.871473. Input B: linear balanced accuracy 0.744955. The metrics differ. A scoped memory check returns needs-clarification. Removing that scope check and taking the larger number would choose majority, whose balanced accuracy is only 0.5. This numerical comparison is invalid; it is not a new task result.\n")
    mixed_metrics = {"overall accuracy", "balanced accuracy"}
    table(out / "07-03/SCOPE-CHECK.csv", [{"distinct_metrics": len(mixed_metrics), "scoped_verdict": "needs-clarification" if len(mixed_metrics) != 1 else "ready", "unsafe_larger_number_choice": "majority"}])
    save(out / "07-03/USE-AND-BENEFIT.md", f"# Persistence, use, and observed choice\n\nThe separate process read the saved memory hash and maximize direction before selecting {memory_choice['candidate']}. The constructed no-memory control selected {no_memory['candidate']}. Cached balanced accuracy is {memory_choice['score']} versus {no_memory['score']}. This demonstrates use and the consequence of these explicit rules on known options. It does not measure learning by an LLM, fresh-task generalization, or a trained weight change.\n")

    # Freeze task skills and the improver before all new fits.
    skills = out / "07-04/skills"
    save(skills / "PARENT.md", "# Parent task research skill\n\nFirst choice: constant.\nSecond choice: tree.\nUse the task's allowed input set, seed 17, and two fits. Retain the candidate with the better declared selection metric; keep the earlier candidate on a tie.\n")
    save(skills / "CHILD.md", "# Child task research skill\n\nFirst choice: constant.\nSecond choice: diagnose slices.\nRead the task's predeclared slice map. Use linear if the largest mean absolute baseline residual is at least 1.5 times the smallest; otherwise use tree. Positive divided by zero is infinite; zero divided by zero is treated as ratio 1. Record diagnosis and choice before fitting.\nUse the task's allowed input set, seed 17, and two fits. Retain the candidate with the better declared selection metric; keep the earlier candidate on a tie.\n")
    improver_origin = repo / "rsi/skills/improve-research-skill/SKILL.md"
    preserve(improver_origin, skills / "IMPROVER-FIXED.md")
    improver_hash = sha(improver_origin)
    frozen = {name: sha(skills / f"{name}.md") for name in ("PARENT", "CHILD")}
    table(out / "07-04/FROZEN-SKILLS.csv", [{"version": name, "sha256": value} for name, value in frozen.items()])
    save(out / "07-04/CHANGE-PROPOSAL.md", "# One task-skill edit\n\nThe known calendar tree result is worse than the calendar linear result. The parent chooses a tree unconditionally. Replace only the second-choice instruction with a residual-slice diagnosis that can choose linear. The choice rule is a teaching heuristic, not a causal explanation or optimal model selector.\n\nExpected effect: avoid the known bike weakness. Risk: large residual variation need not imply linear predictability; another task may lose or tie. Falsifier: child retained selection MAE is no better under two fits per arm. On a tie keep the parent task skill. The author proposes the edit using the unchanged canonical improver. Public bike and wine outcomes are already known.\n")
    save(out / "08-05/INTERFACE-MAP.md", "# Interface fixed before the new wine fits\n\nBike: target cnt, minimize MAE, calendar fields, groups by recorded hr. Wine: target quality at least 7, maximize balanced accuracy, all physicochemical fields, groups by alcohol quartiles computed on training features only. Absolute binary residual equals the misclassification indicator. Second-choice threshold and retained skill bytes stay fixed.\n\nA group average of ordinary errors is not a class-balanced error estimate. The diagnosis can disagree with the retention metric. Author knowledge of prior wine outcomes prevents a claim of uncontaminated transfer. This is a frozen-procedure replay with a prespecified interface adapter.\n")
    comparisons = {}
    for task, lab_id in [("bike", "07-04"), ("wine", "08-05")]:
        summary = []
        for version in ("PARENT", "CHILD"):
            skill = skills / f"{version}.md"
            assert sha(skill) == frozen[version]
            relative = f"{lab_id}/{version.lower()}"
            first, first_row = fit(relative, task, "constant", skill)
            text = skill.read_text(encoding="utf-8")
            second_model = "tree"
            if "Second choice: diagnose slices." in text:
                predictions = pd.read_csv(first / "predictions.csv")
                if task == "bike":
                    group = predictions.hour
                    grouping_note = "Recorded hour from the pinned selection rows."
                else:
                    data = lab.read_data("wine")
                    training = lab.partitions(data, "wine")["train"]
                    cuts = np.quantile(data.loc[training, "alcohol"], [0.25, 0.5, 0.75])
                    group = pd.Series(np.digitize(data.iloc[predictions.source_row.to_numpy()].alcohol, cuts, right=True))
                    grouping_note = f"Alcohol cutpoints from training features only: {cuts.tolist()}."
                errors = pd.DataFrame({"group": group, "absolute_error": np.abs(predictions.actual - predictions.predicted)})
                slices = errors.groupby("group").absolute_error.agg(["count", "mean"])
                slices.to_csv(out / relative / "SLICES.csv")
                low, high = float(slices["mean"].min()), float(slices["mean"].max())
                ratio = high / low if low else (float("inf") if high else 1.0)
                second_model = "linear" if ratio >= 1.5 else "tree"
                note = f"{grouping_note} Largest/smallest mean residual: {ratio:.9f}; threshold 1.5."
            else:
                assert "Second choice: tree." in text
                note = "Read unchanged fixed tree choice; no diagnosis needed by this parent."
            save(out / relative / "SECOND-CHOICE.md", f"# Choice before the second fit\n\nSkill SHA-256: {sha(skill)}\n\n{note}\n\nChoose {second_model}. No second-fit result exists yet in this arm.\n")
            second, second_row = fit(relative, task, second_model, skill)
            candidates = [(first, first_row), (second, second_row)]
            selected = min(candidates, key=lambda c: float(c[1]["score"])) if task == "bike" else max(candidates, key=lambda c: float(c[1]["score"]))
            retained_p = pd.read_csv(selected[0] / "predictions.csv")
            recalls = [float((retained_p.loc[retained_p.actual == label, "predicted"] == label).mean()) for label in (0, 1)] if task == "wine" else ["not applicable", "not applicable"]
            summary.append({"skill": version, "first_score": first_row["score"], "second_model": second_model,
                            "second_score": second_row["score"], "retained_candidate": selected[0].name,
                            "retained_score": selected[1]["score"], "class_0_recall": recalls[0], "class_1_recall": recalls[1],
                            "skill_sha256": sha(skill), "improver_sha256": improver_hash})
        table(out / lab_id / "COMPARISON.csv", summary)
        a, b = map(lambda row: float(row["retained_score"]), summary)
        child_better = b < a if task == "bike" else b > a
        selected_skill = "CHILD" if child_better else "PARENT"
        save(out / lab_id / "DECISION.md", f"# Fixed external acceptance\n\nParent retained: {a:.9f}. Child retained: {b:.9f}. Strict improvement: {child_better}. Active task skill: {selected_skill}, SHA-256 {frozen[selected_skill]}. Parent wins a tie. Improver SHA-256 remains {improver_hash}.\n\nSame author context, two fits per arm, known public task. Changes to task skill do not establish improvement of the improver. This run does not establish unseen transfer. All rejected model attempts remain in their ledgers.\n")
        comparisons[lab_id] = summary
    assert sha(improver_origin) == improver_hash
    assert all(sha(skills / f"{name}.md") == value for name, value in frozen.items())
    save(out / "07-04/UNEXECUTED-IMPROVER-PROPOSAL.md", "# A different proposed experiment\n\nPropose requiring a fresh task family before retaining a changed task skill. This edits the improver's acceptance procedure, unlike the second-model choice edited above. It is unexecuted. Compare old and proposed improvers under a new fixed external task and cost protocol before calling it better.\n")
    save(out / "08-05/NEXT-DEVELOPMENT.md", "# Preserve transfer feedback as a new round\n\nPropose replacing ordinary misclassification slices with class-balanced error diagnostics. The current frozen skills are unchanged. This proposal uses knowledge of the wine task and belongs to a new development round. It needs fresh transfer cases and a declared budget; no such evaluation ran here.\n")

    # One inspectable reporting-skill edit, two cases, fixed external check.
    modification = out / "07-08"
    save(modification / "PARENT.md", "# Reporting skill v0\n\nReport the supplied summary value.\n")
    save(modification / "CHILD.md", "# Reporting skill v1\n\nReport the MAE recomputed from the saved predictions.\n")
    save(modification / "EVALUATOR.md", "# Fixed evaluator\n\nFor both input cases and both versions, accept a reported value only if it matches the same pinned-prediction MAE within 1e-9. Never edit this rule to make the child pass. Retain the child only if it fixes the wrong input without breaking the correct input.\n")
    checks = []
    for label, supplied in [("valid", recomputed), ("wrong-summary", 1.0)]:
        for version in ("PARENT", "CHILD"):
            instruction = (modification / f"{version}.md").read_text()
            if "recomputed" in instruction:
                current_predictions = pd.read_csv(out / "07-01/predictions.csv")
                result = float(np.abs(current_predictions.actual - current_predictions.predicted).mean())
            else:
                result = supplied
            checks.append({"case": label, "version": version, "supplied": supplied, "reported": result,
                           "external_pass": abs(result - recomputed) < 1e-9, "skill_sha256": sha(modification / f"{version}.md")})
    table(modification / "TWO-CASE-CHECKS.csv", checks)
    assert all(row["external_pass"] for row in checks if row["version"] == "CHILD")
    save(modification / "ACTIVE.md", f"# Retained local skill\n\nActive: CHILD.md, SHA-256 {sha(modification / 'CHILD.md')}. Parent remains available. The child repairs the wrong summary without changing the valid one. Its two cases are known fixtures, not evidence of broad LLM improvement. No canonical course skill or evaluator was edited.\n")
    save(modification / "UNEXECUTED-CHECK-DELETION.md", "# Rejected proposal\n\nDeleting the external metric check would let the false summary pass, but would change acceptance rather than improve the report. Keep the evaluator fixed. This deletion was proposed for discussion only and was not applied.\n")

    # Costs from actual attempts, not only the retained winners.
    costs = []
    for version in ("parent", "child"):
        selected_fits = [r for r in fits if r["workspace"] == f"07-04/{version}"]
        selected_commands = [r for r in commands if r["action"].startswith(f"07-04-{version}-")]
        costs.append({"procedure": version, "attempts": len(selected_fits), "fit_seconds": sum(float(r["seconds"]) for r in selected_fits),
                      "fit_and_check_child_wall_seconds": sum(r["wall_seconds"] for r in selected_commands),
                      "checker_calls": len(selected_commands) - len(selected_fits), "failed_attempts": sum(r["status"] != "ok" for r in selected_fits),
                      "agent_cost": "unknown"})
    table(out / "08-03/ACTUAL-COSTS.csv", costs)
    save(out / "08-03/COST.md", "# Reconcile the two bike procedures\n\nEach arm ran two fits and two checker commands. Each retained its second candidate and rejected the worse first candidate; reporting one fit per winner would omit one charged attempt per arm. ALL-FITS.csv preserves their identities and model fit seconds. COMMANDS.csv includes startup and checking; those wall times already include fitting and must not be added to fit seconds.\n\nProposal generation, source inspection, diagnosis, implementation, and review occurred in the shared author process; complete per-arm times and provider charges are unknown. Recorded failed fits and retries: zero. Final evaluation: not performed. Equal fit counts and the same checks are established; equal total cost and total-cost superiority are not.\n\nNumerical illustration, not run data: A costs 20 fit-seconds plus p proposal-seconds; B costs 30 + 10 = 40 seconds. Under sequential additive stages and otherwise equal costs, break-even is p=20. At p=100, A costs 120 seconds and B costs 40. This conclusion depends on the stated accounting assumptions.\n")

    # Four explicit choices over cached actual predictions, then a separate fifth.
    ablation = out / "08-04"
    save(ablation / "ABLATION-PLAN.md", "# Frozen four-arm decision replay\n\nParent selects the checked majority option. Child selects the checked linear option. Memory says: until an error-slice note is present, keep majority. No arm has that note. Apply the memory condition after the skill choice in both versions. Use the same two cached options and balanced accuracy. Four clean decision calls, no fits.\n\nThe follow-up removes only that restrictive memory instruction in a separate fifth call. This is a deterministic interpreter, not a measurement of conflicting-prompt behavior in an LLM.\n")
    save(ablation / "MEMORY.md", "# Restrictive retained rule\n\nUntil an error-slice note is present, keep the majority baseline. This fixture intentionally applies a restriction from another context to an already checked candidate comparison.\n")
    save(ablation / "SKILL-parent.md", "# Fixed parent decision skill\n\nChoose: trial-001.\n")
    save(ablation / "SKILL-child.md", "# Fixed child decision skill\n\nChoose: trial-002.\n")
    save(ablation / "MEMORY-FOLLOWUP.md", "# Separately revised memory\n\nNo additional condition. The restrictive slice-note rule is removed only for the fifth follow-up.\n")

    def ablated_choice(version, memory_path):
        instruction_path = ablation / f"SKILL-{version}.md"
        instruction = instruction_path.read_text()
        proposed = re.search(r"Choose: (trial-\d+)\.", instruction).group(1)
        memory_text = memory_path.read_text() if memory_path else ""
        chosen = "trial-001" if "Until an error-slice note is present" in memory_text else proposed
        return proposed, chosen, sha(instruction_path), sha(memory_path) if memory_path else "none"

    arm_rows = []
    for child_on, memory_on in [(False, False), (False, True), (True, False), (True, True)]:
        initial, chosen, skill_hash, memory_hash = ablated_choice("child" if child_on else "parent", ablation / "MEMORY.md" if memory_on else None)
        arm_rows.append({"skill": "child" if child_on else "parent", "memory": memory_on,
                         "proposed": initial, "chosen": chosen, "cached_balanced_accuracy": wine_scores[chosen],
                         "skill_sha256": skill_hash, "memory_sha256": memory_hash})
    table(ablation / "FOUR-ARMS.csv", arm_rows)
    interaction = (arm_rows[3]["cached_balanced_accuracy"] - arm_rows[2]["cached_balanced_accuracy"]) - (arm_rows[1]["cached_balanced_accuracy"] - arm_rows[0]["cached_balanced_accuracy"])
    _, followed, follow_skill, follow_memory = ablated_choice("child", ablation / "MEMORY-FOLLOWUP.md")
    table(ablation / "SEPARATE-FOLLOWUP.csv", [{"skill": "child", "removed_rule": "require absent slice note before leaving majority", "chosen": followed, "cached_balanced_accuracy": wine_scores[followed], "skill_sha256": follow_skill, "memory_sha256": follow_memory}])
    save(ablation / "INTERPRETATION.md", f"# Memory can block a useful change\n\nParent with/without memory selects the same baseline: 0.5. Child without memory selects the linear option: {wine_scores['trial-002']:.9f}; child with memory is forced back to 0.5. Memory's effect on child minus its effect on parent is {interaction:.9f}. The interaction is negative under this declared order and fixture.\n\nThe fifth follow-up restores the child choice by removing the restrictive rule. It remains separate from the original four arms. The outputs are cached measured scores, not new fits. The known two-option fixture and fixed interpreter do not establish general memory harm or LLM behavior.\n")

    # Restore an actually changed active pointer in a labelled rollback fixture.
    rollback = out / "08-06"
    save(rollback / "VALID-RESEARCH-SKILL.md", "# Previously valid instruction\n\nRetain candidates using declared balanced accuracy. Report both class recalls.\n")
    save(rollback / "MISLEADING-PROPOSAL.md", "# Labelled invalid promotion fixture\n\nPromote the majority recipe because its overall accuracy is high. Omit minority recall. This conflicts with the existing objective.\n")
    save(rollback / "ACTIVE.md", "# Active fixture instruction\n\nVALID-RESEARCH-SKILL.md\n")
    shutil.copyfile(rollback / "ACTIVE.md", rollback / "ACTIVE-BEFORE.md")
    save(rollback / "ACTIVE.md", "# Active fixture instruction\n\nMISLEADING-PROPOSAL.md\n")
    shutil.copyfile(rollback / "ACTIVE.md", rollback / "ACTIVE-INVALID.md")
    majority = pd.read_csv(out / "07-03/inputs/trial-001-predictions.csv")
    accuracy = float((majority.actual == majority.predicted).mean())
    recalls = [float((majority.loc[majority.actual == label, "predicted"] == label).mean()) for label in (0, 1)]
    balanced = sum(recalls) / 2
    table(rollback / "METRICS.csv", [{"accuracy": accuracy, "negative_recall": recalls[0], "positive_recall": recalls[1], "balanced_accuracy": balanced, "rows": len(majority)}])
    shutil.copyfile(rollback / "ACTIVE-BEFORE.md", rollback / "ACTIVE.md")
    assert sha(rollback / "ACTIVE.md") == sha(rollback / "ACTIVE-BEFORE.md")
    save(rollback / "PROMOTION.md", f"# Reject and restore\n\nThe fixture's majority classifier has accuracy {accuracy:.9f}, negative recall {recalls[0]}, positive recall {recalls[1]}, and balanced accuracy {balanced}. The primary metric remains balanced accuracy. Reject the proposed metric switch and restore the exact prior active-file bytes. Both instruction versions and the invalid intermediate pointer remain. No fit was needed.\n")
    save(rollback / "NEW-ACCURACY-TASK.md", "# Separate hypothetical task\n\nObjective: maximize overall correct classifications with equal cost per row. This is a new objective, not a revision of the completed balanced-accuracy comparison. Report both class recalls so the decision maker can see that an all-negative baseline misses every positive case. No new model search or performance claim is made here.\n")

    assert len(fits) == 8 and all(row["status"] == "ok" for row in fits)
    save(out / "COST.md", f"# Complete run resources\n\nNew fits: 8. Fit seconds: {sum(float(r['seconds']) for r in fits):.6f}. Child commands: {len(commands)}. Summed child wall seconds: {sum(r['wall_seconds'] for r in commands):.6f}. Parent elapsed through reporting: {time.perf_counter()-started:.6f}. Nested durations overlap.\n\nReplayed predictions and fixed-rule fixtures are not new fits. No final scoring, GPU, cluster, or automatic retry. Authoring and hosted inference costs remain unknown.\n")
    save(out / "PROGRESS.md", "# Author walkthrough executed\n\nEight new fits, output correction, two reflection replays, retained-memory use, two modification cases, cost reconciliation, four ablation arms plus one separate follow-up, transfer replay, and rollback fixture are retained. No learner, fresh coding-agent context, uncontaminated transfer, model-weight update, or recursive improver change is established.\n")
    table(out / "MANIFEST.csv", [{"path": p.relative_to(out).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(out.rglob("*")) if p.is_file()])
    print(f"Completed eight fits and declared replays: {out}", flush=True)


if __name__ == "__main__":
    main()
