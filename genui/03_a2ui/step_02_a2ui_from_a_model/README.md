# Step 02 - A2UI from a model

<!-- genui-orientation -->
**Lesson 9 of 23.** [Course](../../README.md) · [Theme](../README.md) · [Previous lesson](../step_01_a2ui_messages_by_hand/README.md) · [Next lesson](../step_03_a2ui_lit_and_ag_ui/README.md)

<!-- /genui-orientation -->

**What this step adds:** the model writes the messages. `prompt.py` uses the
`a2ui-agent-sdk` package to build the system prompt from the Basic Catalog,
to parse the reply while it streams, and to repair and validate it when it
is finished. `server.py` runs the spec's prompt-generate-validate loop, keeps
its own mirror of the surface, and answers a `Button` action with an
`updateDataModel`. The page from step 01 gains a prompt box, an SSE reader
over `fetch`, and the action round trip.

## Why: what breaks without it

Step 01's messages were typed by hand, which proves the renderer and
nothing about generation. A model asked for "a contact form" writes
prose, or JSON in a shape of its own, unless the catalog and the rules are
in its prompt; and even then it writes `TextInput` for `TextField`, a
trailing comma, a child it never defines. Without a validator between the
model and the page, the page draws nothing and nobody knows why. This
step is the loop the spec asks for: prompt with the schema, parse while
streaming, validate when finished, send the validator's text back once.

## Quick demo

```bash
python demo.py
```

```text
system prompt: 41083 chars (role + SDK workflow rules + Basic Catalog schema); model gpt-4.1-mini
browser http://127.0.0.1:8742/
  0.40s POST /generate "Make a contact form with first name, email, a newsletter checkbox and a send button."
  4.86s createSurface: main
  5.34s updateComponents: 2 components, 1 loading placeholders, missing refs 0
  5.54s updateComponents: 3 components, 1 loading placeholders, missing refs 0
  5.62s updateComponents: 3 components, 1 loading placeholders, missing refs 0
  ... 35 more progressive updateComponents ...
  10.81s updateComponents: 8 components, 0 loading placeholders, missing refs 0
  10.82s updateDataModel: /form = {"firstName":"","email":"","newsletter":false,"status":""}
  10.82s note {"attempt":1,"usage":{"prompt_tokens":9929,"completion_tokens":600},"reply_chars":2325}
  10.82s done
typed into ['firstNameField', 'emailField']: data model = {"form": {"firstName": "Ada", "email": "ada@example.com", "newsletter": true, "status": ""}}
click -> 11.00s action -> POST /action {"firstName":"Ada","email":"ada@example.com","newsletter":true}
the status Text now reads: Server got 'submit' at 14:58:54 with firstName='Ada', email='ada@example.com', newsletter=True
screenshot: demo.png
```

![demo](demo.png)

## Files

```text
step_02_a2ui_from_a_model/
├── envelope.py           a2ui.py from step 01, renamed so it does not shadow the SDK's `a2ui` package
├── llm.py                model access: API_KEY, BASE_URL, MODEL from the env or ~/.simple-harness/env
├── prompt.py             the a2ui-agent-sdk side: system prompt from the catalog, stream parser, full parser
├── server.py             FastAPI app: POST /generate (the generate loop over SSE, keepalives), POST /action, the STORE mirror reset per generation
├── schema/
│   ├── server_to_client.json   the envelope schema (the four messages)
│   ├── common_types.json       shared types: ComponentId, bindings, actions
│   └── catalog.json            the Basic Catalog: every component and function schema
├── static/
│   ├── index.html        the page shell, the prompt form, a striped style for loading_* rows
│   ├── app.mjs           sends the prompt, reads the SSE body over fetch, posts Button actions; always sets a2uiDone
│   ├── surface.mjs       the DOM-free client state, unchanged from step 01
│   └── render.mjs        the hand painter, unchanged from step 01
├── surface.test.mjs      node --test for surface.mjs
├── test_step.py          offline pytest: a scripted reply stands in for the model; SDK tests skip without it
├── demo.py               a live model call, typing, a click, the server's answer; saves demo.png
├── demo.png              the recorded page
├── package.json          npm test = node --test (no dependencies)
└── README.md             this file
```

## Prompt-first, then validate

A2UI v0.9 is "prompt-first": the schema and the catalog go into the model's
prompt, and the model writes JSON that should match. Nothing constrains the
output at generation time, so the protocol pairs the prompt with a loop:
generate, validate, and if validation fails, send the error back and ask
again. The State of Generative UI report calls this the cost of the
declarative middle: the agent can only say what the catalog allows, and
someone has to check that it did.

