"""The writers' rendering rule (lessons 03, 05, 08) as one function, so the tests can hold the agent's
rendering to it: every `{{placeholder}}` of a template file replaced from the task, nothing else added.

The agent renders the templates itself (it reads the rule in SKILL.md); this is the reference the tests
compare against, and the proof that the same task.json gives the same proposal.
"""

import json
from pathlib import Path

from _lib import packs, recipe

HYPER_MIDDLE = {m: recipe.SCHEMA["hyper"][m][1] for m in recipe.SCHEMA["model"]}


def static_recipes(task):
    """The n_fits recipes at each allowed model's middle hyper value, grid order, the baseline first."""
    out = []
    for model in task["allowed_models"]:
        for scale in recipe.SCHEMA["scale"]:
            for encode in recipe.SCHEMA["encode"]:
                for cw in recipe.SCHEMA["class_weight"]:
                    out.append({"model": model, "hyper": HYPER_MIDDLE[model], "scale": scale, "encode": encode, "class_weight": cw})
    return out[: task["budget"]["n_fits"]]


def values(task):
    return {
        "name": task["name"], "slug": task["name"].replace("_", "-"), "title": task["title"], "metric": task["metric"],
        "n_fits": str(task["budget"]["n_fits"]), "models": json.dumps(task["allowed_models"]),
        "test_rule": json.dumps(task["test_rule"]), "recipes": json.dumps(static_recipes(task), indent=1),
        "profile_keys": json.dumps(task["profile_keys"]),
        "paths": json.dumps([{"id": f"p{i:02d}", "nodes": ["load", "scale", "encode", "model", "fit"], "bindings": r}
                             for i, r in enumerate(static_recipes(task))], indent=1),
    }


def render(template_dir, task, subdirs=None):
    """{path: text} for every file under template_dir, placeholders replaced. `subdirs` renames the template's
    sub-packs (lesson 08: actor/ -> <slug>/, verifier/ -> <slug>-verifier/), so a landed pack is found by its name."""
    vals = values(task)
    out = {}
    for name, text in packs.read_pack(Path(template_dir)).items():
        for key, value in vals.items():
            text = text.replace("{{" + key + "}}", value)
        top, _, rest = name.partition("/")
        if subdirs and rest and top in subdirs:
            name = subdirs[top].replace("{{slug}}", vals["slug"]) + "/" + rest
        out[name] = text
    return out


RSI_SUBDIRS = {"actor": "{{slug}}", "verifier": "{{slug}}-verifier"}
