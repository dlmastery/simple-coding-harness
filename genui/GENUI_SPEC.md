# Generative UI series: build spec

A second codelab in this repository: **zero to hero on generative UI**, the
layer where an agent's output becomes an interface instead of prose. It
continues the harness codelab (Parts 1 to 7) into the user-facing side. The
map comes from the June 2026 "State of Generative UI" report: two
independent choices, **transport** (where the UI appears: AG-UI for your
own product, MCP Apps for a third-party host) and **generation** (what the
agent emits: static, declarative, or open-ended), and the open formats in
the declarative middle (A2UI, OpenUI Lang, json-render, plus YAML and the
legacy Thesys C1 JSON as comparison points).

Layout: `genui/README.md` is the series codelab (written by the lead).
Each sub-theme is a directory `genui/NN_name/` with a short `README.md`
(what the sub-theme covers, the order of its steps) and its steps as
`step_NN_name/` directories. Steps inside a sub-theme build on each other
in order; sub-themes are independent of each other and are built in
parallel, one agent per sub-theme.

## Rules for every step (the harness codelab rules, adapted)

- Every step is self-contained: its own code, `README.md`, `test_step.py`,
  and, where there is a browser part, its own `package.json`. A later step
  in the same sub-theme starts from a copy of the previous one and adds
  one idea. Never edit another sub-theme's directory.
- **Model calls** use the same convention as the harness codelab: the
  OpenAI-compatible `openai` client, env vars `API_KEY`, `BASE_URL`
  (default `https://api.openai.com/v1`), `MODEL` (default `gpt-4.1-mini`),
  loaded from the environment or from `~/.simple-harness/env` (a
  `KEY=VALUE` file; read it, never print it). Put this in one small
  `llm.py` per step. On this machine live calls from Python need
  `truststore.inject_into_ssl()` (guard the import).
- **Offline tests.** `test_step.py` (pytest) never calls a model or the
  network: the model is a fake that returns scripted output (a spec, a
  DSL string, a stream of chunks). Parsers, renderers, encoders and
  servers are tested against those. When a step has Node code, `npm test`
  (`node --test`, `--experimental-strip-types` for `.ts`) is run from
  `test_step.py` through `subprocess` when `node` is on PATH and skipped
  otherwise; if `node_modules` is missing and `npm` is available,
  `test_step.py` runs `npm install` first (CI has network; keep
  dependencies few and pinned). Prefer plain JavaScript modules (`.mjs`)
  with no build step; use React only where the library under study is a
  React library, then use `react` + `react-dom` with `htm` or
  `React.createElement`, no JSX and no bundler, served by a tiny Python
  static server or `npx serve`.
