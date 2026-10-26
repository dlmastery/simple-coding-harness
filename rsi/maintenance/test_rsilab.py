"""Offline tests for rsilab: no API key, no task data, no network."""

import json
import sys
from pathlib import Path

import pytest

RSI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RSI))

from rsilab import agent, edits, evaluate, improve, llm, pareto  # noqa: E402

H0 = RSI / "harnesses" / "h0"


# ---------------------------------------------------------------- edits keep the harness intact

def test_edits_refuse_frozen_model_and_outside_files():
    assert "frozen" in edits.check({"file": "config.json", "action": "set", "key": "model", "value": "x"}, H0)
    assert "outside" in edits.check({"file": "../grader.py", "action": "write", "content": "x"}, H0)
    assert "outside" in edits.check({"file": "skills/../../x.md", "action": "write", "content": "x"}, H0)
    assert "placeholder" in edits.check({"file": "draft.md", "action": "write", "content": "no slots"}, H0)
    assert "outside" in edits.check({"file": "config.json", "action": "set", "key": "steps", "value": 99}, H0)
    assert edits.check({"file": "skills/cv.md", "action": "write", "content": "use k-fold"}, H0) is None


def test_apply_copies_and_reports_refusals(tmp_path):
    bundle = [{"file": "skills/cv.md", "action": "write", "content": "Use 5-fold CV."},
              {"file": "config.json", "action": "set", "key": "steps", "value": 6},
              {"file": "config.json", "action": "set", "key": "model", "value": "gpt-5.5"}]
    applied, refused = edits.apply(H0, bundle, tmp_path / "h1")
    assert len(applied) == 2 and len(refused) == 1
    h1 = agent.load_harness(tmp_path / "h1")
    assert h1["config"]["steps"] == 6 and h1["config"]["model"] == "gpt-5.4-nano"
    assert "cv.md" in h1["skills"] and "Skill: cv" in agent.system_prompt(h1)
    assert "skills/cv.md" in edits.diff(H0, tmp_path / "h1")
    assert not (H0 / "skills" / "cv.md").exists()


def test_render_ignores_unknown_braces():
    assert agent.render("{a} and {not_a_key} {}", {"a": 1}) == "1 and {not_a_key} {}"


# ---------------------------------------------------------------- the agent loop

def fake_solve(monkeypatch, outcomes, lower=True):
    """Drive agent.solve with canned execution results: (ok, val) per step."""
    calls = []
    monkeypatch.setattr(agent, "context", lambda cids: {c: {"lower": lower, "description": "D", "obfuscated": "O",
                                                            "preview": {"3": "P"}, "terms": []} for c in cids})
    monkeypatch.setattr(llm, "chat", lambda messages, *a, **k: (calls.append(messages[1]["content"]) or
                                                               "plan\n```python\nprint(1)\n```", 10, 5))
    results = iter(outcomes)

    def execute(cid, code, run_dir, timeout):
        ok, val = next(results)
        return {"output": "out", "ok": ok, "val": val, "seconds": 1.0,
                "grade": {"norm": val or 0, "beats_forest": False, "score": val, "valid": ok}}
    monkeypatch.setattr(agent, "execute", execute)
    return calls


def test_loop_drafts_debugs_then_improves(monkeypatch, tmp_path):
    calls = fake_solve(monkeypatch, [(False, None), (True, 0.5), (True, 0.4), (True, 0.45)])
    att = agent.solve(agent.load_harness(H0), "comp", 0, tmp_path)
    assert [n.stage for n in att.nodes] == ["draft", "debug", "improve", "improve"]
    assert att.best == 2  # lower is better: 0.4 wins
    assert att.tokens == 60 and att.calls == 4
    assert "This script failed" in calls[1] and "Current best solution" in calls[2]


def test_best_respects_metric_direction(monkeypatch, tmp_path):
    fake_solve(monkeypatch, [(True, 0.5), (True, 0.4), (True, 0.6), (True, 0.55)], lower=False)
    att = agent.solve(agent.load_harness(H0), "comp", 0, tmp_path)
    assert att.best == 2


