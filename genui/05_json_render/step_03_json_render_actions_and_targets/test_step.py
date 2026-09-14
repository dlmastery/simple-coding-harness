"""Step 3 offline tests. A fake model streams a scripted first spec, then
scripted patches for an action turn; the server keeps one transcript and one
compiler across both. The Node suite renders one spec with both targets. No
model or network call.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import llm
import server
from json_patch import SpecStream
from prompt import catalog_json, system_prompt
from spec import check_spec

STEP = Path(__file__).resolve().parent
NODE = shutil.which("node")
NPM = shutil.which("npm")

FIRST_TURN = "\n".join([
    '{"op":"add","path":"/root","value":"card-1"}',
    '{"op":"add","path":"/elements/card-1","value":{"type":"Card","props":{"title":"Lemonade"},"children":["metric-1","button-1","button-2","notes"]}}',
    '{"op":"add","path":"/elements/metric-1","value":{"type":"Metric","props":{"label":"Sales","value":{"$state":"/sales/total"}},"children":[]}}',
    '{"op":"add","path":"/state/sales/total","value":"$250"}',
    '{"op":"add","path":"/elements/button-1","value":{"type":"Button","props":{"label":"Refresh"},"on":{"press":{"action":"refresh_numbers"}},"children":[]}}',
    '{"op":"add","path":"/elements/button-2","value":{"type":"Button","props":{"label":"Notes"},"on":{"press":{"action":"setState","params":{"statePath":"/showNotes","value":true}}},"children":[]}}',
    '{"op":"add","path":"/elements/notes","value":{"type":"Card","props":{"title":"Notes"},"visible":{"$state":"/showNotes"},"children":[]}}',
]) + "\n"

REFRESH_TURN = "\n".join([
    '{"op":"replace","path":"/state/sales/total","value":"$310"}',
    '{"op":"add","path":"/elements/text-1","value":{"type":"Text","props":{"text":"Refreshed"},"children":[]}}',
    '{"op":"add","path":"/elements/card-1/children/-","value":"text-1"}',
])  # no trailing newline on purpose


class FakeStream:
    def __init__(self, text):
        self.text = text
        self.usage = None

    def __iter__(self):
        for i in range(0, len(self.text), 37):
            yield self.text[i:i + 37]
        self.usage = {"prompt_tokens": 10, "completion_tokens": len(self.text) // 4}


def scripted(monkeypatch, *replies):
    """llm.stream_text answers with one scripted reply per call, and records the transcripts."""
    seen = []
    queue = list(replies)

    def stream_text(messages):
        seen.append([dict(m) for m in messages])
        return FakeStream(queue.pop(0))

    monkeypatch.setattr(llm, "stream_text", stream_text)
    return seen


def ensure_node_modules():
    if (STEP / "node_modules").exists():
        return
    if NPM is None:
        pytest.skip("node_modules is missing and npm is not installed")
    subprocess.run([NPM, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True, capture_output=True, timeout=600)


def read_stream(client, method, url, **kwargs):
    with client.stream(method, url, **kwargs) as response:
        return response.status_code, "".join(response.iter_text())


def test_catalog_json_carries_actions_and_check_spec_uses_them():
    catalog = catalog_json()
    assert set(catalog["actions"]) == {"refresh_numbers", "show_details"}
    assert "setState" in catalog["builtInActions"]
    assert "Button" in catalog["components"]
    stream = SpecStream()
    stream.push(FIRST_TURN)
    assert check_spec(stream.spec, catalog) == []
    bad = json.loads(json.dumps(stream.spec))
    bad["elements"]["button-1"]["on"]["press"]["action"] = "launch_rocket"
    assert check_spec(bad, catalog) == ["button-1: on.press: unknown action 'launch_rocket'"]


def test_prompt_lists_the_button_and_the_actions():
    text = system_prompt()
    assert "- Button: " in text
    assert "- refresh_numbers: " in text and "- show_details: " in text
    assert "- setState: " in text


def test_action_needs_a_spec_first_and_a_known_action(monkeypatch):
    scripted(monkeypatch, FIRST_TURN)
    server.SESSION["compiler"] = None
    client = TestClient(server.app)
    assert client.post("/action", json={"action": "refresh_numbers"}).status_code == 409
    read_stream(client, "POST", "/stream", json={"prompt": "lemonade"})
    response = client.post("/action", json={"action": "launch_rocket"})
    assert response.status_code == 400
    assert "refresh_numbers" in response.json()["detail"]


def test_an_action_runs_the_next_turn_on_the_same_transcript_and_compiler(monkeypatch):
    seen = scripted(monkeypatch, FIRST_TURN, REFRESH_TURN)
    client = TestClient(server.app)
    status, body = read_stream(client, "POST", "/stream", json={"prompt": "lemonade"})
    assert status == 200 and body == FIRST_TURN
    status, body = read_stream(client, "POST", "/action", json={"action": "refresh_numbers", "params": {}})
    assert status == 200 and body == REFRESH_TURN

    # the transcript: system, user, assistant, the press, and the reply appended after the stream
    roles = [m["role"] for m in server.SESSION["messages"]]
    assert roles == ["system", "user", "assistant", "user", "assistant"]
    assert seen[1][2]["content"] == FIRST_TURN
    assert 'action "refresh_numbers"' in seen[1][3]["content"]
    assert server.SESSION["messages"][4]["content"] == REFRESH_TURN

    # one compiler across both turns: the replace and the add landed on the first spec
    last = client.get("/last").json()
    assert last["spec"]["state"]["sales"]["total"] == "$310"
    assert last["spec"]["elements"]["card-1"]["children"][-1] == "text-1"
    assert [turn["label"] for turn in last["turns"]] == ["generate", "refresh_numbers"]
    assert len(last["turns"][0]["patches"]) == 7
    assert len(last["turns"][1]["patches"]) == 3, "the last line without a newline is applied by finish()"
    assert last["turns"][1]["usage"]["prompt_tokens"] == 10
    assert last["problems"] == []
    assert last["skipped"] == []


def test_show_details_passes_its_params_to_the_model(monkeypatch):
    seen = scripted(monkeypatch, FIRST_TURN, '{"op":"add","path":"/state/notes","value":"Sales rose 8%."}\n')
    client = TestClient(server.app)
    read_stream(client, "POST", "/stream", json={"prompt": "lemonade"})
    read_stream(client, "POST", "/action", json={"action": "show_details", "params": {"metric": "Sales"}})
    assert 'params {"metric": "Sales"}' in seen[1][3]["content"]
    assert client.get("/spec").json()["state"]["notes"] == "Sales rose 8%."


def test_prompt_cache_matches_node():
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    for script, cache in [("prompt.mjs", "prompt.txt"), ("catalog_json.mjs", "catalog.json")]:
        out = subprocess.run([NODE, script], cwd=STEP, capture_output=True, text=True, encoding="utf-8", check=True).stdout
        assert out == (STEP / cache).read_text(encoding="utf-8"), f"{cache} is stale: delete it and rerun"


def test_ink_cli_renders_a_spec_file(tmp_path):
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    stream = SpecStream()
    stream.push(FIRST_TURN)
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(stream.spec), encoding="utf-8")
    result = subprocess.run([NODE, "ink_render.mjs", str(spec_file)], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert result.returncode == 0, result.stderr
    assert "Lemonade" in result.stdout
    assert "$250" in result.stdout
    assert "[ Refresh ]" in result.stdout
    assert result.stdout.count("Notes") == 1, "the button shows; the hidden notes card does not"


def test_node_suite_passes():
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    result = subprocess.run([NODE, "--test", "tests/targets.test.mjs"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
