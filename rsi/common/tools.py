"""The tool table: every tool a skill may name, and `execute()`, the one place
every call goes through.

Every tool is a gate. `fit_recipe` counts the budget and refuses a recipe a
forbid card rules out; `score_test` refuses before FREEZE and on a second
call; `write_card` refuses a card that names the test split or the intent;
`patch_pack` lands one proposal per visit, under the human or the private
gate, after a snapshot. The skill *says* the rule; the tool *enforces* it -
that is what makes a skill pack testable. An unknown, disallowed or malformed
call is an `Error:` result the model reads, never a crash.
"""

import json
import pickle
import shutil
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

from common import graph, memory, packs, recipe, tasks
from common.budget import BudgetExhausted
from common.gate import TestLocked
from common.recipe import validate as validate_recipe

TOOLS = {}     # name -> (function(run, **args), parameter schema)


def tool(name, **params):
    def register(fn):
        TOOLS[name] = (fn, params)
        return fn
    return register


def schemas_for(allowed):
    """OpenAI tool schemas for the allowed names, in tools.md order. A name the table lacks is skipped."""
    out = []
    for name in allowed:
        if name not in TOOLS:
            continue
        fn, params = TOOLS[name]
        out.append({"type": "function", "function": {
            "name": name, "description": (fn.__doc__ or "").strip().splitlines()[0],
            "parameters": {"type": "object", "properties": {k: {"type": t} for k, t in params.items()}, "required": list(params)},
        }})
    return out