def test_extract_code_takes_longest_block():
    text = "```python\nx=1\n```\nthen\n```python\nimport pandas\nx = 2\n```"
    assert extract_code_lines(text) == 2


def extract_code_lines(text):
    return len(agent.extract_code(text).strip().splitlines())


# ---------------------------------------------------------------- measurement

def result(cells, tokens=1000.0, secs=10.0):
    return evaluate.Result(cells, tokens, secs, 0.5, 1.0)


def test_paired_diff_and_verdict():
    old = result({"a/r0": 0.2, "a/r1": 0.3, "b/r0": 0.5, "b/r1": 0.4})
    new = result({"a/r0": 0.6, "a/r1": 0.7, "b/r0": 0.9, "b/r1": 0.8})
    d = evaluate.paired_diff(new, old)
    assert d["mean"] == pytest.approx(0.4) and d["wins"] == 4 and d["lo"] > 0
    assert evaluate.verdict(d).startswith("better")
    same = evaluate.paired_diff(old, old)
    assert same["ties"] == 4 and evaluate.verdict(same).startswith("not established")


# ---------------------------------------------------------------- RRSI pieces

def test_cosine_budget_shrinks():
    p = improve.Policy(budget_max=5, budget_min=1)
    assert [improve.budget(t, 4, p) for t in range(5)] == [5, 5, 3, 2, 1]


def test_critic_flags_competition_specific_words():
    bundle = [{"file": "skills/x.md", "action": "write", "content": "For the EAP and HPL authors use char n-grams."}]
    assert improve.critic(bundle, {}, ["EAP", "spooky"]) == ["skills/x.md mentions 'EAP'"]
    generic = [{"file": "skills/x.md", "action": "write", "content": "For short texts, add character n-grams."}]
    assert improve.critic(generic, {}, ["EAP", "spooky"]) == []


def test_rrsi_acceptance_rules():
    p = improve.Policy(accept="rrsi")
    best = result({"a": 0.5, "b": 0.5}, tokens=1000, secs=10)
    assert not improve.decide(result({"a": 0.3, "b": 0.3}), best, p, delta=0.05)[0]          # below floor
    assert improve.decide(result({"a": 0.7, "b": 0.7}, 1100, 10), best, p, 0.05)[0]           # real gain, small cost
    assert not improve.decide(result({"a": 0.52, "b": 0.52}, 1000, 10), best, p, 0.05)[0]     # noise, same cost
    assert improve.decide(result({"a": 0.51, "b": 0.51}, 500, 5), best, p, 0.05)[0]           # noise, much cheaper
    assert not improve.decide(result({"a": 0.56, "b": 0.56}, 9000, 90), best, p, 0.05)[0]     # gain bought by cost


# ---------------------------------------------------------------- Pareto profiles

def test_pareto_front_and_profiles():
    pts = [("cheap", 0.30, 100), ("mid", 0.50, 600), ("best", 0.60, 900), ("bad", 0.40, 800)]
    assert [p[0] for p in pareto.front(pts)] == ["cheap", "mid", "best"]
    prof = pareto.profiles(pts)
    assert prof["lite"][0] == "cheap" and prof["heavy"][0] == "best" and prof["medium"][0] == "mid"


# ---------------------------------------------------------------- replay cache

def test_replay_mode_never_calls_the_network(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(llm, "_cache", None)
    monkeypatch.setenv("RSI_LLM", "replay")
    with pytest.raises(llm.ReplayMiss):
        llm.chat([{"role": "user", "content": "hi"}], "m")
    key = llm._key("m", [{"role": "user", "content": "hi"}], 0.7, 0, "none")
    (tmp_path / "ab.jsonl").write_text(json.dumps({"key": key, "text": "cached", "prompt_tokens": 1,
                                                    "completion_tokens": 2}) + "\n", encoding="utf-8")
    monkeypatch.setattr(llm, "_cache", None)
    assert llm.chat([{"role": "user", "content": "hi"}], "m")[0] == "cached"
