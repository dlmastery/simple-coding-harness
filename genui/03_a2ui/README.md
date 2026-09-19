# Sub-theme 03 - A2UI, Google's declarative protocol

A2UI v0.9.1 is a streaming JSON protocol: four envelope messages
(`createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface`), a
flat component list joined by ids, a separate data model addressed by JSON
Pointer, and a swappable component catalog. It sits in the declarative
middle of the generation axis in the State of Generative UI report
(June 2026, https://www.openui.com/blog/state-of-generative-ui-report), and
it is transport-agnostic, which the third step uses.

The server-to-client half is the four envelope messages. The
client-to-server half, which the intro of the spec defines and every step
here uses, is two things:

- the `action` message a `Button` raises, with its `context` resolved
  from the data model at click time:
  `{"name": "submit", "surfaceId": "main", "sourceComponentId": "send", "timestamp": "...", "context": {"email": "ada@example.com"}}`;
  step 01 logs it, step 02 posts it to `/action`, step 03 carries it in
  an AG-UI run's `forwardedProps`;
- `sendDataModel`, a flag on `createSurface`: when the server sets it,
  the client sends its whole data model (`{"version", "surfaces": {id:
  {...}}}`) along with every action, so a server that keeps no mirror
  still knows what the user typed. Step 03's server sets it and echoes the
  fields back.

A repeated `createSurface` for an id that exists is a reset in the hand
store of steps 01 and 02 (an `EventSource` reconnect replays it) and an
error in the official `MessageProcessor` of step 03, so steps 02 and 03
send `deleteSurface` before a new generation. Every page logs a bad
message and goes on (steps 02 and 03 also flip `window.a2uiDone` whatever
the server does), and the demos raise instead of spinning when their
port is taken.

The three steps, in order; each is self-contained and starts from a copy of
the previous one:

1. `step_01_a2ui_messages_by_hand` - the four messages built and validated
   in Python against the official schemas, a DOM-free surface state and a
   hand-written renderer for part of the Basic Catalog; the protocol
   document's own contact form, streamed over SSE and rendered.
2. `step_02_a2ui_from_a_model` - the model writes the messages: the
   `a2ui-agent-sdk` prompt from the catalog, its stream parser for
   progressive rendering, its repair-and-validate pass, the correction
   loop, two-way binding, and a `Button` action answered by the server.
3. `step_03_a2ui_lit_and_ag_ui` - the official `@a2ui/lit` renderer in the
   page, and the same messages carried as AG-UI `CUSTOM` events from a
   server built on `ag-ui-protocol`; the A2UI over AG-UI over A2A stack.

## Layout

```text
03_a2ui/
├── README.md
├── step_01_a2ui_messages_by_hand/
│   ├── a2ui.py
│   ├── server.py
│   ├── contact_form.jsonl
│   ├── schema/
│   ├── static/
│   ├── surface.test.mjs
│   ├── test_step.py
│   ├── demo.py
│   ├── demo.png
│   ├── package.json
│   └── README.md
├── step_02_a2ui_from_a_model/
│   ├── envelope.py
│   ├── llm.py
│   ├── prompt.py
│   ├── server.py
│   ├── schema/
│   ├── static/
│   ├── surface.test.mjs
│   ├── test_step.py
│   ├── demo.py
│   ├── demo.png
│   ├── package.json
│   └── README.md
└── step_03_a2ui_lit_and_ag_ui/
    ├── envelope.py
    ├── llm.py
    ├── prompt.py
    ├── server.py
    ├── schema/
    ├── src/
    ├── static/
    ├── agui.test.mjs
    ├── test_step.py
    ├── demo.py
    ├── demo.png
    ├── package.json
    ├── package-lock.json
    ├── .gitignore
    └── README.md
```

Every step carries the same `schema/` (the three official v0.9.1 files) and
the same envelope module (`a2ui.py`, renamed `envelope.py` from step 02 on);
steps 02 and 03 share `llm.py` and `prompt.py` unchanged, and each step
swaps the server routes and the page while keeping the message shapes.

Packages: `jsonschema` (step 01), `a2ui-agent-sdk` with `a2ui-core` (steps
02 and 03), `ag-ui-protocol` (step 03) on the Python side; `@a2ui/lit`,
`@a2ui/web_core`, `@a2ui/markdown-it`, `@lit/context` and `esbuild` for
the build (step 03) on the npm side. Each step's README says what it took
from each.
