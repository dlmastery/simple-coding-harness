from pathlib import Path

import pytest

import skills
import tools


@pytest.fixture
def skill_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, "SKILL_DIRS", [tmp_path])
    return tmp_path


def write_skill(root, folder, text):
    (root / folder).mkdir()
    (root / folder / "SKILL.md").write_text(text, encoding="utf-8")


def test_frontmatter_becomes_the_index(skill_dir):
    write_skill(skill_dir, "deploy", "---\nname: deploy\ndescription: |\n  Ship it\n  safely\n---\nStep one.\n")
    found = skills.find_skills()
    assert found == {"deploy": {"description": "Ship it safely", "path": skill_dir / "deploy" / "SKILL.md"}}


def test_broken_skill_files_are_skipped_not_fatal(skill_dir, capsys, monkeypatch):
    write_skill(skill_dir, "unclosed", "---\nname: unclosed\ndescription: no closing fence\n# body\n")
    write_skill(skill_dir, "badyaml", "---\nname: bad\ndescription: [unbalanced\n---\nbody\n")
    write_skill(skill_dir, "dashes", "---\nname: dashes\ndescription: with --- inside\n---\nbody\n")
    write_skill(skill_dir, "noname", "---\ndescription: named after its folder\n---\nbody\n")
    write_skill(skill_dir, "crlf", "---\r\nname: 42\r\ndescription: numeric name, CRLF\r\n---\r\nbody\r\n")
    found = skills.find_skills()
    assert set(found) == {"dashes", "noname", "42"}                     # the two broken ones are skipped
    assert found["dashes"]["description"] == "with --- inside"         # a --- in the text is not a fence
    assert "skipping" in capsys.readouterr().err                       # with a note naming the file
    monkeypatch.setattr(skills, "SKILLS", found)
    assert skills.read_skill("42").startswith("---")                  # names are strings, whatever YAML made of them
    assert skills.read_skill("nope") == "No skill named 'nope'."


def test_project_skill_is_indexed_and_readable_on_demand():
    assert "- explain-code:" in skills.skills_prompt()          # index in the prompt
    body = skills.read_skill("explain-code")                     # body only via the tool
    assert body.startswith("---") and "# Explaining code" in body
    assert tools.TOOLS["read_skill"] is skills.read_skill
    assert "read_skill" in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert skills.SKILL_DIRS[-1] == Path.cwd() / ".agents" / "skills"  # the project's own folder
