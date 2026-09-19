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
from fnmatch import fnmatch
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


def actor_arm(run):
    """Whose fits a pack reads: its own arm's, or - for a meta pack booted as `meta` - the memory arm's."""
    return "memory" if run.arm == "meta" else run.arm


@tool("read_traces", scope="string")
def read_traces(run, scope):
    """The fit rows of this problem ("problem") or of every problem so far ("all"): recipe, val_score, error, profile only."""
    if scope not in ("problem", "all"):
        raise ValueError("scope is 'problem' or 'all'")
    match = {"problem": run.problem, "arm": actor_arm(run), "seed": run.seed} if scope == "problem" else {}
    rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"], "problem": r["problem"], "seed": r["seed"],
             **({"arm": r["arm"]} if scope == "all" else {})}     # the arm only across problems: one problem's rows are one arm's
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
    rec = validate_recipe(recipe)
    current = packs.read_pack(run.target)
    allowed_paths = (run.meta.get("metadata") or {}).get("patches")   # the files this meta pack may touch, as globs
    changes, changed_chars = {}, 0
    for name, change in files.items():
        if not isinstance(change, dict) or "after" not in change:
            raise ValueError("each file change is {after: text | null}")
        if allowed_paths and not any(fnmatch(name, pat) for pat in allowed_paths):
            raise ValueError(f"this meta pack may patch {allowed_paths} only, not {name}")
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
    run.visits["patch_pack"] = 1      # a proposal that passed the checks is this visit's one proposal
    mode = (run.meta.get("metadata") or {}).get("approval", "human")
    if mode in ("gate", "both"):
        # the private gate: snapshot, land, score the evidence recipe on the private split; a loss rolls back
        label = land_patch(run, payload)
        verdict = private_gate(run, rec)
        p = {"id": f"g{len(run.proposals.items) + 1}", "kind": "patch", "payload": payload, "decision": "y" if verdict["keep"] else "n",
             "applied": verdict["keep"], "summary": summary}
        run.proposals.items[p["id"]] = p
        if verdict["keep"] and mode == "both":       # the gate kept it; now the human sees the diff and decides
            human = run.proposals.propose("patch", payload, summary)
            p["decision"], p["payload"] = human["decision"], human["payload"]
            if p["decision"] == "edit":
                packs.rollback(run.target, run.versions_dir, label)
                land_patch(run, p["payload"])
        if p["decision"] not in ("y", "edit"):
            p["applied"] = False
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
                           "files": sorted(changes), "checksums": packs.checksums(run.target)})
    return {"id": p["id"], "decision": p["decision"], "gate": verdict, "landed": True, "version": label, "files": sorted(changes)}


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


# ------------------------------------------------------------------ lesson 10: Dream-RSI


@tool("rank_policies", names="array")
def rank_policies(run, names):
    """Replay this problem's log as a simulator: each named policy's best logged val among its first n_fits picks; a pick not in the log is unknown. Zero fits."""
    from common.policies import policy_order

    rows = run.trace.rows("fit", problem=run.problem)
    logged = {recipe.key(r["recipe"]): r["val_score"] for r in rows if r["val_score"] is not None}
    schema = json.loads((run.target / "schema.json").read_text(encoding="utf-8"))
    static, forbid, cards, profile = schema.get("recipes", recipe.static_list()), schema.get("forbid", []), cards_for(run), run.profile
    ranking = []
    for name in names:
        fits, tried, unknown = [], [], 0
        for n in range(1, schema["n_fits"] + 1):
            pick = next((r for r in policy_order(name, static, cards, profile, fits, seed=0, forbid=forbid) if r not in tried), None)
            if pick is None:
                break
            tried.append(pick)
            if recipe.key(pick) in logged:      # the log answers for free
                fits.append(({"recipe": pick}, {"n": n, "val_score": logged[recipe.key(pick)]}))
            else:                               # the gym is silent here: the policy would have to fit to know
                unknown += 1
        best = max((r["val_score"] for _, r in fits), default=None)
        # an adaptive policy whose next pick depends on an unknown result stops early: the gym is silent there
        ranking.append({"policy": name, "best_logged_val": best, "visited": len(fits), "unknown": unknown,
                        "stopped_early": len(fits) + unknown < schema["n_fits"]})
    # the best logged score wins; at a tie the policy that would visit more new places wins - a lap that
    # revisits the log learns nothing
    ranking.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
    run.trace.append(event="rank_policies", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"ranking": ranking, "fits_spent": 0, "log_size": len(logged)})
    return {"ranking": ranking, "fits_spent": 0, "saturated": all(e["unknown"] == 0 for e in ranking)}


