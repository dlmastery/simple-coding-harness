"""Lesson 17 - the map: the ladder places every lesson 00-16 on a rung (09 on two); the side-by-side table reads
each lesson's curve.json and names the lessons not run yet; every lesson 01-16 has a file-and-approver row; the
six terms are defined and genuine RSI is marked as not reached; every external number is printed as reported
with a source; the map runs nothing and changes nothing.
"""

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import testing  # noqa: E402

LESSONS = [f"{i:02d}" for i in range(17)]


def the_map(root=HERE.parent):
    return testing.tool("map", "--lessons", root)


def test_the_ladder_places_every_lesson_on_a_rung():
    m = the_map()
    placed = [l.split()[0] for rung in m["ladder"] for l in rung["lessons"]]
    assert sorted(set(placed)) == LESSONS and placed.count("09") == 2
    for rung in m["ladder"]:
        assert rung["decision"] and rung["human"]


def test_the_side_by_side_curve_reads_each_lessons_curve_and_names_the_missing(tmp_path):
    root = tmp_path / "rsi"
    root.mkdir()
    curve = [{"problem": "p1", "gap_val": 0.0, "gap_test": 0.0, "wasted_memory": 3, "wasted_control": 5, "cards_active": 2},
             {"problem": "p2", "gap_val": 0.01, "gap_test": 0.02, "wasted_memory": 1, "wasted_control": 4, "cards_active": 3}]
    (root / "step_07_proof" / "runs" / "adult-income").mkdir(parents=True)
    (root / "step_07_proof" / "runs" / "adult-income" / "curve.json").write_text(json.dumps(curve), encoding="utf-8")
    m = the_map(root)
    assert m["curves"]["07 proof"][1]["gap_val"] == 0.01 and "07 proof" not in m["not_run"]
    assert "10 Dream-RSI" in m["not_run"] and "not run yet" in m["table"] and "+0.0100" in m["table"] and "4/9" in m["table"]
    empty = the_map(tmp_path / "nothing")
    assert len(empty["not_run"]) == len(empty["curves"]) and "no lesson has been run yet" in empty["table"]


def test_every_lesson_has_a_file_and_an_approver_row():
    m = the_map()
    rows = {r["lesson"].split()[0]: r for r in m["files"]}
    assert sorted(rows) == LESSONS[1:]
    assert all(r["improved"] and r["approved_by"] for r in rows.values())
    assert rows["01"]["improved"] == "nothing" and "human" in rows["03"]["approved_by"] and "gate" in rows["09"]["approved_by"]


def test_the_six_terms_are_defined():
    m = the_map()
    terms = {t["term"]: t["meaning"] for t in m["terms"]}
    assert set(terms) == {"self-refine", "learning", "self-organise / emergence", "AutoML", "bounded RSI", "genuine RSI"}
    assert "not reached" in terms["genuine RSI"]


def test_every_external_number_is_marked_reported_with_a_source():
    m = the_map()
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    for r in m["reported"]:
        assert r["status"] == "reported" and r["source"]
        assert re.search(r"arXiv:\d{4}\.\d{5}|tech report|tutorial", r["source"])
    assert "reported" in m["table"] and "*reported*" in readme


def test_the_map_changes_nothing(tmp_path):
    work = tmp_path / "lesson"
    shutil.copytree(HERE, work, ignore=shutil.ignore_patterns("__pycache__", "runs"))
    before = {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}
    the_map(work.parent)
    after = {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}
    assert before == after


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "reported" in text
