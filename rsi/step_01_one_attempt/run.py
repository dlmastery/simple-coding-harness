"""Lab 01 - one attempt: the frozen model, the harness, and one graded submission."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rsilab import agent, course  # noqa: E402

course.banner("Lab 01 · one attempt")

COMPETITION = "adult"
h = agent.load_harness(course.H0)
print(f"frozen model: {h['config']['model']}   steps: {h['config']['steps']}   "
      f"system prompt: {len(agent.system_prompt(h))} characters, skills: {len(h['skills'])}\n")

att = agent.solve(h, COMPETITION, replica=0, workdir=course.RUNS / "01-work")

rows = []
for n in att.nodes:
    hidden = n.grade["score"] if n.grade else None
    rows.append([n.step, n.stage, "yes" if n.ok else "no", f"{n.val:.4f}" if n.val is not None else "-",
                 f"{hidden:.4f}" if hidden is not None else "-", f"{n.seconds:.0f}s", n.plan[:60].replace("\n", " ")])
course.table(rows, ["step", "stage", "ran", "validation (self-reported)", "hidden test score", "train", "plan"])

final = att.final
print(f"agent's choice: step {att.best} (best self-reported validation; {COMPETITION} metric: AUC, higher is better)")
print(f"hidden grade:   AUC {final['score']}, norm {final['norm']:.2f} "
      f"(0 = constant predictor, 1 = random forest), beats the forest: {final['beats_forest']}")
print(f"cost:           {att.tokens:,} model tokens, {att.exec_seconds:.0f} s of training\n")
course.spend()