- **Quick demo** in every README, right after "What this step adds": the
  exact command (`python demo.py` and/or `npm run demo`), then the real
  recorded output in a ```text fence (at most 40 lines), and, when the
  step renders in a browser, a screenshot `demo.png` taken headlessly
  with Playwright (`playwright` and Chromium are installed on this
  machine: `from playwright.sync_api import sync_playwright`; the demo
  script starts the server, opens the page, waits for the render, saves
  `demo.png`, and exits). The README embeds it with
  `![demo](demo.png)`. Record it by running it; if a part could not run,
  say so in one sentence under the output.
- **README structure**: `# Step NN - Title`; **What this step adds**;
  `## Quick demo`; the idea (why, with the report's terms); `## The code,
  piece by piece` with 4-8 fenced snippets (```python, ```js, ```ts,
  ```html), each introduced by a line naming the file in backticks such as
  `` `server.py`: ``; `## Run it`; `## What to notice`; `## Diff from the
  previous step` (omit in a sub-theme's first step). Every snippet line
  must exist verbatim (whitespace-normalised) in the named file; from the
  repo root `python check_snippets.py genui/NN` checks it (it verifies
  python, js, jsx, ts, tsx, html and css fences). Elide with a line `...`.
  Illustrative JSON goes in ```json fences, which are not checked.
- Prose style: short sentences (about 20 words), active voice, consistent
  terms, no idioms, no first person, no references to any video or author.
  Name the report as "the State of Generative UI report (June 2026)" with
  the link https://www.openui.com/blog/state-of-generative-ui-report once
  per sub-theme README.
- Python 3.10+, Windows-compatible (pathlib; no POSIX-only calls), Node 22.
- Licenses: only open-source packages (MIT, Apache-2.0). Thesys C1 is a
  hosted API and is used only as a JSON *format* for the token comparison,
  never called.
- When done and green: `python run_tests.py genui/NN` and
  `python check_snippets.py genui/NN` from the repo root pass,
  `grep -rn -i "video\|youtube" genui/NN_*` is empty,
  `grep -rl evija genui/NN_*` is empty (no `__pycache__`, no
  `node_modules` committed: both are gitignored), then create the empty
  marker `genui/NN_*/.done`. Report the file list, test output,
  snippet-check output, and for each step a 3-5 line summary with the
  best snippet's file path, for the series README.

## Sub-theme 01 - Foundations: static, declarative, open-ended (`genui/01_foundations`)

The three generation modes with no framework at all, so the reader sees the
mechanism before the libraries. One Python backend (`server.py`, standard
library `http.server` or FastAPI, choose one and keep it), one page
(`index.html` + `app.js`), no build.

- `step_01_static_components`: the agent picks a component and its props.
  The model gets tools `show_metric(title, value, delta)`,
  `show_table(columns, rows)`, `show_chart(kind, labels, values)` as
  function-calling schemas; the server turns each tool call into a JSON
  message `{"component": "Metric", "props": {...}}` on an SSE stream; the
  page has three hand-written renderers keyed by component name. This is
  "static generation": components built ahead of time, the agent selects
  and fills. Demo prompt: "show me a dashboard for a lemonade stand".
- `step_02_declarative_tree`: the agent emits a whole layout as a JSON
  tree from a catalog (`Card`, `Row`, `Column`, `Text`, `Metric`, `Table`,
  `Chart`, `Button`), validated against a JSON Schema built from the
  catalog; the renderer walks the tree. Streaming: the server streams the
  model's JSON as it arrives and the page renders progressively with a
  tolerant partial-JSON parser (`partial_json.py` in Python for the tests,
  `partial-json.mjs` in the page). Show why a flat element map with ids
  (the shape A2UI and json-render use) streams better than a nested tree:
  implement both and show the first-paint time in the demo output.
- `step_03_open_ended_html`: no catalog: the model writes HTML/CSS/JS for
  the same prompt; the page puts it in a sandboxed `<iframe sandbox>` with
  a CSP and `postMessage` for events. Measure tokens for step 1, 2 and 3
  for the same prompt (count with `tiktoken` if installed, else the usage
  from the API) and print the table in the demo. This is the report's
  "5-10x" claim, checked.
- `step_04_hybrid_escape_hatch`: the report's hybrid pattern: the step 2
  catalog gains one `GeneratedView` component whose prop is model-written
  HTML rendered in the sandboxed iframe from step 3; everything else stays
  catalog-constrained. Actions: a `Button` with an `action` name posts an
  event back to the server, which runs the next model turn (the loop
  closes).

## Sub-theme 02 - AG-UI, the transport (`genui/02_ag_ui`)

Package `ag-ui-protocol` (PyPI, `from ag_ui.core import ...`,
`from ag_ui.encoder import EventEncoder`) on the server; a plain `fetch` +
SSE reader on the client first, `@ag-ui/client` (npm) second. Read
https://docs.ag-ui.com (quickstart/server, concepts/events) and the
package source in site-packages for the exact event classes.

- `step_01_ag_ui_server`: a FastAPI endpoint that accepts `RunAgentInput`
  and streams `RUN_STARTED`, `TEXT_MESSAGE_START/CONTENT/END`,
  `RUN_FINISHED` from a real model call; the page reads the SSE stream
  with `fetch` and renders the text. Show the wire format (one event per
  line) in the demo output.
- `step_02_ag_ui_tools_and_state`: tool calls (`TOOL_CALL_START/ARGS/END`)
  and shared state (`STATE_SNAPSHOT`, `STATE_DELTA` as JSON Patch); the
  agent updates a `dashboard` object in state and the page renders state
  with the step 01_foundations renderers: generative UI as state, the
  AG-UI way. Client tools: a tool the *page* executes (`confirm_purchase`)
  and returns as a tool result message on the next run.
- `step_03_ag_ui_from_the_harness`: bridge the harness codelab's loop to
  AG-UI: a copy of `step_21_streaming_headless/harness/` (the stage 15 loop
  with streaming) wrapped so that every model delta and tool call becomes
  an AG-UI event. Then the `@ag-ui/client` `HttpAgent` in the page
  (`npm install @ag-ui/client`) instead of hand-parsed SSE. The demo
  runs a coding task from the browser with tool calls shown live.

## Sub-theme 03 - A2UI, Google's declarative protocol (`genui/03_a2ui`)

Spec v0.9.1 (`createSurface`, `updateComponents` with a flat component
list and `id: "root"`, `updateDataModel` with JSON Pointer paths,
`deleteSurface`; Basic Catalog `https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json`).
Local copies of the protocol document, the basic catalog guide and the
JSON schemas are in
`C:\Users\evija\AppData\Local\Temp\claude\C--Users-evija-class\d9867287-0cb4-4cd5-b7ce-99de7294ae8e\scratchpad\genui_docs\`
(`a2ui_a2ui_protocol.md`, `a2ui_basic_catalog_implementation_guide.md`,
`a2ui_server_to_client.json`). Packages: PyPI `a2ui-core` and
`a2ui-agent-sdk`; npm `@a2ui/lit` and `@a2ui/react`. Check what each
actually exports before relying on it; if a package is thin, say so and
hand-write the small part.

- `step_01_a2ui_messages_by_hand`: a Python `a2ui.py` that builds the four
  envelope messages and validates them against the JSON schema; a
  hand-written renderer `render.mjs` for a subset of the Basic Catalog
  (`Card`, `Column`, `Row`, `Text`, `TextField`, `Button`, `CheckBox`) that
  keeps a surface's component map and data model and re-renders on each
  message. Demo: the spec's contact form stream, rendered, screenshot.
- `step_02_a2ui_from_a_model`: the model emits `updateComponents` messages
  from a prompt built from the catalog (use `a2ui-agent-sdk` if it
  provides prompt construction and message repair; else a
  `prompt_from_catalog.py`); data binding (`{"path": "/contact/email"}`),
  two-way binding from `TextField` into the data model, and client-to-
  server action events (`Button` `action.event`) posted back to the
  server, which answers with `updateDataModel`. Progressive rendering when
  a child id arrives before its component.
- `step_03_a2ui_lit_and_ag_ui`: the official renderer `@a2ui/lit` in the
  page instead of `render.mjs`, and the A2UI messages carried as AG-UI
  custom events (`CUSTOM` event with `name: "a2ui"`) from a server that
  reuses sub-theme 02's encoder; note the "A2UI over AG-UI over A2A"
  stack the report describes, and where each layer stops.

## Sub-theme 04 - OpenUI Lang (`genui/04_openui_lang`)

The report's most token-efficient format: line-oriented statements
`id = Component(args)`, forward references, streaming-first. Packages:
npm `@openuidev/lang-core` (parser), `@openuidev/react-lang` (React
renderer); no Python package. Read https://github.com/thesysdev/openui
(README, `packages/lang-core`, `benchmarks/`).

- `step_01_openui_lang_parser`: the language explained by writing a tiny
  parser for its core in Python (`openui_parse.py`: statements, string and
  number args, lists, forward references resolved into a tree, incomplete
  lines held back) and the same in `openui-parse.mjs`; a catalog of eight
  components with Zod-like schemas written as plain JSON Schema; a
  hand-written DOM renderer. Demo: render a hard-coded program, then the
  same program streamed line by line with the skeleton of forward
  references visible before their definitions arrive (screenshot at two
  points).
- `step_02_openui_react_lang`: the real thing: `@openuidev/lang-core` +
  `@openuidev/react-lang` with a catalog defined with Zod, the system
  prompt generated from the catalog, and a model streaming OpenUI Lang to
  the page (React without JSX, no bundler, or a minimal Vite setup if the
  package cannot load without one; say which and why). Show the prompt
  the catalog generates.
- `step_03_format_benchmark`: reproduce the report's token table for the
  same seven scenarios (or a subset of four: contact form, KPI dashboard,
  data table, pricing page): the same UI written in OpenUI Lang, YAML,
  Thesys C1 JSON (the legacy shape shown in the report), and json-render's
  element map; count tokens with `tiktoken` (`o200k_base`), compute
  time-to-first-render at 60 tokens per second, and print the table. The
  demo output is that table. Say clearly which numbers reproduce the
  report's and which do not.

- `step_04_openui_html_artifact` (added after the first build): the report's
  hybrid pattern on OpenUI's own reference implementation,
  `examples/miscellaneous/html-artifact` in the OpenUI repository and its
  "Open-ended HTML" guide: the step 02 catalog plus a `Markdown` component
  and an `HtmlArtifact(title, document)` component that shows a status
  while streaming and Raw / Rendered tabs when complete, the rendered tab
  a sandboxed iframe with a CSP injected first in the document head (which
  the example leaves out); the example's prompt rules (artifact only when
  the user asks for something interactive, inline CSS and JS only, one
  statement per line). Demo: a catalog-only dashboard reply and an
  interactive-artifact reply, three screenshots, a click inside the
  sandbox, and the token share of the artifact document.

## Sub-theme 05 - json-render, Vercel's declarative renderer (`genui/05_json_render`)

Packages npm `@json-render/core` and `@json-render/react`
(https://github.com/vercel-labs/json-render). Core concepts: `defineCatalog`
with Zod props, spec `{root, elements: {id: {type, props, children}}}`,
`catalog.prompt()`, streaming JSON Patch with `createSpecStreamCompiler`,
actions and `setState`.

- `step_01_json_render_catalog`: a catalog of six components, the spec
  shape, `Renderer` in React (no JSX, no bundler if possible), a Python
  server that asks the model for a complete spec using `catalog.prompt()`
  exported from a small Node script (`prompt.mjs` prints the prompt;
  Python reads it once and caches it to `prompt.txt`). Demo: dashboard
  prompt, screenshot.
- `step_02_json_render_streaming_patches`: the model streams JSON Patch
  operations (RFC 6902) against the element map; the page applies them
  with `createSpecStreamCompiler` and renders after each patch; the Python
  side has `json_patch.py` to validate and apply the same patches for the
  tests. Show first-paint versus the complete spec of step 1.
- `step_03_json_render_actions_and_targets`: actions (`Button` with an
  action name, built-in `setState`) round-tripped to the server for the
  next model turn; then the same spec rendered by a second target from the
  json-render family that needs no browser (`@json-render/ink` for the
  terminal or a plain text/markdown renderer written by hand if the ink
  package is not straightforward): one spec, two renderers, which is the
  report's reason to choose json-render.

## Sub-theme 06 - MCP Apps, UI in a host you do not control (`genui/06_mcp_apps`)

Spec SEP-1865 (https://modelcontextprotocol.io and the ext-apps repo
https://github.com/modelcontextprotocol/ext-apps); packages npm
`@modelcontextprotocol/ext-apps` (2.x) and the community `@mcp-ui/server`;
Python `mcp` (FastMCP) is installed. Fetch the ext-apps README and the spec
page before designing.

- `step_01_mcp_app_resource`: an MCP server (Python FastMCP, streamable
  HTTP) with one tool `lemonade_dashboard` whose result carries a UI
  resource (`ui://` URI with an HTML document) as the spec defines, plus
  the resource endpoint; a minimal host page `host.html` that lists tools,
  calls the tool, mounts the returned HTML in a sandboxed iframe and
  relays `postMessage` calls as the spec's JSON-RPC bridge. Demo: the
  host page with the dashboard mounted, screenshot.
- `step_02_mcp_app_in_a_real_host`: the same server tested against a real
  host: the harness codelab's step 26 MCP client extended to render UI
  resources in the terminal as text (the "host" is our harness), and the
  instructions to add the server to Claude Desktop or Goose for a real
  iframe host with what to expect (not recorded here unless a host is
  available; say so). Compare with sub-theme 02: the same UI, two
  transports; the report's rule "ship both".

## Sub-theme 07 - Generative UI in the harness (`genui/07_harness_genui`)

Ties the two codelabs together.

- `step_01_render_ui_tool`: the harness codelab's stage 15 loop (copy
  `step_15_subagents/harness/` into the step) gains a `render_ui(spec)`
  tool whose argument is a json-render element map validated against the
  sub-theme 05 catalog; the terminal UI draws it as a `rich` table/panel
  tree, and a `--web` flag serves the same spec to a browser page with the
  sub-theme 01 renderer over SSE. One agent, two surfaces.
- `step_02_trueforge_generative_ui`: TrueForge (Part 7 of the harness
  codelab; a local server at http://localhost:8790 with model
  `openai/gpt-4-1-mini`; Python SDK `trueforge_sdk`; client is
  `TrueForge(base_url="http://localhost:8790")`, inline agent
  `SessionAgentSpecBody(spec=AgentSpec(model=Model(name=...), config=RuntimeConfig(generative_ui=GenerativeUiConfig(enabled=True))))`,
  turn via `sessions.create_turn_stream`) has generative UI built in: the
  agent embeds an OpenUI snippet in its reply that the TrueForge chat UI
  renders. Capture such a reply over the SDK, extract the OpenUI Lang
  program from it, and render it with sub-theme 04's parser and DOM
  renderer in our own page. Demo: the raw reply, the extracted program,
  the screenshot. Tests offline with a fake SSE server (see
  `step_46_trueforge_loop/test_step.py` once it exists for the pattern;
  if it does not exist yet, write your own small fake).
