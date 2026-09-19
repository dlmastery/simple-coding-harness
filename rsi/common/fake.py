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
import re

from common import memory, recipe
from common.policies import policy_order

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
            files[name.strip()] = body.split("### PROBLEM")[0].strip()   # the problem block follows the last file
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
        """The rest of the first line starting with `prefix` in the system prompt or the first user message, or None."""
        first_user = next((m["content"] for m in self.messages[1:] if m["role"] == "user"), "")
        for line in (self.system + "\n" + first_user).splitlines():
            text = line.strip().lstrip("-* ").strip()      # a bullet is a line too
            if text.startswith(prefix):
                return text[len(prefix):].strip()
        return None


class FakeModel:
    """`style` is the actor's quirk: "default" walks lists forwards, "reverse" walks them backwards. Two fake
    actors with different quirks are lesson 12's two actors: a module patch must help both."""

    def __init__(self, style="default"):
        self.counter = 0
        self.style = style

    def call(self, name, **args):
        self.counter += 1
        return {"id": f"call_{self.counter}", "name": name, "arguments": json.dumps(args)}

    def reply(self, *calls, text=None):
        return {"content": text, "tool_calls": list(calls)}

    def __call__(self, messages, tool_schemas):
        t = Transcript(messages, tool_schemas)
        if "write_plan" in t.allowed:
            return self.curriculum(t)
        if "fit_recipe" in t.allowed or "walk_path" in t.allowed:
            return self.trainer(t)
        if "write_card" in t.allowed:
            return self.verifier(t)
        if "patch_pack" in t.allowed or ("skill_memory" in t.allowed and "fit_recipe" not in t.allowed):
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
        if "skill_memory" in t.allowed and not t.called("skill_memory") and not self.off(t):
            from common.tools import need_tags
            return self.reply(self.call("skill_memory", action="need", payload={"need": need_tags(profile)}))
        fits = [(a, r) for a, r in t.results("fit_recipe") + t.results("walk_path") if "n" in r]
        refused = sum(1 for a, r in t.results("fit_recipe") if "error" in r and "n" not in r)
        frozen = any(r.get("FREEZE") for _, r in fits) or len(fits) >= n_fits
        if frozen and "write_loop_log" in t.allowed and len(t.results("write_loop_log")) < len(fits):
            a, r = fits[-1]
            return self.reply(self.call("write_loop_log", entry={"t": r["n"], "recipe": a.get("recipe") or a.get("path_id"), "val_score": r["val_score"]}))
        if not frozen and "read_pack" in t.allowed and self.plan(t) is not None and not self.off(t):
            # lesson 11: the experiments come from plan.json; when it runs dry, re-read the pack once, then wait
            plan_left = [r for r in self.plan(t) if r not in [a.get("recipe") for a, _ in fits]]
            if not plan_left:
                if t.messages[-1]["role"] == "user" or not t.calls or t.calls[-1][0] != "read_pack":
                    return self.reply(self.call("read_pack"))       # a new instruction, or not re-read yet: look again
                return self.reply(text=f"Plan exhausted after {len(fits)} fits; {n_fits - len(fits)} fits remain. Waiting for a new plan.")
        if not frozen and fits and "operators.md" in t.files:
            # lesson 15's hard guard: a suspicious score is re-run once before it is believed (it costs a fit)
            from common.tools import JUMP, SUSPICIOUS
            last_args, last = fits[-1]
            earlier = [r["val_score"] for _, r in fits[:-1] if r.get("val_score") is not None]
            suspicious = last.get("val_score") is not None and (last["val_score"] >= SUSPICIOUS or (earlier and last["val_score"] - max(earlier) > JUMP))
            repeated = len(fits) >= 2 and fits[-2][0] == last_args
            if suspicious and not repeated:
                return self.reply(self.call("fit_recipe", recipe=last_args["recipe"]))
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

    @staticmethod
    def off(t):
        return t.files.get("memory.json", "").startswith("(MEMORY_OFF")

    def plan(self, t):
        """The experiments of plan.json: from the latest read_pack result if any, else from the prompt."""
        if t.called("read_pack"):
            files = t.results("read_pack")[-1][1]
            text = files.get("plan.json") if isinstance(files, dict) else None
            return json.loads(text)["experiments"] if text else None
        plan = t.json_file("plan.json")
        return plan["experiments"] if plan else None

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
        if "read_pack" in t.allowed and self.plan(t) is not None and not self.off(t):
            return self.plan(t)
        if "skill_memory" in t.allowed and t.called("skill_memory") and not self.off(t):
            # lesson 13: the selected skill cards are the preferences; the order is obey-memory's
            prefer = t.results("skill_memory")[-1][1].get("prefer", {})
            pseudo = [{"if": {"key": "n_rows", "op": ">=", "value": 0}, "then": {"field": f, "prefer": v}, "evidence": 1, "counter": 0}
                      for f, v in prefer.items()]
            static = t.json_file("schema.json", {}).get("recipes") or recipe.static_list()
            return policy_order("obey-memory", static, pseudo, profile, fits)
        static = t.json_file("recipes.json") or t.json_file("schema.json", {}).get("recipes") or recipe.static_list()
        cards = t.json_file("memory.json", []) or []
        forbid = t.json_file("schema.json", {}).get("forbid", [])
        # the policy line is binding when the pack has one; a pack with cards and no line obeys them
        policy = t.line("Search policy:") or ("obey-memory" if cards else "static")
        if policy == "aide-tree" and "top three" in (t.line("Improve:") or ""):
            policy = "aide-tree-top-3"          # the improve operator's text picks the tree's expansion rule
        if self.off(t):
            policy = "static"      # the off switch: the static order, whatever the policy line or the plan says
        order = policy_order(policy, static, cards, profile, fits, seed=len(t.system), forbid=forbid)
        return list(reversed(order)) if self.style == "reverse" and policy == "static" else order

    # ------------------------------------------------------------------ curriculum (lesson 11)

    def curriculum(self, t):
        """RSIAgent's curriculum pack: pick the next experiments by uncertainty u = (1 - success) + c / (n + 1),
        a broad phase (large c) that touches every family, then a deep phase (small c) that goes where the
        faults are."""
        if not t.called("read_traces"):
            return self.reply(self.call("read_traces", scope="problem"))
        if "read_memory" in t.allowed and not t.called("read_memory"):
            return self.reply(self.call("read_memory"))
        if t.called("write_plan"):
            return self.reply(text=f"Plan written: {json.dumps(t.results('write_plan')[-1][1])}")
        seen = t.results("read_traces")[-1][1]
        rows, profile = seen["rows"], seen["profile"]
        mem = t.results("read_memory")[-1][1] if t.called("read_memory") else {}
        cards = mem.get("cards", []) if isinstance(mem, dict) else []
        want = memory.preferred(cards, profile)
        broad = not rows
        c = float(t.line("Broad c:") or 2.0) if broad else float(t.line("Deep c:") or 0.25)
        per_phase = int(t.line("Experiments per phase:") or 12)
        # the believed family (the cards' model belief) goes first at ties; inside a family, the recipes that
        # carry the most preferred values go first: the memory shapes the experiments, the verifier fills it
        families = sorted(recipe.SCHEMA["model"], key=lambda m: (m != want.get("model"), recipe.SCHEMA["model"].index(m)))
        baseline = next((r["val_score"] for r in rows if r["val_score"] is not None), None)
        n = {m: sum(1 for r in rows if r["recipe"]["model"] == m) for m in families}
        wins = {m: sum(1 for r in rows if r["recipe"]["model"] == m and r["val_score"] is not None and r["val_score"] >= baseline) for m in families}
        tried = [r["recipe"] for r in rows]
        static_keys = {recipe.key(r) for r in recipe.static_list()}
        pool = {m: sorted((r for r in recipe.grid() if r["model"] == m and r not in tried),
                          key=lambda r: (recipe.key(r) not in static_keys, -memory.agreement(r, cards, profile, dict(want, model=m)), recipe.grid().index(r)))
                for m in families}
        plan = []
        for _ in range(per_phase):
            u = {m: (1 - (wins[m] + 1) / (n[m] + 2)) + c / (n[m] + 1) for m in families if pool[m]}
            if not u:
                break
            pick = max(families, key=lambda m: (u.get(m, -1), -families.index(m)))
            rec = next(r for r in pool[pick] if r not in plan)
            plan.append(rec)
            n[pick] += 1
            pool[pick] = [r for r in pool[pick] if r != rec]
        return self.reply(self.call("write_plan", plan={"phase": "broad" if broad else "deep", "c": c, "experiments": plan}))

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
        if lint != {"text": "ok"}:
            return self.reply(text=f"My pack does not lint: {lint}. Stopping.")
        if not t.called("propose"):
            files = self.render(t, task)
            summary = f"a pack for {task['name']} from the template"
            if any(name.endswith("memory.json") for name in files):
                summary += "; this pack will change its own memory.json on every problem it runs"
            return self.reply(self.call("propose", kind="pack", payload=files, summary=summary))
        decision = t.results("propose")[-1][1]
        if decision.get("decision") in ("y", "edit") and not t.called("apply"):
            return self.reply(self.call("apply", id=decision["id"]))
        landed = t.results("apply")[-1][1].get("text", "apply failed") if t.called("apply") else "nothing landed"
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
        scope = "problem" if "skill_memory" in t.allowed else "all"     # a card update is validated on one problem's log
        for name, args in (("read_traces", {"scope": scope}), ("read_memory", {}), ("read_pack", {})):
            if name in t.allowed and not t.called(name):
                return self.reply(self.call(name, **args))
        if t.called("patch_pack"):
            r = t.results("patch_pack")[-1][1]
            return self.reply(text=f"One proposal this visit: {json.dumps(r)}.")
        if "rank_policies" in t.allowed:
            return self.dream(t)
        if "contrast" in t.allowed:
            return self.modular(t)
        if "skill_memory" in t.allowed:
            return self.skill_update(t)
        if "archive" in t.allowed:
            return self.dgm(t)
        if "meter" in t.allowed:
            return self.aide_outer(t)
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
        if any(name.startswith("roles/") for name in pack):
            files, summary = self.evolve(t, pack, rows)      # lesson 16's slow loop: the target is the meta pack itself
        else:
            files, summary = self.meta_patch(pack, cards, rows, traces["profile"],
                                             flip_at=int(t.line("Policy flip threshold:") or 2), per_visit=int(t.line("Cards per visit:") or 3))
        if not files:
            return self.reply(text="Nothing to propose this visit.")
        return self.reply(self.call("patch_pack", files=files, recipe=best, summary=summary))

    def evolve(self, t, pack, rows):
        """Lesson 16: one line of one role file. If the fast loop's memory arm did not beat the control on most of
        the last problems, let it consolidate faster (Cards per visit + 1); else lower the policy flip threshold."""
        problems = []
        for r in rows:
            if r["problem"] not in problems:
                problems.append(r["problem"])
        recent = problems[-3:]
        beaten = 0
        for p in recent:
            mem = max((r["val_score"] for r in rows if r["problem"] == p and r.get("arm") == "memory" and r["val_score"] is not None), default=None)
            ctl = max((r["val_score"] for r in rows if r["problem"] == p and r.get("arm") == "control" and r["val_score"] is not None), default=None)
            beaten += mem is not None and ctl is not None and mem > ctl
        proposer, allocator = pack.get("roles/proposer.md", ""), pack.get("roles/allocator.md", "")
        per_visit = int(t.line("Cards per visit:") or 3) if "Cards per visit:" in proposer else None
        if beaten <= len(recent) // 2 and per_visit is not None:
            after = proposer.replace(f"Cards per visit: {per_visit}", f"Cards per visit: {per_visit + 1}")
            return {"roles/proposer.md": {"after": after}}, f"proposer: cards per visit {per_visit} -> {per_visit + 1} (memory beat control on {beaten} of {len(recent)})"
        flip = next((int(l.split(":")[1]) for l in allocator.splitlines() if l.startswith("Policy flip threshold:")), None)
        if flip is not None and flip > 1:
            after = allocator.replace(f"Policy flip threshold: {flip}", f"Policy flip threshold: {flip - 1}")
            return {"roles/allocator.md": {"after": after}}, f"allocator: policy flip threshold {flip} -> {flip - 1}"
        return {}, ""

    def dream(self, t):
        """Lesson 10: rank the policies named in policies.md on the log, propose the winner as the policy line."""
        names = [line.split("`")[1] for line in t.files.get("policies.md", "").splitlines() if line.startswith("- `")]
        if not t.called("rank_policies"):
            return self.reply(self.call("rank_policies", names=names))
        ranking = t.results("rank_policies")[-1][1]["ranking"]
        pack = t.results("read_pack")[-1][1]
        skill = pack["SKILL.md"]
        current = next((line.split("Search policy:")[1].strip() for line in skill.splitlines() if "Search policy:" in line), None)
        winner = ranking[0]["policy"]
        if winner == current or current is None:
            return self.reply(text=f"The current policy {current!r} is the winner on the log; nothing to propose. Ranking: {json.dumps(ranking)}")
        rows = t.results("read_traces")[-1][1]["rows"]
        scored = [r for r in rows if r["val_score"] is not None and r["problem"] == rows[-1]["problem"]]
        best = max(scored, key=lambda r: r["val_score"])["recipe"]
        after = skill.replace(f"Search policy: {current}", f"Search policy: {winner}")
        return self.reply(self.call("patch_pack", files={"SKILL.md": {"after": after}}, recipe=best,
                                    summary=f"search policy {current} -> {winner}: best logged {ranking[0]['best_logged_val']}, {ranking[0]['unknown']} unvisited picks"))

    VARIANTS = ("static", "obey-memory", "neighbours-of-top-3", "prefer-untried-family")

    @staticmethod
    def policy_of(skill_text):
        lines = (l.strip().lstrip("-* ").strip() for l in skill_text.splitlines())
        return next((l[len("Search policy:"):].strip() for l in lines if l.startswith("Search policy:")), None)

    def dgm(self, t):
        """Lesson 14: archive the current variant with its held-out score, take the parent from the archive, restore
        it when it is not the current pack, re-read, and propose the next rewrite of SKILL.md + loop.json."""
        problem = json.loads(t.system.split("### PROBLEM")[-1].strip())["name"]     # the curriculum problem of this visit
        rows = t.results("read_traces")[-1][1]["rows"]
        scored = [r for r in rows if r["val_score"] is not None and r["problem"] == problem]
        best = max(scored, key=lambda r: r["val_score"])["recipe"]
        done = [a["action"] for a, _ in t.results("archive")]
        if "add" not in done:
            current = self.policy_of(t.results("read_pack")[-1][1]["SKILL.md"])
            arm = t.line("Held-out arm:") or "memory"
            return self.reply(self.call("archive", action="add", payload={"label": f"{problem}-{current}", "arm": arm}))
        failed = [r["error"] for _, r in t.results("archive") if "error" in r]
        if failed:
            return self.reply(text=f"The archive refused: {failed[-1]}. Stopping this generation.")
        if "parent" not in done:
            return self.reply(self.call("archive", action="parent", payload={}))
        parent = next(r for a, r in t.results("archive") if a["action"] == "parent")
        if parent["parent"] != parent["latest"] and "restore" not in done:
            return self.reply(self.call("archive", action="restore", payload={"label": parent["parent"]}))
        if "restore" in done and len(t.results("read_pack")) < 2:
            return self.reply(self.call("read_pack"))           # the restored parent, not the stale copy
        if t.called("patch_pack"):
            return self.reply(text=f"Generation done from parent {parent['parent']}: {json.dumps(t.results('patch_pack')[-1][1])}")
        variants = next(r for a, r in t.results("archive") if a["action"] == "add")["variants"]
        tried = {e["label"].split("-", 1)[1] for e in variants}      # a label is <problem>-<policy>
        nxt = next((v for v in self.VARIANTS if v not in tried), None)
        if nxt is None:
            return self.reply(text="Every variant is in the archive; nothing new to propose.")
        pack = t.results("read_pack")[-1][1]
        parent_policy = self.policy_of(pack["SKILL.md"])
        skill = pack["SKILL.md"].replace(f"Search policy: {parent_policy}", f"Search policy: {nxt}")
        loop = json.loads(pack["loop.json"])
        loop["policy"] = nxt
        return self.reply(self.call("patch_pack", files={"SKILL.md": {"after": skill}, "loop.json": {"after": json.dumps(loop, indent=1) + "\n"}},
                                    recipe=best, summary=f"rewrite from parent {parent['parent']}: policy {parent_policy} -> {nxt}"))

    def aide_outer(self, t):
        """Lesson 15's outer loop: meter the cost, then propose one rewrite of the inner pack's improve operator."""
        if not t.called("meter"):
            return self.reply(self.call("meter", arm=""))
        pack = t.results("read_pack")[-1][1]
        ops = pack.get("operators.md", "")
        if "top three" in ops:
            return self.reply(text="The improve operator already expands the top three; nothing to rewrite this step.")
        rewritten = ops.replace("Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.",
                                "Improve: expand the top three solutions - fit their untried neighbours, one field away, nearest first.")
        if rewritten == ops:
            return self.reply(text="The improve operator has a shape I do not know how to rewrite; nothing proposed.")
        rows = t.results("read_traces")[-1][1]["rows"]
        scored = [r for r in rows if r["val_score"] is not None]
        best = max(scored, key=lambda r: r["val_score"])["recipe"] if scored else recipe.BASELINE
        return self.reply(self.call("patch_pack", files={"operators.md": {"after": rewritten}}, recipe=best,
                                    summary="improve operator: expand the top three instead of the best only"))

    def skill_update(self, t):
        """Lesson 13: one localised card update from the last problem's evidence - the field whose winning value
        the situation's card does not hold yet (or a new card for a situation without one)."""
        from common.tools import need_tags, parse_value

        if t.called("skill_memory"):
            return self.reply(text=f"Update: {json.dumps(t.results('skill_memory')[-1][1])}")
        seen = t.results("read_traces")[-1][1]
        rows = [r for r in seen["rows"] if r["problem"] == seen["rows"][-1]["problem"]]
        wins, losses, _ = memory.tally(rows)
        need = need_tags(seen["profile"])
        # the cards are in the prompt as skill-memory/cards/*.md: the ones whose situation holds here
        held = {}
        for name, text in t.files.items():
            if name.startswith("skill-memory/cards/"):
                front = text.split("---")[1]
                meta = {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in front.strip().splitlines() if ":" in line)}
                tags = [x.strip() for x in meta.get("when", "[]").strip("[]").split(",") if x.strip()]
                if set(tags) <= set(need):
                    held[meta["then"].split("=")[0]] = (meta["name"], meta["then"], tags)
        for field in ("model", "class_weight", "encode", "scale"):
            values = {v for f, v in list(wins) + list(losses) if f == field}
            if not values:
                continue
            best = max(sorted(values, key=str), key=lambda v: wins.get((field, v), 0) - losses.get((field, v), 0))
            if wins.get((field, best), 0) <= losses.get((field, best), 0):
                continue
            then = f"{field}={best if isinstance(best, str) else json.dumps(best)}"
            name, current, tags = held.get(field, (f"{field}-when-{'-'.join(need) or 'any'}", None, need))
            if current == then:
                continue
            body = f"On {rows[-1]['problem']} {then} won {wins[(field, best)]} comparisons and lost {losses.get((field, best), 0)}."
            return self.reply(self.call("skill_memory", action="update", payload={"card": name, "then": then, "when": tags, "body": body}))
        return self.reply(text="Every situation card already holds the value that won; nothing to update.")

    def modular(self, t):
        """Lesson 12: contrast the two actors on the pool, then patch the losing module with the winning text."""
        a, b = t.line("Actor A:"), t.line("Actor B:")
        if not t.called("contrast"):
            return self.reply(self.call("contrast", a=a, b=b))
        c = t.results("contrast")[-1][1]
        if c.get("error") or c["winner"] is None or c["module"] is None:
            return self.reply(text=f"No single module to blame or no clear winner: {json.dumps(c)}. Nothing to propose.")
        if c["winner"] == t.line("Target:"):
            return self.reply(text=f"The target {c['winner']} is the success on the pool; nothing to patch.")
        # the evidence recipe: the winner's best on the pool task this visit was booted for (the gate's split)
        problem = json.loads(t.system.split("### PROBLEM")[-1].strip())["name"]
        pair = next((p for p in c["pairs"] if p["problem"] == problem), c["pairs"][-1])
        best = pair["best"][c["winner"]]["recipe"]
        return self.reply(self.call("patch_pack", files={c["module"]: {"after": c["texts"][c["winner"]]}},
                                    recipe=best, summary=f"{c['module']} from {c['winner']}: wins on the pool {json.dumps(c['wins'])}"))

    def meta_patch(self, pack, cards, rows, profile, flip_at=2, per_visit=3):
        """One change per visit, in this order of preference: the policy line, a schema forbid, new cards."""
        skill = pack.get("SKILL.md", "")
        active = [c for c in cards if memory.active(c)]
        if "Search policy: static" in skill and len(active) >= flip_at:
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
            for d in new[:per_visit]:
                memory.merge(merged, d)
            return {"memory.json": {"after": json.dumps(merged, indent=1) + "\n"}}, f"{len(new[:per_visit])} new cards from the last problem's pairs"
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