def execute(run, call):
    """Turn one tool call into a result string. Never raises; unknown / disallowed / malformed -> `Error:`."""
    name = call.get("name")
    try:
        args = json.loads(call.get("arguments") or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:
        return f"Error: the arguments of {name} are not a JSON object: {e}"
    if name not in run.allowed:
        return f"Error: {name} is not in this pack's tools.md; it is not available"
    if name not in TOOLS:
        return f"Error: no tool named {name!r}"
    fn, params = TOOLS[name]
    if set(args) != set(params):
        return f"Error: {name} takes exactly {sorted(params)}, got {sorted(args)}"
    try:
        result = fn(run, **args)
    except (BudgetExhausted, TestLocked, ValueError, KeyError, FileNotFoundError) as e:
        return f"Error: {e}"
    except Exception as e:   # anything else the tool raises is still a result, not a crash
        return f"Error: {type(e).__name__}: {e}"
    return result if isinstance(result, str) else json.dumps(result, default=str)


# ------------------------------------------------------------------ the trainer's tools


@tool("load_splits")
def load_splits(run):
    """Load the problem's train / val splits and return its profile, metric and budget."""
    parts = run.splits
    run.loaded = True
    return {"profile": run.profile, "metric": run.task["metric"], "n_fits": run.budget.n,
            "sizes": {k: len(v) for k, v in parts.items() if k in ("train", "val")}}


def cards_for(run):
    """The cards that bind this run: the target pack's memory.json, unless MEMORY_OFF."""
    return [] if run.memory_off else memory.load(run.memory_path)


def do_fit(run, rec, error=None):
    """Count one fit, run it (or record the error), append the trace row. The budget counts errors too."""
    n = run.budget.spend()
    if error is None:
        fitted = tasks.fit_for(run.task, run.seed, rec)
        val, error = fitted["val_score"], fitted["error"]
    else:
        val = None
    row = {"recipe": rec, "val_score": val, "error": error}
    run.fits.append(row)
    run.trace.append(event="fit", problem=run.problem, arm=run.arm, seed=run.seed, recipe=rec, val_score=val, error=error,
                     info={"n": n})
    return {"n": n, "val_score": val, "error": error, "fits_left": run.budget.left, **({"FREEZE": True} if run.budget.frozen else {})}


@tool("fit_recipe", recipe="object")
def fit_recipe(run, recipe):
    """Fit one recipe on train, score it on val. Counts one fit; refuses a recipe a forbid card rules out."""
    rec = validate_recipe(recipe)
    if rec["model"] not in run.task["allowed_models"]:
        raise ValueError(f"model {rec['model']} is not allowed by the task")
    card = memory.forbidden(rec, cards_for(run), run.profile)
    if card is not None:
        raise ValueError(f"a forbid card rules this recipe out: {json.dumps(card['then'])} (no fit spent)")
    for rule in json.loads(run.files["schema.json"]).get("forbid", []):   # the schema's own forbids (a meta patch)
        if rec.get(rule["field"]) == rule["value"]:
            raise ValueError(f"schema.json forbids {rule['field']}={rule['value']!r} (no fit spent)")
    return do_fit(run, rec)


@tool("score_test", recipe="object")
def score_test(run, recipe):
    """Score one recipe on the locked test split. Allowed once, after FREEZE."""
    rec = validate_recipe(recipe)
    score = run.gate.score_once(rec)
    run.trace.append(event="score_test", problem=run.problem, arm=run.arm, seed=run.seed, recipe=rec, val_score=score,
                     info={"fits_used": run.budget.used})
    return {"test_score": score}


@tool("save_model", recipe="object")
def save_model(run, recipe):
    """Pickle the fitted pipeline of a recipe this run fitted into the run directory."""
    rec = validate_recipe(recipe)
    if not any(r["recipe"] == rec for r in run.fits):
        raise ValueError("save_model takes a recipe this run fitted")
    fitted = tasks.fit_for(run.task, run.seed, rec)
    path = run.run_dir / f"model_{run.problem}_{run.arm}_{run.seed}.pkl"
    with open(path, "wb") as f:
        pickle.dump(fitted["pipeline"], f)
    return f"saved {path.name}"


@tool("write_loop_log", entry="object")
def write_loop_log(run, entry):
    """Append one audit line to loop_log.jsonl. Nothing reads it back: there is no tool that does."""
    with open(run.run_dir / "loop_log.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"problem": run.problem, "arm": run.arm, **entry}) + "\n")
    return "logged"


@tool("walk_path", path_id="string")
def walk_path(run, path_id):
    """Walk one path of graph.json by id: fit the recipe it binds. An illegal path is skipped and counted."""
    g = json.loads(run.files["graph.json"])
    paths = {p["id"]: p for p in json.loads(run.files["paths.json"])}
    if path_id not in paths:
        raise ValueError(f"no path {path_id!r} in paths.json; the loop walks the paths it has, it does not invent one")
    reason = graph.why_illegal(g, paths[path_id])
    if reason:
        return do_fit(run, graph.path_recipe(paths[path_id]) or paths[path_id].get("bindings"), error=f"illegal path: {reason}")
    return do_fit(run, graph.path_recipe(paths[path_id]))


# ------------------------------------------------------------------ memory: the verifier's tools


@tool("read_memory")
def read_memory(run):
    """The cards of the target pack's memory.json, or a note that MEMORY_OFF is set."""
    if run.memory_off:
        return "(MEMORY_OFF: no cards this run)"
    return {"cards": cards_for(run), "profile": run.profile}


@tool("write_card", card="object")
def write_card(run, card):
    """Merge one card into memory.json: validated against memory.schema.json; refused if it names the test or the intent."""
    if run.memory_off:
        raise ValueError("MEMORY_OFF: no card is written this run")
    if run.memory_frozen:
        raise ValueError("the memory is frozen; no card lands until the next problem")
    schema = json.loads(run.files.get("memory.schema.json") or json.dumps(memory.CARD_SCHEMA))
    try:
        memory.validate_card(card, schema)
    except Exception as e:
        raise ValueError(f"not a card: {str(e).splitlines()[0]}")
    cards = memory.load(run.memory_path)
    was_active = {memory.card_id(c): memory.active(c) for c in cards}
    cards, added = memory.merge(cards, card)
    memory.save(run.memory_path, cards)
    merged = next(c for c in cards if memory.card_id(c) == memory.card_id(card))
    demoted = was_active.get(memory.card_id(card), False) and not memory.active(merged)
    run.trace.append(event="card", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"card": merged, "added": added, "demoted": demoted})
    return {"cards": len(cards), "added": added, "active": memory.active(merged), "demoted": demoted}


@tool("read_traces", scope="string")
def read_traces(run, scope):
    """The fit rows of this problem ("problem") or of every problem so far ("all"): recipe, val_score, error, profile only."""
    if scope not in ("problem", "all"):
        raise ValueError("scope is 'problem' or 'all'")
    match = {"problem": run.problem, "arm": run.arm} if scope == "problem" else {}
    rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"], "problem": r["problem"], "seed": r["seed"]}
            for r in run.trace.rows("fit", **match)]
    return {"rows": rows, "profile": run.profile}


