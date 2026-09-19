"""Running packs over the curriculum: one problem, the two arms, the sequence,
the exam - and the numbers every lesson reports.

`run_problem` boots the inner pack on one task (one arm, one seed), then the
verifier pack on the same log, and returns the scorecard. `run_curriculum`
does that for problems 1..n in order, carrying the pack forward, with a
MEMORY_OFF control arm on every problem at the same budget: the learning
curve is the memory arm minus the control arm, problem by problem. `run_exam`
boots the frozen pack on the held-out problem over several seeds. Nothing
here proposes a recipe; the packs do.
"""

import json

from common import harness, memory, scorecard, tasks
from common.packs import checksums


def run_problem(pack_dir, task, model, run_dir, *, seed=0, arm="memory", verifier_dir=None, memory_off=None,
                memory_frozen=False, human=None, quiet=True, bar=None):
    """Inner pack, then the verifier on its log (unless frozen or MEMORY_OFF). Returns (scorecard, inner run, verifier run).
    `bar` is the control arm's best val score on this problem and seed, the wasted-fits reference."""
    before = memory.load(pack_dir / "memory.json")
    inner = harness.boot(pack_dir, task, seed=seed, arm=arm, run_dir=run_dir, human=human, quiet=quiet, memory_off=memory_off)
    harness.run(inner, model)
    verifier = None
    if verifier_dir is not None and not inner.memory_off and not memory_frozen:
        verifier = harness.boot(verifier_dir, task, seed=seed, arm=arm, run_dir=run_dir, target=pack_dir, human=human, quiet=quiet)
        harness.run(verifier, model)
    after = memory.load(pack_dir / "memory.json")
    return scorecard_for(inner, before, after, bar), inner, verifier


def scorecard_for(run, cards_before, cards_after, bar=None):
    best_val, best_recipe = scorecard.best_of(run.fits)
    test_rows = run.trace.rows("score_test", problem=run.problem, arm=run.arm, seed=run.seed)
    fit_rows = run.trace.rows("fit", problem=run.problem, arm=run.arm, seed=run.seed)
    active_before = {memory.card_id(c) for c in cards_before if memory.active(c)}
    active_after = {memory.card_id(c) for c in cards_after if memory.active(c)}
    return scorecard.make_scorecard(
        problem=run.problem, arm=run.arm, seed=run.seed, n_fits=run.budget.n, fits_used=run.budget.used,
        wasted_fits=scorecard.wasted_fits(run.fits, bar), best_val_score=best_val, best_recipe=best_recipe,
        test_score=run.gate.result["test_score"] if run.gate.result else None,
        test_scored_once=len(test_rows) == 1,
        test_touched_before_freeze=any(r["info"]["fits_used"] < run.budget.n for r in test_rows) if test_rows else False,
        cards_active=len(active_after), cards_added=len(active_after - active_before),
        cards_demoted=len(active_before - active_after),
    )


