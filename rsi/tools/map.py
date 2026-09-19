"""map - lesson 17: the ladder with lessons 00-16 placed, every recorded learning curve side by side, the
file-and-approver table, the terminology, and every external number marked reported.

    python ../tools/map.py --lessons ..
    python ../tools/map.py --lessons .. --section curves

Reads the curve.json each lesson's curriculum skill left under runs/<pack>/ and names the lessons not run yet;
it invents nothing. Every number quoted from elsewhere is printed as *reported* with its source.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli  # noqa: E402

PARSER = cli.parser(__doc__, lessons={"required": True, "help": "the rsi/ directory (the lessons' parent)"},
                    section={"default": "all", "choices": ["all", "ladder", "curves", "files", "terms", "reported"]})

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
    ("09 meta harness", "SKILL.md policy line, schema.json forbid, memory.json", "the human (approval: human) or the private gate (approval: gate); versions/ + rollback.py"),
    ("10 Dream-RSI", "SKILL.md policy line, chosen by replay at zero fits", "the private gate; the policy library is fixed"),
    ("11 RSIAgent", "plan.json per phase; memory.json after score_test only", "the uncertainty rule; memory frozen at test"),
    ("12 ModularRSI", "one of modules/*.md", "the pool's private gate; the allow-list"),
    ("13 Recuris", "one skill card (+ its manifest line)", "the validation rule: the value won on this problem"),
    ("14 DGM lineage", "SKILL.md and loop.json (the harness source)", "the archive rule, the private gate, then the human"),
    ("15 AIDE2", "operators.md (one operator)", "keep-if-better across the set under one metered budget (meter.py --decide)"),
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

# where each lesson's curriculum skill leaves its curve on the real curriculum (curve.py writes it under runs/<pack>/)
CURVES = {
    "07 proof": "step_07_proof/runs/adult-income/curve.json",
    "09 meta (gate)": "step_09_rsi_meta_harness/runs/adult-income/curve.json",
    "10 Dream-RSI": "step_10_rsi_dream/runs/adult-income/curve.json",
    "11 RSIAgent": "step_11_rsi_agent/runs/adult-income-actor/curve.json",
    "13 Recuris": "step_13_rsi_skill_memory/runs/adult-income-skills/curve.json",
    "16 MetaSkill": "step_16_rsi_meta_skills/runs/adult-income/curve.json",
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




def load_curves(root):
    out = {}
    for label, rel in CURVES.items():
        path = Path(root) / rel
        out[label] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return out


def curves_table(curves):
    lines = ["Learning curves on the same curriculum (memory arm - control arm, best val, per problem):"]
    problems = next(([r["problem"] for r in c] for c in curves.values() if c), None)
    if problems is None:
        lines.append("  no lesson has been run yet: run a lesson's curriculum skill and curve.py writes its curve.json")
        return lines
    lines.append(f"  {'lesson':<18}" + "".join(f"{p[:14]:>15}" for p in problems) + f"{'wasted m/c':>12}")
    for label, curve in curves.items():
        if curve is None:
            lines.append(f"  {label:<18}  not run yet (run that lesson's curriculum skill)")
            continue
        rows = [r for r in curve if not r.get("missing")]
        gaps = {r["problem"]: r["gap_val"] for r in rows}
        wasted = f"{sum(r['wasted_memory'] for r in rows)}/{sum(r['wasted_control'] for r in rows)}"
        lines.append(f"  {label:<18}" + "".join(f"{gaps[p]:>+15.4f}" if p in gaps and gaps[p] is not None else f"{'-':>15}" for p in problems) + f"{wasted:>12}")
    return lines


def main(argv=None):
    a = PARSER.parse_args(argv)
    curves = load_curves(a.lessons)
    out = {
        "ladder": [{"rung": r, "lessons": l, "decision": d, "human": h} for r, l, d, h in LADDER],
        "curves": {label: (None if c is None else [{k: r.get(k) for k in ("problem", "gap_val", "gap_test", "wasted_memory", "wasted_control", "cards_active", "missing")} for r in c]) for label, c in curves.items()},
        "not_run": [label for label, c in curves.items() if c is None],
        "files": [{"lesson": l, "improved": w, "approved_by": who} for l, w, who in FILES],
        "terms": [{"term": t, "meaning": m} for t, m in TERMS],
        "reported": [{"claim": c, "source": s, "status": "reported"} for c, s in REPORTED],
    }
    text = []
    if a.section in ("all", "ladder"):
        text.append("The ladder (arXiv:2609.11873): rung | lessons | the decision the system takes | what stays human")
        text += [f"  {r}\n      lessons {', '.join(l)} | {d} | {h}" for r, l, d, h in LADDER]
    if a.section in ("all", "curves"):
        text += curves_table(curves)
    if a.section in ("all", "files"):
        text.append("What improved, and who approved it:")
        text += [f"  {l:<20} {w:<70} {who}" for l, w, who in FILES]
    if a.section in ("all", "terms"):
        text.append("Terminology:")
        text += [f"  {t:<26} {m}" for t, m in TERMS]
    if a.section in ("all", "reported"):
        text.append("Numbers quoted from elsewhere (every one *reported*, none measured here):")
        text += [f"  reported: {c} [{s}]" for c, s in REPORTED]
    out["table"] = "\n".join(text)
    return out if a.section == "all" else {a.section: out[a.section], "not_run": out["not_run"], "table": out["table"]}


if __name__ == "__main__":
    cli.main(main)
