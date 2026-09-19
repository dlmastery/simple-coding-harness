"""Step 15 - AIDE2: the inner pack is an AIDE-style tree search over solutions
(draft / debug / improve, with a reviewer and three guards); the outer loop
rewrites the operator text and keeps the rewrite only if it beats the previous
operators across the whole curriculum under the same fits budget, after the
statistical layer drops outlier successes.

    FAKE_MODEL=1 HUMAN=script:y python run.py
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, packs, steps, tasks  # noqa: E402
from common.tools import aide_keep  # noqa: E402

INNER, VERIFIER, OUTER = "adult-income-aide", "adult-income-verifier", "aide-outer"


def lap(model, inner, verifier, problems, run_dir, arm, quiet=True):
    """The inner pack over every problem under one arm name: per-problem best val, and the fits spent."""
    scores = {}
    for task in problems:
        card, run, _ = curriculum.run_problem(inner, task, model, run_dir, arm=arm, verifier_dir=verifier, quiet=quiet)
        scores[task["name"]] = card["best_val_score"]
    fits = len(harness.TraceLog(run_dir / "traces.jsonl").rows("fit", arm=arm))
    return scores, fits


def outer_step(model, work, problems, run_dir, human=None, quiet=True):
    """One AIDE2 outer step: lap with the current operators, one rewrite, lap with the rewrite, keep-if-better."""
    inner, verifier, outer = work
    before, fits_before = lap(model, inner, verifier, problems, run_dir, "operators-v1", quiet=quiet)
    visit = curriculum.meta_visit(outer, inner, problems[-1], model, run_dir, human=human, quiet=quiet)
    if not (visit["patch"] or {}).get("landed"):
        return {"before": before, "after": None, "keep": False, "detail": "no rewrite landed", "visit": visit, "fits": (fits_before, 0)}
    after, fits_after = lap(model, inner, verifier, problems, run_dir, "operators-v2", quiet=quiet)
    keep, detail = aide_keep(before, after)
    if not keep:
        packs.rollback(inner, run_dir / "versions", visit["patch"]["version"])
    harness.TraceLog(run_dir / "traces.jsonl").append(event="keep_if_better", problem=problems[-1]["name"], arm="outer", seed=0,
                                                     info={"keep": keep, **detail, "fits": {"before": fits_before, "after": fits_after}})
    return {"before": before, "after": after, "keep": keep, "detail": detail, "visit": visit, "fits": (fits_before, fits_after)}


def main():
    model = harness.choose_model()
    work = steps.workspace(HERE, INNER, VERIFIER, OUTER)
    run_dir = steps.run_dir(HERE, "outer")
    result = outer_step(model, work, tasks.curriculum(), run_dir, quiet=False)
    print(f"meter: {json.dumps(harness.TraceLog(run_dir / 'traces.jsonl').rows('meter')[-1]['info'])}")
    print(f"rewrite: {json.dumps(result['visit']['patch'])}")
    print(f"{'problem':<16} {'v1 best val':>12} {'v2 best val':>12} {'gain':>8}")
    for p, b in result["before"].items():
        a = (result["after"] or {}).get(p)
        print(f"{p:<16} {b:>12} {a if a is not None else '-':>12} {(a - b) if a is not None else 0:>+8.4f}")
    print(f"fits per lap: v1 {result['fits'][0]}, v2 {result['fits'][1]}; keep-if-better across the set: {result['keep']} {json.dumps(result['detail'])}")
    improve = next(l for l in (work[0] / "operators.md").read_text(encoding="utf-8").splitlines() if l.startswith("Improve:"))
    print(f"operators.md now: {improve}")


if __name__ == "__main__":
    main()
