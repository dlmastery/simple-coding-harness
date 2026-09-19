"""Step 17 - the ladder places every lesson; the side-by-side curve reads each lesson's curve.json and says which
lessons have not run; every lesson has a file-and-approver row; the six terms are defined; every external number
is marked reported with its source."""

import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import run as themap  # noqa: E402

LESSONS = [f"{i:02d}" for i in range(17)]


def test_the_ladder_places_every_lesson_on_a_rung():
    placed = {}
    for rung, lessons, decision, human in themap.LADDER:
        assert decision and human                                                    # every rung says what moved and what stayed
        for lesson in lessons:
            placed.setdefault(lesson[:2], []).append(rung)
    assert sorted(placed) == LESSONS
    assert len(placed["09"]) == 2 and all(len(v) == 1 for k, v in placed.items() if k != "09")   # 09 sits on two rungs, one line apart
    buf = io.StringIO()
    themap.print_ladder(out=lambda s: buf.write(s + "\n"))
    assert "L5 flavour" in buf.getvalue() and "not RSI" in buf.getvalue()


def test_the_side_by_side_curve_reads_each_lessons_curve_and_names_the_missing(tmp_path, monkeypatch):
    row = lambda p, g, wm, wc: {"problem": p, "gap_val": g, "wasted_memory": wm, "wasted_control": wc}   # noqa: E731
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "curve.json").write_text(json.dumps([row("p1", 0.0, 5, 5), row("p2", 0.02, 1, 9)]), encoding="utf-8")
    monkeypatch.setattr(themap, "ROOT", tmp_path)
    monkeypatch.setattr(themap, "CURVES", {"A": "a/curve.json", "B": "b/curve.json"})
    curves = themap.load_curves()
    assert curves["A"] is not None and curves["B"] is None
    buf = io.StringIO()
    themap.print_curves(curves, out=lambda s: buf.write(s + "\n"))
    text = buf.getvalue()
    assert "+0.0200" in text and "6/14" in text and "B" in text and "not run yet" in text


def test_every_lesson_has_a_file_and_an_approver_row():
    numbers = [row[0][:2] for row in themap.FILES]
    assert numbers == LESSONS[1:]
    assert all(what and who for _, what, who in themap.FILES)
    assert any("nobody" in who for _, _, who in themap.FILES[:2]) and any("human" in who for _, _, who in themap.FILES)


def test_the_six_terms_are_defined():
    assert [t for t, _ in themap.TERMS] == ["self-refine", "learning", "self-organise / emergence", "AutoML", "bounded RSI", "genuine RSI"]
    assert "not reached here" in dict(themap.TERMS)["genuine RSI"]


def test_every_external_number_is_marked_reported_with_a_source():
    buf = io.StringIO()
    themap.print_reported(out=lambda s: buf.write(s + "\n"))
    lines = [l for l in buf.getvalue().splitlines() if re.search(r"\d", l)]
    assert lines and all(l.strip().startswith("reported:") and "[" in l for l in lines)
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    for claim, source in themap.REPORTED:
        assert source.split(",")[0].split(" /")[0] in readme                            # every source is cited on the page
    assert readme.count("*reported*") >= 3
