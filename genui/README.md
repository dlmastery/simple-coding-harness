# Zero to Hero: Generative UI

## When the agent's answer is an interface, not a paragraph

The harness codelab in the parent directory builds the loop behind a coding
agent. This series builds what the user sees. A generative UI is an
interface the agent composes at run time: a metric card, a table, a form
that asks the next question, a chart. The agent still calls a model in a
loop. The difference is what the loop emits and what renders it.

The map for this series comes from the State of Generative UI report
(June 2026, https://www.openui.com/blog/state-of-generative-ui-report). It
separates two choices that are often mixed up.

**Transport: where the UI appears.**

| You want the agent inside | Use | Sub-theme |
|---|---|---|
| your own product | AG-UI, an event protocol over SSE | 02 |
| a host you do not control (Claude, ChatGPT, VS Code, Goose) | MCP Apps, sandboxed HTML resources over MCP | 06 |

**Generation: what the agent emits.**

| Mode | The agent emits | Who decides the layout | Sub-theme |
|---|---|---|---|
| static | a component name and its props | you, ahead of time | 01 |
| declarative | a spec from a catalog: a JSON tree, a flat element map, a DSL | the agent, inside your catalog | 01, 03, 04, 05 |
| open-ended | raw HTML, CSS and JavaScript | the agent, alone, in a sandboxed iframe | 01 |

The declarative middle is where the open formats compete: A2UI from Google,
OpenUI Lang from Thesys, json-render from Vercel. They differ in wire
format, token cost, streaming behaviour and renderer coverage. Sub-theme
04 measures them side by side.

Every step is a directory you can run. Every step has an offline test.
Every step's README opens with a **quick demo**: the command, its recorded
output, and a screenshot when there is a page.

**What you will build**

```text
01  foundations       static, declarative and open-ended generation with no framework,
                      then the hybrid escape hatch; measured in tokens
02  AG-UI             the transport: run lifecycle, text, tool calls and shared state as
                      events; then the harness codelab's loop speaking AG-UI
03  A2UI              Google's protocol: surfaces, flat component lists, data binding,
                      client-to-server actions, the official Lit renderer, A2UI over AG-UI
04  OpenUI Lang       the line-oriented DSL: a parser written by hand, the real React
                      renderer, and the token benchmark across four formats
05  json-render       Vercel's element map: catalog, JSON Patch streaming, actions, two
                      renderers for one spec
06  MCP Apps          UI inside a host you do not control: a tool result that carries an
                      HTML resource, a minimal host, and the harness as a host
07  in the harness    a render_ui tool for the stage 15 harness, and TrueForge's built-in
                      generative UI captured over its SDK
```

## Before you start

```bash
git clone https://github.com/dlmastery/simple-coding-harness
cd simple-coding-harness
pip install -r requirements.txt
pip install ag-ui-protocol a2ui-core jsonschema tiktoken
python -m playwright install chromium        # for the demo screenshots
```

Put your key where the harness codelab reads it: `API_KEY` in the
environment or in `~/.simple-harness/env` as `OPENAI_API_KEY=...`. Steps
with a browser part have a `package.json`; `npm install` in the step
directory fetches the one or two packages they use. Node 22 is required.

```bash
python run_tests.py genui/01          # one sub-theme, offline, no key
python run_tests.py genui             # every genui step
python check_snippets.py genui/03     # every snippet in those READMEs exists in the code
```

## How to read a step

Each step README follows one shape: **What this step adds**, the **quick
demo**, the idea in the report's terms, **the code piece by piece** with
every snippet verified against the source, **run it**, **what to notice**,
and the diff from the previous step. Read the sub-theme README first; it
says what its steps add in order.

<!-- SUBTHEMES -->

## Sub-theme index

| Sub-theme | Steps | Packages |
|---|---|---|
| 01 foundations | static components, declarative tree, open-ended HTML, hybrid escape hatch | none |
| 02 AG-UI | server, tools and state, from the harness | `ag-ui-protocol`, `@ag-ui/client` |
| 03 A2UI | messages by hand, from a model, Lit renderer over AG-UI | `a2ui-core`, `a2ui-agent-sdk`, `@a2ui/lit` |
| 04 OpenUI Lang | parser, React renderer, format benchmark | `@openuidev/lang-core`, `@openuidev/react-lang`, `tiktoken` |
| 05 json-render | catalog, streaming patches, actions and targets | `@json-render/core`, `@json-render/react` |
| 06 MCP Apps | app resource, in a real host | `mcp`, `@modelcontextprotocol/ext-apps` |
| 07 in the harness | render_ui tool, TrueForge generative UI | `rich`, `trueforge_sdk` |

> **Build status.** Sub-themes with a link in the table above are finished
> and tested. The specification they are built from is `GENUI_SPEC.md`.

MIT licensed. The specifications and libraries this series uses are
Apache-2.0 (A2UI, json-render) and MIT (AG-UI, OpenUI, MCP Apps); each
step README names what it uses.
