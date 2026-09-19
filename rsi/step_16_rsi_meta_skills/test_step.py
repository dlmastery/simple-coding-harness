"""Step 16 - task skills change on the fast clock, meta-skills only every k problems; a meta-skill change never lands
without the human's y; the meta pack's version history is a file you can diff."""

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
from run import ACTOR, EVOLVER, META, VERIFIER, run_two_clocks  # noqa: E402

CUR, _ = tasks.test_curriculum()
FOUR = CUR[:4]     # k = 2: two slow visits over four problems


def roles_of(meta):
    return {n: t for n, t in packs.read_pack(meta).items() if n.startswith("roles/")}


def test_task_skills_change_every_problem_and_meta_skills_only_every_k(tmp_path):
    run_dir = tmp_path / "run"
    curve, actor, meta, _ = run_two_clocks(FakeModel(), FOUR, run_dir, human=Human(["y", "y"]), into=tmp_path / "w", k=2)
    fast = [r["meta"]["fast"] for r in curve]
    slow = [r["meta"]["slow"] for r in curve]
    assert len(fast) == 4 and all(f["calls"] > 0 for f in fast)                            # the fast loop visits every problem
    assert [s is not None for s in slow] == [False, True, False, True]                     # the slow loop, every k
    trace = TraceLog(run_dir / "traces.jsonl")
    boots = [b for b in trace.rows("boot", arm="memory") if b["info"]["pack"] == ACTOR]
    task_skill_changes = sum(1 for a, b in zip(boots, boots[1:]) if a["info"]["checksums"] != b["info"]["checksums"])
    assert task_skill_changes >= 2                                                         # cards and the policy line moved between problems
    meta_boots = [b for b in trace.rows("boot", arm="meta") if b["info"]["pack"] == META]
    changes_at = [i + 2 for i, (a, b) in enumerate(zip(meta_boots, meta_boots[1:])) if a["info"]["checksums"] != b["info"]["checksums"]]
    assert changes_at and all(i % 2 == 1 for i in changes_at)                              # the meta pack changed only after a slow visit
    landed = [s["patch"] for s in slow if s and s["patch"] and s["patch"]["landed"]]
    assert landed and all(len(p["files"]) == 1 and p["files"][0].startswith("roles/") for p in landed)


def test_a_meta_skill_change_never_lands_without_the_human_y(tmp_path):
    run_dir = tmp_path / "run"
    before = roles_of(HERE / "skills" / META)
    curve, actor, meta, _ = run_two_clocks(FakeModel(), FOUR, run_dir, human=Human(["n", "n"]), into=tmp_path / "w", k=2)
    assert roles_of(meta) == before                                                        # the roles are what they were
    slow = [r["meta"]["slow"] for r in curve if r["meta"]["slow"]]
    assert slow and all(s["patch"]["decision"] == "n" and not s["patch"]["landed"] for s in slow)
    assert not (run_dir / "meta" / "versions").exists() or not list((run_dir / "meta" / "versions").glob("gen_*"))
    evolver = harness.boot(tmp_path / "w" / EVOLVER, FOUR[0], run_dir=run_dir / "meta", target=meta, arm="meta", quiet=True)
    recipe = {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    assert execute(evolver, checks.call("patch_pack", files={"SKILL.md": {"after": "x"}}, recipe=recipe, summary="x")).startswith("Error: this meta pack may patch ['roles/*.md'] only")
    assert execute(evolver, checks.call("fit_recipe", recipe=recipe)).startswith("Error: fit_recipe is not in this pack's tools.md")


def test_the_meta_packs_version_history_is_a_file_you_can_diff(tmp_path):
    run_dir = tmp_path / "run"
    curve, actor, meta, _ = run_two_clocks(FakeModel(), FOUR, run_dir, human=Human(["y", "y"]), into=tmp_path / "w", k=2)
    versions = sorted(p.name for p in (run_dir / "meta" / "versions").glob("gen_*"))
    assert versions[:1] == ["gen_001"]
    old = packs.read_pack(run_dir / "meta" / "versions" / "gen_001")
    now = packs.read_pack(meta)
    diff = packs.diff({n: old[n] for n in old if n.startswith("roles/")}, {n: now[n] for n in now if n.startswith("roles/")})
    assert diff and ("-Cards per visit: 3" in diff or "-Policy flip threshold: 2" in diff)
    assert (run_dir / "meta" / "versions" / "gen_001" / "CHECKSUMS.json").exists()
    assert packs.lint_pack(meta, FOUR[0]) == [] and packs.lint_pack(tmp_path / "w" / EVOLVER, FOUR[0]) == []
