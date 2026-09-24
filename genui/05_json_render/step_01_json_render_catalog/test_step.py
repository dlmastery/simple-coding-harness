"""Step 1 offline tests. The model is a fake that returns a scripted spec; the
server is driven with FastAPI's TestClient; the Node suite runs the real
@json-render/react renderer with react-dom/server. No model or network call.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import llm
import server
from prompt import catalog_json, system_prompt
from spec import check_spec, walk

STEP = Path(__file__).resolve().parent
NODE = shutil.which("node")
NPM = shutil.which("npm")

SPEC = {
    "root": "card-1",
    "elements": {
        "card-1": {"type": "Card", "props": {"title": "Lemonade"}, "children": ["row-1", "table-1"]},
        "row-1": {"type": "Row", "props": {"gap": "large"}, "children": ["metric-1", "metric-2"]},
        "metric-1": {"type": "Metric", "props": {"label": "Sales", "value": "$250", "delta": "+8%"}, "children": []},
        "metric-2": {"type": "Metric", "props": {"label": "Best day", "value": {"$state": "/sales/bestDay"}}, "children": []},
        "table-1": {"type": "Table", "props": {"columns": ["Day", "Cups"], "rows": [["Mon", "12"]]}, "children": []},
    },
    "state": {"sales": {"bestDay": "Tuesday"}},
}


def fake_complete_spec(spec):
    def complete(system_prompt, user_prompt):
        assert "AVAILABLE COMPONENTS (6)" in system_prompt
        return spec, {"prompt_tokens": 10, "completion_tokens": 5}, 0.01
    return complete


def ensure_node_modules():
    if (STEP / "node_modules").exists():
        return
    if NPM is None:
        pytest.skip("node_modules is missing and npm is not installed")
    subprocess.run([NPM, "install", "--no-audit", "--no-fund"], cwd=STEP, check=True, capture_output=True, timeout=600)


def test_prompt_cache_lists_the_catalog():
    text = system_prompt()
    for name in ["Card", "Row", "Text", "Metric", "Table", "Chart"]:
        assert f"- {name}: " in text
    assert set(catalog_json()["components"]) == {"Card", "Row", "Text", "Metric", "Table", "Chart"}


def test_prompt_cache_matches_node():
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    for script, cache in [("prompt.mjs", "prompt.txt"), ("catalog_json.mjs", "catalog.json")]:
        out = subprocess.run([NODE, script], cwd=STEP, capture_output=True, text=True, encoding="utf-8", check=True).stdout
        assert out == (STEP / cache).read_text(encoding="utf-8"), f"{cache} is stale: delete it and rerun"


def test_check_spec_accepts_a_good_spec():
    assert check_spec(SPEC, catalog_json()) == []


def test_check_spec_reports_each_problem():
    bad = json.loads(json.dumps(SPEC))
    bad["elements"]["card-1"]["children"].append("ghost")
    bad["elements"]["metric-1"]["props"]["value"] = 250
    bad["elements"]["table-1"]["type"] = "Grid"
    problems = check_spec(bad, catalog_json())
    assert any("ghost" in p for p in problems)
    assert any("Metric.value" in p and "string" in p for p in problems)
    assert any("unknown type 'Grid'" in p for p in problems)
    assert check_spec({"root": "x"}, catalog_json()) == ["spec needs a root id and an elements map"]


def test_check_spec_reports_wrong_shapes_and_cycles_instead_of_raising():
    catalog = catalog_json()
    assert check_spec({"root": "a", "elements": {"a": "oops"}}, catalog) == ["a: an element must be an object"]
    assert check_spec({"root": "a", "elements": {"a": {"type": "Card", "props": ["x"], "children": []}}}, catalog) == ["a: props must be an object"]
    problems = check_spec({"root": "a", "elements": {"a": {"type": "Card", "props": {"title": "t"}, "children": [{"id": "b"}]}}}, catalog)
    assert problems == ["a: children must be a list of element ids"]
    loop = {"root": "a", "elements": {"a": {"type": "Card", "props": {"title": "t"}, "children": ["a"]}}}
    assert check_spec(loop, catalog) == ["a: element contains itself"]
    assert [eid for _, eid, _ in walk(loop)] == ["a"]  # walk() visits a cycle once, it does not recurse forever


def test_server_turns_a_model_failure_into_a_502(monkeypatch):
    def broken(system_prompt, user_prompt):
        raise ValueError("the model reply is not JSON: Expecting value")

    monkeypatch.setattr(llm, "complete_spec", broken)
    response = TestClient(server.app).post("/generate", json={"prompt": "x"})
    assert response.status_code == 502
    assert response.json()["detail"]["problems"] == ["model call failed: ValueError: the model reply is not JSON: Expecting value"]


def test_walk_visits_the_tree_in_render_order():
    order = [(depth, element_id) for depth, element_id, _ in walk(SPEC)]
    assert order == [(0, "card-1"), (1, "row-1"), (2, "metric-1"), (2, "metric-2"), (1, "table-1")]


def test_server_returns_the_spec_and_remembers_it(monkeypatch):
    monkeypatch.setattr(llm, "complete_spec", fake_complete_spec(SPEC))
    server.LAST["spec"] = None
    client = TestClient(server.app)
    assert client.get("/spec").status_code == 404
    response = client.post("/generate", json={"prompt": "a lemonade dashboard"})
    assert response.status_code == 200
    body = response.json()
    assert body["spec"] == SPEC
    assert body["usage"]["completion_tokens"] == 5
    assert client.get("/spec").json() == SPEC
    assert "importmap" in client.get("/").text
    assert client.get("/app.mjs").status_code == 200


def test_server_rejects_a_spec_that_fails_the_catalog(monkeypatch):
    bad = {"root": "x", "elements": {"x": {"type": "Hero", "props": {}, "children": []}}}
    monkeypatch.setattr(llm, "complete_spec", fake_complete_spec(bad))
    response = TestClient(server.app).post("/generate", json={"prompt": "anything"})
    assert response.status_code == 502
    assert "unknown type 'Hero'" in response.json()["detail"]["problems"][0]


def test_node_suite_passes():
    if NODE is None:
        pytest.skip("node is not installed")
    ensure_node_modules()
    result = subprocess.run([NODE, "--test", "--test-reporter=tap", "tests/render.test.mjs"], cwd=STEP, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout
