"""Step 03 - the writer cannot fit; the human sees the pack first; n lands nothing, y lands the proposal, edit lands
the human's text; the same task gives the same proposal; the generated pack passes step 02's checks."""

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, packs, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from run import generate  # noqa: E402

TASK = tasks.load_task(HERE / "skills" / "loop-writer" / "task.json")
SYNTH = tasks.test_curriculum()[0][0]


def test_writer_cannot_fit(tmp_path):
    run = generate(FakeModel(), tmp_path / "out", human=Human(["n"]), quiet=True)
    recipe = {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    assert execute(run, checks.call("fit_recipe", recipe=recipe)).startswith("Error: fit_recipe is not in this pack's tools.md")
    assert run.budget.n == 0 and not any(n == "fit_recipe" for n, _ in checks.tool_calls(run))


def test_proposal_is_shown_before_anything_lands_and_n_lands_nothing(tmp_path):
    out = tmp_path / "out"
    buf = io.StringIO()
    with redirect_stdout(buf):
        run = generate(FakeModel(), out, human=Human(["n"]), quiet=False)
    shown = buf.getvalue()
    assert "--- proposal p1: pack" in shown and "### SKILL.md" in shown and "### loop.json" in shown
    assert not out.exists()                                                     # nothing landed
    assert run.proposals.items["p1"]["decision"] == "n" and not run.proposals.items["p1"]["applied"]
    assert not any(n == "apply" for n, _ in checks.tool_calls(run))


def test_y_lands_exactly_the_proposal(tmp_path):
    out = tmp_path / "out"
    run = generate(FakeModel(), out, human=Human(["y"]), quiet=True)
    assert packs.read_pack(out) == run.proposals.items["p1"]["payload"]
    assert packs.lint_pack(out, TASK) == []


def test_edit_lands_the_humans_text(tmp_path):
    out = tmp_path / "out"
    first = generate(FakeModel(), tmp_path / "unused", human=Human(["n"]), quiet=True)
    edited = dict(first.proposals.items["p1"]["payload"])
    edited["SKILL.md"] = edited["SKILL.md"].replace("Nothing else is read.", "Nothing else is read. (edited by the human)")
    run = generate(FakeModel(), out, human=Human([("edit", edited)]), quiet=True)
    assert "(edited by the human)" in (out / "SKILL.md").read_text(encoding="utf-8")
    assert run.proposals.items["p1"]["decision"] == "edit"


def test_generating_twice_gives_byte_identical_proposals(tmp_path):
    a = generate(FakeModel(), tmp_path / "a", human=Human(["n"]), quiet=True)
    b = generate(FakeModel(), tmp_path / "b", human=Human(["n"]), quiet=True)
    assert a.proposals.items["p1"]["payload"] == b.proposals.items["p1"]["payload"]


def test_generated_pack_boots_and_passes_step_02_checks(tmp_path):
    out = tmp_path / "out"
    generate(FakeModel(), out, human=Human(["y"]), quiet=True)
    loop = json.loads((out / "loop.json").read_text(encoding="utf-8"))
    recipes = json.loads((out / "recipes.json").read_text(encoding="utf-8"))
    assert loop["N"] == 24 == len(recipes)
    run = checks.run_pack(out, SYNTH, FakeModel(), tmp_path / "run", arm="control")
    assert [r["recipe"] for r in run.fits] == recipes
    gate = checks.budget_and_gate(run)
    assert gate["fit_25"].startswith("Error: budget") and gate["second_test"].startswith("Error: the test split was scored once")
    assert checks.test_before_freeze(out, SYNTH, tmp_path / "fresh").startswith("Error: the test split is locked")
    assert checks.unchanged(out, lambda: checks.run_pack(out, SYNTH, FakeModel(), tmp_path / "run2", arm="control"))
