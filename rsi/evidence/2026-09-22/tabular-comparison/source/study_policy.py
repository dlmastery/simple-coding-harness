"""Frozen policies and role-file-driven updater; no access to final rows."""
import hashlib
from pathlib import Path
import random
import re

import pandas as pd

ARMS = ["fixed", "random", "memory", "parent", "harness", "updater"]
PREFIX = {
    "classification": ["base:linear", "base:extra-trees", "base:rbf-1", "base:hist-boost"],
    "regression": ["one:median-reference", "base:linear", "base:random-forest", "base:rbf-1"],
}
TAIL = {
    "classification": ["base:random-forest", "base:rbf-10", "base:neighbors-5", "base:neighbors-25"],
    "regression": ["base:extra-trees", "base:hist-boost", "base:rbf-10", "base:neighbors-5"],
}
ROLES = ["Analyzer", "Retriever", "Allocator", "Proposer", "Evolver"]
EXPECTED = {
    "v0": ["incumbent-only", "current-parent-only", "two-local", "bounded-local", "selection-loss-then-earlier"],
    "v1": ["gap-and-reference", "checked-global-ranks", "one-experience-one-local", "scoped-template-and-local", "selection-loss-then-earlier"],
}


def load_roles(directory, version):
    entries = []
    for role, expected in zip(ROLES, EXPECTED[version]):
        path = Path(directory) / version / f"{role}.md"
        raw = path.read_bytes()
        matches = re.findall(r"^Policy: (.+)$", raw.decode().strip(), re.M)
        if matches != [expected]:
            raise ValueError(f"Unrecognized {version}/{role} instruction")
        entries.append(dict(role=role, policy=matches[0], sha256=hashlib.sha256(raw).hexdigest()))
    return entries


def memory_order(experience, kind):
    data = experience[experience.kind == kind].copy()
    data["rank"] = data.groupby("task").selection_loss.rank(method="average")
    return data.groupby("candidate", as_index=False)["rank"].mean().sort_values(["rank", "candidate"]).candidate.tolist()


def winner(history):
    good = [r for r in history if r["status"] == "success"]
    if not good:
        raise ValueError("No valid incumbent; preserve failed study")
    return min(good, key=lambda r: (r["selection_loss"], r["step"]))


def variant(template, kind):
    if "rbf" in template or "svr" in template or "unscaled" in template:
        return "two:unscaled-c1" if kind == "classification" else "two:log-svr"
    if "forest" in template or "extra" in template:
        return "one:extra-leaf2" if kind == "classification" else "one:absolute-forest"
    if "boost" in template:
        return "two:native-category-boost" if kind == "classification" else "one:absolute-boost"
    if "median" in template:
        return "one:absolute-boost"
    return "one:rbf-wide" if kind == "classification" else "two:quadratic-splines"


def proposal(template, factor, parent_step, reason):
    return dict(template=template, factor=round(min(20., max(.05, factor)), 8), parent_step=parent_step, reason=reason)


def unique_local(template, factor, parent_step, reason, history, pending):
    used = {(r["template"], float(r["factor"])) for r in history + pending}
    # A bounded, predeclared collision rule prevents silently refitting the
    # exact same recipe. It is not allowed to inspect unobserved outcomes.
    for multiplier in (1., 1.1, .9, 1.25, .8, 1.5, .67):
        item = proposal(template, factor*multiplier, parent_step, reason)
        if (item["template"], item["factor"]) not in used:
            return item
    raise ValueError("No unique local proposal within the declared collision rule")


def make_plan(arm, task, kind, history, experience, role_directory):
    if len(history) not in (0, 4, 6):
        raise ValueError("Plans are written only before probes or a two-fit skill round")
    if not history:
        return [proposal(t, 1., 0, "common broad probe") for t in PREFIX[kind]], [], "Four common broad probes."
    incumbent = winner(history)
    parent_step = incumbent["step"]
    if arm == "fixed":
        return [proposal(t, 1., 0, "fixed conventional portfolio") for t in TAIL[kind]], [], "Fixed portfolio; no updater."
    order = memory_order(experience, kind)
    if arm == "memory":
        used = {r["template"] for r in history}
        chosen = [t for t in order if t not in used][:4]
        return [proposal(t, 1., 0, "frozen global-rank experience") for t in chosen], [], "Persistent memory is read; no new memory is written."
    if arm == "random":
        rng = random.Random(7341 + int(task))
        pool = sorted(t for t in experience[experience.kind == kind].candidate.unique() if "median" not in t)
        result = []
        for _ in range(4):
            template = rng.choice(pool)
            result.append(unique_local(template, 10**rng.uniform(-1, 1), 0, "seeded conventional random search", history, result))
        return result, [], "Random control uses the full revised builder space."
    version = "v1" if arm == "updater" else "v0"
    roles = load_roles(role_directory, version)
    config = {r["role"]: r["policy"] for r in roles}
    gap = incumbent["selection_loss"] - incumbent["train_loss"]
    diagnosis = "incumbent selected by checked selection loss"
    if config["Analyzer"] == "gap-and-reference":
        diagnosis = "overfit gap" if gap > .15 else "representation or local-capacity question"
        if kind == "regression" and not any(r["template"] == "one:median-reference" for r in history):
            raise ValueError("Required median reference is missing")
        if "median" in incumbent["template"]:
            diagnosis = "no checked feature model beats the median reference"
    template = incumbent["template"]
    if "median" in template:
        template = "base:hist-boost"
    factor = float(incumbent["factor"])
    result = []
    if config["Allocator"] == "one-experience-one-local":
        if config["Retriever"] != "checked-global-ranks" or config["Proposer"] != "scoped-template-and-local":
            raise ValueError("Incoherent revised role contract")
        used = {r["template"] for r in history}
        alternative = next(t for t in order if t not in used)
        result.append(proposal(alternative, 1., parent_step, "checked experience supplies a different template"))
        direction = .3 if gap > .15 else 3.
        result.append(unique_local(template, factor*direction, parent_step, diagnosis, history, result))
    else:
        if config["Retriever"] != "current-parent-only" or config["Proposer"] != "bounded-local":
            raise ValueError("Incoherent parent role contract")
        lower = variant(template, kind) if arm == "harness" else template
        result.append(unique_local(lower, factor*.3, parent_step, "lower-capacity branch; revised harness may change representation" if arm == "harness" else "lower-capacity local branch", history, result))
        result.append(unique_local(template, factor*3., parent_step, "higher-capacity local branch", history, result))
    if config["Evolver"] != "selection-loss-then-earlier":
        raise ValueError("External selection semantics cannot change")
    return result, roles, diagnosis
