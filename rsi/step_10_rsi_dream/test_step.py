"""Step 10 - rank_policies spends no fit; a policy that prefers unvisited recipes scores unknown; the winner is
proposed as the search-policy line and the next lap visits new recipes."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, harness, recipe, steps, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402
from run import ACTOR, META, run_generations  # noqa: E402

CUR, _ = tasks.test_curriculum()
T1, T3 = CUR[0], CUR[2]
POLICIES = ["static", "obey-memory", "random", "neighbours-of-top-3", "prefer-untried-family"]


def static_log(tmp_path):
    """One static run of the actor on T1, then the dream meta booted on that log."""
    actor, meta = steps.workspace(HERE, ACTOR, META, into=tmp_path / "w")
    checks.run_pack(actor, T1, FakeModel(), tmp_path / "run", arm="control", memory_off=True)
    dream = harness.boot(meta, T1, run_dir=tmp_path / "run", target=actor, arm="meta")
    return actor, dream


def test_rank_policies_makes_zero_fits(tmp_path):
    actor, dream = static_log(tmp_path)
    fits_before = len(TraceLog(tmp_path / "run" / "traces.jsonl").rows("fit"))
    result = json.loads(execute(dream, checks.call("rank_policies", names=POLICIES)))
    assert result["fits_spent"] == 0 and dream.budget.used == 0 and dream.budget.n == 0
    assert len(TraceLog(tmp_path / "run" / "traces.jsonl").rows("fit")) == fits_before
    assert execute(dream, checks.call("fit_recipe", recipe=recipe.BASELINE)).startswith("Error: fit_recipe is not in this pack's tools.md")
    assert [e["policy"] for e in result["ranking"]] and len(result["ranking"]) == 5


def test_a_policy_preferring_unvisited_recipes_scores_unknown(tmp_path):
    actor, dream = static_log(tmp_path)
    result = json.loads(execute(dream, checks.call("rank_policies", names=POLICIES)))
    by = {e["policy"]: e for e in result["ranking"]}
    log_best = max(r["val_score"] for r in TraceLog(tmp_path / "run" / "traces.jsonl").rows("fit"))
    assert by["static"]["unknown"] == 0 and by["static"]["visited"] == 24 and by["static"]["best_logged_val"] == log_best
    assert by["random"]["unknown"] > 0 and by["random"]["visited"] + by["random"]["unknown"] == 24
    assert by["random"]["best_logged_val"] <= log_best                                   # the log cannot credit what it never saw
    assert not result["saturated"]
    assert execute(dream, checks.call("rank_policies", names=["walk-on-water"])).startswith("Error: unknown search policy")


def test_the_winner_is_proposed_and_the_next_lap_visits_new_recipes(tmp_path):
    run_dir = tmp_path / "run"
    curve, actor, _ = run_generations(FakeModel(), [T1, T3], run_dir, human=Human(["y", "y"]), into=tmp_path / "w")
    trace = TraceLog(run_dir / "traces.jsonl")
    ranking = trace.rows("rank_policies")[0]["info"]["ranking"]
    winner = ranking[0]["policy"]
    assert winner != "static" and curve[0]["meta"]["patch"]["landed"]
    line = next(l.strip() for l in (actor / "SKILL.md").read_text(encoding="utf-8").splitlines() if "Search policy:" in l)
    assert line.startswith("Search policy:") and trace.rows("rank_policies")[1]["info"]["ranking"][0]["policy"] in POLICIES
    lap1 = {recipe.key(r["recipe"]) for r in trace.rows("fit", problem=T1["name"])}
    lap2 = {recipe.key(r["recipe"]) for r in trace.rows("fit", problem=T3["name"], arm="memory")}
    assert lap2 - lap1, "the next lap must visit recipes the log had never seen"
    assert (run_dir / "versions" / "gen_001" / "SKILL.md").exists()
