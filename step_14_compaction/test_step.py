import os
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import commands, compact, config, history, llm, session  # noqa: E402


def test_cap_spills_and_sweep_cleans():
    big = "x" * (history.CAP + 500)
    capped = history.cap(big)
    assert capped.startswith("x" * history.CAP) and "[output trimmed: 500 of" in capped
    assert history.SPILLS[0].read_text() == big
    history.sweep()
    assert history.SPILLS == [] and history.cap("short") == "short"


def test_strip_and_fit_only_touch_tool_results(monkeypatch):
    messages = [{"role": "system", "content": "s" * 1000},
                {"role": "tool", "tool_call_id": "a", "content": "y" * 1000},
                {"role": "assistant", "content": "z" * 1000}]
    assert history.strip(messages) == 1 and history.strip(messages) == 0
    assert messages[0]["content"] == "s" * 1000 and history.TRIMMED in messages[1]["content"]
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 100)
    messages.append({"role": "tool", "tool_call_id": "b", "content": "w" * 2000})
    assert history.fit(messages) >= 1 and "dropped to fit" in messages[-1]["content"]


def test_compaction_folds_the_summary_into_the_system_prompt(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 1000)
    prompts = []

    def fake(messages, tools=None):
        prompts.append((messages[1]["content"], tools))
        return SimpleNamespace(content="## Goal\nfinish the parser"), {}

    monkeypatch.setattr(llm, "call_llm", fake)
    messages = [{"role": "system", "content": "SYSTEM PROMPT"}]
    for i in range(6):
        messages += [
            {"role": "user", "content": f"turn {i} " + "u" * 300},
            {"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": f"c{i}", "content": "t" * 300},
            {"role": "assistant", "content": f"done {i}"},
        ]
    kept = compact.compact(messages)
    system = kept[0]["content"]
    assert system.startswith("SYSTEM PROMPT") and "<summary>" in system and "finish the parser" in system
    assert kept[1]["role"] == "user"                             # the cut never orphans a tool result
    assert prompts[0][1] == [] and "[called bash" in prompts[0][0]  # the summariser ran with no tools

    # A second compaction carries the earlier note forward and keeps one summary block.
    kept += [{"role": "user", "content": "more " + "m" * 600}, {"role": "assistant", "content": "ok " + "o" * 600},
             {"role": "user", "content": "again " + "m" * 600}, {"role": "assistant", "content": "ok " + "o" * 600}]
    again = compact.compact(kept)
    assert again[0]["content"].count("<summary>") == 1 and "PREVIOUS HANDOFF NOTE" in prompts[1][0]
    assert compact.base_prompt(again[0]["content"]) == "SYSTEM PROMPT"


def test_compaction_is_recorded_in_the_session(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path); monkeypatch.setattr(session, "CURRENT", "s1"); monkeypatch.setattr(session, "WRITTEN", 0)
    session.save([{"role": "system", "content": "s"}, {"role": "user", "content": "a"}])
    small = [{"role": "system", "content": "s\n\n<summary>x</summary>"}]
    session.compacted(small)
    assert session.load("s1") == small
    assert compact.needed({"prompt_tokens": config.CONTEXT_WINDOW}) and not compact.needed({"prompt_tokens": 10})
    assert "/compact" in commands.COMMANDS
