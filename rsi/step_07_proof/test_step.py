"""Step 07 - test scored once per problem; every scorecard field present; the learning curve over the curriculum
is never negative and grows; the frozen pack beats MEMORY_OFF on the exam and the report names a card that did
not transfer. One curriculum run and one exam run, shared by the tests (module scope: ~40 s on this machine)."""

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, memory, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.scorecard import SCORECARD_FIELDS  # noqa: E402
from common.trace import TraceLog  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"
CUR, EXAM = tasks.test_curriculum()


@pytest.fixture(scope="module")
def proof(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("proof")
    actor, verifier = steps.workspace(HERE, ACTOR, VERIFIER, into=tmp / "w")
    curve = curriculum.run_curriculum(actor, verifier, CUR, FakeModel(), tmp / "run")
    checksums = packs.checksums(actor)
    report = curriculum.run_exam(actor, EXAM, FakeModel(), tmp / "exam")
    return {"actor": actor, "curve": curve, "report": report, "trace": TraceLog(tmp / "run" / "traces.jsonl"),
            "exam_trace": TraceLog(tmp / "exam" / "traces.jsonl"), "checksums_before_exam": checksums}


def test_test_is_scored_exactly_once_per_problem_and_arm(proof):
    for task in CUR:
        for arm in ("memory", "control"):
            assert len(proof["trace"].rows("score_test", problem=task["name"], arm=arm, seed=0)) == 1
    for row in proof["curve"]:
        for arm in ("memory", "control"):
            assert row[arm]["test_scored_once"] and not row[arm]["test_touched_before_freeze"]
    for r in proof["report"]["results"]:
        assert len(proof["exam_trace"].rows("score_test", problem=EXAM["name"], arm="memory", seed=r["seed"])) == 1


def test_every_scorecard_field_is_present(proof):
    for row in proof["curve"]:
        for arm in ("memory", "control"):
            assert tuple(row[arm]) == SCORECARD_FIELDS
    eval_md = (HERE / "skills" / ACTOR / "eval.md").read_text(encoding="utf-8")
    assert all(field in eval_md for field in SCORECARD_FIELDS)                      # eval.md names them all
    assert "`test_touched_before_freeze` must be `no`" in eval_md


def test_the_pack_is_carried_forward_and_the_learning_curve_grows(proof):
    curve = proof["curve"]
    assert [r["index"] for r in curve] == [1, 2, 3, 4, 5, 6]
    assert all(r["gap_val"] >= 0 for r in curve)
    assert curve[5]["gap_val"] > curve[1]["gap_val"]
    assert curve[0]["cards_active"] > 0 and curve[5]["cards_active"] >= curve[1]["cards_active"]   # carried forward
    assert sum(r["wasted_memory"] for r in curve) < sum(r["wasted_control"] for r in curve)
    boots = [b for b in proof["trace"].rows("boot", arm="memory") if b["info"]["pack"] == ACTOR]
    assert boots[-1]["info"]["checksums"]["memory.json"] != boots[0]["info"]["checksums"]["memory.json"]


def test_the_frozen_pack_beats_memory_off_on_the_exam(proof):
    report = proof["report"]
    assert len(report["seeds"]) == 5 and report["wins"] >= 3
    assert report["pack_unchanged"] and packs.checksums(proof["actor"]) == proof["checksums_before_exam"]
    assert proof["exam_trace"].rows("card") == []                                    # frozen: nothing written
    assert report["did_not_transfer"], "the report names the cards that did not transfer"
    for c in report["did_not_transfer"]:
        assert memory.active(c) and memory.matches(c, tasks.profile(EXAM))
