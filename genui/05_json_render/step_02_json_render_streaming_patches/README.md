# Step 02 - Streaming JSON Patch into the element map

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
spec: `add` creates a missing parent, because the model's first element
patch is `/elements/card-1` and no `/elements` patch comes before it, and
`replace` creates a missing target.

```python
def apply_patch(doc, patch):
    """Apply one operation in place. Returns doc."""
    op = patch.get("op")
    if op not in OPS:
        raise PatchError(f"unknown op {op!r}")
    ...
    if op == "add":
        if path == "":
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
the stream ends without a newline. The same rules as `createSpecStreamCompiler`.

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
patch list and the moment the first paint became possible.

```python
def relay(prompt):
    """Forward each chunk as it arrives, and compile a copy on the way."""
    started = time.perf_counter()
    stream = llm.stream_text(system_prompt(), prompt)
    compiler = SpecStream()
    timings = {"first_chunk": None, "first_paint": None, "complete": None}
    for chunk in stream:
        if timings["first_chunk"] is None:
            timings["first_chunk"] = time.perf_counter() - started
        compiler.push(chunk)
        if timings["first_paint"] is None and compiler.has_root():
            timings["first_paint"] = time.perf_counter() - started
        yield chunk
    compiler.finish()
    timings["complete"] = time.perf_counter() - started
```

`app.mjs`: the page reads the body with a stream reader and pushes each
chunk into the library's compiler. `newPatches` is empty while a line is
still incomplete; `result` is a new object whenever a patch applied, so
`setSpec` re-renders.

```js
    const compiler = createSpecStreamCompiler();
    const response = await fetch("/stream", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    for await (const chunk of chunks(response)) {
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
```

`app.mjs`: state patches mutate `spec.state` in place. `StateProvider`
compares `initialState` by reference, so a fresh copy per spec version is
what makes `/state/...` patches reach the store.

```js
  const state = useMemo(() => ({ ...(spec?.state ?? {}) }), [spec]);
```

## Run it

```
npm install
python server.py          # http://127.0.0.1:8056, press Generate
python demo.py            # streams once, saves demo_first_paint.png and demo.png
python -m pytest -q test_step.py
npm test
```

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
  element maps.
- The prompt is 4,000 tokens and the reply is under 500. Streaming does
  not change the prompt cost, only when the user sees something.

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
