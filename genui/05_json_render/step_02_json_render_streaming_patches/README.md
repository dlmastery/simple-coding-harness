# Step 02 - Streaming JSON Patch into the element map

<!-- genui-orientation -->
**Lesson 16 of 23.** [Course](../../README.md) · [Theme](../README.md) · [Previous lesson](../step_01_json_render_catalog/README.md) · [Next lesson](../step_03_json_render_actions_and_targets/README.md)

<!-- /genui-orientation -->

**What this step adds:** the model streams the spec as JSON Patch operations
(RFC 6902), one per line, and the page renders after every patch instead of
waiting for the whole document. The four rules from step 1 are gone; the
prompt is the library's own JSONL format. The server forwards the model's
text as it arrives (`/stream`) and compiles a copy with `json_patch.py`, a
small RFC 6902 implementation with the same tolerances as
`createSpecStreamCompiler`. The page pushes each chunk into that compiler and
hands the result to `Renderer`. First paint moves from the end of the reply
to its second line.

## Quick demo

```
python demo.py
```

```text
page: first paint at 3.48 s, complete at 10.14 s, 13 patches
server: first chunk 2.53 s, first paint possible 3.46 s, complete 10.11 s
step 1 for comparison: first paint 5.8 s (the complete spec, nothing earlier)
13 patches, 9 elements, 4043 prompt tokens, 487 completion tokens
  {"op": "add", "path": "/root", "value": "dashboard"}
  {"op": "add", "path": "/elements/dashboard", "value": {"type": "Card", "props": {"title": "Lemon...
  {"op": "add", "path": "/elements/row-metrics", "value": {"type": "Row", "props": {"gap": "large"...
  {"op": "add", "path": "/elements/metric-sales", "value": {"type": "Metric", "props": {"label": "...
  {"op": "add", "path": "/elements/metric-best-day", "value": {"type": "Metric", "props": {"label"...
  {"op": "add", "path": "/elements/metric-products-sold", "value": {"type": "Metric", "props": {"l...
  ... 7 more
catalog check: ok
saved demo_spec.json, demo_first_paint.png and demo.png
```

The page at the first paint, one card with a title and no children yet:

![first paint](demo_first_paint.png)

The same page when the stream ends:

![demo](demo.png)

The runs vary with the model's speed. In this one the first element was on
screen 3.5 s after the request and the last one at 10.1 s; step 1 showed
nothing until its whole object arrived at 5.8 s. The time to the first chunk
(2.5 s here) is the model reading a 4,000-token prompt, and no format can
remove that part.

## Files

```text
step_02_json_render_streaming_patches/
├── server.py           FastAPI app: POST /stream forwards the model's JSONL chunk by chunk; GET /last has the compiled spec, patches, timings, usage
├── llm.py              OpenAI-compatible client; stream_text() yields deltas, .usage from the last chunk
├── json_patch.py       RFC 6902 JSON Patch and RFC 6901 JSON Pointer; SpecStream compiles a chunked JSONL stream
├── prompt.py           runs prompt.mjs and catalog_json.mjs once and caches prompt.txt and catalog.json
├── spec.py             check_spec(): unknown types, dangling child ids and wrong prop types, against catalog.json
├── catalog.mjs         the same six components; PROMPT is the library's default JSONL prompt plus one id rule
├── registry.mjs        one React function per catalog entry through defineRegistry, written with htm (no JSX)
├── app.mjs             the page: read the stream, push each chunk into createSpecStreamCompiler, render after each patch
├── index.html          the page shell and the import map of pinned esm.sh builds
├── prompt.mjs          prints the system prompt json-render generates from the catalog
├── catalog_json.mjs    prints the catalog as JSON Schema, one entry per component
├── prompt.txt          the cached prompt
├── catalog.json        the cached JSON Schema of the six components
├── demo_spec.json      the spec the recorded stream compiled to
├── tests/
│   ├── patches.jsonl   a 13-patch fixture stream whose last line has no newline
│   ├── compile.mjs     compiles a JSONL file with createSpecStreamCompiler and prints the spec
│   └── stream.test.mjs node --test: the compiler on the fixture cut at arbitrary points; rendering a spec still arriving
├── test_step.py        offline pytest: RFC 6902 examples, SpecStream against compile.mjs, the relay with a fake model
├── demo.py             starts the server, streams in a headless page, saves demo_first_paint.png and demo.png, prints the patches
├── demo_first_paint.png   the page at the first paint
├── demo.png            the page when the stream ended
├── package.json        the same pins as step 1; npm test
├── package-lock.json   the lockfile for those pins
└── README.md           this file
```

