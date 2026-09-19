"""Step 11 - RSIAgent: three packs. The curriculum pack chooses the experiments
(broad, then deep), the actor runs them, the verifier writes cards after the
test is scored. Memory is frozen while the actor runs and on the exam.

    FAKE_MODEL=1 python run.py             # the curriculum, then the exam
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import curriculum, harness, memory, steps, tasks  # noqa: E402

ACTOR, CURRICULUM, VERIFIER = "adult-income-actor", "adult-income-curriculum", "adult-income-verifier"


def agent_problem(model, packs, task, run_dir, *, seed=0, bar=None, frozen=False, quiet=True):
    """One problem, RSIAgent style: curriculum (broad) -> actor -> curriculum (deep) -> actor resumes to FREEZE and
    score_test -> verifier (unless frozen). Returns (scorecard, actor run)."""
    actor, curr, verifier = packs
    before = memory.load(actor / "memory.json")
    plan = harness.boot(curr, task, seed=seed, arm="memory", run_dir=run_dir, target=actor, quiet=quiet)
    harness.run(plan, model)                                                # broad: a plan before any fit
    run = harness.boot(actor, task, seed=seed, arm="memory", run_dir=run_dir, quiet=quiet)
    run.memory_frozen = True                                                # no card lands while the actor runs
    harness.run(run, model)                                                 # fits the broad plan, then waits
    plan = harness.boot(curr, task, seed=seed, arm="memory", run_dir=run_dir, target=actor, quiet=quiet)
    harness.run(plan, model)                                                # deep: from the broad results
    harness.resume(run, model, "plan.json was updated: continue with the new experiments.")
    if not frozen:
        ver = harness.boot(verifier, task, seed=seed, arm="memory", run_dir=run_dir, target=actor, quiet=quiet)
        harness.run(ver, model)
    return curriculum.scorecard_for(run, before, memory.load(actor / "memory.json"), bar), run


def main():
    model = harness.choose_model()
    packs = steps.workspace(HERE, ACTOR, CURRICULUM, VERIFIER)
    run_dir = steps.run_dir(HERE, "curriculum")
    curve = curriculum.run_curriculum(packs[0], packs[2], tasks.curriculum(), model, run_dir,
                                      memory_arm=lambda task, bar: agent_problem(model, packs, task, run_dir, bar=bar))
    curriculum.print_curve(curve)
    trace = harness.TraceLog(run_dir / "traces.jsonl")
    for row in curve:
        plans = trace.rows("plan", problem=row["problem"])
        print(f"  {row['problem']:<16} broad: {' '.join(plans[0]['info']['families'][:6])} ... | deep: {' '.join(plans[1]['info']['families'][:6])} ...")
    exam_dir = steps.run_dir(HERE, "exam")
    report = curriculum.run_exam(packs[0], tasks.exam(), model, exam_dir,
                                 memory_arm=lambda task, seed, bar: agent_problem(model, packs, task, exam_dir, seed=seed, bar=bar, frozen=True))
    curriculum.print_exam(report)


if __name__ == "__main__":
    main()
