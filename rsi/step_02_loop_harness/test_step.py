"""Step 02 - loop.json is honoured by the tools, the audit log is never read back, the pack does not change."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import checks, packs, steps, tasks, tools  # noqa: E402
from common.fake import FakeModel  # noqa: E402

PACK = "adult-income-loop"
TASK = tasks.test_curriculum()[0][0]


def booted(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    return checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control"), pack


def test_loop_json_is_honoured_by_the_tools(tmp_path):
    run, pack = booted(tmp_path)
    loop = json.loads((pack / "loop.json").read_text(encoding="utf-8"))
    recipes = json.loads((pack / "recipes.json").read_text(encoding="utf-8"))
    assert [r["recipe"] for r in run.fits] == recipes and len(run.fits) == loop["N"] == 24
    gate = checks.budget_and_gate(run)
    assert gate["fit_25"].startswith("Error: budget of 24 fits used")           # "change N" is not the model's to do
    assert gate["second_test"].startswith("Error: the test split was scored once")
    assert checks.test_before_freeze(pack, TASK, tmp_path / "p" / "fresh").startswith("Error: the test split is locked until FREEZE")
    assert packs.lint_pack(pack, TASK) == []


def test_the_audit_log_is_written_and_never_read_back(tmp_path):
    run, pack = booted(tmp_path)
    lines = (run.run_dir / "loop_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 24 and json.loads(lines[0])["t"] == 1
    assert [n for n in tools.TOOLS if "loop_log" in n] == ["write_loop_log"]       # the only tool that touches it writes
    results = [m["content"] for m in run.messages if m["role"] == "tool"]
    assert not any("loop_log" in r for r in results if not r.startswith("logged"))  # and no result carried it back
    assert len(checks.tool_calls(run, "write_loop_log")) == 24


def test_pack_is_byte_identical_after_a_run(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    assert checks.unchanged(pack, lambda: checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control"))
    assert not (pack / "memory.json").exists()                                    # "write memory.json" is illegal, and did not happen


def test_generation_n_plus_1_loads_the_same_loop(tmp_path):
    a, pack = booted(tmp_path)
    b = checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run2", arm="control")
    assert checks.fit_sequence(a) == checks.fit_sequence(b)                        # nothing was learned, by design
