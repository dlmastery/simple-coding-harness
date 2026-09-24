"""Explain frozen outcome ties from archived constructors and predictions; zero fits."""
import csv
import argparse
import hashlib
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "rsi/evidence/2026-09-22/nested-research-evaluation"
OUT = ROOT / "how-did-i-generate-it/rsi/validation/nested-outcome-diagnosis"


def main(output=OUT):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Fresh diagnostic output required; preserve previous output")
    manifest = {r["path"]: r for r in csv.DictReader((ARCHIVE / "ARCHIVE-MANIFEST.csv").open(newline="", encoding="utf-8"))}
    identities, checks = {}, []

    def read(relative):
        raw = (ARCHIVE / relative).read_bytes()
        entry = manifest[relative]
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry["sha256"] or len(raw) != int(entry["bytes"]):
            raise ValueError("Archived input changed: " + relative)
        identities[relative] = dict(path=relative, bytes=len(raw), sha256=digest)
        return list(csv.DictReader(raw.decode("utf-8").splitlines()))

    def check(name, passed):
        checks.append(dict(check=name, passed=bool(passed)))
        if not passed:
            raise ValueError(name)

    panel = read("PANEL.csv")
    choices = {(r["task"], r["arm"]): r for r in read("CHOICES.csv")}
    scores = {(r["task"], r["arm"]): r for r in read("SCORES.csv")}
    check("six tasks and thirty unique choices", len(panel) == 6 and len(choices) == len(scores) == 30)
    outcomes = []
    for task in panel:
        tid, kind = task["task"], task["kind"]
        ledgers, predictions, native = {}, {}, {}
        for arm in ("parent", "i0", "i1"):
            ledger = read(f"runs/{tid}/{arm}/LEDGER.csv")
            check(f"{tid}/{arm} twelve successful attempts", len(ledger) == 12 and all(r["status"] == "success" for r in ledger))
            check(f"{tid}/{arm} ordered steps", [int(r["step"]) for r in ledger] == list(range(1, 13)))
            choice, score = choices[(tid, arm)], scores[(tid, arm)]
            selected = ledger[int(choice["step"]) - 1]
            check(f"{tid}/{arm} frozen selected identity", selected["constructor_sha256"] == choice["constructor_sha256"] and selected["candidate_sha256"] == choice["candidate_sha256"] == score["candidate_sha256"])
            minimum = min(ledger, key=lambda r: (float(r["selection_loss"]), int(r["step"])))
            check(f"{tid}/{arm} selection argmin", choice["step"] == minimum["step"])
            rows = read(f"scoring/{tid}/{arm}/final-predictions.csv")
            check(f"{tid}/{arm} final rows unique", len(rows) == int(task["final"]) and len({r["row_id"] for r in rows}) == len(rows))
            if kind == "classification":
                labels = sorted({r["truth"] for r in rows})
                value = statistics.mean(sum(r["truth"] == label and r["prediction"] == label for r in rows) / sum(r["truth"] == label for r in rows) for label in labels)
                predictions[arm] = [r["prediction"] for r in rows]
            else:
                value = statistics.mean(abs(float(r["truth"]) - float(r["prediction"])) for r in rows)
                predictions[arm] = [float(r["prediction"]) for r in rows]
            check(f"{tid}/{arm} native score recomputes", math.isclose(value, float(score["final_score"]), rel_tol=1e-12, abs_tol=1e-10))
            native[arm] = value
            ledgers[arm] = ledger
            row_keys = [(r["row_id"], r["truth"]) for r in rows]
            if arm == "parent":
                parent_rows = row_keys
            else:
                check(f"{tid}/{arm} same final rows and truth", parent_rows == row_keys)
        for arm in ("i0", "i1"):
            parent, child = choices[(tid, "parent")], choices[(tid, arm)]
            before, after = ledgers["parent"], ledgers[arm]
            check(f"{tid}/{arm} common eight-model prefix", all(a["constructor_sha256"] == b["constructor_sha256"] for a, b in zip(before[:8], after[:8])))
            changed = sum(a["constructor_sha256"] != b["constructor_sha256"] for a, b in zip(before, after))
            differences = sum(a != b for a, b in zip(predictions["parent"], predictions[arm]))
            constructor_equal = parent["constructor_sha256"] == child["constructor_sha256"]
            delta = native[arm] - native["parent"]
            loss_delta = float(scores[(tid, arm)]["final_loss"]) - float(scores[(tid, "parent")]["final_loss"])
            tied = abs(loss_delta) <= 1e-12
            explanation = ("same selected constructor and predictions" if constructor_equal and differences == 0 else
                           "different selected constructors, identical predictions" if differences == 0 else
                           "different predictions, same aggregate score" if tied else "different predictions and score")
            outcomes.append(dict(task=tid, name=task["name"], kind=kind, child=arm,
                changed_search_positions=changed, parent_selected_step=parent["step"], child_selected_step=child["step"],
                parent_template=parent["template"], child_template=child["template"], parent_factor=parent["factor"], child_factor=child["factor"],
                same_selected_constructor=constructor_equal, final_rows=len(parent_rows), changed_final_predictions=differences,
                child_from_shared_prefix=int(child["step"]) <= 8,
                selection_loss_change=float(child["selection_loss"]) - float(parent["selection_loss"]),
                native_parent=native["parent"], native_child=native[arm], native_score_change=delta,
                final_loss_change=loss_delta, outcome="tie" if tied else "better" if loss_delta < 0 else "worse", explanation=explanation))

    output.mkdir(parents=True)
    def write(name, rows):
        with (output / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    write("OUTCOMES.csv", outcomes)
    write("INPUTS.csv", list(identities.values()))
    write("CHECKS.csv", checks)
    (output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    for r in outcomes:
        print(r["task"], r["child"], r["outcome"], r["changed_final_predictions"], r["explanation"])
    print(f"{len(checks)} checks; {len(identities)} archived inputs; zero model fits")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT,
                        help="New output directory; existing reports are never overwritten")
    args = parser.parse_args()
    if not args.output.is_absolute():
        parser.error("--output must be an absolute path")
    main(args.output)
