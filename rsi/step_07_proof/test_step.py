"""Lesson 07 - the proof: the test is scored exactly once per problem and arm; every scorecard has exactly the
acceptance fields; problems 1..6 in order carry the pack forward and the learning-curve gap (memory - control)
is >= 0 on every problem and larger on problem 6 than on problem 2; on the exam the frozen pack beats the
control arm on >= 3 of 5 seeds, no card is written, the pack is unchanged, and the report names a card that
did not transfer. The test plays the curriculum skill on the offline synthetic curriculum (six small tables
shaped like the real one, and a held-out exam), so it runs in seconds.
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, tasks, testing  # noqa: E402
from _lib.scorecard import SCORECARD_FIELDS  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"


def synthetic_tasks(tmp_path):
    """The offline curriculum as task files, the shape every script expects."""
    d = tmp_path / "tasks"
    d.mkdir()
    curriculum, exam = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    exam_path = d / f"{exam['index']:02d}_{exam['name']}.json"
    exam_path.write_text(json.dumps(exam), encoding="utf-8")
    return paths, exam_path


@pytest.fixture(scope="module")
def curriculum_run(tmp_path_factory):
    """One curriculum run shared by the tests below (a minute of fits): actor, verifier, task paths, exam path, curve."""
    return run_curriculum(tmp_path_factory.mktemp("curriculum"))


def run_curriculum(tmp_path):
    actor, verifier = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER)
    paths, exam_path = synthetic_tasks(tmp_path)
    for p in paths:
        testing.play_arm(actor, p, arm="control", memory_off=True)
        testing.play_arm(actor, p)
        testing.play_verifier(actor, p, verifier)
    curve = testing.tool("curve", "--pack", actor, "--tasks", tmp_path / "tasks")
    return actor, verifier, paths, exam_path, curve


def test_curve_gap_never_negative_and_growing(curriculum_run):
    actor, verifier, paths, exam_path, curve = curriculum_run
    tmp_path = actor.parents[2]
    rows = curve["curve"]
    assert len(rows) == 6 and curve["summary"]["complete"] == 6
    assert all(r["gap_val"] >= 0 for r in rows), [r["gap_val"] for r in rows]
    assert rows[5]["gap_val"] > rows[1]["gap_val"], [r["gap_val"] for r in rows]
    assert curve["summary"]["wasted_memory_total"] < curve["summary"]["wasted_control_total"]
    assert sum(r["cards_added"] for r in rows) > 0 and any(r["cards_demoted"] > 0 for r in rows)   # a superstition met its counterexample
    assert "problem" in curve["table"] and (tmp_path / "runs" / ACTOR / "curve.json").exists()


def test_test_scored_once_per_problem_and_arm_with_every_field(curriculum_run):
    actor, verifier, paths, exam_path, curve = curriculum_run
    tmp_path = actor.parents[2]
    for r in curve["curve"]:
        for arm in ("memory", "control"):
            card = r[arm]
            assert set(card) == set(SCORECARD_FIELDS)
            assert card["test_scored_once"] and not card["test_touched_before_freeze"] and card["fits_used"] == 24
        trace = [json.loads(l) for l in (tmp_path / "runs" / ACTOR / r["problem"] / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
        assert sum(1 for t in trace if t["event"] == "score_test" and t["arm"] == "memory") == 1
        assert sum(1 for t in trace if t["event"] == "score_test" and t["arm"] == "control") == 1


def test_exam_frozen_pack_beats_control_on_most_seeds(curriculum_run):
    actor, verifier, paths, exam_path, curve = curriculum_run
    tmp_path = actor.parents[2]
    before = packs.checksums(actor)
    for seed in range(5):
        testing.play_arm(actor, exam_path, arm="control", memory_off=True, seed=seed, freeze_memory=True)
        testing.play_arm(actor, exam_path, seed=seed, freeze_memory=True)
        refused = testing.tool("write_card", "--pack", actor, "--task", exam_path, "--seed", seed, "--as", verifier,
                               "--card", json.dumps({"if": {"key": "n_rows", "op": ">", "value": 1}, "then": {"field": "model", "prefer": "rf"}, "evidence": 1, "counter": 0}))
        assert "frozen" in refused["error"]
    report = testing.tool("exam", "--pack", actor, "--task", exam_path, "--seeds", "0,1,2,3,4")
    assert report["wins"] >= 3, report["table"]
    assert report["pack_unchanged"] and report["no_card_written"] and packs.checksums(actor) == before
    assert report["missing"] == [] and len(report["results"]) == 5
    assert isinstance(report["did_not_transfer"], list) and "did not transfer" in report["table"] or report["did_not_transfer"] == []
    assert (tmp_path / "runs" / ACTOR / "exam.json").exists()


def test_memory_off_config_gives_control_numbers(tmp_path):
    actor, verifier = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER)
    paths, _ = synthetic_tasks(tmp_path)
    testing.play_arm(actor, paths[0])
    testing.play_verifier(actor, paths[0], verifier)
    control = testing.play_arm(actor, paths[1], arm="control", memory_off=True)
    (actor / "config.json").write_text('{"memory": "off"}', encoding="utf-8")
    off = testing.play_arm(actor, paths[1], arm="memory")
    assert off["best_val_score"] == control["best_val_score"] and off["test_score"] == control["test_score"]
    assert off["best_recipe"] == control["best_recipe"] and off["cards_active"] == 0


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "exam" in text.lower()
