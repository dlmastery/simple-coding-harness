"""Step 09 - generation n+1 boots what generation n wrote; under approval: human nothing lands without a y and an
edit lands the human's version; under approval: gate a patch that raises val and lowers the private score is
rejected and versions/ restores the pack; META_OFF leaves the pack alone; the meta pack cannot call score_test."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, harness, packs, steps, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402
from run import ACTOR, META, VERIFIER, run_generations  # noqa: E402

CUR, _ = tasks.test_curriculum()
T1, T3, T6 = CUR[0], CUR[2], CUR[5]
FIXED = ("SKILL.md", "tools.md", "schema.json", "memory.schema.json", "eval.md")   # everything but memory.json


def fixed_checksums(pack):
    return {k: v for k, v in packs.checksums(pack).items() if k in FIXED}


def test_generation_n_plus_1_boots_the_files_generation_n_wrote(tmp_path):
    run_dir = tmp_path / "run"
    curve, actor, versions = run_generations(FakeModel(), "human", [T1, T3], run_dir, human=Human(["y", "y"]), into=tmp_path / "w")
    trace = TraceLog(run_dir / "traces.jsonl")
    applied = trace.rows("apply")
    assert applied and applied[0]["info"]["version"] == "gen_001"
    boots = [b for b in trace.rows("boot", arm="memory") if b["info"]["pack"] == ACTOR]
    assert boots[1]["info"]["checksums"] == applied[0]["info"]["checksums"]         # problem 2 booted what generation 1 wrote
    assert boots[1]["info"]["checksums"]["SKILL.md"] != boots[0]["info"]["checksums"]["SKILL.md"]
    assert "Search policy: obey-memory" in (actor / "SKILL.md").read_text(encoding="utf-8")
    assert (versions / "gen_001" / "SKILL.md").exists() and "Search policy: static" in (versions / "gen_001" / "SKILL.md").read_text(encoding="utf-8")
    assert curve[1]["meta"]["patch"]["landed"] and curve[0]["meta"]["patch"]["version"] == "gen_001"


def test_under_human_approval_nothing_lands_without_a_y(tmp_path):
    before = fixed_checksums(HERE / "skills" / ACTOR)
    curve, actor, versions = run_generations(FakeModel(), "human", [T1, T3], tmp_path / "run", human=Human(["n", "n"]), into=tmp_path / "w")
    assert fixed_checksums(actor) == before and not versions.exists()
    assert all(not (r["meta"]["patch"] or {}).get("landed") for r in curve)
    assert "Search policy: static" in (actor / "SKILL.md").read_text(encoding="utf-8")


def test_under_human_approval_an_edit_lands_the_humans_version(tmp_path):
    skill = (HERE / "skills" / ACTOR / "SKILL.md").read_text(encoding="utf-8")
    mine = skill.replace("Search policy: static", "Search policy: obey-memory (edited by the human)")
    recipe = {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    edit = ("edit", {"files": {"SKILL.md": {"after": mine}}, "recipe": recipe})
    curve, actor, versions = run_generations(FakeModel(), "human", [T1], tmp_path / "run", human=Human([edit]), into=tmp_path / "w")
    assert curve[0]["meta"]["patch"]["decision"] == "edit" and curve[0]["meta"]["patch"]["landed"]
    assert "(edited by the human)" in (actor / "SKILL.md").read_text(encoding="utf-8")
    assert (versions / "gen_001" / "CHECKSUMS.json").exists()


def worse_on_private(task, incumbent):
    """A recipe with a higher val score than the incumbent but a lower private score: the gate's job is to catch it."""
    from common import recipe as R

    val_a, priv_a = tasks.fit_for(task, 0, incumbent)["val_score"], tasks.score_on(task, 0, incumbent, "private")
    for cand in R.grid():
        fitted = tasks.fit_for(task, 0, cand)
        if fitted["val_score"] is not None and fitted["val_score"] > val_a and tasks.score_on(task, 0, cand, "private") < priv_a:
            return cand
    raise AssertionError("no recipe raises val and lowers the private score on this table")


def test_under_the_gate_a_patch_that_raises_val_and_lowers_private_is_rejected_and_rolled_back(tmp_path):
    actor, meta = steps.workspace(HERE, ACTOR, META["gate"], into=tmp_path / "w")
    incumbent = {"model": "rf", "hyper": 16, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    inner = harness.boot(actor, T1, run_dir=tmp_path / "run")
    execute(inner, checks.call("fit_recipe", recipe=incumbent))                        # the log's only fit: the incumbent
    candidate = worse_on_private(T1, incumbent)
    before = packs.checksums(actor)
    gate = harness.boot(meta, T1, run_dir=tmp_path / "run", target=actor, arm="meta")
    patched = (actor / "SKILL.md").read_text(encoding="utf-8").replace("Search policy: static", "Search policy: obey-memory")
    result = json.loads(execute(gate, checks.call("patch_pack", files={"SKILL.md": {"after": patched}}, recipe=candidate, summary="looks better on val")))
    assert result["decision"] == "n" and not result["landed"] and result["rolled_back_to"] == "gen_001"
    assert result["gate"]["after"] < result["gate"]["before"] and not result["gate"]["keep"]
    assert packs.checksums(actor) == before                                            # versions/ restored the previous pack
    assert TraceLog(tmp_path / "run" / "traces.jsonl").rows("rollback")[-1]["info"]["version"] == "gen_001"
    assert execute(gate, checks.call("patch_pack", files={}, recipe=incumbent, summary="again")).startswith("Error: one proposal per visit")


def test_under_the_gate_a_patch_that_holds_on_private_lands(tmp_path):
    curve, actor, versions = run_generations(FakeModel(), "gate", [T1, T3], tmp_path / "run", into=tmp_path / "w")
    first = curve[0]["meta"]["patch"]
    assert first["landed"] and first["gate"]["keep"] and first["decision"] == "y"
    assert "Search policy: obey-memory" in (actor / "SKILL.md").read_text(encoding="utf-8")
    assert TraceLog(tmp_path / "run" / "traces.jsonl").rows("gate")                     # the gate's verdicts are in the log the human reads


def test_meta_off_leaves_the_pack_byte_identical(tmp_path):
    before = fixed_checksums(HERE / "skills" / ACTOR)
    curve, actor, versions = run_generations(FakeModel(), "human", [T1, T3], tmp_path / "run", meta_off=True, into=tmp_path / "w")
    assert fixed_checksums(actor) == before and not versions.exists()
    assert all(r["meta"]["off"] for r in curve)


def test_the_meta_pack_cannot_call_score_test_or_fit(tmp_path):
    actor, meta = steps.workspace(HERE, ACTOR, META["human"], into=tmp_path / "w")
    run = harness.boot(meta, T1, run_dir=tmp_path / "run", target=actor, arm="meta")
    recipe = {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    assert execute(run, checks.call("score_test", recipe=recipe)).startswith("Error: score_test is not in this pack's tools.md")
    assert execute(run, checks.call("fit_recipe", recipe=recipe)).startswith("Error: fit_recipe is not in this pack's tools.md")
    assert execute(run, checks.call("write_card", card={})).startswith("Error: write_card is not in this pack's tools.md")
    assert packs.lint_pack(meta, T1) == [] and packs.lint_pack(HERE / "skills" / META["gate"], T1) == []