## The idea

Step 1 rendered once. That was fine for a reader, and slow for a user: a
spec of 500 tokens takes several seconds to write, and a nested JSON tree
cannot be rendered until its last bracket closes. The State of Generative UI
report calls the fix "streaming-first" formats, and the flat element map is
one: each element is one line, complete on its own, and addressed by id.

json-render streams RFC 6902 operations against the spec object:

```json
{"op":"add","path":"/root","value":"dashboard"}
{"op":"add","path":"/elements/dashboard","value":{"type":"Card","props":{"title":"Lemonade"},"children":["row-metrics"]}}
{"op":"add","path":"/elements/row-metrics","value":{"type":"Row","props":{"gap":"large"},"children":[]}}
{"op":"add","path":"/state/sales/total","value":"$500"}
```

The first line names the root. The second line gives the root an element,
and the page can paint. The parent lists children that do not exist yet;
the renderer skips them until their line arrives. `replace` and `remove`
work on the same paths, which is what step 3 uses to edit a spec that is
already on screen.

## The code, piece by piece

`catalog.mjs`: the same six components. The prompt is now the library's
default: JSONL patches, `/root` first, one element per line.

```js
export const PROMPT = catalog.prompt({
  system: "You are a dashboard builder. You turn a request into a UI spec.",
  customRules: ["Use short element ids such as card-1, row-1, metric-1."],
});
```

`llm.py`: a streaming call. No JSON mode: JSONL is many objects, and JSON
mode would insist on one.

```python
class Stream:
    """Iterates over text deltas as they arrive. After the loop, .usage holds
    the token counts the API sends with its last chunk."""

    def __init__(self, response):
        self.response = response
        self.usage = None

    def __iter__(self):
        for chunk in self.response:
            if chunk.usage is not None:
                self.usage = {"prompt_tokens": chunk.usage.prompt_tokens, "completion_tokens": chunk.usage.completion_tokens}
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

`json_patch.py`: RFC 6902 with JSON Pointer paths, on plain dicts and lists.
Two tolerances are copied from the library, so both sides build the same
spec for a well-formed stream: `add` creates a missing parent, because the
model's first element patch is `/elements/card-1` and no `/elements`
patch comes before it, and `replace` creates a missing target. On
malformed lines the library is more forgiving (see "When a line does not
apply"); a bad patch here raises `PatchError` and nothing else, so the
compiler can skip the line and go on:

```python
def apply_patch(doc, patch):
    """Apply one operation in place. Returns doc. A bad patch raises PatchError, nothing else."""
    if not isinstance(patch, dict):  # a JSON array or string on the line: not a patch
        raise PatchError(f"a patch must be an object, got {type(patch).__name__}")
    op = patch.get("op")
    if op not in OPS:
        raise PatchError(f"unknown op {op!r}")
    ...
    if op == "add":
        if path == "":
            if not isinstance(patch["value"], dict):
                raise PatchError("the whole document must be an object")
            doc.clear()
            doc.update(patch["value"])
        else:
            _add(doc, path, copy.deepcopy(patch["value"]))
    elif op == "remove":
        _remove(doc, path)
    elif op == "replace":
        parent, key = _parent(doc, path, create=True)
        if isinstance(parent, list) and key < len(parent):
            parent[key] = copy.deepcopy(patch["value"])
        else:
            _add(doc, path, copy.deepcopy(patch["value"]))
    elif op == "move":
        value = _remove(doc, patch["from"])
        _add(doc, path, value)
    elif op == "copy":
        _add(doc, path, copy.deepcopy(get_path(doc, patch["from"])))
    elif op == "test":
        if get_path(doc, path) != patch["value"]:
            raise PatchError(f"test failed at {path}")
    return doc
```

`json_patch.py`: the stream compiler. Chunks arrive at any boundary; only
complete lines are parsed, and the last line is applied by `finish()` when
the stream ends without a newline. The same line rules as
`createSpecStreamCompiler`; a line that does not apply goes to `skipped`
with its reason, whatever the reason was:

```python
class SpecStream:
    """Feed text chunks in; complete patch lines come out, applied to .spec."""

    def __init__(self):
        self.spec = {}
        self.patches = []
        self.buffer = ""
        self.skipped = []

    def push(self, chunk):
        self.buffer += chunk
        lines = self.buffer.split("\n")
        self.buffer = lines.pop()
        return self._apply_lines(lines)
