"""Learner-owned bounded controller generated for the clean journey.

Run from a coding agent. No concurrent writes to one workspace are supported.
The controller records refusals and preserves the same limit across processes.
"""
import argparse
import csv
import hashlib
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "compare", "final"])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--task", choices=["bike", "wine"], default="bike")
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--model", default="constant")
    parser.add_argument("--features", default="calendar")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--hypothesis", default="")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--candidate")
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve() / "rsi/tools"))
    import lab
    import check_result

    if not 1 <= args.limit <= lab.MAX_ATTEMPTS:
        parser.error("Limit must be within the shared tool's attempt bound.")
    lab.MAX_ATTEMPTS = args.limit
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    version = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    expected = f"# Controller contract\n\nSource: {version}\nTask: {args.task}\nAttempt limit: {args.limit}\nUnlabelled duplicate recipes: refused\n"
    control = workspace / "CONTROLLER-CONTRACT.md"
    started = time.perf_counter()
    before = len(lab.records(workspace))
    code = 0
    try:
        if control.exists() and control.read_text(encoding="utf-8") != expected:
            raise lab.Refusal("Controller or limit changed; preserve this experiment and use a new workspace.")
        if not control.exists():
            with control.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(expected)
        rows = lab.records(workspace)
        if args.action == "run":
            recipe = (args.task, args.model, args.features, str(args.seed))
            if any(tuple(row[k] for k in ["task", "model", "features", "seed"]) == recipe for row in rows):
                raise lab.Refusal("Duplicate recipe; no new fit. Use a separately declared replication experiment.")
            row = lab.experiment(workspace, args.task, args.model, args.features,
                                 args.seed, args.hypothesis, args.policy)
            check_result.check(workspace / row["candidate"])
            message = f"Checked {row['candidate']}; score {row['score']:.6f}."
        elif args.action == "compare":
            lab.check_contract(workspace, args.task)
            for row in rows:
                if row["status"] == "ok":
                    check_result.check(workspace / row["candidate"])
            message = f"Selected {lab.compare(workspace)}."
        else:
            if not args.candidate:
                raise lab.Refusal("Name the frozen candidate before final evaluation.")
            check_result.check(workspace / args.candidate)
            message = f"Final score {lab.final_evaluation(workspace, args.candidate):.6f}."
    except (lab.Refusal, ValueError, OSError) as error:
        code, message = 1, f"REFUSED: {error}"
    request = dict(action=args.action, model=args.model, features=args.features,
                   attempts_before=before, attempts_after=len(lab.records(workspace)),
                   exit_status=code, command_seconds=round(time.perf_counter()-started, 6),
                   outcome=message)
    path = workspace / "requests.csv"
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(request))
        if not exists:
            writer.writeheader()
        writer.writerow(request)
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
