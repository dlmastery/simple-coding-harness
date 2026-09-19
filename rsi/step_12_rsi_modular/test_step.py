"""Step 12 - contrast names the module whose text differs; the patch touches exactly one module; validation runs
on the pool, never the eval table; the patched module helps both fake actors."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, harness, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402
from run import A, B, META, pool_tasks, run_pool, transfer  # noqa: E402

CUR, _ = tasks.test_curriculum()
EVAL = CUR[5]                                     # t6: trees, imbalanced - the eval table the pool must never touch
POOL = [t["name"] for t in pool_tasks()]


def pooled(tmp_path):
    work = steps.workspace(HERE, A, B, META, into=tmp_path / "w")
    before = transfer(work[0], EVAL, tmp_path / "before")
    visit = run_pool(FakeModel(), work, tmp_path / "pool")
    return work, before, visit, TraceLog(tmp_path / "pool" / "traces.jsonl")


def test_contrast_names_the_module_whose_text_differs(tmp_path):
    work, before, visit, trace = pooled(tmp_path)
    c = trace.rows("contrast")[-1]["info"]
    assert c["modules_differing"] == ["modules/context.md"] and c["module"] == "modules/context.md"
    assert c["winner"] == B and c["wins"] == {A: 0, B: 2} and [p["problem"] for p in c["pairs"]] == POOL
    assert all(p["success"] == B and p["failure"] == A for p in c["pairs"])
    assert "Search policy: obey-memory" in c["texts"][B] and "Search policy: static" in c["texts"][A]


def test_the_patch_touches_exactly_one_module_file(tmp_path):
    work, before, visit, trace = pooled(tmp_path)
    assert visit["patch"]["landed"] and visit["patch"]["version"] == "gen_001"
    a_now, a_then = packs.read_pack(work[0]), packs.read_pack(tmp_path / "pool" / "versions" / "gen_001")
    changed = [n for n in a_now if a_now[n] != a_then.get(n)]
    assert changed == ["modules/context.md"] and a_now["modules/context.md"] == packs.read_pack(work[1])["modules/context.md"]
    meta = harness.boot(work[2], pool_tasks()[-1], run_dir=tmp_path / "pool", target=work[0], arm="meta")
    recipe = {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}
    assert execute(meta, checks.call("patch_pack", files={"SKILL.md": {"after": "x"}}, recipe=recipe, summary="not a module")) \
        .startswith("Error: this meta pack may patch ['modules/*.md'] only, not SKILL.md")


def test_validation_runs_on_the_pool_never_the_eval_table(tmp_path):
    work, before, visit, trace = pooled(tmp_path)
    gate = trace.rows("gate")[-1]
    assert gate["problem"] in POOL and visit["patch"]["gate"]["keep"]
    assert {r["problem"] for r in trace.rows("fit")} == set(POOL)                  # the pool log holds pool tables only
    assert EVAL["name"] not in {r["problem"] for r in trace.rows()}
    assert all(t["name"] not in {c["name"] for c in CUR} for t in pool_tasks())     # disjoint from the curriculum by construction


def test_the_patched_module_helps_both_fake_actors(tmp_path):
    work, before, visit, trace = pooled(tmp_path)
    after = transfer(work[0], EVAL, tmp_path / "after")
    assert set(before) == set(after) == {"default", "reverse"}
    assert all(after[s] >= before[s] for s in before) and any(after[s] > before[s] for s in before)
    reverse_before = harness.boot(steps.workspace(HERE, A, into=tmp_path / "w2"), EVAL, arm="rev", run_dir=tmp_path / "rev", quiet=True)
    harness.run(reverse_before, FakeModel("reverse"))
    assert reverse_before.fits[0]["recipe"] != json.loads((HERE / "skills" / A / "schema.json").read_text(encoding="utf-8"))["recipes"][0]  # the two actors do differ