The `a2ui-agent-sdk` package covers both halves. `DirectJsonFormat` renders
the catalog schema into prompt text and wraps the workflow rules (root
first, parents before children, blocks in `<a2ui-json>` tags).
`DirectJsonStreamParser` reads the reply as it streams and yields
`updateComponents` messages as soon as a component is reachable from
`root`, standing an empty `Row` named `loading_<id>` in for every child it
has not seen yet. The full parser repairs small faults such as trailing
commas and validates each block against the catalog.

## The code, piece by piece

The SDK prompt: a role paragraph, the SDK's workflow rules, then the JSON
schema of the whole catalog. The role text asks for one surface, bindings
under `/form`, a status `Text`, and a `submit` action that carries the bound
fields.

`prompt.py`:

```python
def inference_format():
    """Loads the bundled v0.9.1 schemas and the Basic Catalog once."""
    global _format
    if _format is None:
        _format = DirectJsonFormat(version=SPEC_VERSION, catalogs=[BasicCatalog.get_config(SPEC_VERSION)])
    return _format
...
def system_prompt():
    """Role text, the SDK's workflow rules, then the full JSON schema of the catalog."""
    return inference_format().prompt_generator.generate(role_description=ROLE, include_schema=True)


def stream_parser():
    """Feed model text chunks in; get A2UI messages out as soon as they are usable."""
    return DirectJsonStreamParser(inference_format()._supported_catalogs[0])
```

The full parser turns a finished reply into messages and prose, or raises
with the validator's text. A part holds the prose that preceded a block and
the block's messages.

`prompt.py`:

```python
    try:
        parts = inference_format().parser.parse_response(text)
    except (A2uiCompilationError, A2uiParseError) as error:
        raise ValueError(str(error)) from error
    messages, prose = [], []
    for part in parts:  # a part holds the prose before a block and the block's messages
        if part.text and part.text.strip():
            prose.append(part.text.strip())
        messages.extend(part.a2ui_json or [])
    return messages, prose
```

The generate loop. Chunks go into the stream parser and its messages go
straight to the page; partial `updateDataModel` yields are held back
because they arrive without their `path`. When the reply is complete the
full parser runs; on failure the partial surface is withdrawn and the error
goes back to the model once.

`server.py`:

```python
def generate(user_prompt):
    """Yield (event, payload) pairs: the progressive messages, then the final ones."""
    conversation = [{"role": "system", "content": prompt.system_prompt()}, {"role": "user", "content": user_prompt}]
    for attempt in range(1, ATTEMPTS + 1):
        parser = prompt.stream_parser()
        created, reply = [], []
        for chunk in stream_model(conversation):
            reply.append(chunk)
            if parser is None:
                continue  # the progressive pass gave up; the final pass still runs
            try:
                parts = parser.process_chunk(chunk)
            except Exception as error:  # the stream parser does not repair; the full parser does
                yield "note", {"attempt": attempt, "streaming_stopped": f"{type(error).__name__}: {error}"[:200]}
                parser = None
                continue
            for part in parts:
                for message in part.a2ui_json or []:
                    kind = envelope.message_type(message)
                    if kind == "createSurface":
                        created.append(message["createSurface"]["surfaceId"])
                    if kind == "updateDataModel":
                        continue  # partial values arrive without their path; the final pass sends them
                    yield mirror(message)
        text = "".join(reply)
        try:
            messages, prose = prompt.parse_reply(text)
        except ValueError as error:
            yield "note", {"attempt": attempt, "error": str(error)[:300]}
            for surface_id in created:
                yield mirror(envelope.delete_surface(surface_id))
            conversation += [{"role": "assistant", "content": text},
                             {"role": "user", "content": f"The reply failed validation. Fix it and send the complete reply again.\n{error}"}]
            continue
```

The streaming pass skips `updateDataModel` (a partial value has no path
yet), so the generated fields stay empty until the final pass sends the
whole data model; in the recorded run that is the last 10 ms.

Every generation begins by withdrawing the previous one:

`server.py`:

```python
    for surface_id in list(STORE.surfaces):
        yield mirror(envelope.delete_surface(surface_id))  # the previous generation goes first
```

Press Generate twice on one page and the model sends `createSurface main`
again. Step 01's hand store treats that as a reset, but the official
renderer in step 03 throws `Surface main already exists`, and without the
delete the server's own mirror would keep the first form's components
merged into the second. So the reset is explicit: `deleteSurface` on the
wire, the mirror cleared, then the new surface.

The server keeps the same `SurfaceStore` the page keeps, fed with every
message it sends. When a click arrives, the mirror knows which `Text` the
model bound for confirmations, so the answer lands in the right path even
when the model chose `/form/status` over `/status`. The mirror is one
per process, so this server is for one page at a time; two tabs would
answer each other's clicks. It is also not authoritative: what the user
typed lives only in the page's data model until an action carries it (or
`sendDataModel` does, see "What to notice").

`server.py`:

```python
def status_path(surface):
    """The path of the Text the model bound for confirmations: the mirror knows the structure."""
    for component in surface.components.values():
        path = component.get("text", {}).get("path") if isinstance(component.get("text"), dict) else None
        if component["component"] == "Text" and path and path.endswith("status"):
            return path
    return "/status"


def answer_action(action):
    """What a click gets back. A model turn could go here; this step answers
    directly so the loop stays visible: action in, updateDataModel out."""
    fields = ", ".join(f"{key}={value!r}" for key, value in action.get("context", {}).items())
    when = datetime.now(timezone.utc).strftime("%H:%M:%S")
    surface = STORE.surfaces.get(action["surfaceId"])
    path = status_path(surface) if surface else "/status"
    reply = envelope.update_data_model(action["surfaceId"], path, f"Server got '{action['name']}' at {when} with {fields}")
    return [mirror(reply)[1]]
```

The page reads the POST's SSE body by hand, because `EventSource` cannot
send a body. A `Button` click posts the action (context resolved from the
local data model at that moment) and applies the messages that come back.

`static/app.mjs`:

```js
  onAction: async (action) => {
    if (running) return note('action ignored: a generation is still streaming');
    note(`action -> POST /action ${JSON.stringify(action.context)}`);
    try {
      const response = await fetch('/action', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(action) });
      if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
      for (const message of await response.json()) receive(message);
    } catch (error) {
      note(`action failed: ${error.message}`);
    }
  },
...
      while ((end = buffer.indexOf('\n\n')) >= 0) {
        const frame = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        const event = frame.match(/^event: (.*)$/m)?.[1];
        const line = frame.match(/^data: (.*)$/m)?.[1];
        if (line === undefined) continue; // a comment, such as the keepalive
        const data = JSON.parse(line);
        if (event === 'note') note(`note ${JSON.stringify(data)}`);
        else if (event === 'done') { note('done'); finished = true; }
        else receive(data);
      }
```

The framing `/generate` uses, which the page's regex reader depends on:

| frame | meaning |
|---|---|
| `data: {"version": ..., "createSurface": ...}` | one A2UI envelope, apply it |
| `event: note` + `data: {...}` | progress: `streaming_stopped`, a validation `error` or `warning`, the model's `prose`, the `usage` |
| `event: done` + `data: {}` | the end; the page sets `window.a2uiDone` |
| `: keepalive` | an SSE comment every 15 s of silence while the model thinks; no data line, skipped |

The read loop sits in a `try`/`finally`: a dead server, a 422, a message
the store refuses or a stream that ends without `done` is logged as
`generate failed: ...` or `the stream ended without done`, and
`a2uiDone` flips either way, so nothing waits forever.

The model reaches the server through the harness convention: `API_KEY`,
`BASE_URL`, `MODEL`, from the environment or `~/.simple-harness/env`.

`llm.py`:

```python
BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")
```

## Run it

```bash
pip install a2ui-agent-sdk==0.6.0 fastapi uvicorn openai jsonschema playwright
python server.py          # then open http://127.0.0.1:8742/ and press Generate
python demo.py            # a live model call; writes demo.png
python -m pytest test_step.py   # offline: a scripted reply stands in for the model
npm test
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."     # or API_KEY=... in ~\.simple-harness\env
pip install a2ui-agent-sdk==0.6.0 fastapi uvicorn openai jsonschema playwright
python -m playwright install chromium
python server.py
python demo.py
python -m pytest test_step.py
npm test
```

`a2ui-agent-sdk` 0.6.0 depends on `a2ui-core` 0.1.1 (the pydantic models,
validators and bundled schemas), and also pulls `google-adk`, `a2a-sdk` and
an ANTLR runtime for parts this step does not touch. The version is
pinned because `prompt.stream_parser` reaches into the format's
`_supported_catalogs`, a private attribute with no public accessor in
0.6.0. Tests that need the SDK skip when it is absent.

