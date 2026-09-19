# Sub-theme 05 - json-render, Vercel's declarative renderer

json-render is one of the open formats in the declarative middle of the
[State of Generative UI report (June 2026)](https://www.openui.com/blog/state-of-generative-ui-report):
the model emits a JSON document that names components from a catalog you
wrote, and a renderer draws it. The catalog is the contract. From one object
(`defineCatalog` with Zod props) the library produces the system prompt
(`catalog.prompt()`), the typed component map (`defineRegistry`), the
validation and the JSON Schema. The spec is a flat element map,
`{root, elements: {id: {type, props, children}}, state}`, which streams as
RFC 6902 patches and renders on any target that has a component map.

Packages: `@json-render/core` 0.20.0, `@json-render/react` 0.20.0 and
`@json-render/ink` 0.20.0, pinned in each step's `package.json`. The browser
page runs React 19 without JSX or a bundler: `htm` for templates and an
import map of pinned esm.sh builds, because React 19 ships no browser ESM
build. Node uses `node_modules` for the prompt export, the tests
(`react-dom/server`) and the terminal target. The Python server uses
FastAPI and the OpenAI-compatible `openai` client; a small `json_patch.py`
mirrors the library's stream compiler for the tests.

## Steps

1. [`step_01_json_render_catalog`](step_01_json_render_catalog/README.md):
   a catalog of six components, the spec shape, `Renderer` in the page, and
   a server that asks the model for one complete spec with the prompt the
   catalog generates. Demo: the lemonade dashboard, one paint at 5.8 s.
2. [`step_02_json_render_streaming_patches`](step_02_json_render_streaming_patches/README.md):
   the model streams JSON Patch lines; the page applies them with
   `createSpecStreamCompiler` and renders after each one; `json_patch.py`
   applies the same patches in Python. Demo: first paint at 3.5 s, complete
   at 10.1 s, with a screenshot at each point.
3. [`step_03_json_render_actions_and_targets`](step_03_json_render_actions_and_targets/README.md):
   a `Button` with actions. `setState` stays in the page; catalog actions go
   to the server for the next model turn, which answers with patches against
   the spec on screen. Then the same spec rendered in the terminal by
   `@json-render/ink`: one spec, two renderers.

Each step is self-contained. From the repository root,
`python run_tests.py genui/05` runs the offline tests and
`python check_snippets.py genui/05` checks that every README snippet exists
in the code.

## Layout

```text
05_json_render/
├── README.md                                  this file
├── step_01_json_render_catalog/
│   ├── server.py  llm.py  prompt.py  spec.py    the server: one complete spec per request, checked against catalog.json
│   ├── catalog.mjs  registry.mjs  app.mjs       the catalog, the React component map, the page
│   ├── index.html  prompt.mjs  catalog_json.mjs the page shell with its import map; the two Node exports
│   ├── prompt.txt  catalog.json  demo_spec.json the cached prompt and JSON Schema; the recorded spec
│   ├── tests/render.test.mjs  test_step.py      the Node suite and the offline pytest
│   ├── demo.py  demo.png                        the recorded demo and its screenshot
│   └── package.json  package-lock.json          pinned json-render, react, htm, zod
├── step_02_json_render_streaming_patches/
│   ├── server.py  llm.py  prompt.py  spec.py    the server: /stream relays JSONL chunk by chunk
│   ├── json_patch.py                            RFC 6902 patches and SpecStream, new in this step
│   ├── catalog.mjs  registry.mjs  app.mjs       the page now compiles the stream with createSpecStreamCompiler
│   ├── index.html  prompt.mjs  catalog_json.mjs
│   ├── prompt.txt  catalog.json  demo_spec.json
│   ├── tests/  test_step.py                     patches.jsonl, compile.mjs, stream.test.mjs; the offline pytest
│   ├── demo.py  demo_first_paint.png  demo.png  two screenshots: first paint and complete
│   └── package.json  package-lock.json
└── step_03_json_render_actions_and_targets/
    ├── server.py  llm.py  prompt.py  spec.py    the server: /stream starts a session, /action runs the next turn
    ├── json_patch.py                            unchanged from step 2
    ├── catalog.mjs  registry.mjs  app.mjs       a Button, two actions, handlers that call the server
    ├── ink_render.mjs                           the terminal target, new in this step
    ├── index.html  prompt.mjs  catalog_json.mjs
    ├── prompt.txt  catalog.json  demo_spec.json
    ├── tests/targets.test.mjs  test_step.py     one spec through both targets; the offline pytest
    ├── demo.py  demo.png
    └── package.json  package-lock.json          adds @json-render/ink and ink
```

Every step has the same shape: a Python server (`server.py`, `llm.py`,
`prompt.py`, `spec.py`), a Node catalog and page (`catalog.mjs`,
`registry.mjs`, `app.mjs`, `index.html`), the two exports that feed Python
(`prompt.mjs`, `catalog_json.mjs`) and their caches; later steps add
`json_patch.py` and `ink_render.mjs`, and each step has its own tests.

Two things hold for every step and are said once here:

- **The model may produce lines the compiler cannot apply.** On the page
  json-render's compiler drops such a line silently; on the server
  `SpecStream` skips it and records `(line, reason)`, and `GET /last`
  returns that list as `skipped`. When the page and the server disagree,
  `skipped` is where to look; the demos print it. A model call that fails
  part-way ends the stream with one `{"error": "..."}` line (steps 02 and
  03), which both compilers skip and the page reads as the reason.
- **One session, no concurrency.** Each server keeps one `LAST` result
  (step 03: one `SESSION` transcript and compiler) at module level. Two
  browsers on the same server overwrite each other; the pages disable
  `Generate` and drop presses while a turn runs, and nothing more. The
  step 01 server also serves its whole directory as static files.
