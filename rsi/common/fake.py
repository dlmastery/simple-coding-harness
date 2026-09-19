"""A scripted, rule-driven fake model, so every claim is provable without a key.

It is not a language model: it is a rule table over what a pack gives it -
the tools its tools.md allows, the files appended to its prompt, the results
in its transcript. A pack that allows `fit_recipe` makes it a trainer; one
that allows `write_card` makes it a verifier; `read_task` + `propose` a
writer; `patch_pack` a meta pack. It reads `schema.json`, `recipes.json`,
`paths.json`, `memory.json` and the `Search policy:` line out of its prompt
exactly as a real model would, so the same pack text drives both.

The policies it knows (`policies.md` of step 10 names them): `static`
(walk the list), `obey-memory` (the 72-recipe grid sorted by how many
applicable prefer cards a recipe satisfies), `random`, `neighbours-of-top-3`
and `prefer-untried-family`.
"""

import json
import random
import re

from common import memory, recipe

FILE_RE = re.compile(r"^### FILE: (.+)$", re.M)


class Transcript:
    """What the fake reads back: the prompt files, and every tool call with its result."""

    def __init__(self, messages, tool_schemas):
        self.messages = messages
        self.allowed = [t["function"]["name"] for t in tool_schemas]
        self.system = messages[0]["content"]
        self.files = self.parse_files(self.system)
        self.calls = []
        pending = {}
        for m in messages[1:]:
            if m["role"] == "assistant":
                for c in m.get("tool_calls") or []:
                    pending[c["id"]] = (c["function"]["name"], json.loads(c["function"]["arguments"] or "{}"))
            elif m["role"] == "tool":
                name, args = pending.pop(m["tool_call_id"])
                self.calls.append((name, args, self.parse(m["content"])))

    @staticmethod
    def parse_files(system):
        files, blocks = {}, FILE_RE.split(system)
        for name, body in zip(blocks[1::2], blocks[2::2]):
            files[name.strip()] = body.strip()
        return files

    @staticmethod
    def parse(text):
        if text.startswith("Error:"):
            return {"error": text}
        try:
            return json.loads(text)
        except ValueError:
            return {"text": text}

    def json_file(self, name, default=None):
        text = self.files.get(name)
        if text is None or text.startswith("(MEMORY_OFF"):
            return default
        try:
            return json.loads(text)
        except ValueError:
            return default

    def results(self, name):
        return [(args, result) for n, args, result in self.calls if n == name]

    def called(self, name):
        return any(n == name for n, _, _ in self.calls)

    def line(self, prefix):
        """The rest of the first prompt line starting with `prefix`, or None."""
        for line in self.system.splitlines():
            if line.strip().startswith(prefix):
                return line.strip()[len(prefix):].strip()
        return None


