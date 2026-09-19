"""Step 10 - Dream-RSI: after every problem the meta pack replays the log as a
simulator, ranks the search policies at zero fits, and proposes the winner as
the actor's policy line under the approval cycle.

    FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py     # scripted approvals; drop HUMAN to answer yourself
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, steps, tasks  # noqa: E402

ACTOR, VERIFIER, META = "adult-income", "adult-income-verifier", "adult-income-meta-dream"


def run_generations(model, problems, run_dir, human=None, into=None, quiet=True):
    """Lesson 09's inner -> verifier -> meta -> inner sequence with the Dream-RSI meta pack."""
    actor, verifier, meta = steps.workspace(HERE, ACTOR, VERIFIER, META, into=into)
    visit = lambda task, i: curriculum.meta_visit(meta, actor, task, model, run_dir, human=human, quiet=quiet)  # noqa: E731
    curve = curriculum.run_curriculum(actor, verifier, problems, model, run_dir, human=human, meta=visit, quiet=quiet)
    return curve, actor, run_dir


def main():
    model = harness.choose_model()
    run_dir = steps.run_dir(HERE, "curriculum")
    curve, actor, _ = run_generations(model, tasks.curriculum(), run_dir, quiet=False)
    curriculum.print_curve(curve)
    for row, rank in zip(curve, harness.TraceLog(run_dir / "traces.jsonl").rows("rank_policies")):
        top = rank["info"]["ranking"][0]
        print(f"  after problem {row['index']}: log {rank['info']['log_size']} recipes, fits spent {rank['info']['fits_spent']}; "
              f"winner {top['policy']} (best logged {top['best_logged_val']}, unknown {top['unknown']}); patch {json.dumps(row['meta']['patch'])}")
    print("policy line now: " + next(l.strip() for l in (actor / "SKILL.md").read_text(encoding="utf-8").splitlines() if "Search policy:" in l))


if __name__ == "__main__":
    main()