# ------------------------------------------------------------------ lesson 11: RSIAgent


@tool("write_plan", plan="object")
def write_plan(run, plan):
    """Write plan.json into the actor pack: {phase: broad | deep, c: number, experiments: [recipes]}. The actor fits them in order."""
    if not isinstance(plan, dict) or plan.get("phase") not in ("broad", "deep") or not isinstance(plan.get("experiments"), list):
        raise ValueError("a plan is {phase: broad | deep, c: number, experiments: [recipes]}")
    experiments = [validate_recipe(r) for r in plan["experiments"]]
    if not experiments:
        raise ValueError("a plan needs at least one experiment")
    plan = {"phase": plan["phase"], "c": float(plan.get("c", 0)), "experiments": experiments}
    with open(run.target / "plan.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    run.trace.append(event="plan", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"phase": plan["phase"], "c": plan["c"], "families": [r["model"] for r in experiments]})
    return {"written": "plan.json", "phase": plan["phase"], "experiments": len(experiments)}


# ------------------------------------------------------------------ lesson 12: ModularRSI


@tool("contrast", a="string", b="string")
def contrast(run, a, b):
    """Pair the success and the failure of two actor packs on every pool task they both ran, and name the module whose text differs between them."""
    root = run.target.parent
    pa, pb = packs.read_pack(root / a), packs.read_pack(root / b)
    if not pa or not pb:
        raise ValueError(f"both packs must sit next to the target: {root / a}, {root / b}")
    differing = sorted(n for n in set(pa) | set(pb) if n.startswith("modules/") and pa.get(n) != pb.get(n))
    problems = sorted({r["problem"] for r in run.trace.rows("fit", arm=a)} & {r["problem"] for r in run.trace.rows("fit", arm=b)})
    pairs = []
    for problem in problems:
        best = {}
        for arm in (a, b):
            rows = [r for r in run.trace.rows("fit", problem=problem, arm=arm) if r["val_score"] is not None]
            top = max(rows, key=lambda r: r["val_score"]) if rows else None
            best[arm] = {"val": top["val_score"] if top else None, "recipe": top["recipe"] if top else None}
        if best[a]["val"] == best[b]["val"]:
            continue
        success, failure = (a, b) if (best[a]["val"] or 0) > (best[b]["val"] or 0) else (b, a)
        pairs.append({"problem": problem, "success": success, "failure": failure, "best": best})
    wins = {arm: sum(1 for p in pairs if p["success"] == arm) for arm in (a, b)}
    winner = max((a, b), key=lambda arm: wins[arm]) if pairs and wins[a] != wins[b] else None
    module = differing[0] if len(differing) == 1 else None
    result = {"pairs": pairs, "modules_differing": differing, "module": module, "winner": winner, "wins": wins,
              "texts": {a: pa.get(module), b: pb.get(module)} if module else {}}
    run.trace.append(event="contrast", problem=run.problem, arm=run.arm, seed=run.seed, info=result)
    return result


# ------------------------------------------------------------------ lesson 13: Recuris


def need_tags(profile):
    """The situation tags a working memory names: what the table is like, nothing about the signal."""
    tags = []
    if profile["n_rows"] < 1000:
        tags.append("small")
    if profile["has_categorical"]:
        tags.append("categorical")
    if profile["imbalance"] < 0.35:
        tags.append("imbalanced")
    if profile["n_classes"] > 2:
        tags.append("multiclass")
    return tags


def parse_value(text):
    """A `then` value as the recipe holds it: numbers and null as JSON, everything else as a string."""
    try:
        return json.loads(text)
    except ValueError:
        return text


def skill_cards(pack_dir):
    """The skill package: manifest.yaml entries joined with each card's front matter (when, then, validated, horizon)."""
    import yaml

    manifest = yaml.safe_load((pack_dir / "skill-memory" / "manifest.yaml").read_text(encoding="utf-8")) or {}
    cards = []
    for entry in manifest.get("cards", []):
        meta, body = packs.split_front_matter((pack_dir / "skill-memory" / entry["file"]).read_text(encoding="utf-8"))
        cards.append({**entry, **{k: meta[k] for k in ("when", "then", "validated", "horizon") if k in meta}, "body": body.strip()})
    return cards


@tool("skill_memory", action="string", payload="object")
def skill_memory(run, action, payload):
    """need: select the skill cards whose `when` tags fit the need and write working.md (actor). update: one localised, validated card update (meta)."""
    root = run.target / "skill-memory"
    if action == "need":
        need = list(payload.get("need", []))
        # selection by need, not by recency: every card whose situation tags all hold, in manifest order
        chosen = [c for c in skill_cards(run.target) if c.get("validated") and set(c.get("when", [])) <= set(need)]
        prefer = {}
        for c in chosen:
            field, value = c["then"].split("=")
            prefer[field] = parse_value(value)
        text = "# Working memory\n\nNeed: " + ", ".join(need) + "\nCards: " + (", ".join(c["name"] for c in chosen) or "none") + "\n"
        with open(run.target / "working.md", "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        run.trace.append(event="working", problem=run.problem, arm=run.arm, seed=run.seed, info={"need": need, "cards": [c["name"] for c in chosen]})
        return {"need": need, "cards": [{"name": c["name"], "when": c["when"], "then": c["then"], "horizon": c.get("horizon", 0)} for c in chosen], "prefer": prefer}
    if action == "update":
        name, then, when = payload.get("card"), payload.get("then"), list(payload.get("when", []))
        if not name or not then or "=" not in then:
            raise ValueError("an update is {card: name, then: field=value, when: [tags], body: text}")
        field, value = then.split("=")
        value = parse_value(value)
        rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]}
                for r in run.trace.rows("fit", problem=run.problem, arm=actor_arm(run), seed=run.seed)]
        wins, losses, _ = memory.tally(rows)
        if wins.get((field, value), 0) <= losses.get((field, value), 0):
            raise ValueError(f"not validated: {then} did not win its comparisons on {run.problem} "
                             f"({wins.get((field, value), 0)} wins, {losses.get((field, value), 0)} losses); nothing lands")
        if run.visits.get("skill_update", 0) >= 1:
            raise ValueError("one card update per visit")
        run.visits["skill_update"] = 1
        label = f"gen_{len(list(run.versions_dir.glob('gen_*'))) + 1:03d}" if run.versions_dir.exists() else "gen_001"
        packs.snapshot(run.target, run.versions_dir, label)
        cards = skill_cards(run.target)
        existing = next((c for c in cards if c["name"] == name), None)
        horizon = (existing.get("horizon", 0) if existing else 0) + 1
        text = (f"---\nname: {name}\nwhen: [{', '.join(when)}]\nthen: {then}\nvalidated: true\nhorizon: {horizon}\n---\n"
                f"{payload.get('body', '').strip()}\n")
        path = root / (existing["file"] if existing else f"cards/{name}.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if not existing:
            import yaml
            manifest = yaml.safe_load((root / "manifest.yaml").read_text(encoding="utf-8")) or {"cards": []}
            manifest["cards"].append({"name": name, "file": f"cards/{name}.md"})
            with open(root / "manifest.yaml", "w", encoding="utf-8", newline="\n") as f:
                yaml.safe_dump(manifest, f, sort_keys=False)
        run.trace.append(event="skill_update", problem=run.problem, arm=run.arm, seed=run.seed,
                         info={"card": name, "then": then, "when": when, "horizon": horizon, "version": label, "new": existing is None})
        return {"card": name, "file": path.relative_to(run.target).as_posix(), "horizon": horizon, "version": label, "new": existing is None}
    raise ValueError("action is need or update")


# ------------------------------------------------------------------ lesson 14: the Darwin Goedel Machine lineage


def held_out_tasks(run):
    """The fixed held-out benchmark a DGM meta pack names in its front matter (`held_out: <dir>`), relative to the pack."""
    rel = (run.meta.get("metadata") or {}).get("held_out")
    return tasks.all_tasks(run.pack_dir / rel) if rel else []


def archive_index(run):
    path = run.run_dir / "archive" / "archive.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


@tool("archive", action="string", payload="object")
def archive(run, action, payload):
    """add: store the target pack as a variant with its held-out gain (private score of its best recipe minus the control arm's, over the held-out problems an arm ran). list: every variant. parent: the best-scoring variant's label. restore: make a variant the current pack."""
    root = run.run_dir / "archive"
    root.mkdir(parents=True, exist_ok=True)
    index = archive_index(run)
    if action == "add":
        label, arm = payload.get("label"), payload.get("arm")
        if not label or not arm:
            raise ValueError("add takes {label, arm}: the variant's name and the arm under which it ran the held-out problems")
        # the held-out score: over every problem the arm ran, the private score of its best recipe minus the
        # control arm's on the same problem and seed - a gain over the static walk on a fixed benchmark
        gains = {}
        for problem in sorted({r["problem"] for r in run.trace.rows("fit", arm=arm)}):
            for seed in sorted({r["seed"] for r in run.trace.rows("fit", arm=arm, problem=problem)}):
                task = tasks.load_task(problem) if problem in {t["name"] for t in tasks.all_tasks()} else run.task
                if task["name"] != problem:   # a held-out table outside rsi/tasks: the meta pack names it in its front matter
                    task = next(t for t in held_out_tasks(run) if t["name"] == problem)
                mine = [r for r in run.trace.rows("fit", problem=problem, arm=arm, seed=seed) if r["val_score"] is not None]
                control = [r for r in run.trace.rows("fit", problem=problem, arm="control", seed=seed) if r["val_score"] is not None]
                if not mine or not control:
                    continue
                best = max(mine, key=lambda r: r["val_score"])["recipe"]
                base = max(control, key=lambda r: r["val_score"])["recipe"]
                gains[f"{problem}/{seed}"] = round(tasks.score_on(task, seed, best, "private") - tasks.score_on(task, seed, base, "private"), 4)
        if not gains:
            raise ValueError(f"arm {arm!r} has no held-out problem with a control arm to compare against")
        score = round(sum(gains.values()) / len(gains), 4)
        packs.snapshot(run.target, root, label)
        index = [e for e in index if e["label"] != label]
        index.append({"label": label, "problem": run.problem, "seed": run.seed, "arm": arm, "gains": gains, "held_out": score,
                      "checksums": packs.checksums(run.target), "parent": payload.get("parent")})
    elif action == "restore":
        label = payload.get("label")
        if label not in {e["label"] for e in index}:
            raise ValueError(f"no variant {label!r} in the archive")
        packs.rollback(run.target, root, label)
    elif action == "parent":
        if not index:
            raise ValueError("the archive is empty; add a variant first")
        # the parent is the best held-out score, ties to the older variant: never "the latest" by default
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
        run.trace.append(event="archive", problem=run.problem, arm=run.arm, seed=run.seed,
                         info={"action": action, "label": best["label"], "latest": index[-1]["label"], "size": len(index)})
        return {"parent": best["label"], "held_out": best["held_out"], "latest": index[-1]["label"]}
    elif action != "list":
        raise ValueError("action is add, list, parent or restore")
    with open(root / "archive.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, indent=1)
        f.write("\n")
    run.trace.append(event="archive", problem=run.problem, arm=run.arm, seed=run.seed,
                     info={"action": action, "label": payload.get("label"), "size": len(index)})
    return {"action": action, "variants": [{k: e[k] for k in ("label", "problem", "held_out", "parent")} for e in index]}


# ------------------------------------------------------------------ lesson 15: AIDE2


@tool("meter", arm="string")
def meter(run, arm):
    """The cost so far under one arm (or all with ""): fits from the trace, tokens estimated from the transcripts' size at each stop."""
    fits = run.trace.rows("fit", **({"arm": arm} if arm else {}))
    stops = run.trace.rows("stop", **({"arm": arm} if arm else {}))
    tokens = sum(s["info"].get("tokens", 0) for s in stops)
    out = {"arm": arm or "all", "fits": len(fits), "tokens": tokens, "problems": sorted({r["problem"] for r in fits})}
    run.trace.append(event="meter", problem=run.problem, arm=run.arm, seed=run.seed, info=out)
    return out


SUSPICIOUS = 0.999    # a validation score this close to perfect is re-run before it is believed
JUMP = 0.2            # so is one that jumps this far above the previous best in one fit


def aide_keep(before, after, mad_k=3.0):
    """AIDE2's outer rule: keep a rewrite only if it is better across the whole set under the same budget, after the
    statistical layer drops outlier successes - a per-problem gain more than `mad_k` MADs above the median gain is
    discarded, so one lucky problem cannot carry the decision. Returns (keep, detail)."""
    problems = sorted(set(before) & set(after))
    gains = {p: round(after[p] - before[p], 4) for p in problems}
    values = sorted(gains.values())
    median = values[len(values) // 2] if values else 0.0
    mad = max(sorted(abs(v - median) for v in values)[len(values) // 2] if values else 0.0, 0.01)   # a floor of one AUC point: rounding is not spread
    outliers = [p for p, g in gains.items() if g - median > mad_k * mad]
    kept = {p: g for p, g in gains.items() if p not in outliers}
    total = round(sum(kept.values()), 4)
    keep = bool(kept) and total > 0 and sum(1 for g in kept.values() if g < 0) <= len(kept) // 2
    return keep, {"gains": gains, "outliers_discarded": outliers, "total_gain": total, "wins": sum(1 for g in kept.values() if g > 0),
                  "losses": sum(1 for g in kept.values() if g < 0)}
