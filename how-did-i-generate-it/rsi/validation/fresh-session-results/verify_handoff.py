"""Read-only checks of the one-fit handoff archive; never trains a model."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(name, passed):
        checks.append((name, bool(passed)))
        if not passed:
            raise AssertionError(name)

    # The plan's status text may be updated after dispatch. Scientific inputs
    # and both actual packets must remain identical.
    frozen = rows(HERE / "PRE-DISPATCH-SOURCES.csv")
    for record in frozen:
        if record["path"].endswith("fresh-session-plan/README.md"):
            continue
        check("frozen source " + record["path"], digest(REPO / record["path"]) == record["sha256"])
    complete = HERE / "complete"
    ledger = rows(complete / "trials.csv")
    check("one admitted attempt", len(ledger) == 1)
    trial = ledger[0]
    for key, expected in {"candidate": "trial-001", "status": "ok", "task": "bike",
                          "model": "constant", "features": "calendar", "seed": "17"}.items():
        check("recipe " + key, trial[key] == expected)
    skill = REPO / "how-did-i-generate-it/rsi/validation/fresh-session-plan/complete/BASELINE-SKILL.md"
    check("ledger skill identity", trial["policy_sha256"] == digest(skill))
    check("snapshot skill identity", digest(complete / "trial-001/POLICY-SNAPSHOT.md") == digest(skill))
    check("one trial directory", len(list(complete.glob("trial-*"))) == 1)
    source = rows(REPO / "rsi/examples/bike-demand/source/hour.csv")
    train = [int(row["cnt"]) for row in source if row["dteday"] < "2012-01-01"]
    selection = [(index, row) for index, row in enumerate(source)
                 if "2012-01-01" <= row["dteday"] < "2012-07-01"]
    prediction_path = complete / "trial-001/predictions.csv"
    predictions = rows(prediction_path)
    check("selection row count", len(predictions) == len(selection))
    median = statistics.median(train)
    errors = []
    for prediction, (index, row) in zip(predictions, selection):
        check(f"row {index} identity", int(prediction["source_row"]) == index)
        check(f"row {index} target", float(prediction["actual"]) == int(row["cnt"]))
        check(f"row {index} fixed median", float(prediction["predicted"]) == median)
        errors.append(abs(float(prediction["predicted"]) - int(row["cnt"])))
    mae = statistics.mean(errors)
    check("independent MAE", math.isclose(mae, float(trial["score"]), abs_tol=1e-10))
    old = REPO / "rsi/evidence/2026-09-20/clean-journey/01-05/trial-001/predictions.csv"
    check("old recipe prediction bytes", digest(prediction_path) == digest(old))
    baseline_exit = json.loads((complete / "commands/03-baseline/exit.json").read_text())
    check("baseline exit", baseline_exit["exit_code"] == 0 and not baseline_exit["timed_out"])
    check("timeout configured", baseline_exit["timeout_seconds"] == 60)
    check("baseline within timeout", baseline_exit["elapsed_seconds"] < 60)
    contract = (complete / "CONTRACT.md").read_text().splitlines()
    check("attempt limit in frozen contract", "- max_attempts: 1" in contract)
    check("frozen split", "- split: 2011 / 2012-H1 / 2012-H2" in contract)
    command_records = [json.loads(path.read_text()) for path in (complete / "commands").glob("*/command.json")]
    check("one run command", sum("run" in record["argv"] for record in command_records) == 1)
    check("no final command", all("final" not in record["argv"] for record in command_records))
    missing = HERE / "missing"
    check("no missing-packet task", not (skill.parent.parent / "missing-task/TASK.md").exists())
    check("missing report identifies task", "TASK.md" in (missing / "FINDINGS.md").read_text(encoding="utf-8-sig"))
    check("no missing-session model artifacts", not list(missing.rglob("predictions.csv")) and not list(missing.rglob("trials.csv")))
    report = (f"# Independent handoff checks\n\n{len(checks)} checks passed. Zero additional fits.\n\n"
              f"Training median: {median:g} rentals/hour. Selection rows: {len(selection)}.\n"
              f"Selection MAE: {mae:.12f} rentals/hour. All predictions match the earlier recipe byte for byte.\n\n"
              "The unchanged skill reproduced the fixed baseline. This is evidence of reuse, not improvement.\n"
              "Missing-session zero-fit and read-scope claims also rely on the recorded command ledger;\n"
              "absence of prediction files alone is not an OS-level execution or access audit.\n")
    (HERE / "CHECKS.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
