"""The search policies a pack may name on its `Search policy:` line, as one
function: the order in which a policy would try the recipes, given the fits
so far. The fake model follows it; `rank_policies` (lesson 10) replays it on
the log; a real model reads the same descriptions in `policies.md`.

- `static`: the list in `recipes.json` / `schema.json`, in order.
- `obey-memory`: probe one recipe per model (believed model first), then the
  believed family - its static recipes, then its hyper variants - ranked by
  the cards, then the rest of the grid.
- `random`: the grid shuffled by a seed.
- `neighbours-of-top-3`: six static fits, then the untried neighbours of the
  three best so far.
- `prefer-untried-family`: the family with the fewest fits so far first.
- `aide-tree`: draft (one probe per model), then improve (the untried
  neighbours of the best so far), the operators of lesson 15.
"""

import random

from common import memory, recipe


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
        want = memory.preferred(cards, profile)
        if not want:
            return static + [r for r in full if r not in static]   # a forbid card shortens the list; the grid fills the budget
        # probe: one fit per model with the preferred preprocessing at the default hyper, believed model first
        base = {"scale": want.get("scale", "yes"), "encode": want.get("encode", "onehot"), "class_weight": want.get("class_weight", "none")}
        models = sorted(allowed, key=lambda m: (m != want.get("model"), recipe.SCHEMA["model"].index(m)))
        probes = [dict(model=m, hyper=recipe.SCHEMA["hyper"][m][1], **base) for m in models]
        probes = [p for p in probes if p in full]
        probed = [(v, r) for v, r in scored if r in probes]
        if len(probed) < len(probes):
            return probes
        # then obey: the grid ranked by the cards, with the probe winner as the model belief
        want["model"] = max(probed, key=lambda x: x[0])[1]["model"]
        # the believed family first; inside it the static recipes before the hyper variants; then the cards
        ranked = sorted(full, key=lambda r: (r["model"] != want["model"], recipe.key(r) not in static_keys,
                                             -memory.agreement(r, cards, profile, want), full.index(r)))
        return probes + ranked
    if policy == "random":
        order = list(full)
        random.Random(seed).shuffle(order)
        return order
    if policy == "neighbours-of-top-3":
        if len(tried) < 6:
            return static
        top = [r for _, r in sorted(scored, key=lambda x: -x[0])[:3]]
        near = [n for r in top for _, n in recipe.neighbours(r) if n in full and n not in tried]
        return near + static
    if policy == "prefer-untried-family":
        counts = {m: sum(1 for r in tried if r["model"] == m) for m in sorted(allowed)}
        return sorted(full, key=lambda r: (counts[r["model"]], recipe.key(r) not in static_keys, full.index(r)))
    if policy in ("aide-tree", "aide-tree-top-3"):
        # draft: one probe per model at the default hyper with the baseline preprocessing
        probes = [dict(recipe.BASELINE, model=m, hyper=recipe.SCHEMA["hyper"][m][1]) for m in recipe.SCHEMA["model"] if m in allowed]
        probes = [p for p in probes if p in full]
        if any(p not in tried for p in probes):
            return probes
        # improve: the untried neighbours of the best solution (or of the top three), nearest first
        k = 3 if policy.endswith("top-3") else 1
        top = [r for _, r in sorted(scored, key=lambda x: -x[0])[:k]]
        near = [n for r in top for _, n in recipe.neighbours(r) if n in full and n not in tried]
        return probes + near + static
    raise ValueError(f"unknown search policy {policy!r}")
