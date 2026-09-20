"""Small executable teaching mechanisms. Synthetic fixtures are labelled.

These checks illustrate control and evidence rules; they are not autonomous
agent runs, private evaluation, or reproductions of research papers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path


def save(path, body):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")


def order_is_valid(order, dependencies):
    if len(order) != len(set(order)) or set(order) != set(dependencies):
        return False
    completed = set()
    for node in order:
        if not set(dependencies[node]) <= completed:
            return False
        completed.add(node)
    return True


def join_checks(candidate, contract, results):
    if {r["check"] for r in results} != {"data", "resources"} or len(results) != 2:
        return "incomplete"
    if any(r["candidate"] != candidate or r["contract"] != contract for r in results):
        return "mismatch"
    return "pass" if all(r["status"] == "pass" for r in results) else "fail"


def repair_cycle(has_target, repairs, limit=2):
    trace = []
    for attempt in range(limit + 1):
        trace.append((attempt, "valid" if has_target else "missing target"))
        if has_target:
            return "pass", trace
        if attempt == limit:
            return "exhausted", trace
        has_target = repairs[attempt] if attempt < len(repairs) else False
    raise AssertionError("Unreachable")


def affected_nodes(changed, dependencies):
    affected = set(changed)
    while True:
        more = {node for node, inputs in dependencies.items() if set(inputs) & affected}
        if more <= affected:
            return affected
        affected |= more


def replay(tree, order, budget):
    visited, outcomes, spent = set(), [], 0.0
    for node_id in order:
        if node_id not in tree:
            outcomes.append((node_id, "unknown", None))
            break
        node = tree[node_id]
        if node["parent"] is not None and node["parent"] not in visited:
            outcomes.append((node_id, "unsupported path", None))
            break
        if node_id in visited:
            outcomes.append((node_id, "duplicate", None))
            break
        if spent + node["cost"] > budget:
            outcomes.append((node_id, "budget stop", None))
            break
        spent += node["cost"]
        visited.add(node_id)
        outcomes.append((node_id, "recorded", node["score"]))
    return outcomes, spent


def relative_advantages(rewards):
    mean = sum(rewards) / len(rewards)
    variance = sum((r - mean) ** 2 for r in rewards) / len(rewards)
    std = math.sqrt(variance)
    return [(r - mean) / (std + 1e-8) for r in rewards]


def toy_policy_update(rewards, rate=0.1):
    # One gradient step for J = sum_i p_i A_i, p = softmax(logits).
    # This is NOT the GRPO clipped token-level objective.
    advantages = relative_advantages(rewards)
    p = [1 / len(rewards)] * len(rewards)
    expected = sum(pi * a for pi, a in zip(p, advantages))
    logits = [rate * pi * (a - expected) for pi, a in zip(p, advantages)]
    weights = [math.exp(z) for z in logits]
    updated = [w / sum(weights) for w in weights]
    return advantages, updated


def operator(state, surface, evidence_version):
    if evidence_version != state["version"]:
        raise ValueError("stale evidence")
    if surface not in ("data", "harness", "model"):
        raise ValueError("undeclared write surface")
    result = dict(state)
    result[surface] += 1
    result["version"] += 1
    return result


def run_checks(output):
    output = Path(output)
    checks = []

    def record(name, observed, expected):
        passed = observed == expected
        checks.append((name, str(observed), str(expected), "pass" if passed else "FAIL"))
        if not passed:
            raise AssertionError(f"{name}: {observed} != {expected}")

    deps = {"frame": [], "inspect": ["frame"], "split": ["inspect"], "fit": ["split"], "check": ["fit"], "report": ["check"]}
    record("Valid action order", order_is_valid(list(deps), deps), True)
    record("Checking before fitting", order_is_valid(["frame", "inspect", "split", "check", "fit", "report"], deps), False)
    a = {"check": "data", "candidate": "A", "contract": "v1", "status": "pass"}
    b = {"check": "resources", "candidate": "A", "contract": "v1", "status": "pass"}
    record("Matching join", join_checks("A", "v1", [a, b]), "pass")
    record("Missing join result", join_checks("A", "v1", [a]), "incomplete")
    record("Wrong-candidate join", join_checks("A", "v1", [a, dict(b, candidate="B")]), "mismatch")
    record("Stale-contract join", join_checks("A", "v1", [a, dict(b, contract="v0")]), "mismatch")
    status, trace = repair_cycle(False, [True])
    record("Effective repair", status, "pass")
    status2, trace2 = repair_cycle(False, [False, False])
    record("Ineffective repair stops", (status2, len(trace2)), ("exhausted", 3))
    record("Report-only recovery", affected_nodes({"report"}, deps), {"report"})
    record("Split invalidation", affected_nodes({"split"}, deps), {"split", "fit", "check", "report"})
    save(output / "graph/TRACE.md", f"# Synthetic graph fixtures\n\nEffective repair: {trace}\n\nExhausted repair: {trace2}\n\nThese are constructed control-flow checks, not ML performance results.\n")

    tree = {"root": {"parent": None, "cost": 1, "score": 160},
            "linear": {"parent": "root", "cost": 1, "score": 110},
            "tree": {"parent": "root", "cost": 2, "score": 115}}
    outcomes, cost = replay(tree, ["root", "linear", "unvisited"], 5)
    record("Absent replay branch", outcomes[-1], ("unvisited", "unknown", None))
    record("Replay charges realized cost", cost, 2.0)
    record("Replay enforces budget", replay(tree, ["root", "tree"], 2)[0][-1][1], "budget stop")
    record("Replay requires parent", replay(tree, ["tree"], 5)[0][-1][1], "unsupported path")
    save(output / "replay/README.md", f"# Synthetic replay fixture\n\nConstructed scores 160, 110, and 115 are not measurements. Outcomes: {outcomes}. Recorded cost units: {cost}. No environment fits occur. Proposal and replay-computation costs are not represented by those units.\n")

    advantage, updated = toy_policy_update([0, 0, 1, 1])
    record("Grouped signal signs", [a > 0 for a in advantage], [False, False, True, True])
    record("Equal rewards give zero centered signal", relative_advantages([1, 1, 1, 1]), [0.0] * 4)
    record("Toy probabilities sum to one", round(sum(updated), 12), 1.0)
    record("Toy preferred actions increase", updated[2] > 0.25, True)
    save(output / "grouped-rewards/README.md", f"# Numerical illustration\n\nSynthetic rewards: [0, 0, 1, 1]. Advantages: {advantage}.\n\nUniform initial probabilities: [0.25, 0.25, 0.25, 0.25]. After one toy update: {updated}.\n\nObjective: expected fixed advantage under a categorical softmax. Learning rate: 0.1. This is not token-level GRPO, LLM training, or a ScienceBuddy reproduction.\n")

    state = {"data": 0, "harness": 0, "model": 0, "version": 0}
    changed = operator(state, "harness", 0)
    record("Restricted operator write", (changed["data"], changed["harness"], changed["model"]), (0, 1, 0))
    try:
        operator(changed, "model", 0)
    except ValueError as error:
        record("Stale evidence rejected", str(error), "stale evidence")
    else:
        raise AssertionError("Stale evidence accepted")
    try:
        operator(changed, "evaluator", 1)
    except ValueError as error:
        record("Evaluator write rejected", str(error), "undeclared write surface")
    else:
        raise AssertionError("Evaluator write accepted")

    output.mkdir(parents=True, exist_ok=True)
    with (output / "checks.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["check", "observed", "expected", "status"])
        writer.writerows(checks)
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    save(output / "README.md", f"# Executed mechanism checks\n\n{len(checks)} checks passed. Source SHA-256: {code_hash}.\n\nThese are deterministic author checks of small mechanisms. They do not validate every learner prompt, independent agent context, teaching effectiveness, or any frontier paper result. Inputs and outputs marked synthetic are constructed fixtures.\n")
    return len(checks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"{run_checks(args.output)} mechanism checks passed")
