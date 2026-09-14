"""Step 04 tests. Offline: the model is a fake that yields scripted chunks.

The Python side (the SSE route with its usage event, artifact extraction,
the prompt rules, the CSP policy text) is tested here. The Node side (the
catalog with Markdown and HtmlArtifact, the streaming parser on a partial
document, <Renderer> in both states, sandbox.mjs, markdown.mjs) runs through
`npm test`; when node_modules is missing and npm is available the pinned
packages are installed first.
"""

import json
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import artifact  # noqa: E402
import llm  # noqa: E402
import nodetools  # noqa: E402
import server  # noqa: E402

DOC = "<!doctype html><html><head><style>body{font:14px system-ui}</style></head><body><button id='b'>0</button><script>document.querySelector('#b').onclick=e=>{e.target.textContent='1'}</script></body></html>"
SCRIPTED = [
    "root = Stack([intro, art])\n",
    'intro = Markdown("A **counter** with a \\"quote\\":")\n',
    'art = HtmlArtifact("Counter", ' + json.dumps(DOC)[:60],
    json.dumps(DOC)[60:] + ")\n",
]
PROGRAM = "".join(SCRIPTED)


def fake_stream(messages, usage=None):
    """What the model would say, in four chunks; the messages are checked."""
    assert messages[0]["role"] == "system" and "HtmlArtifact" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "calculator"}
    yield from SCRIPTED
    if usage is not None:
        usage.update(prompt_tokens=1500, completion_tokens=120)


def test_messages_have_the_generated_prompt_as_system_message():
    messages = server.messages_for("hi", "SYSTEM")
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[0]["content"] == "SYSTEM"


def test_generate_route_streams_deltas_then_usage(monkeypatch):
    monkeypatch.setattr(llm, "stream_completion", fake_stream)
    srv = server.make_server(system_prompt="HtmlArtifact(title: string, document: string)")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{srv.server_port}/generate",
            data=json.dumps({"prompt": "calculator"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            assert response.headers["Content-Type"] == "text/event-stream"
            body = response.read().decode()
    finally:
        srv.shutdown()
        srv.server_close()
    events = body.split("\n\n")
    deltas = [json.loads(e[6:]) for e in events if e.startswith("data: ")]
    assert deltas == SCRIPTED
    done = [e for e in events if e.startswith("event: done")]
    assert done == ['event: done\ndata: {"usage": {"prompt_tokens": 1500, "completion_tokens": 120}}']
    assert server.LAST["program"] == PROGRAM
    assert server.LAST["usage"] == {"prompt_tokens": 1500, "completion_tokens": 120}


def test_find_artifacts_reads_the_two_string_arguments():
    found = artifact.find_artifacts(PROGRAM)
    assert [a.title for a in found] == ["Counter"]
    assert found[0].document == DOC
    assert artifact.find_artifacts('root = Stack([m])\nm = Metric("Cups", 1)\n') == []


def test_string_escapes_follow_the_language():
    value, end = artifact.read_string(r'"a \"b\" \\ c\nd" rest', 0)
    assert value == 'a "b" \\ c\nd'
    assert end == 17  # the index after the closing quote
    with pytest.raises(ValueError):
        artifact.read_string('"open', 0)


def test_artifact_token_share_uses_the_document_only():
    program_tokens = artifact.count_tokens(PROGRAM)
    document_tokens = artifact.count_tokens(DOC)
    assert 0 < document_tokens < program_tokens
    assert document_tokens > program_tokens * 0.6  # the document is most of the program


def test_csp_policy_blocks_the_network_and_keeps_inline_code():
    source = (HERE / "sandbox.mjs").read_text(encoding="utf-8")
    assert 'export const CSP = "default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; img-src data:";' in source
    assert 'sandbox: "allow-scripts"' in (HERE / "html-artifact.mjs").read_text(encoding="utf-8")
    assert 'referrerPolicy: "no-referrer"' in (HERE / "html-artifact.mjs").read_text(encoding="utf-8")


def test_api_key_falls_back_to_openai_key():
    """The env file holds OPENAI_API_KEY; llm.py maps it to API_KEY once."""
    source = (HERE / "llm.py").read_text(encoding="utf-8")
    assert 'os.environ["API_KEY"] = os.environ["OPENAI_API_KEY"]' in source
    assert "print(" not in source


# ── the Node side ───────────────────────────────────────────────────────────

def need_node_modules():
    if nodetools.NODE is None or nodetools.NPM is None:
        pytest.skip("node and npm are not installed")
    if not nodetools.ensure_node_modules():
        pytest.skip("npm install did not run")


def test_prompt_carries_the_html_artifact_rules_and_examples():
    need_node_modules()
    text = nodetools.ensure_prompt()
    assert "HtmlArtifact(title: string, document: string)" in text
    assert "Markdown(text: string)" in text
    assert "Only use HtmlArtifact when the user explicitly asks you to build something interactive" in text
    assert "inline CSS and JavaScript only" in text
    assert "Never put a dashboard into an HtmlArtifact" in text
    assert 'artifact = HtmlArtifact("Interactive counter", "<!doctype html>' in text


def test_node_suite_passes():
    need_node_modules()
    result = nodetools.run(nodetools.NPM, "test")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# fail 0" in result.stdout


def test_bundle_builds_with_esbuild():
    need_node_modules()
    bundle = nodetools.ensure_bundle()
    text = bundle.read_text(encoding="utf-8")
    assert "process.env" not in text  # defined away; the browser has no process
    assert 'name: "HtmlArtifact"' in text
    assert "Content-Security-Policy" in text
