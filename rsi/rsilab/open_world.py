"""Harness^2 at laptop scale: improve the harness during each task, without a verifier.

Competitions arrive one at a time. The system never sees a hidden grade. For
each one it runs the contrastive improvement step of Harness^2 (arXiv 2610.14224):

  1. reference  run the current harness once
  2. propose    an editor writes an INVARIANT candidate (how to do ML engineering)
                and a DOMAIN candidate (what this kind of data needs)
  3. probe      run both on the same competition
  4. compose    a composer reads the behavioral contrast (did scripts run, what
                validation they reported, how long they took, what went wrong)
                and keeps only the edits the contrast supports
  5. deliver    run the composed harness; submit its best node

Then the recursion: lessons the contrast supported go into an improvement
library (EXPERIENCE.md). The library is what the editor reads first on the
next competition. The base harness itself is never inherited; only the
experience of editing it is.

Hidden grades are computed for the course's report only, after the stream.
"""

import json
import re
from pathlib import Path

from . import agent, edits, llm

EDITOR = """You edit the harness of an ML-engineering agent while it works on a Kaggle-style task.
No grader is available: you only see what the agent did and what validation it reported.

# Current harness
{harness}

# Improvement library: lessons from earlier tasks, with their evidence
{library}

# Reference run on this task
{reference}

Write two candidate edit bundles (at most 3 edits each):
- "invariant": changes that make the agent a better ML engineer on any task
  (validation protocol, debugging, use of time, planning). No dataset names.
- "domain": changes for the kind of data in this task (text, tabular, JSON, multi-label...).

Allowed files: system.md, draft.md, improve.md, debug.md (keep their {{placeholders}}),
skills/<name>.md, config.json keys steps, num_drafts, max_debug, preview_rows, temperature.

Reply with one JSON object only:
{{"invariant": {{"why": "...", "edits": [ ... ]}}, "domain": {{"why": "...", "edits": [ ... ]}}}}
Each edit is {{"file": ..., "action": "write"|"set"|"delete", "content"|"key"+"value": ...}}."""

COMPOSER = """You compose a harness for an ML-engineering agent from a behavioral contrast.
There is no grader. Validation numbers are self-reported by the agent's scripts and can be
wrong (leaky splits, a bug that scores the training data). Weigh plausibility, not just size.

{contrast}

Decide which candidate edits the evidence supports. Then state at most two lessons for
later tasks: general, without dataset names, each with the evidence that supports it.

Reply with one JSON object only:
{{"use": ["invariant", "domain"] (any subset, possibly empty),
 "lessons": [{{"when": "...", "do": "...", "evidence": "..."}}]}}"""


def behavior(att, lower):
    """What an operator could observe without a grader."""
    lines = []
    for n in att.nodes:
        lines.append(f"  step {n.step} {n.stage}: ran={'yes' if n.ok else 'no'} validation={n.val} "
                     f"seconds={n.seconds}  {n.plan[:120]!r}")
        if not n.ok:
            lines.append("    error tail: " + n.output[-300:].replace("\n", " | "))
    best = att.nodes[att.best].val if att.best is not None else None
    lines.append(f"  best self-reported validation: {best} ({'lower' if lower else 'higher'} is better)")
    return "\n".join(lines)


def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def step(h_dir, cid, library, out, model, replica=0, use_library=True):
    """One contrastive improvement step on one competition. Returns (delivered attempt, record)."""
    out = Path(out)
    lower = agent.context([cid])[cid]["lower"]
    h = agent.load_harness(h_dir)
    ref = agent.solve(h, cid, replica, out / "work")
    lib_text = library.read_text(encoding="utf-8") if use_library and library.exists() else "(empty)"
    harness_text = "\n\n".join(f"=== {k} ===\n{v}" for k, v in edits.files(h_dir).items())
    prompt = agent.render(EDITOR, {"harness": harness_text, "library": lib_text,
                                   "reference": behavior(ref, lower)}).replace("{{", "{").replace("}}", "}")
    plan = _json(llm.chat([{"role": "user", "content": prompt}], model, 1.0, sample=replica,
                          max_tokens=6000, effort="medium")[0])
    probes, record = {}, {"competition": cid, "reference": _summ(ref), "candidates": {}}
    for name in ("invariant", "domain"):
        bundle = (plan.get(name) or {}).get("edits", [])[:3]
        applied, refused = edits.apply(h_dir, bundle, out / name)
        att = agent.solve(agent.load_harness(out / name), cid, replica + 10 + len(probes), out / "work")
        probes[name] = (bundle, att)
        record["candidates"][name] = {"why": (plan.get(name) or {}).get("why", ""), "applied":
                                      [edits.summary(e) for e in applied], "refused": refused, "run": _summ(att)}
    contrast = f"Reference (current harness):\n{behavior(ref, lower)}\n\n" + "\n\n".join(
        f"Candidate {name}: {record['candidates'][name]['why']}\nEdits: {record['candidates'][name]['applied']}\n"
        f"{behavior(att, lower)}" for name, (_, att) in probes.items())
    decision = _json(llm.chat([{"role": "user", "content": agent.render(COMPOSER, {"contrast": contrast})
                               .replace("{{", "{").replace("}}", "}")}], model, 1.0, sample=replica,
                              max_tokens=4000, effort="medium")[0])
    use = [u for u in decision.get("use", []) if u in probes]
    composed = [e for u in use for e in probes[u][0]]
    edits.apply(h_dir, composed, out / "composed")
    delivered = agent.solve(agent.load_harness(out / "composed"), cid, replica + 20, out / "work") if use else ref
    record.update(use=use, lessons=decision.get("lessons", []), delivered=_summ(delivered))
    if use_library:
        with open(library, "a", encoding="utf-8") as f:
            for les in decision.get("lessons", []):
                f.write(f"- When {les.get('when', '?')}: {les.get('do', '?')} "
                        f"(evidence: {les.get('evidence', '?')})\n")
    (out / "record.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    return delivered, record


def _summ(att):
    return {"best_val": att.nodes[att.best].val if att.best is not None else None,
            "ran": sum(n.ok for n in att.nodes), "steps": len(att.nodes), "tokens": att.tokens,
            "seconds": round(att.exec_seconds, 1), "hidden_beats": att.final["beats"]}