```

`server.py`: the relay. Every chunk goes to the page unchanged, and into a
`SpecStream` on the way, so the server ends with the complete spec, the
patch list and the moment the first paint became possible. A model call
that fails part-way cannot change the HTTP status (the headers went out
with the first chunk), so the stream ends with one more line,
`{"error": "..."}`: not a patch, both compilers skip it, and the page
reads it as the terminal state. `/last` records the same `error`:

```python
def relay(prompt):
    started = time.perf_counter()
    compiler = SpecStream()
    timings = {"first_chunk": None, "first_paint": None, "complete": None}
    error, usage = None, None
    try:
        stream = llm.stream_text(system_prompt(), prompt)
        for chunk in stream:
            if timings["first_chunk"] is None:
                timings["first_chunk"] = time.perf_counter() - started
            compiler.push(chunk)
            if timings["first_paint"] is None and compiler.has_root():
                timings["first_paint"] = time.perf_counter() - started
            yield chunk
        usage = stream.usage
    except Exception as failure:  # noqa: BLE001 - the model call failed: say so on the wire and in /last
        error = f"{type(failure).__name__}: {failure}"
        yield "\n" + json.dumps({"error": error}) + "\n"
    compiler.finish()
    timings["complete"] = time.perf_counter() - started
```

`app.mjs`: the page reads the body with a stream reader and pushes each
chunk into the library's compiler. `newPatches` is empty while a line is
still incomplete; `result` is a new object whenever a patch applied, so
`setSpec` re-renders. The whole read is one `try/finally`: a non-200
answer, a lost connection or the server's `{"error"}` line all end in a
status line that says what happened, and `loading` is cleared either
way, so `Generate` (disabled while a stream runs) is never stuck.

```js
    const compiler = createSpecStreamCompiler();
    try {
      const response = await fetch("/stream", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      for await (const chunk of chunks(response)) {
        text += chunk;
        const { result, newPatches } = compiler.push(chunk);
        if (newPatches.length === 0) continue;
        // The first patch sets /root alone; Renderer reads spec.elements[spec.root]
        // with no guard, so give it an empty map until /elements arrives.
        setSpec(result.elements ? result : { ...result, elements: {} });
        if (firstPaint === null && result.root && result.elements?.[result.root]) {
          firstPaint = seconds();
          setStatus(`first paint at ${firstPaint} s`);
        }
      }
      setSpec(compiler.getResult()); // applies a last line that had no newline
      const failed = errorLine(text);
      setStatus(failed
        ? `stopped after ${compiler.getPatches().length} patches: ${failed}`
        : `first paint at ${firstPaint} s, complete at ${seconds()} s, ${compiler.getPatches().length} patches`);
    } catch (error) {
      setStatus(`stream failed: ${error.message}`); // a dead server or a lost connection: a terminal state, not "streaming..." forever
    } finally {
      setLoading(false);
    }
```

`app.mjs`: state patches mutate `spec.state` in place. `StateProvider`
compares `initialState` by reference, so a fresh copy per spec version is
what makes `/state/...` patches reach the store.

```js
  const state = useMemo(() => ({ ...(spec?.state ?? {}) }), [spec]);
```

## Why: what breaks without it

Step 01 waits 5.8 s for one object and then draws everything. The model
wrote the first card in the first second; the format hid it. JSON Patch
lines make every element its own complete line, so the page can apply
each as it lands. The cost is a stream of lines the model can get wrong
one at a time: a line wrapped in `[...]`, a bare string, an `add` below a
scalar, an object where `/root` should hold an id. Before this round
each of those was an exception out of `relay()` in the middle of a
`StreamingResponse`: uvicorn dropped the body, the page's reader
rejected, and the status said `streaming...` forever. Now each is a
skipped line with a reason, and a failed model call is a terminal line
the page can read.

## Run it

Prerequisites as step 01 (Node 20+ and `npm install`, fastapi/uvicorn/
httpx/jsonschema/openai, a key, Playwright for `demo.py`).

bash:

```
npm install
export API_KEY=sk-...
python server.py          # http://127.0.0.1:8056, press Generate
python demo.py            # streams once, saves demo_first_paint.png and demo.png
python -m pytest -q test_step.py
npm test
```

PowerShell:

```
npm install
$env:API_KEY = "sk-..."
python server.py
python demo.py
python -m pytest -q test_step.py
npm test
```

Expected output: the `Quick demo` transcript above; timings vary with
the model. `catalog check: ok` and an empty `skipped` list (the demo
prints skipped lines when there are any) are the checks.

## When a line does not apply

- **On the page:** `createSpecStreamCompiler` never throws; a line it
  cannot apply is dropped and the next one is applied. The page shows no
  trace of it.
- **On the server:** `SpecStream` skips the line and records
  `(line, reason)` in `skipped`; `/last` returns it and `demo.py` prints
  it. That is where to look when the page and the server disagree.
- **Where Python and the library differ**, on malformed lines only: the
  library accepts `path: ""` as a key named `""` while Python replaces
  the document (object) or skips (anything else); the library counts a
  `remove` of a missing path as applied, Python skips it; the library
  overwrites a scalar parent silently, Python skips with
  `parent is not a container`. `LAST["skipped"]` shows every divergence.
- **A transport error:** a non-200 answer (`stream failed: server
  answered 500: ...`), a dead server or a lost connection end in the
  status line and `Generate` is enabled again.
- **A model failure part-way:** the stream ends with `{"error": "..."}`;
  the status reads `stopped after N patches: <reason>` and what arrived
  stays on screen. `/last` carries `error` and the partial spec.

## Error handling

- `demo.py` gives uvicorn 10 s to bind port 8056 and raises
  `RuntimeError("the server did not start ...; is the port free?")` when
  it cannot (a `python server.py` still running holds the port).
- `check_spec` reports wrong shapes and cycles as sentences (step 01).
- ctrl-c stops `server.py` and `demo.py`.

## What to notice

- Two compilers, one fixture. `tests/patches.jsonl` is compiled by
  `json_patch.SpecStream` and by `createSpecStreamCompiler`
  (`tests/compile.mjs`); the test asserts the same spec. The RFC examples
  from appendix A of RFC 6902 run against the Python side.
- A stream that ends without a newline is normal. In `tests/patches.jsonl`
  the loop applies 12 patches and `getResult()` applies the 13th;
  `tests/stream.test.mjs` asserts that count.
- The first paint needs two lines, `/root` and the root element. A parent
  that lists a child that has not arrived renders without it; nothing
  breaks. That is the property the report calls out in favour of flat
  element maps. The first-paint numbers depend on the model emitting
  `/root` and then the root element first, as the library's prompt asks;
  a model that writes the leaves first shows nothing until the root
  arrives, and the page's status stays at `streaming...` until then.
- The prompt is 4,000 tokens and the reply is under 500. Streaming does
  not change the prompt cost, only when the user sees something.

## Gotchas / What this is not

- One `LAST` result on the server, no sessions; two pages streaming at
  once interleave their `LAST`. The streams themselves are independent.
- The page and the server compile the same text with different code; on
  a well-formed stream they agree (the test pins it), on a malformed one
  `skipped` is the record of where they did not.
- JSON mode is off (`stream_text` sends no `response_format`): JSONL is
  not one JSON document, and the model is trusted to write one patch per
  line because the library's prompt says so.

## Diff from the previous step

- `catalog.mjs`: the four "one JSON object" rules are gone; the library's
  JSONL prompt is used as is.
- `llm.py`: `complete_spec()` became `stream_text()`, a streaming call with
  `stream_options={"include_usage": True}` and no JSON mode.
- `json_patch.py`: new. RFC 6902 operations, JSON Pointer and `SpecStream`.
- `server.py`: `/generate` became `/stream` (a `StreamingResponse`), plus
  `/last` with the compiled spec, patches, timings and usage.
- `app.mjs`: a stream reader, `createSpecStreamCompiler`, the root-only
  guard and the per-version copy of `spec.state`.
- `tests/`: `patches.jsonl`, `compile.mjs` and `stream.test.mjs` replace
  `render.test.mjs`.

## What the next step adds

Step 03 adds actions (a button press becomes a server turn on the same
transcript and compiler), a Python-side check of the action params, and
a second render target: the same spec drawn with Ink in a terminal.