class FakeModel:
    def __init__(self):
        self.counter = 0

    def call(self, name, **args):
        self.counter += 1
        return {"id": f"call_{self.counter}", "name": name, "arguments": json.dumps(args)}

    def reply(self, *calls, text=None):
        return {"content": text, "tool_calls": list(calls)}

    def __call__(self, messages, tool_schemas):
        t = Transcript(messages, tool_schemas)
        if "fit_recipe" in t.allowed or "walk_path" in t.allowed:
            return self.trainer(t)
        if "write_card" in t.allowed:
            return self.verifier(t)
        if "patch_pack" in t.allowed:
            return self.meta(t)
        if "propose" in t.allowed and "read_task" in t.allowed:
            return self.writer(t)
        return self.reply(text="This pack allows no tool I know a procedure for; stopping.")

    # ------------------------------------------------------------------ trainer

    def trainer(self, t):
        if not t.called("load_splits"):
            return self.reply(self.call("load_splits"))
        loaded = t.results("load_splits")[-1][1]
        profile, n_fits = loaded["profile"], loaded["n_fits"]
        fits = [(a, r) for a, r in t.results("fit_recipe") + t.results("walk_path") if "n" in r]
        refused = sum(1 for a, r in t.results("fit_recipe") if "error" in r and "n" not in r)
        frozen = any(r.get("FREEZE") for _, r in fits) or len(fits) >= n_fits
        if frozen and "write_loop_log" in t.allowed and len(t.results("write_loop_log")) < len(fits):
            a, r = fits[-1]
            return self.reply(self.call("write_loop_log", entry={"t": r["n"], "recipe": a.get("recipe") or a.get("path_id"), "val_score": r["val_score"]}))
        if not frozen:
            if refused > 3 * n_fits:   # a policy that only proposes refused recipes stops instead of looping
                frozen = True
            else:
                nxt = self.next_fit(t, profile, fits)
                if nxt is None:
                    frozen = True
                else:
                    calls = []
                    if "write_loop_log" in t.allowed and fits:
                        a, r = fits[-1]
                        calls.append(self.call("write_loop_log", entry={"t": r["n"], "recipe": a.get("recipe") or a.get("path_id"), "val_score": r["val_score"]}))
                    return self.reply(*calls, nxt)
        scored = [(r["val_score"], a) for a, r in fits if r.get("val_score") is not None]
        if not scored:
            return self.reply(text="Every fit errored; nothing to score.")
        best_val, best_args = max(scored, key=lambda x: x[0])
        best = best_args.get("recipe") or self.path_recipe(t, best_args["path_id"])
        if not t.called("score_test"):
            return self.reply(self.call("score_test", recipe=best))
        test = t.results("score_test")[-1][1]
        if "error" in test and "locked" in test["error"]:   # counted wrong: fit on until FREEZE
            nxt = self.next_fit(t, profile, fits)
            if nxt is not None:
                return self.reply(nxt)
        if "save_model" in t.allowed and not t.called("save_model"):
            return self.reply(self.call("save_model", recipe=best))
        return self.reply(text=f"Done. Best val {best_val} with {json.dumps(best)}; test {test.get('test_score')}; {len(fits)} fits.")

    def path_recipe(self, t, path_id):
        from common.graph import path_recipe
        return path_recipe(next(p for p in t.json_file("paths.json", []) if p["id"] == path_id))

    def next_fit(self, t, profile, fits):
        """The next tool call of the search: a path, a static recipe, or the policy's pick. None when the order is exhausted."""
        tried = [a.get("recipe") for a, _ in fits if "recipe" in a]
        if "walk_path" in t.allowed:
            walked = {a["path_id"] for a, _ in t.results("walk_path")}
            for p in t.json_file("paths.json", []):
                if p["id"] not in walked:
                    return self.call("walk_path", path_id=p["id"])
            return None
        refused = [a["recipe"] for a, r in t.results("fit_recipe") if "error" in r and "n" not in r]
        order = self.order(t, profile, fits)
        for rec in order:
            if rec not in tried and rec not in refused:
                return self.call("fit_recipe", recipe=rec)
        return None

    def order(self, t, profile, fits):
        """The recipes in the order this pack's files and policy line say to try them."""
        policy = t.line("Search policy:") or "static"
        static = t.json_file("recipes.json") or t.json_file("schema.json", {}).get("recipes") or recipe.static_list()
        cards = t.json_file("memory.json", []) or []
        forbid = t.json_file("schema.json", {}).get("forbid", [])
        if policy == "static" and cards:
            policy = "obey-memory"
        return policy_order(policy, static, cards, profile, fits, seed=len(t.system), forbid=forbid)

    # ------------------------------------------------------------------ verifier

    def verifier(self, t):
        if not t.called("read_traces"):
            return self.reply(self.call("read_traces", scope="problem"))
        if t.called("write_card") or t.results("read_traces")[-1][1].get("error"):
            n = len(t.results("write_card"))
            return self.reply(text=f"Wrote {n} cards from the log; nothing else was in my input.")
        seen = t.results("read_traces")[-1][1]
        rows, profile = seen["rows"], seen["profile"]
        existing = {memory.card_id(c) for c in (t.json_file("memory.json", []) or [])}
        deltas = [d for d in memory.compare(rows, profile) if d["evidence"] > 0 or memory.card_id(d) in existing]
        if not deltas:
            return self.reply(text="No pair of fits one field apart: no card to write.")
        return self.reply(*(self.call("write_card", card=d) for d in deltas))

    # ------------------------------------------------------------------ writer

    def writer(self, t):
        if not t.called("read_task"):
            return self.reply(self.call("read_task"))
        task = t.results("read_task")[-1][1]
        if not t.called("lint_pack"):
            return self.reply(self.call("lint_pack", files=self.render(t, task)))
        lint = t.results("lint_pack")[-1][1]
        if lint != "ok" and not isinstance(lint, str):
            return self.reply(text=f"My pack does not lint: {lint}. Stopping.")
        if not t.called("propose"):
            return self.reply(self.call("propose", kind="pack", payload=self.render(t, task), summary=f"a pack for {task['name']} from the template"))
        decision = t.results("propose")[-1][1]
        if decision.get("decision") in ("y", "edit") and not t.called("apply"):
            return self.reply(self.call("apply", id=decision["id"]))
        landed = t.results("apply")[-1][1] if t.called("apply") else "nothing landed"
        return self.reply(text=f"Proposal {decision.get('id')} decided {decision.get('decision')}: {landed}.")

    def render(self, t, task):
        """The pack from the template files in the prompt, placeholders filled from the task. Deterministic."""
        static = [r for r in recipe.static_list() if r["model"] in task["allowed_models"]]
        values = {
            "name": task["name"], "title": task["title"], "metric": task["metric"], "n_fits": task["budget"]["n_fits"],
            "models": json.dumps(task["allowed_models"]), "test_rule": json.dumps(task["test_rule"]),
            "recipes": json.dumps(static, indent=1), "profile_keys": json.dumps(task["profile_keys"]),
            "paths": json.dumps(paths_for(static), indent=1), "slug": task["name"].replace("_", "-"),
            "card_schema": json.dumps(memory.CARD_SCHEMA, indent=1), "task": json.dumps(task, indent=1),
        }
        files = {}
        for name, text in t.files.items():
            if name.startswith("template/"):
                for k, v in values.items():
                    text = text.replace("{{" + k + "}}", str(v))
                files[name[len("template/"):]] = text + "\n"
        return files

    # ------------------------------------------------------------------ meta

    def meta(self, t):
        for name, args in (("read_traces", {"scope": "all"}), ("read_memory", {}), ("read_pack", {})):
            if name in t.allowed and not t.called(name):
                return self.reply(self.call(name, **args))
        if t.called("patch_pack"):
            r = t.results("patch_pack")[-1][1]
            return self.reply(text=f"One proposal this visit: {json.dumps(r)}.")
        traces = t.results("read_traces")[-1][1]
        pack = t.results("read_pack")[-1][1]
        mem = t.results("read_memory")[-1][1]
        cards = mem.get("cards", []) if isinstance(mem, dict) else []
        rows = traces["rows"]
        if not rows:
            return self.reply(text="No fits in the log yet; nothing to improve.")
        last_problem = rows[-1]["problem"]
        scored = [r for r in rows if r["problem"] == last_problem and r["val_score"] is not None]
        if not scored:
            return self.reply(text="The last problem has no scored fit; nothing to improve.")
        best = max(scored, key=lambda r: r["val_score"])["recipe"]
        files, summary = self.meta_patch(pack, cards, rows, traces["profile"])
        if not files:
            return self.reply(text="Nothing to propose this visit.")
        return self.reply(self.call("patch_pack", files=files, recipe=best, summary=summary))

    def meta_patch(self, pack, cards, rows, profile):
        """One change per visit, in this order of preference: the policy line, a schema forbid, new cards."""
        skill = pack.get("SKILL.md", "")
        active = [c for c in cards if memory.active(c)]
        if "Search policy: static" in skill and len(active) >= 2:
            return {"SKILL.md": {"after": skill.replace("Search policy: static", "Search policy: obey-memory")}}, \
                "search policy: obey the cards (>= 2 active)"
        schema = json.loads(pack["schema.json"]) if "schema.json" in pack else {}
        losers = never_won(rows)
        forbid = schema.get("forbid", [])
        for field, value in losers:
            if {"field": field, "value": value} not in forbid:
                schema["forbid"] = forbid + [{"field": field, "value": value}]
                return {"schema.json": {"after": json.dumps(schema, indent=1) + "\n"}}, f"schema forbid: {field}={value!r} never won a comparison"
        deltas = memory.compare([r for r in rows if r["problem"] == rows[-1]["problem"]], profile)
        new = [d for d in deltas if d["evidence"] >= memory.MIN_EVIDENCE and memory.card_id(d) not in {memory.card_id(c) for c in cards}]
        if new:
            merged = [dict(c) for c in cards]
            for d in new[:3]:
                memory.merge(merged, d)
            return {"memory.json": {"after": json.dumps(merged, indent=1) + "\n"}}, f"{len(new[:3])} new cards from the last problem's pairs"
        return {}, ""


