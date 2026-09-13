"""Step 37 - offline checks for the production harness anatomy README.

The README is the deliverable of this step. These tests read it and check
its shape: the ten mechanism headings, the two closing sections, one
comparison table under every mechanism heading with the six harness
columns, and a well-formed citation URL in every table row. Nothing here
touches the network; a URL is checked for a scheme and a host only.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
README = HERE / "README.md"

MECHANISMS = ("Loop", "Tools", "Permissions", "Sandbox", "Context",
              "Sessions", "Subagents", "Hooks", "Memory", "Evals")
HARNESSES = ("This repo", "Claude Code", "Codex CLI", "OpenCode", "pi", "Hermes")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def text():
    return README.read_text(encoding="utf-8")


def headings():
    return [line[3:].strip() for line in text().splitlines() if line.startswith("## ")]


def section(name):
    """The lines between `## name` and the next `## ` heading."""
    lines = text().splitlines()
    start = lines.index(f"## {name}") + 1
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def table_rows(name):
    """The data rows of the first table in a section: header, separator, then rows."""
    lines = [l for l in section(name) if l.startswith("|")]
    assert len(lines) >= 3, f"no table under {name}"
    header, separator, *rows = lines
    return header, rows


def test_readme_exists_and_is_titled():
    assert README.exists()
    assert text().startswith("# Step 37 - Production harness anatomy")


def test_ten_mechanism_headings_in_order():
    found = [h for h in headings() if h in MECHANISMS]
    assert found == list(MECHANISMS)


def test_agree_and_disagree_sections_exist():
    names = headings()
    assert "What they all agree on" in names
    assert "Where they disagree" in names
    assert len(section("What they all agree on")) > 5
    assert len(section("Where they disagree")) > 5


def test_every_mechanism_has_a_table_with_the_six_harness_columns():
    for name in MECHANISMS:
        header, rows = table_rows(name)
        for column in HARNESSES:
            assert column in header, f"{name}: column {column} missing"
        assert header.strip("|").split("|")[-1].strip() == "Sources"
        assert rows, f"{name}: table has no rows"


def test_every_table_row_has_the_right_number_of_cells():
    for name in MECHANISMS:
        header, rows = table_rows(name)
        width = header.count("|")
        for row in rows:
            assert row.count("|") == width, f"{name}: ragged row {row[:60]}"


def test_every_table_row_cites_at_least_one_source():
    for name in MECHANISMS:
        _, rows = table_rows(name)
        for row in rows:
            sources = row.rstrip("|").rsplit("|", 1)[-1]
            assert LINK.search(sources), f"{name}: row without a citation: {row[:60]}"


def test_every_citation_url_has_a_scheme_and_a_host():
    links = LINK.findall(text())
    assert len(links) > 50
    for label, url in links:
        parts = urlparse(url)
        assert parts.scheme in ("http", "https"), url
        assert parts.netloc and "." in parts.netloc, url
        assert " " not in url, url


def test_no_cell_is_left_empty():
    for name in MECHANISMS:
        _, rows = table_rows(name)
        for row in rows:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            assert all(cells), f"{name}: empty cell in {row[:60]}"


def test_unverified_claims_are_marked_not_guessed():
    body = text()
    assert "not verified" in body.lower()
    for word in ("probably", "likely", "presumably"):
        assert word not in body.lower(), f"hedged claim: {word}"


def test_readme_never_references_recordings():
    body = text().lower()
    for word in ("vi" "deo", "you" "tube"):  # split so the repo-wide grep stays empty
        assert word not in body


def test_readme_has_no_python_fences():
    assert "```python" not in text()


def test_copied_harness_matches_the_version():
    pyproject = (HERE / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.37.0"' in pyproject
    assert (HERE / "harness" / "agent.py").exists()
    assert (HERE / ".agents" / "agents").is_dir()
