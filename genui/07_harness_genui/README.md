# Sub-theme 07 - Generative UI in the harness

The two codelabs meet here. The harness codelab built an agent loop and
then moved it onto TrueForge; the generative UI series showed the formats
an agent can emit instead of prose. This sub-theme puts a rendering
surface on both harnesses.

The State of Generative UI report (June 2026,
https://www.openui.com/blog/state-of-generative-ui-report) separates
the transport (where the UI appears) from the generation mode (what the
agent emits). Both steps here are declarative generation; the transports
are a terminal, a browser page fed over SSE, and the TrueForge SDK.

| Step | What it adds |
|------|--------------|
| `step_01_render_ui_tool` | The stage 15 loop gains a `render_ui(spec)` tool. The spec is a json-render element map validated against a six-component catalog. The terminal draws it with `rich`; `--web` serves it to a browser page over SSE. One agent, two surfaces. |
| `step_02_trueforge_generative_ui` | TrueForge's built-in generative UI: an agent with `generative_ui` enabled answers with an OpenUI Lang program in its reply. The step captures it over the SDK, parses the language (Python and JavaScript, streaming-first with forward references) and renders it in a page of its own, one line per event. |

Read them in order. Step 01 is the harness drawing from a spec it
validated; step 02 is a hosted harness that already speaks a UI language,
with the parser and renderer written here so the language is understood
rather than delegated.

From the repository root:

```
python run_tests.py genui/07          # offline tests for both steps
python check_snippets.py genui/07     # every README snippet exists in its file
```
