"""write_card - merge one card (or a list) into a pack's memory.json. The verifier's only pen.

    python ../tools/write_card.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json \\
        --card '{"if": {"key": "imbalance", "op": "<", "value": 0.35}, "then": {"field": "class_weight", "prefer": "balanced"}, "evidence": 1, "counter": 0}'
    python ../tools/write_card.py --pack ... --task ... --cards @cards.json --as adult-income-verifier

A card is validated against the pack's memory.schema.json: exactly `if`,
`then`, `evidence`, `counter`; no note, no reason, no field the schema does
not name, and never the words "test" or "intent". A card whose counters
reach half its evidence is demoted (it no longer applies); the result says
so. Refused under MEMORY_OFF and when the memory is frozen (the exam).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, card="one card: JSON or @file", cards="a JSON list of cards (or @file)",
                               **{"as": {"dest": "writer", "default": None, "help": "the pack writing (for the trace), e.g. adult-income-verifier"}}))


def write_one(run, card, schema, cards):
    try:
        memory.validate_card(card, schema)
    except Exception as e:
        raise ValueError(f"not a card: {str(e).splitlines()[0]}")
    was_active = {memory.card_id(c): memory.active(c) for c in cards}
    cards, added = memory.merge(cards, card)
    merged = next(c for c in cards if memory.card_id(c) == memory.card_id(card))
    demoted = was_active.get(memory.card_id(card), False) and not memory.active(merged)
    run.log("card", card=merged, added=added, demoted=demoted)
    return {"card": merged, "added": added, "active": memory.active(merged), "demoted": demoted}


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    if a.writer and Path(a.writer).is_dir():
        require_tool(a.writer, "write_card")
    if run.memory_off:
        raise ValueError("MEMORY_OFF: no card is written this run")
    if run.opened and run.arm_state.get("memory_frozen"):
        raise ValueError("the memory is frozen; no card lands (the exam problem is never written to)")
    schema = json.loads(run.files["memory.schema.json"]) if "memory.schema.json" in run.files else memory.CARD_SCHEMA
    todo = [cli.value(a.card)] if a.card else cli.value(a.cards) if a.cards else None
    if not todo or not isinstance(todo, list):
        raise ValueError("give --card (one) or --cards (a JSON list)")
    cards = memory.load(run.memory_path)
    results = []
    for card in todo:
        try:
            results.append(write_one(run, card, schema, cards))
        except ValueError as e:
            results.append({"card": card, "error": str(e), "refused": True})
    memory.save(run.memory_path, cards)
    written = [r for r in results if not r.get("refused")]
    out = {"cards": len(cards), "written": len(written), "added": sum(1 for r in written if r["added"]),
           "demoted": sum(1 for r in written if r["demoted"]), "refused": sum(1 for r in results if r.get("refused")),
           "by": a.writer or run.pack}
    if len(results) == 1:
        return {**results[0], **out} if not results[0].get("refused") else {"error": results[0]["error"], "card": results[0]["card"]}
    return {**out, "results": results}


if __name__ == "__main__":
    cli.main(main)
