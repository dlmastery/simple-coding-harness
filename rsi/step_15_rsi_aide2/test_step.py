"""Step 15 - keep-if-better is evaluated across every problem under one metered budget; a rewrite that wins on
one problem and loses on the set is rejected; the guards are in every operator and a suspicious score is re-run."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, harness, packs, steps, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import aide_keep, execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402
from run import INNER, OUTER, VERIFIER, outer_step  # noqa: E402

CUR, _ = tasks.test_curriculum()
THREE = [CUR[0], CUR[1], CUR[5]]


def test_keep_if_better_is_evaluated_across_every_problem_under_one_metered_budget(tmp_path):
    work = steps.workspace(HERE, INNER, VERIFIER, OUTER, into=tmp_path / "w")
    result = outer_step(FakeModel(), work, THREE, tmp_path / "run", human=Human(["y"]))
    trace = TraceLog(tmp_path / "run" / "traces.jsonl")
    decision = trace.rows("keep_if_better")[-1]["info"]
    assert set(decision["gains"]) == {t["name"] for t in THREE}                          # every problem, not the last one
    assert decision["fits"]["before"] == decision["fits"]["after"] == 24 * len(THREE)      # one metered budget per lap
    meter = trace.rows("meter")[-1]["info"]
    assert meter["problems"] == sorted(t["name"] for t in THREE) and meter["tokens"] > 0 and meter["fits"] >= 24 * len(THREE)
    assert result["visit"]["patch"]["files"] == ["operators.md"]
    improve = next(l for l in (work[0] / "operators.md").read_text(encoding="utf-8").splitlines() if l.startswith("Improve:"))
    assert ("top three" in improve) == result["keep"]                                    # kept iff better on the set


def test_a_rewrite_that_wins_on_one_problem_and_loses_on_the_set_is_rejected():
    before = {"a": 0.90, "b": 0.90, "c": 0.90}
    keep, detail = aide_keep(before, {"a": 0.95, "b": 0.88, "c": 0.88})
    assert not keep and detail["outliers_discarded"] == ["a"] and detail["losses"] == 2   # the one win is an outlier, the set loses
    keep, detail = aide_keep(before, {"a": 0.91, "b": 0.895, "c": 0.895})
    assert not keep and detail["wins"] == 1 and detail["losses"] == 2                    # a modest win on one, a loss on the set
    keep, detail = aide_keep({"a": 0.9, "b": 0.9, "c": 0.9, "d": 0.9}, {"a": 1.2, "b": 0.89, "c": 0.89, "d": 0.89})
    assert not keep and detail["outliers_discarded"] == ["a"]                            # one lucky problem cannot carry it
    keep, detail = aide_keep(before, {"a": 0.91, "b": 0.905, "c": 0.90})
    assert keep and detail["total_gain"] == 0.015 and detail["losses"] == 0
    keep, detail = aide_keep(before, before)
    assert not keep and detail["total_gain"] == 0


def test_the_guards_are_in_every_operator_and_lint_refuses_one_without(tmp_path):
    work = steps.workspace(HERE, INNER, VERIFIER, OUTER, into=tmp_path / "w")
    text = (work[0] / "operators.md").read_text(encoding="utf-8")
    sections = text.split("\n## ")[1:]
    assert [s.splitlines()[0] for s in sections] == ["draft", "debug", "improve", "review"]
    assert all(packs.ANTI_OVERFIT in s for s in sections) and "fit the same recipe again" in text and "statistical layer" in text
    assert packs.lint_pack(work[0], THREE[0]) == []
    broken = text.replace(packs.ANTI_OVERFIT, "no guard here", 1)
    outer = harness.boot(work[2], THREE[0], run_dir=tmp_path / "run", target=work[0], arm="meta", quiet=True)
    (work[0] / "operators.md").write_text(broken, encoding="utf-8")
    assert any("lacks the anti-overfitting line" in p for p in packs.lint_pack(work[0], THREE[0]))
    recipe = {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    assert execute(outer, checks.call("patch_pack", files={"SKILL.md": {"after": "x"}}, recipe=recipe, summary="x")).startswith("Error: this meta pack may patch ['operators.md'] only")


def test_a_suspicious_score_is_re_run(tmp_path):
    easy = tasks.synth_task("t_easy", 9, n=400, seed=909, shift=1, imbalance=0.4, noise=0.05)   # a near-perfect table
    work = steps.workspace(HERE, INNER, VERIFIER, OUTER, into=tmp_path / "w")
    run = harness.boot(work[0], easy, run_dir=tmp_path / "run")
    harness.run(run, FakeModel())
    recipes = [r["recipe"] for r in run.fits]
    suspicious = [i for i, r in enumerate(run.fits) if r["val_score"] is not None and r["val_score"] >= 0.999]
    assert suspicious, "the easy table should produce a suspicious score"
    first = suspicious[0]
    assert recipes[first + 1] == recipes[first]                                          # re-run: the same recipe, one more fit
    assert run.budget.used == 24 and run.gate.result is not None                         # it cost a fit, and the budget held
