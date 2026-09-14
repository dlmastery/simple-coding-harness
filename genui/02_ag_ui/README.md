# Sub-theme 02 - AG-UI, the transport

The State of Generative UI report (June 2026)
(https://www.openui.com/blog/state-of-generative-ui-report) separates two
choices: what the agent generates, and how it travels to the screen. This
sub-theme is about the second one. AG-UI is the transport for a product
you own: one `RunAgentInput` request, one stream of typed events back.
The three steps build the server side with `ag-ui-protocol` (PyPI), the
client side first by hand and then with `@ag-ui/client` (npm), and end by
putting the harness codelab's coding agent behind the protocol.

| Step | Adds |
|------|------|
| `step_01_ag_ui_server` | A FastAPI endpoint that streams `RUN_STARTED`, `TEXT_MESSAGE_*`, `RUN_FINISHED` from a real model call; a page that reads the stream with `fetch`. The wire format, one event per line. |
| `step_02_ag_ui_tools_and_state` | Tool calls (`TOOL_CALL_*`) and shared state (`STATE_SNAPSHOT`, `STATE_DELTA` as JSON Patch). Server tools patch a `dashboard` object and the page renders it. A client tool, `confirm_purchase`, that the page executes. |
| `step_03_ag_ui_from_the_harness` | The harness codelab's step 21 loop wrapped so every delta, tool call, permission question and todo update is an AG-UI event; `HttpAgent` from `@ag-ui/client` in the page. A coding task run from the browser. |

## Layout

```text
02_ag_ui/
├── README.md
├── step_01_ag_ui_server/
│   ├── server.py  agent.py  llm.py  sse.py
│   ├── index.html  app.js  sse.mjs  sse.test.mjs
│   ├── test_step.py  demo.py  demo.png  package.json
│   └── README.md
├── step_02_ag_ui_tools_and_state/
│   ├── server.py  agent.py  tools.py  json_patch.py  llm.py  sse.py
│   ├── index.html  app.js  render.mjs  json-patch.mjs  sse.mjs  json-patch.test.mjs  sse.test.mjs
│   ├── test_step.py  demo.py  demo.png  package.json
│   └── README.md
└── step_03_ag_ui_from_the_harness/
    ├── server.py  bridge.py  llm.py  sse.py  harness/
    ├── index.html  app.js  client-entry.mjs  http-agent.test.mjs
    ├── test_step.py  demo.py  demo.png  package.json  package-lock.json  .gitignore
    └── README.md
```

Every step has the same shape: `server.py` exposes `POST /agent` and
serves the page, `llm.py` loads the same settings, `sse.py` reads the
stream for the tests and the demo, and `test_step.py` runs offline with a
fake model. Steps 01 and 02 write the client by hand (`app.js`,
`sse.mjs`); step 03 replaces the agent with `bridge.py` over `harness/` and
the client with `@ag-ui/client`.

Each step is self-contained. Run `python demo.py` in a step for the
recorded demo (needs a model key), `python -m pytest -q test_step.py` and
`npm test` for the offline tests.
