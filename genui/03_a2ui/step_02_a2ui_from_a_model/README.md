# Step 02 - A2UI from a model

**What this step adds:** the model writes the messages. `prompt.py` uses the
`a2ui-agent-sdk` package to build the system prompt from the Basic Catalog,
to parse the reply while it streams, and to repair and validate it when it
is finished. `server.py` runs the spec's prompt-generate-validate loop, keeps
its own mirror of the surface, and answers a `Button` action with an
`updateDataModel`. The page from step 01 gains a prompt box, an SSE reader
over `fetch`, and the action round trip.

## Quick demo

```
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

The server keeps the same `SurfaceStore` the page keeps, fed with every
message it sends. When a click arrives, the mirror knows which `Text` the
model bound for confirmations, so the answer lands in the right path even
when the model chose `/form/status` over `/status`.

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
    note(`action -> POST /action ${JSON.stringify(action.context)}`);
    const response = await fetch('/action', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(action) });
    for (const message of await response.json()) receive(message);
  },
...
    while ((end = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const event = frame.match(/^event: (.*)$/m)?.[1];
      const data = JSON.parse(frame.match(/^data: (.*)$/m)[1]);
      if (event === 'note') note(`note ${JSON.stringify(data)}`);
      else if (event === 'done') note('done');
      else receive(data);
    }
```

The model reaches the server through the harness convention: `API_KEY`,
`BASE_URL`, `MODEL`, from the environment or `~/.simple-harness/env`.

`llm.py`:

```python
BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")
```

## Run it

```
pip install a2ui-agent-sdk fastapi uvicorn openai jsonschema playwright
python server.py          # then open http://127.0.0.1:8742/ and press Generate
python demo.py            # a live model call; writes demo.png
python -m pytest test_step.py   # offline: a scripted reply stands in for the model
npm test
```

`a2ui-agent-sdk` 0.6.0 depends on `a2ui-core` 0.1.1 (the pydantic models,
validators and bundled schemas), and also pulls `google-adk`, `a2a-sdk` and
an ANTLR runtime for parts this step does not touch. Tests that need the
SDK skip when it is absent.

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
  the client can send its data model with every action instead.

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