# ------------------------------------------------------------------ the writers' tools


@tool("read_task")
def read_task(run):
    """The task.json this pack was booted for: target, metric, budget, allowed models, test rule, profile keys."""
    return run.task


@tool("lint_pack", files="object")
def lint_pack(run, files):
    """Lint a proposed pack ({path: text}) against the task and boot it dry. Returns "ok" or the problems."""
    if not isinstance(files, dict) or not all(isinstance(v, str) for v in files.values()):
        raise ValueError("files is {path: text}")
    tmp = Path(tempfile.mkdtemp(prefix="lint_"))
    try:
        packs.write_pack(tmp, files)
        problems = packs.lint_pack(tmp, run.task)
        if not problems:
            from common.harness import Run
            # a dry boot of each pack (a directory of packs has one per subdirectory): the prompt builds or it does not
            for pack_dir in ([tmp] if (tmp / "SKILL.md").exists() else sorted(p.parent for p in tmp.glob("*/SKILL.md"))):
                Run(pack_dir, run.task, run_dir=tmp / "dry", human=run.human, quiet=True)
    except Exception as e:
        problems = [f"dry boot failed: {e}"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return "ok" if not problems else {"problems": problems}


@tool("propose", kind="string", payload="object", summary="string")
def propose(run, kind, payload, summary):
    """Show a proposal (kind: pack | patch | text) to the human and return their decision: y, n or edit."""
    if kind not in ("pack", "patch", "text"):
        raise ValueError("kind is pack, patch or text")
    if kind == "pack":
        problems = lint_pack(run, payload)
        if problems != "ok":
            raise ValueError(f"lint_pack refuses this pack before the human sees it: {problems['problems']}")
    p = run.proposals.propose(kind, payload, summary)
    return {"id": p["id"], "decision": p["decision"]}


@tool("apply", id="string")
def apply(run, id):
    """Land an approved proposal on the target pack. Refuses one the human answered n to, or never saw."""
    if not run.proposals.approved(id):
        raise ValueError(f"proposal {id} is not approved; nothing lands")
    p = run.proposals.items[id]
    if p["applied"]:
        raise ValueError(f"proposal {id} was applied already")
    if p["kind"] == "pack":
        if run.target.exists():
            shutil.rmtree(run.target)
        packs.write_pack(run.target, p["payload"])
    elif p["kind"] == "patch":
        land_patch(run, p["payload"])
    else:
        raise ValueError("a text proposal has nothing to apply")
    p["applied"] = True
    run.trace.append(event="apply", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"proposal": id, "decision": p["decision"], "checksums": packs.checksums(run.target)})
    return f"applied {id} ({p['decision']}) to {run.target.name}"


# ------------------------------------------------------------------ the meta harness's tools


@tool("read_pack")
def read_pack(run):
    """Every file of the target pack, {path: text}."""
    return packs.read_pack(run.target)


def land_patch(run, patch):
    """Snapshot the target pack, then write the patched files. `versions/gen_NNN` is the rollback point."""
    label = f"gen_{len(list(run.versions_dir.glob('gen_*'))) + 1:03d}" if run.versions_dir.exists() else "gen_001"
    packs.snapshot(run.target, run.versions_dir, label)
    for name, change in patch["files"].items():
        path = run.target / name
        if change.get("after") is None:
            path.unlink(missing_ok=True)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(change["after"])
    return label


SIZE_CAP = 0.20   # a patch may change at most this share of the pack's text


