"""Step 17 - the map: the ladder with lessons 01-16 placed, every method's
learning curve on the same curriculum side by side (from the curve.json each
lesson's run.py wrote), and the file-by-file table of what changed and who
approved it.

    python run.py                 # reads the runs that exist; says which lessons have not been run yet
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

ROOT = HERE.parent

# the ladder: rung -> lessons, the decision the system takes, what stays human
LADDER = [
    ("not RSI (B0 / AutoML / harness engineering)", ["01", "02", "04"], "none: a fixed procedure", "everything"),
    ("L1  what to improve, how, success - specified by humans; AI executes a generation procedure", ["00", "03", "05", "08"], "renders a pack from task.json", "the spec, the acceptance (y / n / edit), the verifier contract"),
    ("L2  how to improve: the search strategy", ["10", "12"], "ranks policies on the log; names the module to patch", "the policy library, the module boundaries, the pool"),
    ("L3  which experience to acquire", ["11"], "picks the next experiments by uncertainty", "the uncertainty rule, the phase lengths"),
    ("L4  revise persistent state from deployment feedback under an acceptance rule", ["06", "07", "09 (human)", "13"], "writes and demotes cards; one patch per generation", "the verifier contract, the off switches, the human at the prompt"),
    ("L5 flavour  revise the improver / verifier / successor procedure itself", ["09 (gate)", "14", "15", "16"], "rewrites its own policy line, source, operators, meta-skills", "the gate, the archive rule, the budget, the clock, the human on the slow clock"),
]

# every lesson: which file improved, and who approved it
FILES = [
    ("01 regular", "nothing", "nobody (nothing changes)"),
    ("02 loop", "nothing (loop.json is read, the audit log is never read back)", "nobody"),
    ("03 loop writer", "a whole loop pack is generated", "the human: y / n / edit on the whole pack"),
    ("04 graph", "nothing (graph.json and paths.json are mutable: false)", "nobody"),
    ("05 graph writer", "a whole graph pack is generated", "the human, after lint_pack; edit lands the human's graph"),
    ("06 RSI harness", "memory.json (cards)", "the verifier contract, written by the human"),
    ("07 proof", "memory.json over problems 1-6; nothing on the exam", "the evaluator is frozen: split, metric, seeds"),
    ("08 RSI writer", "actor + verifier packs generated", "the human approves the verifier contract explicitly"),
    ("09 meta harness", "SKILL.md policy line, schema.json forbid, memory.json", "the human (approval: human) or the private gate (approval: gate); versions/ + rollback"),
    ("10 Dream-RSI", "SKILL.md policy line, chosen by replay at zero fits", "the human; the policy library is fixed"),
    ("11 RSIAgent", "plan.json per phase; memory.json after score_test only", "the uncertainty rule; memory frozen at test"),
    ("12 ModularRSI", "one of modules/*.md", "the pool's private gate; the allow-list"),
    ("13 Recuris", "one skill card (+ its manifest line)", "the validation rule: the value won on this problem"),
    ("14 DGM lineage", "SKILL.md and loop.json (the harness source)", "the archive rule, the private gate, then the human"),
    ("15 AIDE2", "operators.md (one operator)", "the human, then keep-if-better across the set under one budget"),
    ("16 MetaSkill-Evolve", "task skills every problem; roles/*.md every k problems", "the gate (fast clock); the human (slow clock)"),
]

# the six words, and what each means here
TERMS = [
    ("self-refine", "a better answer this turn, nothing persists (B0). Lesson 01 with a smarter prompt would still be this."),
    ("learning", "persistent state changes from feedback: memory.json after lesson 06. Necessary, not sufficient."),
    ("self-organise / emergence", "structure that nobody wrote appears; nothing in this series claims it."),
    ("AutoML", "a fixed search over a fixed space: lessons 01-05, however fancy the graph."),
    ("bounded RSI", "the loop revises its own state or procedure inside limits a human set: lessons 06-16, every one with an off switch."),
    ("genuine RSI", "closed loops with persistence, transferred and attributed autonomy, verified inheritance under matched budgets - the paper's bar; not reached here, and said so."),
]

# where each lesson's run.py leaves its curve on the real curriculum
CURVES = {
    "07 proof": "step_07_proof/runs/curriculum/curve.json",
    "09 meta (human)": "step_09_rsi_meta_harness/runs/curriculum_human/curve.json",
    "09 meta (gate)": "step_09_rsi_meta_harness/runs/curriculum_gate/curve.json",
    "10 Dream-RSI": "step_10_rsi_dream/runs/curriculum/curve.json",
    "11 RSIAgent": "step_11_rsi_agent/runs/curriculum/curve.json",
    "13 Recuris": "step_13_rsi_skill_memory/runs/curriculum/curve.json",
    "14 DGM": "step_14_rsi_self_modifying/runs/curriculum/curve.json",
    "16 MetaSkill": "step_16_rsi_meta_skills/runs/curriculum/curve.json",
}

# numbers this series quotes from elsewhere: every one is *reported*, none is measured here
REPORTED = [
    ("Headroom-Closed Index: advanced mathematics 86.4, graduate science 85.8, software engineering 52.6, search / terminal agents 56.8, tool agents 39.9", "arXiv:2609.11873v2"),
    ("Goedel Agent lost ground in 14 % of trials", "arXiv:2609.11873v2, Challenge 1"),
    ("DGM raised SWE-bench 20 -> 50 % with a human-fixed archive and parent rule", "arXiv:2609.11873v2 / arXiv:2505.22954"),
    ("A-Evolve-Training 0.80 -> 0.86 over four rounds", "arXiv:2609.11873v2"),
    ("Recuris +32.2 on the longest tasks", "arXiv:2608.24876"),
    ("AIDE2: seven successive improved versions in 100 outer steps, 16x context compression", "Weco AI tech report, July 2026; code not released"),
    ("the tutorial's 162x, 71.97 -> 78.98, 47.57 -> 52.43, 8xA100", "the source tutorial; not in the papers' abstracts"),
]


def load_curves():
    out = {}
    for label, rel in CURVES.items():
        path = ROOT / rel
        out[label] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return out


def print_ladder(out=print):
    out("The ladder (arXiv:2609.11873): rung | lessons | the decision the system takes | what stays human")
    for rung, lessons, decision, human in LADDER:
        out(f"  {rung}\n      lessons {', '.join(lessons)} | {decision} | {human}")


def print_curves(curves, out=print):
    out("\nLearning curves on the same curriculum (memory arm - MEMORY_OFF arm, best val, per problem):")
    problems = None
    for label, curve in curves.items():
        if curve:
            problems = [r["problem"] for r in curve]
            break
    if problems is None:
        out("  no lesson has been run yet: FAKE_MODEL=1 python run.py in a lesson writes its curve.json")
        return
    out(f"  {'lesson':<18}" + "".join(f"{p[:14]:>15}" for p in problems) + f"{'wasted m/c':>12}")
    for label, curve in curves.items():
        if curve is None:
            out(f"  {label:<18}" + "  not run yet (FAKE_MODEL=1 python run.py in that lesson)")
            continue
        gaps = {r["problem"]: r["gap_val"] for r in curve}
        wasted = f"{sum(r['wasted_memory'] for r in curve)}/{sum(r['wasted_control'] for r in curve)}"
        out(f"  {label:<18}" + "".join(f"{gaps.get(p, float('nan')):>+15.4f}" for p in problems) + f"{wasted:>12}")


def print_files(out=print):
    out("\nWhat improved, and who approved it:")
    for lesson, what, who in FILES:
        out(f"  {lesson:<20} {what:<70} {who}")


def print_terms(out=print):
    out("\nTerminology:")
    for term, meaning in TERMS:
        out(f"  {term:<26} {meaning}")


def print_reported(out=print):
    out("\nNumbers quoted from elsewhere (every one *reported*, none measured here):")
    for claim, source in REPORTED:
        out(f"  reported: {claim} [{source}]")


def main():
    print_ladder()
    print_curves(load_curves())
    print_files()
    print_terms()
    print_reported()


if __name__ == "__main__":
    main()