def run_curriculum(pack_dir, verifier_dir, task_list, model, run_dir, *, seed=0, human=None, meta=None, quiet=True):
    """Problems in order, memory arm (learning) and MEMORY_OFF arm (control) each, the pack carried forward.
    `meta(task, index)` runs between problems when given (step 09). Returns the learning curve rows."""
    curve = []
    for i, task in enumerate(task_list, 1):
        control, _, _ = run_problem(pack_dir, task, model, run_dir, seed=seed, arm="control", memory_off=True, human=human, quiet=quiet)
        card, inner, _ = run_problem(pack_dir, task, model, run_dir, seed=seed, arm="memory", verifier_dir=verifier_dir, human=human, quiet=quiet,
                                     bar=control["best_val_score"])
        row = curve_row(i, task, card, control)
        if meta is not None:
            row["meta"] = meta(task, i)
        curve.append(row)
    with open(run_dir / "curve.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(curve, f, indent=1)
        f.write("\n")
    return curve


def curve_row(i, task, card, control):
    gap = None if card["best_val_score"] is None or control["best_val_score"] is None else round(card["best_val_score"] - control["best_val_score"], 4)
    test_gap = None if card["test_score"] is None or control["test_score"] is None else round(card["test_score"] - control["test_score"], 4)
    return {"index": i, "problem": task["name"], "title": task["title"], "memory": card, "control": control,
            "gap_val": gap, "gap_test": test_gap, "wasted_memory": card["wasted_fits"], "wasted_control": control["wasted_fits"],
            "cards_added": card["cards_added"], "cards_demoted": card["cards_demoted"], "cards_active": card["cards_active"]}


def run_exam(pack_dir, exam_task, model, run_dir, *, seeds=(0, 1, 2, 3, 4), quiet=True):
    """The frozen pack on the held-out problem: memory arm vs MEMORY_OFF arm per seed, no verifier, no card written."""
    cards = memory.load(pack_dir / "memory.json")
    before = checksums(pack_dir)
    results = []
    for seed in seeds:
        control, _, _ = run_problem(pack_dir, exam_task, model, run_dir, seed=seed, arm="control", memory_off=True, memory_frozen=True, quiet=quiet)
        mem, inner, _ = run_problem(pack_dir, exam_task, model, run_dir, seed=seed, arm="memory", memory_frozen=True, quiet=quiet,
                                    bar=control["best_val_score"])
        gap = round(mem["test_score"] - control["test_score"], 4)
        results.append({"seed": seed, "memory": mem, "control": control, "gap_test": gap,
                        "gap_val": round(mem["best_val_score"] - control["best_val_score"], 4),
                        # a win: a higher test score, or the same score reached with fewer wasted fits (same budget)
                        "win": gap > 0 or (gap == 0 and mem["wasted_fits"] < control["wasted_fits"])})
    profile = tasks.profile(exam_task)
    applicable = memory.applicable(cards, profile)
    best = [r["memory"]["best_recipe"] for r in results]
    did_not_transfer = [c for c in applicable if "prefer" in c["then"]
                        and sum(1 for b in best if b and b[c["then"]["field"]] == c["then"]["prefer"]) <= len(best) // 2]
    report = {"problem": exam_task["name"], "seeds": list(seeds), "results": results,
              "wins": sum(1 for r in results if r["win"]), "wins_on_score": sum(1 for r in results if r["gap_test"] > 0),
              "ties": sum(1 for r in results if r["gap_test"] == 0),
              "mean_gap_test": round(sum(r["gap_test"] for r in results) / len(results), 4),
              "cards_applicable": applicable, "did_not_transfer": did_not_transfer,
              "pack_unchanged": checksums(pack_dir) == before}
    with open(run_dir / "exam.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    return report


def print_curve(curve, out=print):
    out(f"{'#':>2} {'problem':<22} {'mem val':>8} {'ctl val':>8} {'gap':>7} {'mem test':>9} {'ctl test':>9} {'wasted m/c':>10} {'cards +/-/act':>13}")
    for r in curve:
        m, c = r["memory"], r["control"]
        out(f"{r['index']:>2} {r['problem']:<22} {m['best_val_score']:>8} {c['best_val_score']:>8} {r['gap_val']:>+7.4f} "
            f"{m['test_score']:>9} {c['test_score']:>9} {r['wasted_memory']:>4}/{r['wasted_control']:<5} "
            f"{r['cards_added']:>3}/{r['cards_demoted']}/{r['cards_active']}")


def print_exam(report, out=print):
    out(f"exam {report['problem']}: memory arm beats MEMORY_OFF on {report['wins']} of {len(report['seeds'])} seeds "
        f"({report['wins_on_score']} on test score, {report['ties']} same score; a tie won by fewer wasted fits), "
        f"mean test gap {report['mean_gap_test']:+.4f}; pack unchanged: {report['pack_unchanged']}")
    for r in report["results"]:
        out(f"  seed {r['seed']}: memory test {r['memory']['test_score']} val {r['memory']['best_val_score']} wasted {r['memory']['wasted_fits']} | "
            f"control test {r['control']['test_score']} val {r['control']['best_val_score']} wasted {r['control']['wasted_fits']} | "
            f"gap {r['gap_test']:+.4f} {'win' if r['win'] else 'loss'}")
    for c in report["did_not_transfer"]:
        out(f"  did not transfer: {json.dumps(c['if'])} -> {json.dumps(c['then'])} (evidence {c['evidence']}, counter {c['counter']})")
