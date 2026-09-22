import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, compact, config, history, llm, prompt, session, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


def test_cap_spills_and_sweep_cleans():
    big = "x" * (history.CAP + 500)
    capped = history.cap(big)
    assert capped.startswith("x" * history.CAP) and "[output capped: 500 of" in capped
    assert history.SPILLS[0].read_text(encoding="utf-8") == big
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


def test_a_capped_result_is_still_stripped_once_its_turn_is_over():
    # cap() and strip() leave different markers: capped output is on disk for one
    # turn, stripped output is gone. strip must not mistake the first for the second.
    messages = [{"role": "tool", "tool_call_id": "a", "content": history.cap("x" * (history.CAP + 5))}]
    history.sweep()
    assert history.CAPPED in messages[0]["content"] and history.TRIMMED not in messages[0]["content"]
    assert history.strip(messages) == 1 and len(messages[0]["content"]) < 400


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
    assert compact.COMPACTED_AT == len(kept)
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
    assert "/compact" in commands.COMMANDS


def test_compaction_does_not_fire_twice_on_the_same_transcript(monkeypatch):
    full = {"prompt_tokens": config.CONTEXT_WINDOW}
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    monkeypatch.setattr(compact, "COMPACTED_AT", 0)
    assert compact.needed(full, messages) and not compact.needed({"prompt_tokens": 10}, messages)
    monkeypatch.setattr(compact, "COMPACTED_AT", len(messages))  # just compacted, still over the line
    assert not compact.needed(full, messages)
    messages.append({"role": "user", "content": "c"})               # grown since: allowed again
    assert compact.needed(full, messages)
    monkeypatch.setattr(compact, "COMPACTED_AT", 0)
    monkeypatch.setattr(compact, "compact", lambda m: (_ for _ in ()).throw(RuntimeError("summariser down")))
    assert commands.compact(messages) is messages and compact.COMPACTED_AT == len(messages)  # a failure waits for growth too


def test_the_cut_lands_on_a_user_message_even_when_turns_end_with_tool_calls():
    messages = [{"role": "system", "content": "s"}]
    for i in range(3):
        messages += [{"role": "user", "content": f"u{i}"},
                     {"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
                     {"role": "tool", "tool_call_id": f"c{i}", "content": "t"},
                     {"role": "assistant", "content": f"done {i}"}]
    for start in range(1, len(messages)):
        cut = compact.safe_boundary(messages, start)
        assert cut == len(messages) or messages[cut]["role"] == "user"


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content}


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def run_loop(monkeypatch, tmp_path, replies, inputs):
    """Drive main() with scripted replies and typed lines; return every request sent."""
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    seen = []

    def fake(messages, **kw):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)  # agent.py binds call_llm by name at import
    lines = iter(inputs)

    def typed(_prompt):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError  # ctrl-d once the script runs out

    monkeypatch.setattr(prompt, "read", typed)
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()
    return seen


def test_bad_tool_calls_become_results_not_crashes(monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    replies = [
        FakeMessage(content=None, tool_calls=[
            call("c1", "no_such_tool", "{}"),
            call("c2", "bash", '{"command": "ls"'),
            call("c3", "read_file", '{"path": "missing.txt"}'),
            call("c4", "write_todos", '{"todos": [{"content": "a", "activeForm": "b", "status": "done"}]}'),
        ]),
        FakeMessage(content="carried on", tool_calls=None),
    ]
    seen = run_loop(monkeypatch, tmp_path, replies, ["go"])   # then ctrl-d
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3", "c4"}
    assert results["c1"] == "Error: no tool named 'no_such_tool'."
    assert results["c2"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c3"].startswith("Error:") and results["c4"].startswith("Error: item 0")
    assert session.load(session.CURRENT)[-1]["content"] == "carried on"


def test_utf8_round_trip(tmp_path):
    path = str(tmp_path / "tree.md")
    text = "├── café Łódź 🎉\n"
    assert tools.write_file(path, text) == f"Wrote {path}"
    assert tools.read_file(path) == text
    utf8_bytes = "import sys; sys.stdout.buffer.write('Łódź'.encode('utf-8'))"
    assert tools.bash(f'python -X utf8 -c "{utf8_bytes}"') == "Łódź"


def test_rewind_offers_only_user_messages_and_load_repairs(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "fresh")
    monkeypatch.setattr(session, "WRITTEN", 0)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "r"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "two"},
    ]
    offered = {}
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.setdefault("rows", rows) and 1)
    monkeypatch.setattr(ui, "clear", lambda: None)
    kept = commands.rewind(messages)
    assert offered["rows"] == ["one", "two"] and kept[-1]["content"] == "done"
    session.save(kept + [{"role": "assistant", "content": None, "tool_calls": [{"id": "c9", "type": "function", "function": {"name": "bash", "arguments": "{"}}]}])
    loaded = session.load(session.CURRENT)
    assert loaded[-1] == {"role": "tool", "tool_call_id": "c9", "content": session.STOPPED}
    ui.replay(loaded)
