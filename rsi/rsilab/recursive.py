"""Improving the improver: the step that makes self-improvement recursive.

Three objects, kept apart on purpose:

    the agent's output     a submission                        (changed by the agent)
    the harness            harnesses/<h>/                       (changed by an improver)
    the improver           improvers/<i>/propose.md, policy.json (changed by the meta-improver)

`meta_step` reads one improver's complete run (every proposal, every decision
and its reason, and how its final harness did on competitions the improver
never saw) and writes a revised improver. `compare` then gives both improvers
the same starting harness, the same budget and the same evolve competitions,
and scores the harnesses they produce on held-out and OOD competitions.

A revised improver counts as a recursive gain only if (a) it was actually used
to produce the later harness, and (b) that harness beats the one produced by
the old improver under the same conditions. AIDE^2 (arXiv 2609.26457) runs this
loop with the improver and the agent being the same code; here they are kept
separate so each claim can be checked.
"""

import json
import re
import shutil
from pathlib import Path

from . import edits, evaluate, improve, llm, mle

META = """You are improving an IMPROVER: a procedure that edits the harness of an ML-engineering agent.
The improver's instructions are propose.md; its settings are policy.json.

# The improver
=== propose.md ===
{propose}
=== policy.json ===
{policy}

# Its last run on the evolve competitions
{archive}

# How the harness it produced did on competitions it never saw
{transfer}

Diagnose what made this improver weak: which proposals it wasted, which decisions let noise or
overfitting through, what it ignored. Then revise it. You may rewrite propose.md (it must keep the
placeholders {{harness}}, {{archive}}, {{evidence}}, {{budget}}) and set policy.json keys:
evidence ("scores"|"traces"), k (1-4), budget_max, budget_min (1-6), critic (bool), prune (bool),
accept ("greedy"|"rrsi"), cost_slack, cost_per_gain, proposer_effort ("low"|"medium"|"high").

Reply with one JSON object only:
{{"diagnosis": "...", "propose_md": "<full new file or null>", "policy": {{"key": value, ...}}}}"""

PLACEHOLDERS = ["{harness}", "{archive}", "{evidence}", "{budget}"]


def transfer_report(product_dir, competitions, replicas=(0, 1)):
    res = evaluate.evaluate(Path(product_dir), competitions, replicas)
    return res, "\n".join(f"- {c}: beats {v:.2f} of Kaggle teams" for c, v in res.per_competition().items())


def meta_step(improver_dir, run_dir, out_dir, transfer_text, model="gpt-5.5", sample=0):
    """Write a revised improver to out_dir. Returns (diagnosis, refused_reasons)."""
    improver_dir, out_dir = Path(improver_dir), Path(out_dir)
    prompt = (improve.agent.render(META, {
        "propose": (improver_dir / "propose.md").read_text(encoding="utf-8"),
        "policy": (improver_dir / "policy.json").read_text(encoding="utf-8"),
        "archive": improve.archive_table(run_dir), "transfer": transfer_text})
        .replace("{{", "{").replace("}}", "}"))
    text, _, _ = llm.chat([{"role": "user", "content": prompt}], model, 1.0, sample=sample,
                          max_tokens=8000, effort="high")
    m = re.search(r"\{.*\}", text, re.S)
    data = json.loads(m.group(0)) if m else {}
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(improver_dir, out_dir)
    refused = []
    new_md = data.get("propose_md")
    if new_md:
        missing = [p for p in PLACEHOLDERS if p not in new_md]
        if missing:
            refused.append(f"propose.md lost placeholders {missing}")
        else:
            (out_dir / "propose.md").write_text(new_md.rstrip() + "\n", encoding="utf-8")
    policy = json.loads((out_dir / "policy.json").read_text(encoding="utf-8"))
    for k, v in (data.get("policy") or {}).items():
        if k in improve.POLICY_KEYS:
            policy[k] = v
        else:
            refused.append(f"policy key {k!r} is not editable")
    (out_dir / "policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    (out_dir / "DIAGNOSIS.md").write_text(data.get("diagnosis", "") + "\n", encoding="utf-8")
    return data.get("diagnosis", ""), refused


def run_improver(improver_dir, run_dir, start_harness, rounds, progress=print):
    p = improve.load_policy(improver_dir)
    best = improve.evolve(run_dir, start_harness, mle.SPLITS["evolve"], rounds, p, progress, improver_dir)
    return Path(run_dir) / best / "harness"


def provenance(run_dir, improver_dir):
    """Evidence that the revised improver governed the run: its protocol text is in every proposal prompt."""
    return {"improver": str(improver_dir), "propose_md": (Path(improver_dir) / "propose.md").read_text(encoding="utf-8")[:200],
            "candidates": len(improve.candidates(run_dir)) - 1}
