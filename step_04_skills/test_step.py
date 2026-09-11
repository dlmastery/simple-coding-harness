from pathlib import Path

import skills
import tools


def test_frontmatter_becomes_the_index(tmp_path):
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "SKILL.md").write_text("---\nname: deploy\ndescription: |\n  Ship it\n  safely\n---\nStep one.\n")
    found = skills.find_skills.__wrapped__(None) if hasattr(skills.find_skills, "__wrapped__") else None
    skills.SKILL_DIRS[:] = [tmp_path]
    found = skills.find_skills()
    assert found == {"deploy": {"description": "Ship it safely", "path": tmp_path / "deploy" / "SKILL.md"}}
    skills.SKILL_DIRS[:] = [Path.home() / ".agents" / "skills", Path.cwd() / ".agents" / "skills"]


def test_project_skill_is_indexed_and_readable_on_demand():
    assert "- explain-code:" in skills.skills_prompt()          # index in the prompt
    body = skills.read_skill("explain-code")                     # body only via the tool
    assert body.startswith("---") and "# Explaining code" in body
    assert skills.read_skill("nope") == "No skill named 'nope'."
    assert tools.TOOLS["read_skill"] is skills.read_skill
    assert "read_skill" in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
