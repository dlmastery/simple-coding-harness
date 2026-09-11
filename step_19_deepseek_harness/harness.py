"""Step 19 - the same harness on DeepSeek Harness (dsh).

dsh is an "everything is a plugin" agent harness: the model adapter, the
tool registry, the session log, the agent loop and the permission gate are
all Cordis plugins composed by a profile. The Python SDK launches the bundled
`dsh --profile sdk` runtime over JSON-RPC on stdio and hands it prompts.

Two halves here:
  harness.py          the Python client: sessions, notifications, the REPL
  plugin/             our policy as a dsh plugin: a `tools/pre-execute` gate
                      running the step 11 rules, mounted through a patch file

Run:   python harness.py [--resume SESSION_ID] [--minimal]
Needs: DEEPSEEK_API_KEY (and optionally DEEPSEEK_BASE_URL).
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from deepseek_harness import DeepSeekHarness, Notification

HOME = Path.home() / ".simple-harness" / "dsh-home"
PLUGIN = Path(__file__).resolve().parent / "plugin" / "simple-harness-plugin" / "src" / "index.js"


# --- the patch: how a plugin enters the tree --------------------------------------
# A profile is an ordered list of Cordis rows. A patch inserts or replaces rows.
# The plugin path must be absolute, so the patch is written at launch time.


def make_patch(plugin_path: Path, minimal: bool) -> str:
    rows = [
        "- insert:",
        "    - id: simple-harness-policy",
        f"      name: '{plugin_path.as_posix()}'",
    ]
    if minimal:  # sdk-minimal ships only a shell; add the editor and its fs provider
        rows += [
            "    - id: fs-local",
            "      name: '@deepseek-ai/dsh-fs-local'",
            "      config:",
            "        cwd: !!js process.cwd()",
            "    - id: tool-str-replace-editor",
            "      name: '@deepseek-ai/dsh-tool-str-replace-editor'",
        ]
    return "\n".join(rows) + "\n"


def write_patch(minimal: bool) -> Path:
    HOME.mkdir(parents=True, exist_ok=True)
    path = HOME / "simple-harness.patch.yml"
    path.write_text(make_patch(PLUGIN, minimal), encoding="utf-8")
    return path


def build(minimal=False, model=None, patch=None):
    """The client object. Nothing launches until the first run()."""
    return DeepSeekHarness(
        provider="deepseek-official",
        model=model or os.environ.get("MODEL", "deepseek-v4-flash"),
        cwd=os.getcwd(),
        dsh_home=str(HOME),
        profile="sdk-minimal" if minimal else "sdk",
        patches=(str(patch),) if patch else (),
    )


# --- step 8: sessions are JSONL logs under the harness home ----------------------


def list_sessions():
    """Newest first: session ids the runtime has written under <home>/sessions."""
    root = HOME / "sessions"
    if not root.exists():
        return []
    dirs = [p for p in root.rglob("*") if p.is_dir() and any(p.glob("session*.jsonl*"))]
    return [p.name for p in sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)]


# --- step 3: notifications are the event stream; we pick what to show -------------


def summarize(note: Notification):
    """One line for the events worth a person's eyes, None for the rest."""
    payload = note.payload or {}
    event = payload.get("event", payload)
    kind = event.get("type") or note.method
    data = event.get("data", {}) if isinstance(event, dict) else {}
    if kind == "tool/call":
        name = data.get("name") or data.get("tool") or "?"
        args = data.get("arguments") or data.get("args") or ""
        return f"  tool> {name} {str(args)[:90]}"
    if kind == "tool/result":
        content = data.get("content") or data.get("result") or ""
        text = " ".join(str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content) if isinstance(content, list) else str(content)
        return f"        {' '.join(text.split())[:110] or '(no output)'}"
    if kind == "turn/end":
        reason = (data.get("reason") or {}).get("kind") if isinstance(data.get("reason"), dict) else data.get("reason")
        return f"  turn ended: {reason}" if reason else None
    if kind == "compaction":
        return "  compacted"
    return None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="harness-dsh")
    parser.add_argument("--resume", metavar="SESSION_ID", help="continue a saved session")
    parser.add_argument("--minimal", action="store_true", help="use the sdk-minimal profile (shell + editor only)")
    cli = parser.parse_args()

    patch = write_patch(cli.minimal)
    session_id = cli.resume or datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"\n  simple coding harness · deepseek harness · profile {'sdk-minimal' if cli.minimal else 'sdk'}"
          f" · session {session_id} · /sessions, ctrl-d to exit")

    with build(minimal=cli.minimal, patch=patch) as harness:
        while True:
            try:
                text = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                break
            if text == "/sessions":
                for sid in list_sessions():
                    print(f"  {sid}")
                continue
            result = harness.run(
                text,
                session_id=session_id,
                on_notification=lambda n: (line := summarize(n)) and print(line),
            )
            print(f"\n  agent> {result.final_response}")
            print(f"  finish: {result.finish_reason} · {len(result.events)} events")


if __name__ == "__main__":
    sys.exit(main())