@tool("patch_pack", files="object", recipe="object", summary="string")
def patch_pack(run, files, recipe, summary):
    """Propose one patch ({path: {after}}) with the recipe that motivates it; the human or the private gate decides; land it if approved."""
    if run.visits.get("patch_pack", 0) >= 1:
        raise ValueError("one proposal per visit; this visit already made one")
    run.visits["patch_pack"] = 1
    rec = validate_recipe(recipe)
    current = packs.read_pack(run.target)
    changes, changed_chars = {}, 0
    for name, change in files.items():
        if not isinstance(change, dict) or "after" not in change:
            raise ValueError("each file change is {after: text | null}")
        before, after = current.get(name) or "", change["after"] or ""
        changes[name] = {"before": current.get(name), "after": change["after"]}
        # the unmatched characters of the diff: a rewrite costs its length, a one-line change costs one line
        changed_chars += round((1 - SequenceMatcher(None, before, after).ratio()) * max(len(before), len(after)))
    total = sum(len(t) for t in current.values()) or 1
    if changed_chars > SIZE_CAP * total:
        raise ValueError(f"the patch changes {changed_chars} of {total} characters, more than {int(SIZE_CAP * 100)} % of the pack; one small change per generation")
    if "SKILL.md" in changes and changes["SKILL.md"]["after"] and "after FREEZE" not in changes["SKILL.md"]["after"]:
        raise ValueError("a patch may not remove the test rule from SKILL.md")
    payload = {"files": changes, "recipe": rec}
    mode = (run.meta.get("metadata") or {}).get("approval", "human")
    if mode == "gate":
        # the private gate: snapshot, land, score the evidence recipe on the private split; a loss rolls back
        label = land_patch(run, payload)
        verdict = private_gate(run, rec)
        p = {"id": f"g{len(run.proposals.items) + 1}", "kind": "patch", "payload": payload, "decision": "y" if verdict["keep"] else "n",
             "applied": verdict["keep"], "summary": summary}
        run.proposals.items[p["id"]] = p
        if not verdict["keep"]:
            packs.rollback(run.target, run.versions_dir, label)
            run.trace.append(event="rollback", problem=run.problem, arm=run.arm, seed=run.seed,
                             info={"proposal": p["id"], "version": label, "gate": verdict, "checksums": packs.checksums(run.target)})
            return {"id": p["id"], "decision": "n", "gate": verdict, "landed": False, "rolled_back_to": label}
    else:
        p = run.proposals.propose("patch", payload, summary)
        verdict = None
        if p["decision"] not in ("y", "edit"):
            run.trace.append(event="reject", problem=run.problem, arm=run.arm, seed=run.seed, info={"proposal": p["id"]})
            return {"id": p["id"], "decision": p["decision"], "landed": False}
        label = land_patch(run, p["payload"])
        p["applied"] = True
    run.trace.append(event="apply", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"proposal": p["id"], "decision": p["decision"], "version": label, "gate": verdict,
                           "checksums": packs.checksums(run.target)})
    return {"id": p["id"], "decision": p["decision"], "gate": verdict, "landed": True, "version": label}


def incumbent_recipe(run):
    """The recipe the current pack is standing on: the best val fit of the newest problem in the trace, else the baseline."""
    rows = run.trace.rows("fit")
    scored = [r for r in rows if r["val_score"] is not None]
    if not scored:
        return recipe.BASELINE
    last_problem = scored[-1]["problem"]
    return max((r for r in scored if r["problem"] == last_problem), key=lambda r: r["val_score"])["recipe"]


def private_gate(run, candidate):
    """Keep-or-rollback on the private split: the candidate recipe must not score below the incumbent."""
    before = tasks.score_on(run.task, run.seed, incumbent_recipe(run), "private")
    after = tasks.score_on(run.task, run.seed, candidate, "private")
    keep = after is not None and (before is None or after >= before)
    run.trace.append(event="gate", problem=run.problem, arm=run.arm, seed=run.seed, info={"before": before, "after": after, "keep": keep})
    return {"before": before, "after": after, "keep": keep}


@tool("private_score", recipe="object")
def private_score(run, recipe):
    """Score one recipe on the private split the inner pack never sees. Twice per visit at most: it is the gate's split."""
    if run.visits.get("private_score", 0) >= 2:
        raise ValueError("private_score twice per visit at most; repeated evaluator access is how gates get gamed")
    run.visits["private_score"] = run.visits.get("private_score", 0) + 1
    rec = validate_recipe(recipe)
    score = tasks.score_on(run.task, run.seed, rec, "private")
    run.trace.append(event="private_score", problem=run.problem, arm=run.arm, seed=run.seed, recipe=rec, val_score=score)
    return {"private_score": score}


@tool("rollback", version="string")
def rollback(run, version):
    """Restore the target pack from versions/<version>/."""
    packs.rollback(run.target, run.versions_dir, version)
    run.trace.append(event="rollback", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"version": version, "checksums": packs.checksums(run.target)})
    return f"rolled back to {version}"
