"""Agent-generated entry point from the adjacent readable bike harness brief."""
import argparse
import hashlib
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--model", default="constant")
    parser.add_argument("--features", default="calendar")
    parser.add_argument("--hypothesis", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve() / "rsi/tools"))
    import lab
    import check_result

    # The brief asks for a stricter limit than the general teaching runner.
    lab.MAX_ATTEMPTS = 2
    args.workspace.mkdir(parents=True, exist_ok=True)
    version = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    wrapper_contract = args.workspace / "GENERATED-CONTRACT.md"
    expected = f"# Generated harness contract\n\nWrapper SHA-256: {version}\n\nTask: bike. Attempt limit: 2, including failures. Metric: MAE.\n"
    try:
        if wrapper_contract.exists():
            if wrapper_contract.read_text(encoding="utf-8") != expected:
                raise lab.Refusal("Generated harness changed; use a new workspace.")
        else:
            # Exclusive creation avoids overwriting another process's contract.
            with wrapper_contract.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(expected)
        row = lab.experiment(args.workspace, "bike", args.model, args.features, 17, args.hypothesis)
        score = check_result.check(args.workspace / row["candidate"])
        print(f"Checked {row['candidate']}: selection MAE {score:.6f}. Attempts used: {len(lab.records(args.workspace))}/2.")
        return 0
    except (lab.Refusal, ValueError, FileExistsError) as error:
        print(f"REFUSED: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
