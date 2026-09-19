"""Step 14 - the archive holds every variant with its held-out score; the parent is chosen from the archive, not
always the latest; a rewrite that lowers the held-out score never becomes a parent; SKILL.md and loop.json are the
only self-modified files."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, harness, packs, steps, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import archive_index, execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402
from run import ACTOR, META, VERIFIER, held_out, run_generations  # noqa: E402

CUR, _ = tasks.test_curriculum()
T1, T2 = CUR[0], CUR[1]


def two_generations(tmp_path):
    run_dir = tmp_path / "run"
    curve, actor, _ = run_generations(FakeModel(), [T1, T2], run_dir, human=Human(["y", "y"]), into=tmp_path / "w")
    meta = harness.boot(tmp_path / "w" / META, T1, run_dir=run_dir, target=actor, arm="meta", quiet=True)
    return curve, actor, run_dir, archive_index(meta), TraceLog(run_dir / "traces.jsonl")


def test_the_archive_holds_every_variant_with_its_held_out_score(tmp_path):
    curve, actor, run_dir, index, trace = two_generations(tmp_path)
    assert [e["label"] for e in index] == [f"{T1['name']}-static", f"{T2['name']}-obey-memory"]
    for e in index:
        assert isinstance(e["held_out"], float) and set(e["gains"]) == {f"{t['name']}/0" for t in held_out()}
        assert (run_dir / "archive" / e["label"] / "SKILL.md").exists() and (run_dir / "archive" / e["label"] / "loop.json").exists()
        snapshot = {k: v for k, v in packs.checksums(run_dir / "archive" / e["label"]).items() if k != "CHECKSUMS.json"}
        assert e["checksums"] == snapshot                                                    # the variant is the pack as it ran
    heldout_rows = trace.rows("fit", arm="heldout-1")
    assert {r["problem"] for r in heldout_rows} == {t["name"] for t in held_out()}          # scored on the fixed benchmark
    assert not ({t["name"] for t in held_out()} & {t["name"] for t in CUR})                  # which no curriculum problem shares


def test_the_parent_is_chosen_from_the_archive_not_always_the_latest(tmp_path):
    actor, meta = steps.workspace(HERE, ACTOR, META, into=tmp_path / "w")
    run = harness.boot(meta, T1, run_dir=tmp_path / "run", target=actor, arm="meta", quiet=True)
    root = tmp_path / "run" / "archive"
    root.mkdir(parents=True)
    packs.snapshot(actor, root, "older-good")
    packs.snapshot(actor, root, "latest-worse")
    index = [{"label": "older-good", "problem": "x", "seed": 0, "held_out": 0.02, "parent": None},
             {"label": "latest-worse", "problem": "y", "seed": 0, "held_out": -0.01, "parent": "older-good"}]
    (root / "archive.json").write_text(json.dumps(index), encoding="utf-8")
    parent = json.loads(execute(run, checks.call("archive", action="parent", payload={})))
    assert parent == {"parent": "older-good", "held_out": 0.02, "latest": "latest-worse"}
    listed = json.loads(execute(run, checks.call("archive", action="list", payload={})))
    assert [v["label"] for v in listed["variants"]] == ["older-good", "latest-worse"]


def test_a_rewrite_that_lowers_the_held_out_score_never_becomes_a_parent(tmp_path):
    curve, actor, run_dir, index, trace = two_generations(tmp_path)
    scores = {e["label"]: e["held_out"] for e in index}
    picks = [r["info"] for r in trace.rows("archive") if r["info"]["action"] == "parent"]
    assert len(picks) == 2
    worst = min(scores, key=scores.get)
    if scores[worst] < max(scores.values()):
        meta = harness.boot(tmp_path / "w" / META, T2, run_dir=run_dir, target=actor, arm="meta", quiet=True)
        parent = json.loads(execute(meta, checks.call("archive", action="parent", payload={})))
        assert parent["parent"] != worst and parent["held_out"] == max(scores.values())
    restore = [r for r in trace.rows("archive") if r["info"]["action"] == "restore"]
    if restore:
        assert restore[-1]["info"]["label"] != worst


def test_skill_md_and_loop_json_are_the_only_self_modified_files(tmp_path):
    curve, actor, run_dir, index, trace = two_generations(tmp_path)
    applied = trace.rows("apply")
    assert applied and all(set(a["info"]["files"]) <= {"SKILL.md", "loop.json"} for a in applied)
    meta = harness.boot(tmp_path / "w" / META, T1, run_dir=run_dir, target=actor, arm="meta", quiet=True)
    recipe = {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    assert execute(meta, checks.call("patch_pack", files={"schema.json": {"after": "{}"}}, recipe=recipe, summary="x")) \
        .startswith("Error: this meta pack may patch ['SKILL.md', 'loop.json'] only, not schema.json")
    assert execute(meta, checks.call("patch_pack", files={"tools.md": {"after": "x"}}, recipe=recipe, summary="x")).startswith("Error: this meta pack may patch")
    variants = [packs.read_pack(run_dir / "archive" / e["label"]) for e in index]
    differing = {n for v in variants for n in v if n != "CHECKSUMS.json" and v[n] != variants[0].get(n)}
    assert differing <= {"SKILL.md", "loop.json", "memory.json"}                         # memory.json is the verifier's, not a rewrite
    loop = json.loads((run_dir / "archive" / index[1]["label"] / "loop.json").read_text(encoding="utf-8"))
    assert loop["policy"] == "obey-memory" and loop["N"] == 24                              # the rewrite kept the budget
    assert packs.lint_pack(run_dir / "archive" / index[1]["label"], T2) == []


def test_the_human_can_refuse_what_the_gate_kept(tmp_path):
    run_dir = tmp_path / "run"
    curve, actor, _ = run_generations(FakeModel(), [T1], run_dir, human=Human(["n"]), into=tmp_path / "w")
    patch = curve[0]["meta"]["patch"]
    assert patch["gate"]["keep"] and patch["decision"] == "n" and not patch["landed"] and patch["rolled_back_to"] == "gen_001"
    assert "Search policy: static" in (actor / "SKILL.md").read_text(encoding="utf-8")