Expected output: the page shows a striped card within about five seconds
(the `loading_*` rows), then the fields, labels and button appear over
the next few seconds while the log on the right lists one
`updateComponents` per repaint; the fields fill in with the final
`updateDataModel`, then `note {... "usage": ...}` and `done`. Typing and
clicking Send writes `Server got 'submit' at ...` into the status line.
The quick demo above is the same run, driven headlessly.

## Error handling

- No key or the model call fails: `note {"error": "AuthenticationError: ..."}`
  then `done`; the page logs it and stops, nothing is drawn.
- The reply fails validation: `note {"attempt": 1, "error": ...}`, the
  partial surface is withdrawn with `deleteSurface`, and the error goes
  back to the model once; a second failure ends with
  `note {"error": "gave up after the correction attempt"}` and an empty
  page.
- The stream parser hits something it cannot heal (a trailing comma):
  `note {"streaming_stopped": ...}`; the page keeps what it has, and the
  final pass sends the repaired messages.
- The model is silent for 15 s: a `: keepalive` comment, skipped by the
  page.
- A body that is not `{"prompt": "<string>"}`, or an action without
  `name`/`surfaceId`: `422` from FastAPI; the page logs
  `generate failed: 422 ...` / `action failed: 422 ...`.
- The server is down or the stream is cut: `generate failed: ...` or
  `the stream ended without done`; `a2uiDone` is set either way, so
  `demo.py` stops instead of waiting two minutes.
- A message the store refuses (a prototype key in a path): logged as
  `generate failed`, the rest of that stream is not read; the next
  Generate starts clean.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- One page per process: the mirror is a global, not per session. Step 03
  has a `threadId` on the wire and still uses a global; a product keys
  the mirror by it.
- A click during a generation is ignored (logged), and Generate is
  disabled until `done`.
- The fields are empty until the final pass (see above); a spinner would
  be honest there.
- The correction loop is one round; the second request carries the whole
  failed reply plus the validator text, about 10K tokens more.
- Fixed port 8742; no authentication; the prompt goes to the model as
  typed.

## What to notice

- The prompt is 41K characters, about 9.9K tokens, before the user says a
  word. That is the whole catalog schema riding along on every request;
  the first message reached the page 4.5 seconds after the POST. A custom
  catalog with fewer components is the usual answer.
- The SDK asks the model for `"version": "v0.9"` and the `v0_9` catalog id
  even when configured for 0.9.1; the bundled 0.9.1 files are the 0.9
  files. Both versions validate.
- Progressive rendering is real: 38 `updateComponents` messages arrived
  before the final one. The stream parser substitutes `loading_<id>` rows
  for children it has not seen, so the page never has a missing reference;
  step 01's `waiting for <id>` placeholder is the other way to handle the
  same moment. Many of the 38 are the same components with a longer
  `label` or `text`: the SDK heals cut strings and re-sends them.
- The stream parser does not repair. A trailing comma stops it (the test
  shows the `streaming_stopped` note), and the final pass still delivers the
  repaired, validated messages. Streaming is an optimisation on top of the
  validated result, not a replacement for it.
- The correction loop costs a second 10K-token request. In the tests an
  unknown component name triggers it; the recorded run needed one attempt.
- Server and page hold the same state through the same messages. That is
  why `sendDataModel` exists in the spec: when a server does not mirror,
  the client can send its data model with every action instead. The
  mirror here is a convenience, not a source of truth: it knows the
  structure, never what the user typed until the action's context
  carries it.

## What the next step adds

The same loop with the SDK's `to_events`, the official Lit renderer in
the page, and AG-UI as the transport: the A2UI messages ride as `CUSTOM`
events, the action comes back as `forwardedProps`.

## Diff from the previous step

- `a2ui.py` is now `envelope.py`, same content: the SDK's package is also
  called `a2ui`, and a local module would shadow it.
- New `llm.py` (model access) and `prompt.py` (the SDK's prompt, stream
  parser and full parser).
- `server.py`: `contact_form.jsonl` replay replaced by `POST /generate`
  (the generate loop over SSE), `POST /action`, and the `STORE` mirror.
- `static/app.mjs`: a prompt form, an SSE reader over `fetch`, actions
  posted to the server; `static/index.html`: the form and a striped style
  for `loading_*` rows.
- `surface.mjs` and `render.mjs` are unchanged.
