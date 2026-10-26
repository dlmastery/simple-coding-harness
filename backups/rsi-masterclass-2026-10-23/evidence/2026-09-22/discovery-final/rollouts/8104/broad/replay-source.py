"""Recorded discovery trees and a shared policy interface for bounded runs.

This implements replay semantics, not an autonomous policy-development agent.
No counterfactual score is synthesized for an unrecorded continuation.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Observation:
    node: str
    parent: str
    status: str
    loss: float | None
    seconds: float


@dataclass(frozen=True)
class View:
    observations: tuple[Observation, ...]
    remaining_rounds: int

    @property
    def eligible(self) -> tuple[str, ...]:
        parents = {item.parent for item in self.observations}
        return ("root",) + tuple(item.node for item in self.observations if item.node not in parents)

    @property
    def best_loss(self) -> float | None:
        values = [item.loss for item in self.observations if item.loss is not None]
        return min(values) if values else None


Policy = Callable[[View], str | None]


class World:
    """An ordered, immutable record. Non-root nodes have one continuation at most."""

    def __init__(self, observations: tuple[Observation, ...]):
        seen = {"root"}
        expanded = set()
        for item in observations:
            if not item.node or item.node in seen or item.parent not in seen:
                raise ValueError("Duplicate node or parent missing before child")
            if item.parent != "root" and item.parent in expanded:
                raise ValueError("A non-root node cannot have multiple recorded continuations")
            if item.status not in ("ok", "failed", "timeout"):
                raise ValueError("Only terminal attempts belong in a replay world")
            if not math.isfinite(item.seconds) or item.seconds < 0:
                raise ValueError("Every attempt needs a finite nonnegative cost")
            if item.status == "ok":
                if item.loss is None or not math.isfinite(item.loss):
                    raise ValueError("A successful attempt needs a finite loss")
            elif item.loss is not None:
                raise ValueError("Failed attempts must not acquire invented scores")
            expanded.add(item.parent)
            seen.add(item.node)
        self.observations = observations

    @classmethod
    def read(cls, path: Path) -> World:
        with path.open(encoding="utf-8", newline="") as stream:
            return cls(tuple(Observation(row["node"], row["parent"], row["status"],
                                         float(row["loss"]) if row["loss"] else None,
                                         float(row["seconds"])) for row in csv.DictReader(stream)))

    def continuation(self, parent: str, revealed: set[str]) -> Observation | None:
        return next((item for item in self.observations
                     if item.parent == parent and item.node not in revealed), None)


@dataclass(frozen=True)
class Replay:
    observations: tuple[Observation, ...]
    decisions: tuple[tuple[str, str], ...]
    terminal: str

    @property
    def best_loss(self) -> float | None:
        return View(self.observations, 0).best_loss

    @property
    def represented_seconds(self) -> float:
        return sum(item.seconds for item in self.observations)

    @property
    def unknown_requests(self) -> int:
        return sum(child == "UNKNOWN" for _, child in self.decisions)


def replay(world: World, policy: Policy, rounds: int) -> Replay:
    """Policy sees only revealed nodes. Unknown requests consume a decision round.

    W=1 is the laptop adaptation. Recorded fit cost is represented cost, not
    the much smaller wall time consumed by this replay calculation.
    """
    if rounds < 1:
        raise ValueError("A positive round limit is required")
    observed: list[Observation] = []
    decisions: list[tuple[str, str]] = []
    terminal = "round_limit"
    for step in range(rounds):
        if len(observed) == len(world.observations):
            terminal = "world_exhausted"
            break
        view = View(tuple(observed), rounds - step)
        parent = policy(view)
        if parent is None:
            terminal = "policy_stop"
            break
        if parent not in view.eligible:
            raise ValueError("Policy selected an unobserved node or a non-leaf parent")
        child = world.continuation(parent, {item.node for item in observed})
        decisions.append((parent, child.node if child is not None else "UNKNOWN"))
        if child is not None:
            observed.append(child)
    return Replay(tuple(observed), tuple(decisions), terminal)


def diverse_then_greedy(view: View) -> str:
    """Conventional fixed control: three independent drafts, then best leaf."""
    if sum(item.parent == "root" for item in view.observations) < 3:
        return "root"
    leaves = [item for item in view.observations if item.node in view.eligible and item.loss is not None]
    return min(leaves, key=lambda item: item.loss).node if leaves else "root"
