"""The improver: propose harness edits, evaluate them, keep or reject, repeat.

Everything is written to a run directory, one folder per candidate, in the
style of Meta-Harness: the proposer reads the archive of earlier candidates
(their files, scores and raw traces) rather than a compressed summary.

    runs/<name>/c000/harness/     the starting harness
    runs/<name>/c000/result.json  its evolve-set score and cost
    runs/<name>/c000/attempts/    every node of every attempt: code, output, validation
    runs/<name>/c001/meta.json    parent, proposed edits, refused edits, decision and reason

The regularizers come from RRSI (arXiv 2609.24972): a cosine edit budget, a
leakage critic that screens diffs before they are evaluated, a pruner that
deletes machinery without measured gain, and an acceptance rule with a noise
floor and a cost check. Each is a switch, so labs can turn them on one at a time.
"""

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import agent, edits, evaluate, llm

IMPROVER = Path(__file__).resolve().parents[1] / "improvers" / "i0"


@dataclass
class Policy:
    proposer_model: str = "gpt-5.4-mini"
    proposer_effort: str = "medium"
    evidence: str = "traces"      # "scores": per-competition scores only; "traces": raw attempt logs too
    k: int = 3                    # candidates per round
    budget_max: int = 4           # RRSI edit budget: most edits in one bundle, first round
    budget_min: int = 4           # ... last round (equal to budget_max: no schedule)
    critic: bool = False          # RRSI leakage critic
    prune: bool = False           # RRSI pruner
    accept: str = "greedy"        # "greedy": any higher score; "rrsi": noise floor + cost check
    replicas: tuple = (0, 1)
    cost_slack: float = 0.25      # rrsi: allowed relative cost growth ...
    cost_per_gain: float = 5.0    # ... plus this much per unit of score gain
    protocol: str = "propose.md"  # the improver's own instructions (lab 08 edits this file)
    extra: dict = field(default_factory=dict)


POLICY_KEYS = {"proposer_effort", "evidence", "k", "budget_max", "budget_min", "critic", "prune", "accept",
               "cost_slack", "cost_per_gain"}


def load_policy(improver_dir, **override):
    """An improver is a directory: propose.md (its instructions) and policy.json (its settings)."""
    data = json.loads((Path(improver_dir) / "policy.json").read_text(encoding="utf-8"))
    return Policy(**{**data, **override})


def budget(t, rounds, p):
    """RRSI eq. 4: b_t = ceil(b_min + (b_max - b_min) * (1 + cos(pi t / T)) / 2)."""
    return math.ceil(p.budget_min + (p.budget_max - p.budget_min) * 0.5 * (1 + math.cos(math.pi * t / max(1, rounds))))


# ---------------------------------------------------------------- the archive

def read(run, cid):
    d = Path(run) / cid
    out = {"id": cid, "dir": d, "meta": json.loads((d / "meta.json").read_text(encoding="utf-8"))}
    if (d / "result.json").exists():
        out["result"] = json.loads((d / "result.json").read_text(encoding="utf-8"))
    return out


def candidates(run):
    return [read(run, p.name) for p in sorted(Path(run).glob("c[0-9][0-9][0-9]"))]


def archive_table(run):
    rows = ["| id | parent | round | edits | evolve norm | cost | decision |", "|---|---|---|---|---|---|---|"]
    for c in candidates(run):
        m, r = c["meta"], c.get("result", {})
        rows.append(f"| {c['id']} | {m.get('parent') or '-'} | {m.get('round', 0)} | "
                    f"{'; '.join(m.get('edit_summary', [])) or '(start)'} | "
                    f"{r.get('score', float('nan')):.3f} | {r.get('cost', float('nan')):.0f} | {m.get('decision', '')} |")
    return "\n".join(rows)


