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

## Layout

```text
07_harness_genui/
├── README.md
├── step_01_render_ui_tool/
│   ├── harness/          the stage 15 loop plus genui.py and web.py
│   ├── web/              index.html, app.js: the browser surface
│   ├── test_step.py
│   ├── demo.py
│   ├── demo.png
│   └── README.md
└── step_02_trueforge_generative_ui/
    ├── client/           genui.py: the TrueForge session and the fence extractor
    ├── web/              index.html, app.js, openui-parse.mjs, render.mjs
    ├── openui_parse.py
    ├── server.py
    ├── openui-parse.test.mjs
    ├── test_step.py
    ├── demo.py
    ├── demo_stream.png
    ├── demo.png
    ├── sample_reply.md
    ├── package.json
    └── README.md
```

Both steps share the same surface shape: a standard library `http.server`
in a daemon thread pushing SSE events to a `web/` page, a `demo.py` that
runs one turn and saves the page with Playwright, and a `test_step.py` that
never calls a model; step 02 swaps the local `harness/` for a TrueForge
session and pushes one line of OpenUI Lang per event instead of a whole
spec.

Read them in order. Step 01 is the harness drawing from a spec it
validated; step 02 is a hosted harness that already speaks a UI language,
with the parser and renderer written here so the language is understood
rather than delegated.

From the repository root:

```
python run_tests.py genui/07          # offline tests for both steps
python check_snippets.py genui/07     # every README snippet exists in its file
```
