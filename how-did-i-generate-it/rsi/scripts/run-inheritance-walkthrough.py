"""Author-guided execution of a selected improver; not an autonomous RSI trial."""
import hashlib
import shutil
import subprocess
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
EVIDENCE = REPO / "rsi/evidence/2026-09-20"
OUT = EVIDENCE / "inherited-improver"
POLICY = OUT / "IMPROVER-v1.md"

# The author selected and read this procedure before writing the walkthrough.
policy_bytes = POLICY.read_bytes()
policy_hash = hashlib.sha256(policy_bytes).hexdigest()
if (OUT / "executed-round").exists():
    raise SystemExit("Preserve the existing round. Choose a new output folder for another run.")
round_dir = OUT / "executed-round"
round_dir.mkdir()
incumbent = 109.807668
cases = [
    ("false-summary", "02-01-model-change", "trial-001", "reject"),
    ("valid-improvement", "02-03-feature-change", "trial-002", "retain"),
]
trace = [
    "# Executed author-guided round", "",
    f"Selected procedure: IMPROVER-v1.md. SHA-256: `{policy_hash}`.", "",
    "The authoring agent read this procedure and generated this driver to execute its required checks. "
    "This is one shared context with a selected procedure, not autonomous proposal generation or an independent agent comparison.", "",
    f"Fixed incumbent selection MAE: {incumbent:.6f}. Lower is better. No new model fits.", "",
    "| Case | Check exit | Observed decision |", "|---|---:|---|",
]
for label, source_run, candidate, expected in cases:
    source = EVIDENCE / "walkthrough" / source_run
    workspace = round_dir / label
    workspace.mkdir()
    shutil.copy2(source / "trials.csv", workspace / "trials.csv")
    shutil.copy2(source / "CONTRACT.md", workspace / "CONTRACT.md")
    shutil.copytree(source / candidate, workspace / candidate)
    report = workspace / candidate / "RESULT.md"
    if label == "false-summary":
        original = report.read_text(encoding="utf-8")
        if "159.947912" not in original:
            raise ValueError("Source result changed; do not manufacture a replacement.")
        report.write_text(original.replace("159.947912", "9.000000"), encoding="utf-8")
        (workspace / "FIXTURE.md").write_text(
            "# Deliberately false summary\n\nTeaching copy: report MAE changed from 159.947912 to 9.000000. "
            "Predictions, actual targets, and ledger remain original. The false score is not a measured result.\n", encoding="utf-8")
    command = [sys.executable, str(REPO / "rsi/tools/check_result.py"),
               str(workspace / candidate), "--report", str(workspace / "CHECK.md")]
    result = subprocess.run(command, text=True, capture_output=True, timeout=60)
    (workspace / "COMMAND-OUTPUT.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode == 1:
        decision = "reject"
    elif result.returncode == 0:
        import csv
        with (workspace / "trials.csv").open(newline="", encoding="utf-8") as stream:
            row = next(r for r in csv.DictReader(stream) if r["candidate"] == candidate)
        decision = "retain" if float(row["score"]) < incumbent else "reject"
    else:
        raise RuntimeError(f"Checker could not run: {result.stderr}")
    if decision != expected:
        raise AssertionError(f"Unexpected {label} decision: {decision}")
    trace.append(f"| {label} | {result.returncode} | {decision} |")
trace += ["", "The mismatch was rejected; the valid improvement was retained. The checker requirement was executed in this round. "
          "The unchanged task metric decides retention only after evidence agrees.", "",
          "The weak v0 rule would prefer the advertised 9.0 if it trusted that summary. This is rule analysis; "
          "no independent v0 agent decision was executed. These two fixtures do not estimate a general improvement rate, "
          "cost-adjusted advantage, or recursive acceleration.", ""]
if POLICY.read_bytes() != policy_bytes:
    raise ValueError("Policy changed during execution.")
(OUT / "EXECUTION-TRACE.md").write_text("\n".join(trace), encoding="utf-8")
print("Completed two inherited-procedure checks: mismatch rejected; valid result retained.")
