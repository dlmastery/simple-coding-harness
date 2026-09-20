"""Persist and read controller state before actions; one declared correction fit."""
import argparse
import csv
import hashlib
import io
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--action", choices=["fit", "check"], required=True)
    args = parser.parse_args()
    repo, out, prior = args.repo.resolve(), args.workspace.resolve(), args.prior.resolve()
    events = out / "EVENTS.csv"
    state_file = out / "STATE.md"
    if not out.exists():
        if args.action != "fit":
            raise SystemExit("No fit exists to check.")
        out.mkdir(parents=True)
        shutil.copyfile(__file__, out / "coordinator.source.py")
        shutil.copyfile(repo / "how-did-i-generate-it/rsi/validation/LIVE-COORDINATOR-PROTOCOL.md", out / "PROTOCOL.md")
        save(out / "COORDINATOR.md", "# Execute one checked baseline\n\nRead STATE.md before each action. Only ready admits one bike constant/calendar fit at seed 17. Save running before launch. On success save awaiting-check and exit. The next process checks task, full candidate identity, saved predictions, and result. Only agreement permits complete. Missing evidence stays awaiting-check; scientific ambiguity needs clarification. Complete forbids further fitting. A failed command needs review and cannot auto-retry.\n")
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        save(out / "SOURCE.md", f"# Source\n\nRevision: {revision}\n\nDriver SHA-256: {sha(Path(__file__))}\n\nSame author context. A fresh check process reads saved control state; it is not an independent coding agent.\n")

    def event(action, state, detail):
        rows = []
        if events.exists():
            with events.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
        rows.append({"sequence": len(rows) + 1, "utc": datetime.now(timezone.utc).isoformat(),
                     "action": action, "state": state, "detail": detail})
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        save(events, stream.getvalue())

    def transition(state, reason):
        text = f"# Coordinator state\n\nState: {state}\nTask: bike\nCandidate: run/trial-001\nFit allowance: 1\nReason: {reason}\n"
        save(state_file, text)
        event("state-saved", state, reason)
        snapshots = out / "states"
        index = len(list(snapshots.glob("*.md"))) + 1
        save(snapshots / f"{index:02d}-{state}.md", text)

    def current():
        text = state_file.read_text(encoding="utf-8")
        return re.search(r"^State: ([a-z-]+)$", text, re.MULTILINE).group(1)

    def execute(label, script, arguments):
        command = [sys.executable, str(script), *map(str, arguments)]
        event("command-start", current(), label)
        start = time.perf_counter()
        try:
            result = subprocess.run(command, cwd=repo, text=True, capture_output=True,
                                    encoding="utf-8", timeout=60)
            status, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            status, stdout, stderr = 124, str(error.stdout or ""), str(error.stderr or "")
        elapsed = time.perf_counter() - start
        save(out / "commands" / f"{label}.md", f"# {label}\n\nArguments: {command!r}\n\nExit: {status}. Wall seconds: {elapsed:.6f}.\n\n```text\n{stdout}\n```\n\n```text\n{stderr}\n```\n")
        event("command-exit", current(), f"{label}; exit {status}; wall_seconds {elapsed:.6f}")
        if status != 0:
            transition("needs-review", f"{label} failed; no automatic retry")
            raise SystemExit(status)

    if not state_file.exists():
        transition("ready", "unambiguous bike task and one-fit contract")
    event("state-read", current(), f"process invoked with action {args.action}")
    candidate = out / "run/trial-001"
    if args.action == "fit":
        if current() != "ready":
            event("refused", current(), "fit is only allowed from ready; no tool launched")
            print("REFUSED: fit is only allowed from ready; no tool launched.")
            raise SystemExit(1)
        transition("running", "reserve sole fit before launching")
        execute("fit", repo / "rsi/tools/lab.py", ["run", "--task", "bike", "--workspace", out / "run",
                "--model", "constant", "--features", "calendar", "--seed", 17, "--attempt-limit", 1,
                "--hypothesis", "Verify live state-controlled handoffs with the unchanged baseline recipe."])
        save(out / "PENDING-CHECK.md", f"# Pending evidence\n\nTask: bike\nCandidate: {candidate}\nPredictions SHA-256: {sha(candidate / 'predictions.csv')}\n")
        transition("awaiting-check", "fit succeeded; checker not yet launched")
        print("Saved awaiting-check. End this process before checking.")
        return

    if current() != "awaiting-check":
        event("refused", current(), "check requires awaiting-check")
        raise SystemExit(1)
    expected = ("bike", str(candidate), sha(candidate / "predictions.csv"))
    pending = (out / "PENDING-CHECK.md").read_text(encoding="utf-8")
    assert f"Candidate: {expected[1]}\n" in pending and f"Predictions SHA-256: {expected[2]}\n" in pending

    def accept(target_known, packet):
        if not target_known:
            return "needs-clarification"
        if packet is None or packet[:3] != expected or packet[3] != 0:
            return "awaiting-check"
        return "complete"

    earlier = prior / "02-06/arm-a/trial-001"
    assert (earlier / "CHECK.md").read_text().find("PASS:") >= 0
    wrong = ("bike", str(earlier), sha(earlier / "predictions.csv"), 0)
    assert wrong[2] == expected[2] and wrong[1] != expected[1]
    cases = [("missing-check", True, None, "awaiting-check"),
             ("ambiguous-target", False, None, "needs-clarification"),
             ("wrong-candidate", True, wrong, "awaiting-check")]
    lines = ["# Handoff fixtures", "", "These execute acceptance checks without changing the active run.", ""]
    for label, target_known, packet, verdict in cases:
        actual = accept(target_known, packet)
        assert actual == verdict
        event("fixture", current(), f"{label}: {actual}")
        lines.append(f"- {label}: {actual}.")
    lines += ["", f"Wrong-candidate packet: {wrong!r}", "", "Its predictions are byte-identical; its full candidate identity is different."]
    save(out / "FIXTURES.md", "\n".join(lines) + "\n")
    execute("check", repo / "rsi/tools/check_result.py", [candidate, "--report", candidate / "CHECK.md"])
    assert sha(candidate / "predictions.csv") == expected[2]
    verdict = accept(True, (*expected, 0))
    assert verdict == "complete"
    transition(verdict, "matching task, full candidate identity, predictions, and successful checker")
    print("Complete: actual saved state governed both commands.")


if __name__ == "__main__":
    main()
