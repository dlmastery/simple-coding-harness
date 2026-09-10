from types import SimpleNamespace

from harness import agent, llm, skills, tools

USAGE = {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None}


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_discovers_skill_from_frontmatter(tmp_path):
    skill = tmp_path / "skills" / "deploy" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: deploy\ndescription: |\n  Ship it\n  safely\n---\nStep one.\n")
    found = skills.find_skills([tmp_path / "skills"])
    assert found == {"deploy": {"description": "Ship it safely", "path": skill}}


def test_example_skill_is_in_prompt_and_readable():
    from harness.prompts import SYSTEM_PROMPT

    assert "- explain-code:" in SYSTEM_PROMPT
    assert "# Explaining code" in skills.read_skill("explain-code")
    assert "No skill named" in skills.read_skill("nope")


def test_read_skill_is_a_tool(monkeypatch):
    assert "read_skill" in tools.TOOLS
    replies = [
        (SimpleNamespace(content=None, tool_calls=[call("c1", "read_skill", '{"name": "explain-code"}')]), USAGE),
        (SimpleNamespace(content="ok", tool_calls=None), USAGE),
    ]
    monkeypatch.setattr(llm, "complete", lambda messages, tools=None: replies.pop(0))
    messages = [{"role": "system", "content": "s"}]
    agent.turn(messages, "explain agent.py")
    assert "Explaining code" in messages[3]["content"]
