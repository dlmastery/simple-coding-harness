"""Step 11 - the broad phase touches every family before the deep phase repeats one; the deep phase prefers the
family with the most faults; the memory is frozen before score_test and unchanged on the transfer table."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402
from run import ACTOR, CURRICULUM, VERIFIER, agent_problem  # noqa: E402

CUR, EXAM = tasks.test_curriculum()
T1 = CUR[0]


def one_problem(tmp_path, task=T1, frozen=False):
    pk = steps.workspace(HERE, ACTOR, CURRICULUM, VERIFIER, into=tmp_path / "w")
    card, run = agent_problem(FakeModel(), pk, task, tmp_path / "run", frozen=frozen)
    return card, run, pk, TraceLog(tmp_path / "run" / "traces.jsonl")


def test_broad_phase_touches_every_family_before_deep_repeats_one(tmp_path):
    card, run, pk, trace = one_problem(tmp_path)
    plans = trace.rows("plan", problem=T1["name"])
    assert [p["info"]["phase"] for p in plans] == ["broad", "deep"] and plans[0]["info"]["c"] > plans[1]["info"]["c"]
    broad = plans[0]["info"]["families"]
    assert set(broad[:3]) == {"logreg", "rf", "hgb"}                                     # every family, before any repeat
    assert len(broad) == 12 and all(set(broad[i:i + 3]) == {"logreg", "rf", "hgb"} for i in range(0, 12, 3))
    fits = trace.rows("fit", problem=T1["name"], arm="memory")
    assert [r["recipe"]["model"] for r in fits[:12]] == broad and card["fits_used"] == 24


def test_deep_phase_prefers_the_family_with_the_most_faults(tmp_path):
    card, run, pk, trace = one_problem(tmp_path)
    fits = trace.rows("fit", problem=T1["name"], arm="memory")
    baseline = fits[0]["val_score"]
    faults = {m: sum(1 for r in fits[:12] if r["recipe"]["model"] == m and (r["val_score"] is None or r["val_score"] < baseline)) for m in ("logreg", "rf", "hgb")}
    deep = trace.rows("plan", problem=T1["name"])[1]["info"]["families"]
    assert deep[0] == max(faults, key=faults.get) and max(faults.values()) > min(faults.values())
    assert [r["recipe"]["model"] for r in fits[12:]] == deep


def test_the_actor_proposes_nothing_of_its_own_and_waits_for_a_plan(tmp_path):
    card, run, pk, trace = one_problem(tmp_path)
    experiments = [e for p in trace.rows("plan", problem=T1["name"]) for e in p["info"]["families"]]
    assert [r["recipe"]["model"] for r in run.fits] == experiments
    waited = [m for m in run.messages if m["role"] == "assistant" and m.get("content", "") and "Plan exhausted" in m["content"]]
    assert len(waited) == 1 and "12 fits remain" in waited[0]["content"]
    assert execute(run, checks.call("write_plan", plan={})).startswith("Error: write_plan is not in this pack's tools.md")
    curr = pk[1]
    assert packs.lint_pack(curr, T1) == [] and packs.lint_pack(pk[0], T1) == []


def test_memory_is_frozen_before_score_test_and_unchanged_on_the_transfer_table(tmp_path):
    card, run, pk, trace = one_problem(tmp_path)
    rows = trace.rows()
    boot = next(i for i, r in enumerate(rows) if r["event"] == "boot" and r["info"]["pack"] == ACTOR)
    scored = next(i for i, r in enumerate(rows) if r["event"] == "score_test" and r["arm"] == "memory")
    assert not any(r["event"] == "card" for r in rows[boot:scored + 1])                  # nothing landed before the test
    assert any(r["event"] == "card" for r in rows[scored:]) and card["cards_added"] > 0    # the verifier wrote after it
    before = packs.checksums(pk[0])
    exam_card, exam_run = agent_problem(FakeModel(), pk, EXAM, tmp_path / "exam", frozen=True)
    assert packs.checksums(pk[0]) == {**before, "plan.json": packs.checksums(pk[0])["plan.json"]}   # only the plan differs
    assert TraceLog(tmp_path / "exam" / "traces.jsonl").rows("card") == [] and exam_card["cards_added"] == 0
    assert exam_card["test_scored_once"] and not exam_card["test_touched_before_freeze"]
