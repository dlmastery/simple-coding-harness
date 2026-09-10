from types import SimpleNamespace

from harness import agent, compact, config, history, llm, session, tools
from harness.ui import ui


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "CURRENT", "s1")
    monkeypatch.setattr(session, "WRITTEN", 0)


def test_cap_spills_to_a_temp_file_and_sweep_removes_it():
    big = "x" * (history.CAP + 500)
    capped = history.cap(big)
    assert capped.startswith("x" * history.CAP) and "[output trimmed: 500 of" in capped
    assert len(history.SPILLS) == 1 and history.SPILLS[0].read_text() == big
    history.sweep()
    assert history.SPILLS == []
    assert history.cap("short") == "short"


def test_strip_shrinks_old_tool_results_but_not_the_locked_prefix():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "tool", "tool_call_id": "a", "content": "y" * 1000},   # inside the frozen block
        {"role": "user", "content": "<summary>old</summary>"},
        {"role": "tool", "tool_call_id": "b", "content": "z" * 1000},   # live tail
    ]
    assert history.locked(messages) == 3
    assert history.strip(messages) == 1                      # only the unlocked one
    assert messages[1]["content"] == "y" * 1000
    assert messages[3]["content"].startswith("z" * history.STUB) and history.TRIMMED in messages[3]["content"]
    assert history.strip(messages) == 0                      # idempotent


def test_fit_drops_oldest_first(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 400)  # budget = 340 tokens ~ 1360 chars
    messages = [{"role": "system", "content": "s"}] + [
        {"role": "tool", "tool_call_id": str(i), "content": "w" * 600} for i in range(4)
    ]
    dropped = history.fit(messages)
    assert dropped >= 1 and "dropped to fit" in messages[1]["content"]
    assert history.estimate(messages) <= 340


def test_compact_keeps_system_summary_and_a_safe_tail(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 1000)   # COMPACT_TO -> 350-token tail
    rendered = {}

    def fake(messages, tools=None):
        rendered["prompt"] = messages[1]["content"]
        return SimpleNamespace(content="## Goal\nfinish the parser", tool_calls=None), {}

    monkeypatch.setattr(llm, "complete", fake)
    messages = [{"role": "system", "content": "s"}]
    for i in range(6):
        messages += [
            {"role": "user", "content": f"turn {i} " + "u" * 300},
            {"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}", "type": "function",
                                                                    "function": {"name": "bash", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": f"c{i}", "content": "t" * 300},
            {"role": "assistant", "content": f"done {i}"},
        ]
    kept = compact.compact(messages)
    assert kept[0] == messages[0]
    assert kept[1]["content"].startswith("<summary>") and "finish the parser" in kept[1]["content"]
    assert kept[2]["role"] == "user"                          # cut on a fresh exchange, never orphaning a tool result
    assert "[called bash" in rendered["prompt"] and "turn 0" in rendered["prompt"]
    assert history.locked(kept) == 2


def test_compaction_is_recorded_and_reloads(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}]
    session.save(messages)
    small = [messages[0], {"role": "user", "content": "<summary>x</summary>"}]
    session.compacted(small)
    assert session.load("s1") == small
    session.save(small + [{"role": "assistant", "content": "after"}])
    assert [m.get("content") for m in session.load("s1")][-1] == "after"


def test_turn_auto_compacts_when_prompt_is_large(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    monkeypatch.setattr(compact, "needed", lambda usage: True)
    monkeypatch.setattr(compact, "compact", lambda messages: [messages[0], {"role": "user", "content": "<summary>s</summary>"}])
    monkeypatch.setattr(llm, "complete", lambda messages, tools=None: (SimpleNamespace(content="ok", tool_calls=None), {"prompt_tokens": 1}))
    messages = [{"role": "system", "content": "s"}]
    out = agent.turn(messages, "hello")
    assert out is not messages and "<summary>" in out[1]["content"]


def test_tool_results_are_capped():
    _, r = tools.execute(call("c", "read_file", '{"path": "harness/config.py"}'))
    assert "[output trimmed" not in r and "CONTEXT_WINDOW" in r  # small file: untouched
    assert len(history.cap("q" * 20_000)) < 20_000
    history.sweep()