def trace_digest(cand_dir, limit=1200):
    """Raw evidence for the proposer: every node of every attempt, outputs truncated, no hidden grades per node."""
    parts = []
    for f in sorted((Path(cand_dir) / "attempts").glob("*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        parts.append(f"### {a['competition']} replica {a['replica']}: final submission norm "
                     f"{a['final']['norm']:.2f} (1.0 = random-forest baseline)")
        for n in a["nodes"]:
            parts.append(f"- step {n['step']} {n['stage']}: ok={n['ok']} validation={n['val']} "
                         f"train-seconds={n['seconds']}. Plan: {n['plan'][:200]!r}")
            parts.append("  output tail: " + n["output"][-limit // 3:].replace("\n", " | "))
        best = a["best"]
        if best is not None:
            parts.append("  best node code (start):\n```python\n" + a["nodes"][best]["code"][:limit] + "\n```")
    return "\n".join(parts)


# ---------------------------------------------------------------- RRSI regularizers

def leakage_terms(competitions):
    """Words that identify a specific evolve competition: names, ids, distinctive column and class names."""
    ctx = agent.context(competitions)
    generic = {"id", "target", "label", "text", "train", "test", "submission", "sample", "score", "data",
               "class", "classification", "competition", "prediction", "predictions", "kaggle",
               # everyday column names: a skill that says "log-transform a price target" is general advice
               "price", "date", "year", "age", "sex", "race", "income", "category", "value", "count"}
    terms = set()
    for cid in competitions:
        terms |= {w for w in re.split(r"[-_]", cid) if len(w) >= 5}
        terms |= {w.lower() for w in ctx[cid].get("terms", [])}
    return sorted(t for t in terms if t.lower() not in generic and len(t) >= 3)


def critic(bundle, base_files, terms):
    """Reject edits that write evolve-specific names or values into the harness (RRSI leakage screening)."""
    hits = []
    for e in bundle:
        text = e.get("content") or ""
        old = base_files.get(e["file"], "")
        for t in terms:
            pat = re.compile(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", re.I)
            if pat.search(text) and not pat.search(old):
                hits.append(f"{e['file']} mentions {t!r}")
    return hits


def prune_bundle(run, best_id, delta):
    """Delete skill files whose introduction never bought a gain larger than the noise band."""
    best_files = edits.files(Path(run) / best_id / "harness")
    credit = {}
    for c in candidates(run):
        m = c["meta"]
        if m.get("decision") != "accepted":
            continue
        for e in m.get("edits", []):
            if e["file"].startswith("skills/") and e["action"] == "write":
                credit[e["file"]] = max(credit.get(e["file"], -1), m.get("gain", 0))
    dead = [f for f in best_files if f.startswith("skills/") and credit.get(f, 0) <= delta]
    return [{"file": f, "action": "delete", "why": f"pruner: no gain above noise ({credit.get(f, 0):+.3f})"}
            for f in dead]


def decide(new, best, p, delta):
    """Return (accept, reason). `new` and `best` are evaluate.Result."""
    gain = new.score - best.score
    if p.accept == "greedy":
        return gain > 0, f"gain {gain:+.3f}"
    if gain < -delta:
        return False, f"gain {gain:+.3f} below the noise floor -{delta:.3f}"
    rel_cost = (new.cost - best.cost) / max(best.cost, 1)
    if gain > delta:
        limit = p.cost_slack + p.cost_per_gain * gain
        return rel_cost <= limit, f"gain {gain:+.3f} > noise {delta:.3f}; cost {rel_cost:+.0%} (limit {limit:+.0%})"
    return rel_cost < -0.10, f"gain {gain:+.3f} within noise {delta:.3f}; accept only if 10% cheaper ({rel_cost:+.0%})"


# ---------------------------------------------------------------- the proposer

def propose(run, best_id, b, round_, j, p, improver_dir=IMPROVER):
    best_dir = Path(run) / best_id
    template = (Path(improver_dir) / p.protocol).read_text(encoding="utf-8")
    harness_text = "\n\n".join(f"=== {name} ===\n{text}" for name, text in edits.files(best_dir / "harness").items())
    evidence = trace_digest(best_dir) if p.evidence == "traces" else json.dumps(
        json.loads((best_dir / "result.json").read_text(encoding="utf-8"))["cells"], indent=1)
    prompt = agent.render(template, {"harness": harness_text, "archive": archive_table(run), "evidence": evidence,
                                     "budget": b, "best": best_id})
    text, pt, ct = llm.chat([{"role": "user", "content": prompt}], p.proposer_model, 1.0,
                            sample=round_ * 10 + j, max_tokens=6000, effort=p.proposer_effort)
    match = re.search(r"\{.*\}", text, re.S)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    return data.get("edits", [])[:b], data.get("hypothesis", ""), pt + ct


# ---------------------------------------------------------------- the loop

def start(run, harness_dir, competitions, p, progress=None):
    run = Path(run)
    c0 = run / "c000"
    if not (c0 / "result.json").exists():
        edits.apply(harness_dir, [], c0 / "harness")
        res = evaluate.evaluate(c0 / "harness", competitions, p.replicas, progress=progress, save_to=c0)
        (c0 / "meta.json").write_text(json.dumps({"parent": None, "round": 0, "decision": "start"}), encoding="utf-8")
        return res
    return load_result(c0, competitions, p)


def load_result(cdir, competitions, p):
    return evaluate.evaluate(Path(cdir) / "harness", competitions, p.replicas)  # replay: every call is cached


def evolve(run, harness_dir, competitions, rounds, p, progress=print, improver_dir=IMPROVER):
    """Hill-climb on the evolve competitions. Returns the id of the final harness."""
    run = Path(run)
    run.mkdir(parents=True, exist_ok=True)
    best_id, best = "c000", start(run, harness_dir, competitions, p)
    terms = leakage_terms(competitions) if p.critic else []
    progress(f"start c000: {best}")
    next_id = len(candidates(run))
    for t in range(rounds):
        b = budget(t, rounds, p)
        delta = evaluate.noise_band(best)
        base_files = edits.files(run / best_id / "harness")
        bundles = []
        for j in range(p.k):
            proposed, hypothesis, used = propose(run, best_id, b, t, j, p, improver_dir)
            bundles.append((proposed, hypothesis))
        if p.prune:
            dead = prune_bundle(run, best_id, delta)
            if dead:
                bundles.append((dead, "pruner: remove machinery without measured gain"))
        round_results = []
        for proposed, hypothesis in bundles:
            cid = f"c{next_id:03d}"
            next_id += 1
            cdir = run / cid
            meta = {"parent": best_id, "round": t + 1, "budget": b, "hypothesis": hypothesis, "edits": proposed}
            hits = critic(proposed, base_files, terms) if p.critic else []
            applied, refused = edits.apply(run / best_id / "harness", [] if hits else proposed, cdir / "harness")
            meta.update(edit_summary=[edits.summary(e) for e in applied], refused=refused, critic=hits)
            if hits or not applied:
                meta["decision"] = "rejected before evaluation: " + ("; ".join(hits) if hits else "no valid edits")
                (cdir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
                progress(f"round {t + 1} {cid}: {meta['decision'][:120]}")
                continue
            res = evaluate.evaluate(cdir / "harness", competitions, p.replicas, save_to=cdir)
            ok, reason = decide(res, best, p, delta)
            meta.update(decision="candidate" if ok else "rejected", reason=reason, gain=res.score - best.score)
            (cdir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
            progress(f"round {t + 1} {cid}: {res}  [{reason}] {'; '.join(meta['edit_summary'])[:160]}")
            if ok:
                round_results.append((res.score, -res.cost, cid, res))
        if round_results:
            _, _, winner, res = max(round_results)
            for _, _, cid, _ in round_results:
                m = json.loads((run / cid / "meta.json").read_text(encoding="utf-8"))
                m["decision"] = "accepted" if cid == winner else "rejected (another candidate won the round)"
                (run / cid / "meta.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
            best_id, best = winner, res
            progress(f"round {t + 1}: new best {best_id} {best}")
    (run / "BEST").write_text(best_id, encoding="utf-8")
    return best_id


def lineage(run, cid):
    out = []
    while cid:
        c = read(run, cid)
        out.append(c)
        cid = c["meta"].get("parent")
    return out[::-1]
