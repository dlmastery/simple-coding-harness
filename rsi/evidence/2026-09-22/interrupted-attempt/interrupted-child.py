import importlib.util
from pathlib import Path
import sys
import time

source, workspace = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("course_lab", source)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

def wait_before_training(*args, **kwargs):
    (workspace / "NO-TRAINING-MARKER.txt").write_text("Admitted attempt reached a wait stub; no estimator fit called.\n", encoding="utf-8")
    time.sleep(60)
    raise RuntimeError("Parent did not stop the fixture within its readiness budget")

lab.fit_once = wait_before_training
raise SystemExit(lab.main(["run", "--task", "bike", "--workspace", str(workspace),
    "--attempt-limit", "3", "--model", "constant", "--features", "calendar",
    "--seed", "17", "--hypothesis", "No-training interruption fixture; preserve the charged slot."]))