# ---------------------------------------------------------------------- search policies


def paths_for(recipes):
    """One path per recipe: the nodes in dependency order with the recipe as bindings."""
    return [{"id": f"p{i:02d}", "nodes": ["load", "scale", "encode", "model", "fit"], "bindings": r} for i, r in enumerate(recipes)]


def never_won(rows):
    """(field, value) pairs that lost every comparison one field apart, at least three times, across the log."""
    wins, losses = {}, {}
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["problem"] != b["problem"] or a["val_score"] is None or b["val_score"] is None:
                continue
            field = memory.differing_field(a["recipe"], b["recipe"])
            if field is None or field == "hyper" or a["val_score"] == b["val_score"]:
                continue
            win, lose = (a, b) if a["val_score"] > b["val_score"] else (b, a)
            wins[(field, win["recipe"][field])] = wins.get((field, win["recipe"][field]), 0) + 1
            losses[(field, lose["recipe"][field])] = losses.get((field, lose["recipe"][field]), 0) + 1
    return sorted(k for k, n in losses.items() if n >= 3 and wins.get(k, 0) == 0)


def policy_order(policy, static, cards, profile, fits, seed=0, forbid=()):
    """The recipe order a named policy produces. Adaptive policies look at the fits so far."""
    tried = [a["recipe"] for a, _ in fits if "recipe" in a]
    scored = [(r["val_score"], a["recipe"]) for a, r in fits if r.get("val_score") is not None]
    allowed = {r["model"] for r in static}
    full = [r for r in recipe.grid() if r["model"] in allowed]
    full = [r for r in full if memory.forbidden(r, cards, profile) is None
            and not any(r[f["field"]] == f["value"] for f in forbid)]
    static = [r for r in static if r in full]
    static_keys = {recipe.key(r) for r in static}
    if policy == "static":
        return static
    if policy == "obey-memory":
        # no applicable card: nothing to obey, the static order (so MEMORY_OFF and an empty memory agree)
        if not memory.preferred(cards, profile):
            return static
        by_cards = sorted(full, key=lambda r: (-memory.agreement(r, cards, profile), recipe.key(r) not in static_keys, full.index(r)))
        if not scored:
            return by_cards
        # then climb: an untried neighbour of the best so far, fields in order of how much they usually matter
        best = max(scored, key=lambda x: x[0])[1]
        near = [n for f in ("model", "class_weight", "encode", "scale", "hyper") for n in recipe.neighbours(best)
                if n in full and n not in tried and memory.differing_field(best, n) == f]
        return near + by_cards
    if policy == "random":
        order = list(full)
        random.Random(seed).shuffle(order)
        return order
    if policy == "neighbours-of-top-3":
        if len(tried) < 6:
            return static
        top = [r for _, r in sorted(scored, key=lambda x: -x[0])[:3]]
        near = [n for r in top for n in recipe.neighbours(r) if n in full and n not in tried]
        return near + static
    if policy == "prefer-untried-family":
        counts = {m: sum(1 for r in tried if r["model"] == m) for m in sorted(allowed)}
        return sorted(full, key=lambda r: (counts[r["model"]], recipe.key(r) not in static_keys, full.index(r)))
    raise ValueError(f"unknown search policy {policy!r}")
