"""Agent-written author walkthrough; students use the lab's Markdown prompts.

Thirteen fits under the separately versioned protocol. Keep failed commands.
No independent agent context, final evaluation, or learner response is implied.
"""
import argparse
import csv
import hashlib
import io
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def table(path, rows):
    assert rows
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    save(path, stream.getvalue())


def route(task, target_type):
    routes = {"bike": ("regression", "MAE"), "wine": ("classification", "balanced accuracy")}
    if task not in routes:
        return "rejected", "unknown task"
    if not target_type:
        return "needs-clarification", "target type missing"
    if target_type != routes[task][0]:
        return "needs-clarification", "target type conflicts with fixed task"
    return "ready", routes[task][1]


def handoff(target_known, expected, evidence):
    if not target_known:
        return "needs-clarification", "target is ambiguous"
    if evidence is None:
        return "awaiting-check", "checker evidence is missing"
    for field in ("task", "candidate", "predictions_sha256"):
        if evidence[field] != expected[field]:
            return "awaiting-check", f"rejected {field} mismatch"
    if evidence["checker_exit"] != 0:
        return "awaiting-check", "checker did not pass"
    return "complete", "identity, predictions, and check agree"


def reaches_fit_stub(features, domain_check, allowlist_check):
    allowed = {"season", "yr", "mnth", "hr", "holiday", "weekday", "workingday"}
    leaked = {"casual", "registered", "cnt"}
    if domain_check and set(features) & leaked:
        return False, "domain check rejects outcome information"
    if allowlist_check and not set(features) <= allowed:
        return False, "tool allowlist rejects undeclared inputs"
    return True, "dry-run fit stub reached; no training called"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.workspace.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    tool = repo / "rsi/tools/lab.py"
    checker = repo / "rsi/tools/check_result.py"
    protocol = repo / "how-did-i-generate-it/rsi/validation/LOOPS-AND-SYSTEMS-PROTOCOL.md"
    shutil.copyfile(protocol, out / "PROTOCOL.md")
    shutil.copyfile(Path(__file__), out / "driver.source.py")
    shutil.copyfile(tool, out / "lab.source.py")
    shutil.copyfile(checker, out / "checker.source.py")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    save(out / "SOURCE.md", f"# Source and context\n\nGit revision: {commit}\n\nPython: {platform.python_version()}; platform: {platform.platform()}.\n\nDriver SHA-256: {digest(Path(__file__))}\n\nProtocol SHA-256: {digest(protocol)}\n\nRuntime SHA-256: {digest(tool)}\n\nChecker SHA-256: {digest(checker)}\n\nNew workspace and child processes; shared author-agent context. Several baseline outcomes were already known. No learner participated.\n")
    from importlib.metadata import distributions
    table(out / "PACKAGE-VERSIONS.csv", sorted([
        {"package": d.metadata["Name"], "version": d.version} for d in distributions()
    ], key=lambda row: row["package"].lower()))
    sys.path.insert(0, str(repo / "rsi/tools"))
    import lab
    import numpy as np
    import pandas as pd
    commands, fits = [], []

    def execute(label, script, arguments):
        command = [sys.executable, str(script), *map(str, arguments)]
        before = time.perf_counter()
        try:
            result = subprocess.run(command, cwd=repo, capture_output=True, text=True,
                                    encoding="utf-8", timeout=60)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = 124, str(error.stdout or ""), str(error.stderr or "")
        elapsed = time.perf_counter() - before
        commands.append({"action": label, "exit": code, "wall_seconds": elapsed})
        save(out / "commands" / f"{len(commands):03d}-{label}.md",
             f"# {label}\n\nArguments: {command!r}\n\nExit: {code}. Wall seconds: {elapsed:.6f}.\n\nStandard output:\n\n```text\n{stdout}\n```\n\nStandard error:\n\n```text\n{stderr}\n```\n")
        table(out / "COMMANDS.csv", commands)
        print(f"{label}: exit {code}; {elapsed:.2f}s", flush=True)
        if code != 0:
            save(out / "PROGRESS.md", f"# Stopped\n\nUnexpected exit {code} for {label}. Preserve the attempted run and inspect its log. Do not rerun this workspace.\n")
            raise RuntimeError(label)

    def fit(relative, task, model, limit, seed=17, hypothesis="Run the declared fixed recipe."):
        work = out / relative
        execute(relative.replace("/", "-") + "-" + model + f"-{seed}", tool,
                ["run", "--task", task, "--workspace", work, "--model", model,
                 "--features", "calendar" if task == "bike" else "all", "--seed", seed,
                 "--attempt-limit", limit, "--hypothesis", hypothesis])
        row = read_rows(work / "trials.csv")[-1]
        candidate = work / row["candidate"]
        execute(relative.replace("/", "-") + "-check-" + candidate.name, checker,
                [candidate, "--report", candidate / "CHECK.md"])
        fits.append({"workspace": relative, **row})
        table(out / "ALL-FITS.csv", fits)
        return candidate, row

    # Two fixed ways to spend the same fit count.
    loop = out / "02-06"
    save(loop / "COMPARISON-PLAN.md", protocol.read_text(encoding="utf-8") +
         "\nArm A deliberately repeats its recipe. The runtime permits this explicit replication. Both arm contracts allow two attempts.\n")
    a1, ar1 = fit("02-06/arm-a", "bike", "constant", 2)
    a2, ar2 = fit("02-06/arm-a", "bike", "constant", 2,
                  hypothesis="Intentional replication under the predeclared fixed-retry control.")
    b1, br1 = fit("02-06/arm-b", "bike", "constant", 2)
    hourly = read_rows(b1 / "error-by-hour.csv")
    smallest, largest = min(hourly, key=lambda r: float(r["mean"])), max(hourly, key=lambda r: float(r["mean"]))
    ratio = float(largest["mean"]) / float(smallest["mean"])
    selected = "linear" if ratio >= 1.5 else "tree"
    save(loop / "DECISION-B.md", f"# Decision before arm B's second fit\n\nRead arm-b/trial-001/error-by-hour.csv. Lowest hourly MAE: {smallest['mean']} at hour {smallest['hour']}. Highest: {largest['mean']} at hour {largest['hour']}. Ratio: {ratio:.6f}.\n\nThe predeclared rule chooses {selected}/calendar. Only the model changes. A varying error profile motivates testing calendar-conditioned predictions; it does not prove this model will help. The decision rule and public baseline outcomes are author-known.\n")
    decision_hash = digest(loop / "DECISION-B.md")
    b2, br2 = fit("02-06/arm-b", "bike", selected, 2,
                  hypothesis=f"Pre-fit decision SHA-256 {decision_hash}: test a calendar-conditioned model from hourly baseline errors.")
    assert digest(a1 / "predictions.csv") == digest(a2 / "predictions.csv") == digest(b1 / "predictions.csv")
    a_score, b_score = min(float(ar1["score"]), float(ar2["score"])), min(float(br1["score"]), float(br2["score"]))
    save(loop / "COMPARISON.md", f"# Measured two-fit comparison\n\nArm A retained MAE {a_score:.9f}. Arm B retained MAE {b_score:.9f}. Baseline predictions are byte-identical across both starts and the deliberate repeat. Each arm spent two fits.\n\nThe gain is local to these fixed teaching procedures on this known task. Model-fit time is in ALL-FITS.csv; command wall time is in COMMANDS.csv. Agent proposal and review cost is unmeasured. There is no changed improver or fresh agent context.\n\nAdditional exercise, not executed: giving B ten fits changes its search opportunity. Even a lower error would not establish superiority under equal resources. No extra fits were performed.\n")

    # Fixed semantic routing, with actual source partition checks.
    routing = out / "05-02"
    save(routing / "ROUTING.md", "# Fixed routes\n\n| Task | Target type | Data card | Baseline | Metric | Required check |\n|---|---|---|---|---|---|\n| bike | regression | BIKE-DATA-CARD.md | training median | MAE | selection rows, target identity, leakage |\n| wine | classification | WINE-DATA-CARD.md | training majority | balanced accuracy | grouped duplicate inputs, both class recalls |\n\nReject an unknown task. A missing or conflicting target type needs clarification before fitting. A fixed table selects procedures; it does not learn routing.\n")
    for task, folder in [("bike", "bike-demand"), ("wine", "wine-quality")]:
        shutil.copyfile(repo / f"rsi/examples/{folder}/DATA-CARD.md", routing / f"{task.upper()}-DATA-CARD.md")
    (routing / "source").mkdir()
    for folder, filename in [("bike-demand", "Readme.txt"), ("wine-quality", "winequality.names")]:
        shutil.copyfile(repo / f"rsi/examples/{folder}/source/{filename}", routing / "source" / filename)
    route_checks = []
    for task, target_type, expected in [("bike", "regression", "ready"), ("wine", "classification", "ready"),
                                        ("unknown", "regression", "rejected"), ("bike", "", "needs-clarification")]:
        state, reason = route(task, target_type)
        assert state == expected
        route_checks.append({"task": task, "target_type": target_type, "state": state, "reason": reason})
    table(routing / "ROUTE-CHECKS.csv", route_checks)
    routed_bike, _ = fit("05-02/bike", "bike", "constant", 2)
    wine, _ = fit("05-02/wine", "wine", "constant", 1)
    data = lab.read_data("wine")
    masks = lab.partitions(data, "wine")
    features = lab.feature_names("wine", "all", data)
    group_parts = {}
    assignments = []
    for partition, mask in masks.items():
        for index in np.flatnonzero(mask):
            vector = tuple(data.iloc[index][features])
            identity = hashlib.sha256(repr(vector).encode()).hexdigest()
            group_parts.setdefault(identity, set()).add(partition)
            assignments.append({"source_row": int(index), "input_group_sha256": identity, "partition": partition})
    assert all(len(parts) == 1 for parts in group_parts.values())
    table(routing / "WINE-GROUP-PARTITIONS.csv", sorted(assignments, key=lambda r: r["source_row"]))
    predictions = pd.read_csv(wine / "predictions.csv")
    recalls = [float((predictions.loc[predictions.actual == label, "predicted"] == label).mean()) for label in (0, 1)]
    accuracy = float((predictions.actual == predictions.predicted).mean())
    save(routing / "COMPARISON.md", f"# Same process, different meanings\n\nWine selection contains {len(predictions)} rows: {(predictions.actual == 0).sum()} negatives and {(predictions.actual == 1).sum()} positives. Majority accuracy: {accuracy:.9f}; class-0 recall: {recalls[0]:.9f}; class-1 recall: {recalls[1]:.9f}; balanced accuracy: {statistics.mean(recalls):.9f}.\n\nChecked all {len(data)} source rows: {len(group_parts)} distinct input vectors, with no vector crossing partition boundaries. Full assignments are retained. Bike MAE has rental-count units; wine balanced accuracy averages recalls. Both routes frame, fit once, and verify source identities. Their metric interpretations are different. Unknown and missing-type requests did not trigger any fit.\n")

    # Two context checks against a real partially used contract.
    context = out / "05-03"
    contract = (routed_bike.parent / "CONTRACT.md").read_text(encoding="utf-8")
    assert digest(routed_bike.parent / "CONTRACT.md") == (routed_bike.parent / "CONTRACT.sha256").read_text().strip()
    limit = int(re.search(r"^- max_attempts: (\d+)$", contract, re.MULTILINE).group(1))
    ledger = read_rows(routed_bike.parent / "trials.csv")
    remaining = limit - len(ledger)
    assert remaining == 1
    availability = "Observed weather is a retrospective input; an advance forecast needs a justified forecast source."
    packet = f"# Context for the current bike run\n\nContract: ../05-02/bike/CONTRACT.md (SHA-256 {digest(routed_bike.parent / 'CONTRACT.md')}).\n\nLedger: ../05-02/bike/trials.csv (SHA-256 {digest(routed_bike.parent / 'trials.csv')}).\n\nTask: hourly rentals, cnt, MAE. Current candidate: {ledger[-1]['candidate']}, status {ledger[-1]['status']}, score {ledger[-1]['score']}. Attempts: {len(ledger)} spent of {limit}; {remaining} left. This driver reserves the last attempt.\n\nReference: ../05-02/BIKE-DATA-CARD.md. Exclude outcome components. {availability}\n\nWine-specific metrics and unrelated prior results were not copied into this packet.\n"
    save(context / "CONTEXT.md", packet)
    save(context / "STALE-NOTE.md", "# Deliberately stale fixture\n\nThree attempts remain. This statement conflicts with the actual current ledger.\n")
    table(context / "CONTEXT-CHECKS.csv", [
        {"note": "current", "claimed_remaining": 1, "verified_remaining": remaining, "accepted": 1 == remaining},
        {"note": "stale", "claimed_remaining": 3, "verified_remaining": remaining, "accepted": 3 == remaining},
    ])
    save(context / "MISSING-AVAILABILITY.md", packet.replace(availability, "[Input availability deliberately omitted in this fixture.]"))
    save(context / "CONFLICT-AND-RECOVERY.md", "# Use verified state\n\nThe stale claim of three remaining attempts is rejected. The intact contract allows two and the ledger has charged one. Retrieval cannot refund the spent attempt.\n\nAdditional reading exercise: the altered packet no longer supports deciding whether observed weather is available at prediction time. Consult the linked original data card. Do not infer a day-ahead forecasting task or silently fit extra candidates. This is a derived summary, not a replacement for original evidence.\n")

    # A real baseline and explicit coordinator transitions.
    coordinator = out / "05-04"
    save(coordinator / "COORDINATOR.md", "# Fixed coordinator\n\nReady requires a recognized task and unambiguous target. Reserve one fit before entering running. A successful fit enters awaiting-check, not complete. Complete requires a successful checker packet for this exact task, candidate, and prediction digest. Missing or mismatched evidence stays awaiting-check. Ambiguous target enters needs-clarification; only a real clarification can resolve it. No human approval is fabricated.\n\nOne baseline fit; two main failure fixtures. The additional wrong-candidate fixture is separately declared and uses no fit.\n")
    candidate, _ = fit("05-04/run", "bike", "constant", 1)
    expected = {"task": "bike", "candidate": "05-04/run/" + candidate.name,
                "predictions_sha256": digest(candidate / "predictions.csv")}
    packet = {**expected, "checker_exit": 0, "checker_report_sha256": digest(candidate / "CHECK.md")}
    wrong_packet = {**packet, "candidate": "02-06/arm-a/" + a1.name,
                    "predictions_sha256": digest(a1 / "predictions.csv"),
                    "checker_report_sha256": digest(a1 / "CHECK.md")}
    assert packet["predictions_sha256"] == wrong_packet["predictions_sha256"]
    table(coordinator / "CHECK-PACKETS.csv", [{"case": "actual", **packet}, {"case": "wrong-candidate", **wrong_packet}])
    transitions = [
        {"case": "actual", "from": "ready", "to": "running", "reason": "one reserved fit"},
        {"case": "actual", "from": "running", "to": "awaiting-check", "reason": "fit returned successfully"},
    ]
    for case, target_known, supplied, required in [
        ("actual", True, packet, "complete"),
        ("missing-check-fixture", True, None, "awaiting-check"),
        ("ambiguous-target-fixture", False, packet, "needs-clarification"),
        ("additional-wrong-candidate", True, wrong_packet, "awaiting-check"),
    ]:
        state, reason = handoff(target_known, expected, supplied)
        assert state == required
        transitions.append({"case": case, "from": "ready" if not target_known else "awaiting-check", "to": state, "reason": reason})
    table(coordinator / "TRANSITIONS.csv", transitions)
    save(coordinator / "INTERPRETATION.md", "# Identity matters even when predictions match\n\nThe baseline reached complete only after its actual checker passed. Missing evidence stayed awaiting-check; the ambiguous target required clarification. The additional packet came from a different, genuinely checked baseline. Its prediction bytes are identical, but its candidate identity is wrong. The coordinator rejected that handoff.\n\nChecker calculation is separate code within the same local access boundary. The fixed coordinator is a small executable implementation of the written procedure, not an independent reviewing agent. These fixtures do not measure how reliably an LLM follows arbitrary prose.\n")

    # Two overlapping protections make the first removal a null ablation.
    ablation = out / "05-05"
    save(ablation / "ABLATION-PLAN.md", "# Main four-case ablation\n\nInputs: valid calendar fields [hr, weekday]; leaked fields [hr, weekday, casual]. Compare full system with domain-check removed, keeping the tool allowlist active. Outcome: does the input reach the dry-run fit stub? No actual fitting is possible in this fixture function.\n\nSeparate additional two-case ablation: remove both protections using the same inputs. This changes two components relative to the full system and answers a combined-protection question.\n")
    ablation_rows = []
    for system, domain_on, allowlist_on, phase in [("full", True, True, "main"), ("domain-removed", False, True, "main"), ("both-removed", False, False, "additional")]:
        for fixture, fields in [("valid", ["hr", "weekday"]), ("leaked", ["hr", "weekday", "casual"])]:
            reached, reason = reaches_fit_stub(fields, domain_on, allowlist_on)
            assert reached == (fixture == "valid" or system == "both-removed")
            ablation_rows.append({"phase": phase, "system": system, "fixture": fixture, "features": " ".join(fields),
                                  "domain_check": domain_on, "allowlist_check": allowlist_on, "fit_stub_reached": reached, "reason": reason})
    table(ablation / "OUTCOMES.csv", ablation_rows)
    save(ablation / "INTERPRETATION.md", "# A null effect with a concrete explanation\n\nAll valid proposals reached the fit stub. The leaked proposal was blocked in both main arms. Removing the domain check alone made no difference because the tool allowlist still rejected casual. In the separate additional ablation, removing both allowed the leaked input to reach the stub.\n\nThe main result does not show that domain knowledge is useless. Two guards overlap on this one fixture. The follow-up demonstrates dependence on their combined protection, not each guard's isolated contribution across arbitrary failures. No leaked model was trained and no prediction-quality improvement was measured.\n")

    # All seed pairs, without selecting only a favorable one.
    repeated = out / "08-01"
    save(repeated / "REPETITION-PLAN.md", "# Fixed repeated comparison\n\nTree versus forest, calendar features, seeds 17, 29, 43. Same bike partitions and selection MAE. Three attempts per recipe, six total. Report forest minus tree MAE for every seed, its mean and range, all fit costs, and a plot. Recipes differ in family and complexity. No final evaluation or claim about unseen datasets.\n")
    pairs = []
    for seed in (17, 29, 43):
        _, tree = fit("08-01/tree", "bike", "tree", 3, seed)
        _, forest = fit("08-01/forest", "bike", "forest", 3, seed)
        pairs.append({"seed": seed, "tree_mae": float(tree["score"]), "forest_mae": float(forest["score"]),
                      "forest_minus_tree": float(forest["score"]) - float(tree["score"]),
                      "tree_fit_seconds": float(tree["seconds"]), "forest_fit_seconds": float(forest["seconds"])})
    table(repeated / "PAIRED-RESULTS.csv", pairs)
    differences = [p["forest_minus_tree"] for p in pairs]
    best = min(pairs, key=lambda p: p["forest_minus_tree"])
    save(repeated / "INTERPRETATION.md", f"# Repeat the comparison, keep all outcomes\n\nForest minus tree MAE: mean {statistics.mean(differences):.9f}; range [{min(differences):.9f}, {max(differences):.9f}]. Negative favors forest. Total recorded fit seconds: {sum(p['tree_fit_seconds'] + p['forest_fit_seconds'] for p in pairs):.6f}.\n\nAdditional reporting exercise: a report that selects only seed {best['seed']} would show {best['forest_minus_tree']:.9f}, the most favorable observed difference. The complete table exposes the discarded pairs. This selection is labelled post hoc and does not replace the original mean.\n\nThree paired seeds share one fixed data split. They assess this limited seed sensitivity, not uncertainty from dataset selection or future demand. Matching seed numbers does not align every random draw across different algorithms. Recipe family and complexity differ. All comparisons use the same author context and public task; inference cost is unknown.\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    for key, label, color in [("tree_mae", "Bounded tree", "#416A92"), ("forest_mae", "Forest", "#B15D31")]:
        axes[0].plot([p["seed"] for p in pairs], [p[key] for p in pairs], "o-", label=label, color=color)
    axes[0].set(xlabel="Predeclared seed", ylabel="Selection MAE (rentals/hour)", title="Both frozen recipes, all three seeds", xticks=[17, 29, 43])
    axes[0].legend(frameon=False)
    axes[1].bar([str(p["seed"]) for p in pairs], differences, color="#578176")
    axes[1].axhline(0, color="#777777", linewidth=1)
    axes[1].set(xlabel="Predeclared seed", ylabel="Forest MAE − tree MAE", title="Negative means lower forest error")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("One split, six measured CPU fits", fontsize=16)
    fig.savefig(repeated / "paired-seeds.png", dpi=160, facecolor="white")
    plt.close(fig)

    assert len(fits) == 13 and all(row["status"] == "ok" for row in fits)
    assert not list(out.rglob("FINAL-LOCK.md"))
    save(out / "COST.md", f"# Recorded resources\n\nModel fits: {len(fits)}. Recorded fit seconds: {sum(float(r['seconds']) for r in fits):.6f}. Child commands: {len(commands)}; their wall seconds sum to {sum(c['wall_seconds'] for c in commands):.6f}. Parent driver elapsed seconds through reporting: {time.perf_counter()-started:.6f}. These durations overlap; do not add them.\n\nNo model-search retries, final evaluations, extra seed fits, GPU jobs, or cluster jobs. Proposal, implementation, review, and LLM inference costs are not fully metered. Unknown is not zero. Only a baseline fit was used from the routed bike contract; its one remaining attempt was reserved for the context example and not spent.\n")
    save(out / "PROGRESS.md", "# Author execution finished\n\nDeclared thirteen fits and local fixtures completed. All prediction checks passed. No final partition was evaluated. Source review, candidate artifacts, command logs, and actual-data plot are preserved.\n\nLearner predictions, quizzes, and teach-back: unattempted. Optional ten-fit unequal-budget experiment: not run. Other native coding agents and GPU or cluster backends: not run. A human-readable review and image inspection follow separately.\n")
    entries = [{"path": p.relative_to(out).as_posix(), "sha256": digest(p), "bytes": p.stat().st_size}
               for p in sorted(out.rglob("*")) if p.is_file()]
    table(out / "MANIFEST.csv", entries)
    print(f"Retained {len(entries)} files plus manifest; 13 fits complete: {out}", flush=True)


if __name__ == "__main__":
    main()
