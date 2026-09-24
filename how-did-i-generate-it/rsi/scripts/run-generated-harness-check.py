"""Execute the generated harness's baseline and concrete refusal requests."""
import hashlib
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[3]
root = repo / "rsi/evidence/2026-09-20/generated-harness"
workspace = root / "executed"
if workspace.exists():
    raise SystemExit("Preserve the existing walkthrough; use a new output folder for another run.")
outputs = root / "command-outputs"
outputs.mkdir(exist_ok=False)
base = [sys.executable, str(root / "package/run.py"), "--repo", str(repo), "--workspace", str(workspace)]
cases = [
    ("baseline", ["--hypothesis", "Use the training median under the frozen task"], 0),
    ("leakage", ["--features", "casual,registered", "--hypothesis", "Test refusal of outcome component inputs"], 1),
    ("budget", ["--model", "linear", "--hypothesis", "Test refusal after two charged attempts"], 1),
]
lines = ["# Generated harness execution", "", "Author-guided check of labs 06.01–06.04. No learner responses were supplied.", "",
         "| Request | Exit | Output |", "|---|---:|---|"]
for name, arguments, expected in cases:
    result = subprocess.run(base + arguments, text=True, capture_output=True, timeout=60)
    text = result.stdout + result.stderr
    (outputs / f"{name}.txt").write_text(text, encoding="utf-8")
    if result.returncode != expected:
        raise RuntimeError(f"Unexpected {name} result: {result.returncode}: {text}")
    lines.append(f"| {name} | {result.returncode} | {text.strip().replace('|', '/')} |")
lines += ["", "One model fit ran. The leaked-feature request consumed the second attempt and failed before fitting. "
          "The third request was refused before another candidate was admitted. The brief's two-attempt limit was executed, not merely documented.", "",
          "The builder skill was read during course authoring; this package was generated and run by that same authoring agent. "
          "This is a concrete generation walkthrough, not independent regeneration or autonomous improvement of the builder.", "",
          "Builder skill SHA-256: `"+hashlib.sha256((repo / "rsi/skills/build-ml-harness/SKILL.md").read_bytes()).hexdigest()+"`.", ""]
(root / "EXECUTION.md").write_text("\n".join(lines), encoding="utf-8")
print("Generated harness: baseline checked, leakage refused, attempt limit enforced.")
