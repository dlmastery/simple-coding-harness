"""The claim checks steps share, so a generated pack can be held to the same
tests as the hand-written one it imitates (step 03 reuses step 02's checks,
step 08 reuses step 06's). Each returns plain values; the step's test asserts.
"""

import json

from common import harness, packs
from common.tools import execute


def call(name, **args):
    return {"id": f"chk_{name}", "name": name, "arguments": json.dumps(args)}


def tool_calls(run, name=None):
    """The (name, args) of every tool call in a run's transcript, optionally one tool's."""
    out = []
    for m in run.messages:
        for c in m.get("tool_calls") or []:
            if name is None or c["function"]["name"] == name:
                out.append((c["function"]["name"], json.loads(c["function"]["arguments"] or "{}")))
    return out


def tool_results(run, name):
    """The result strings of one tool's calls, in order."""
    ids = {c["id"] for m in run.messages for c in m.get("tool_calls") or [] if c["function"]["name"] == name}
    return [m["content"] for m in run.messages if m["role"] == "tool" and m["tool_call_id"] in ids]


def run_pack(pack_dir, task, model, run_dir, **kw):
    session = harness.boot(pack_dir, task, run_dir=run_dir, **kw)
    harness.run(session, model)
    return session


def budget_and_gate(run):
    """After a full run: the 25th fit and the second score_test are Error results, not exceptions."""
    fit_25 = execute(run, call("fit_recipe", recipe=run.fits[0]["recipe"]))
    test_2 = execute(run, call("score_test", recipe=run.fits[0]["recipe"]))
    return {"fits_used": run.budget.used, "n_fits": run.budget.n, "fit_25": fit_25, "second_test": test_2,
            "test_scored_once": len(run.trace.rows("score_test", problem=run.problem, arm=run.arm, seed=run.seed)) == 1}


def test_before_freeze(pack_dir, task, run_dir):
    """A fresh boot: score_test before any fit is refused with the lock message."""
    fresh = harness.boot(pack_dir, task, run_dir=run_dir, arm="probe")
    return execute(fresh, call("score_test", recipe={"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}))


def unchanged(pack_dir, action):
    """Checksums before and after `action()`: True when the pack is byte-identical."""
    before = packs.checksums(pack_dir)
    action()
    return packs.checksums(pack_dir) == before


def fit_sequence(run):
    return [(r["recipe"], r["val_score"]) for r in run.fits]


def verifier_isolation(actor, verifier):
    """What the verifier saw: whether any actor message text reached it, and the keys of the rows it read."""
    actor_texts = {str(m.get("content")) for m in actor.messages if m["role"] == "assistant" and m.get("content")}
    verifier_text = "\n".join(str(m.get("content") or "") for m in verifier.messages)
    leaked = [t for t in actor_texts if t in verifier_text]
    rows = json.loads(tool_results(verifier, "read_traces")[0])["rows"] if tool_results(verifier, "read_traces") else []
    keys = sorted({k for r in rows for k in r})
    return {"leaked": leaked, "row_keys": keys, "system_has_actor_skill": "## Procedure\n1. Call `load_splits`" in verifier.system}
