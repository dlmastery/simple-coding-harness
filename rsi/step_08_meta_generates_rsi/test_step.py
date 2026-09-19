"""Step 08 - the proposal carries the verifier contract verbatim and is refused without it; the generated packs
pass lesson 06's checks; scripted n lands nothing."""

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, curriculum, harness, memory, packs, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from run import generate_rsi  # noqa: E402

TASK = tasks.load_task(HERE / "skills" / "rsi-writer" / "task.json")
CUR, _ = tasks.test_curriculum()
T1, T3, T6 = CUR[0], CUR[2], CUR[5]
STEP01 = HERE.parent / "step_01_regular_harness" / "skills" / "adult-income-regular"


def test_proposal_contains_the_verifier_contract_and_the_human_sees_it_first(tmp_path):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run = generate_rsi(FakeModel(), tmp_path / "out", human=Human(["n"]), quiet=False)
    shown = buf.getvalue()
    payload = run.proposals.items["p1"]["payload"]
    assert packs.VERIFIER_CONTRACT in payload["verifier/SKILL.md"]
    assert shown.index("### verifier contract (the acceptance rule you are approving)") < shown.index("### actor/SKILL.md")
    assert "will change its own memory.json" in run.proposals.items["p1"]["summary"]
    assert not (tmp_path / "out").exists()                                             # n: nothing landed


def test_lint_refuses_a_proposal_without_the_contract(tmp_path):
    run = generate_rsi(FakeModel(), tmp_path / "out", human=Human(["n"]), quiet=True)
    files = dict(run.proposals.items["p1"]["payload"])
    files["verifier/SKILL.md"] = files["verifier/SKILL.md"].replace(packs.VERIFIER_CONTRACT, "The verifier reads the log.")
    result = execute(run, checks.call("propose", kind="pack", payload=files, summary="no contract"))
    assert result.startswith("Error: lint_pack refuses") and "verifier: a verifier pack must state the verifier contract verbatim" in result
    files["verifier/tools.md"] = run.proposals.items["p1"]["payload"]["verifier/tools.md"].replace("## Allowed\n", "## Allowed\n- fit_recipe - grade my own homework\n")
    result = execute(run, checks.call("propose", kind="pack", payload=files, summary="a verifier that fits"))
    assert "no one grades their own homework" in result
    assert len(run.human.asked) == 1


def test_generated_packs_pass_step_06_checks(tmp_path):
    out = tmp_path / "out"
    generate_rsi(FakeModel(), out, human=Human(["y"]), quiet=True)
    actor, verifier = out / "actor", out / "verifier"
    assert packs.lint_pack(out, TASK) == [] and sorted(p.name for p in out.iterdir()) == ["actor", "verifier"]
    # the verifier sees only the log
    _, inner, ver = curriculum.run_problem(actor, T1, FakeModel(), tmp_path / "run", verifier_dir=verifier)
    iso = checks.verifier_isolation(inner, ver)
    assert iso["leaked"] == [] and iso["row_keys"] == ["error", "problem", "recipe", "seed", "val_score"]
    # write_card refuses the word test
    card = {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "test"}, "evidence": 1, "counter": 0}
    assert execute(ver, checks.call("write_card", card=card)).startswith("Error: not a card: a card may not mention 'test'")
    # MEMORY_OFF reproduces step 01 exactly
    off = checks.run_pack(actor, T1, FakeModel(), tmp_path / "off", arm="control", memory_off=True)
    assert checks.fit_sequence(off) == checks.fit_sequence(checks.run_pack(STEP01, T1, FakeModel(), tmp_path / "reg", arm="control"))
    # the memory arm >= MEMORY_OFF at the same budget after two problems of experience
    curve = curriculum.run_curriculum(actor, verifier, [T1, T3, T6], FakeModel(), tmp_path / "curve")
    assert curve[-1]["gap_val"] >= 0 and curve[-1]["wasted_memory"] < curve[-1]["wasted_control"]
    assert len(memory.load(actor / "memory.json")) > 0


def test_generating_twice_gives_the_same_proposal(tmp_path):
    a = generate_rsi(FakeModel(), tmp_path / "a", human=Human(["n"]), quiet=True)
    b = generate_rsi(FakeModel(), tmp_path / "b", human=Human(["n"]), quiet=True)
    assert a.proposals.items["p1"]["payload"] == b.proposals.items["p1"]["payload"]
    assert harness.boot(HERE / "skills" / "rsi-writer", TASK, run_dir=tmp_path / "w", quiet=True).budget.n == 0   # a writer has no fits
