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
