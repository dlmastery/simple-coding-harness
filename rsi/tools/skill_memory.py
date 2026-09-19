"""skill_memory - Recuris: memory as a skill package (markdown cards under skill-memory/) plus a working memory.

    # the actor, at boot: name the situation, select the cards by need, rewrite working.md
    python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json \\
        --action need --need small,categorical,imbalanced
    # the meta pack, after a problem: one localised, validated card update
    python ../tools/skill_memory.py --pack .claude/skills/adult-income-skills --task ../tasks/01_adult_income.json \\
        --action update --as .claude/skills/skill-memory-meta --card onehot-for-categorical --then encode=onehot --when categorical --body "..."
    python ../tools/skill_memory.py --pack ... --task ... --action tags          # the need tags this profile has

`need` selects every validated card whose `when` tags all hold for the need
- by the situation, never by which card is newest - and returns their `then`
values as preferences. `update` refuses a `then` that did not win its
pairwise comparisons on this problem's log, keeps one file per card, snapshots
the pack under versions/ first, raises the card's `horizon` (the number of
problems it was updated on), and allows one update per visit.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml  # noqa: E402

from _lib import cli, memory, packs  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, action={"required": True, "choices": ["need", "update", "tags", "list"]},
                               need="need tags, comma-separated (action need)",
                               card="the card's name (action update)", then="field=value (action update)",
                               when="the situation tags, comma-separated (action update)", body={"default": "", "help": "the card's text (action update)"},
                               visit={"type": int, "default": 1, "help": "the visit number (one update per visit)"},
                               **{"as": {"dest": "writer", "default": None, "help": "the meta pack running the update"}}))


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
    try:
        return json.loads(text)
    except ValueError:
        return text


def skill_cards(pack_dir):
    manifest = yaml.safe_load((pack_dir / "skill-memory" / "manifest.yaml").read_text(encoding="utf-8")) or {}
    cards = []
    for entry in manifest.get("cards", []):
        meta, body = packs.split_front_matter((pack_dir / "skill-memory" / entry["file"]).read_text(encoding="utf-8"))
        cards.append({**entry, **{k: meta[k] for k in ("when", "then", "validated", "horizon") if k in meta}, "body": body.strip()})
    return cards


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    root = run.pack_dir / "skill-memory"
    if not root.exists():
        raise ValueError("this pack has no skill-memory/ directory")
    if a.action == "tags":
        return {"need": need_tags(run.profile), "profile": run.profile}
    if a.action == "list":
        return {"cards": skill_cards(run.pack_dir)}
    if a.action == "need":
        require_tool(run.pack_dir, "skill_memory")
        need = [t.strip() for t in (a.need or "").split(",") if t.strip()] or need_tags(run.profile)
        chosen = [c for c in skill_cards(run.pack_dir) if c.get("validated") and set(c.get("when", [])) <= set(need)]
        prefer = {}
        for c in chosen:
            field, value = c["then"].split("=")
            prefer[field] = parse_value(value)
        text = "# Working memory\n\nNeed: " + ", ".join(need) + "\nCards: " + (", ".join(c["name"] for c in chosen) or "none") + "\n"
        with open(run.pack_dir / "working.md", "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        run.log("working", need=need, cards=[c["name"] for c in chosen])
        return {"need": need, "cards": [{"name": c["name"], "when": c["when"], "then": c["then"], "horizon": c.get("horizon", 0)} for c in chosen],
                "prefer": prefer, "working": str(run.pack_dir / "working.md")}
    # update: the acting pack's tools.md must allow skill_memory *for updates* (the actor's line allows need only)
    writer = Path(a.writer) if a.writer and Path(a.writer).is_dir() else run.pack_dir
    require_tool(writer, "skill_memory")
    line = next((l for l in (writer / "tools.md").read_text(encoding="utf-8").splitlines() if l.startswith("- skill_memory")), "") if (writer / "tools.md").exists() else "update"
    if "update" not in line:
        raise ValueError(f"skill_memory --action update is not in {writer.name}'s tools.md (its skill_memory line allows need only); the meta pack updates cards")
    if not a.card or not a.then or "=" not in a.then:
        raise ValueError("an update is --card <name> --then field=value --when tag,tag --body text")
    field, value = a.then.split("=", 1)
    value = parse_value(value)
    rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]} for r in run.fit_rows()]
    wins, losses, _ = memory.tally(rows)
    if wins.get((field, value), 0) <= losses.get((field, value), 0):
        raise ValueError(f"not validated: {a.then} did not win its comparisons on {run.problem} "
                         f"({wins.get((field, value), 0)} wins, {losses.get((field, value), 0)} losses); nothing lands")
    updates = [r for r in run.trace.rows("skill_update") if (r["info"] or {}).get("visit") == a.visit and r["problem"] == run.problem]
    if updates:
        raise ValueError("one card update per visit")
    versions = run.versions_dir
    label = f"gen_{len(list(versions.glob('gen_*'))) + 1:03d}" if versions.exists() else "gen_001"
    packs.snapshot(run.pack_dir, versions, label)
    cards = skill_cards(run.pack_dir)
    existing = next((c for c in cards if c["name"] == a.card), None)
    horizon = (existing.get("horizon", 0) if existing else 0) + 1
    when = [t.strip() for t in (a.when or "").split(",") if t.strip()]
    text = (f"---\nname: {a.card}\nwhen: [{', '.join(when)}]\nthen: {a.then}\nvalidated: true\nhorizon: {horizon}\n---\n{a.body.strip()}\n")
    path = root / (existing["file"] if existing else f"cards/{a.card}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    if not existing:
        manifest = yaml.safe_load((root / "manifest.yaml").read_text(encoding="utf-8")) or {"cards": []}
        manifest["cards"].append({"name": a.card, "file": f"cards/{a.card}.md"})
        with open(root / "manifest.yaml", "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(manifest, f, sort_keys=False)
    run.log("skill_update", card=a.card, then=a.then, when=when, horizon=horizon, version=label, new=existing is None, visit=a.visit)
    return {"card": a.card, "file": path.relative_to(run.pack_dir).as_posix(), "horizon": horizon, "version": label, "new": existing is None,
            "wins": wins.get((field, value), 0), "losses": losses.get((field, value), 0)}


if __name__ == "__main__":
    cli.main(main)
