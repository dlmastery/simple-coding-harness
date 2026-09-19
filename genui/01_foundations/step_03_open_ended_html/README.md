# Step 03 - Open-ended HTML

**What this step adds:** the third generation mode. No catalog, no schema:
the model writes the whole page as HTML, CSS and JS. The host puts that
document in an `<iframe sandbox>` with a Content Security Policy, and the
only way back out is `postMessage`. The demo runs the same prompt in static,
declarative and open-ended mode and counts the tokens each one cost, which
is the report's "5 to 10 times" claim, checked.

## Why: what breaks without it

The catalog of step 02 cannot draw a gauge, a map or a sparkline the
product never built. Open-ended generation can, because the model writes
the code. The cost is trust: `dashboard.innerHTML = modelHtml` would run
the model's `<script>` with the host's cookies and DOM, and a model that
was prompt-injected through the data it summarises would run someone
else's script. So the document must run in a box, and this step is about
the box as much as the mode.

## Quick demo

```bash
python demo.py
```

```text
prompt: show me a dashboard for a lemonade stand
mode    what the model wrote         tiktoken    api  vs flat
static  tool calls (name + args)          196    208     0.6x
flat    JSON element map                  328    328     1.0x
html    HTML document                    3013   3013     9.2x
time to the last byte: static 4.7s, flat 4.0s, html 32.5s
html: 8718 chars, 208 tags, 1 button(s) in the sandbox
clicked the first button; the host received: [{"type": "event", "name": "refreshData", "payload": {"updatedData": [{"hour": "9 AM", "cups": 18}, ...
saved demo.png
```

Two earlier runs gave 233 / 261 / 2545 (9.8x) and 233 / 344 / 3577 (10.4x).
The bridge line is cut here; the demo prints the whole payload.

![demo](demo.png)

## Files

```text
step_03_open_ended_html/
├── server.py         FastAPI app: /api/run gains html mode and HTML_PROMPT; every done carries raw
├── llm.py            one streamed call over the OpenAI-compatible API
├── catalog.py        the step 02 catalog, schemas, prompt and validate()
├── partial_json.py   the step 02 tolerant JSON parser
├── progress.py       the step 02 streaming measurement
├── tokens.py         counts what each mode made the model write, with tiktoken's o200k_base
├── page/
│   ├── index.html    the page shell with the sandbox iframe and the inbox panel
│   ├── app.js        four modes; mounts the finished document and listens for postMessage; always ends in data-state=done
│   ├── partial-json.mjs   the step 02 parser in JavaScript
│   ├── render.mjs    the step 02 renderers and walkers
│   └── sandbox.mjs   the box: sandbox="allow-scripts", the CSP meta tag first in <head>, meta refresh stripped, isEvent()
├── tests/
│   ├── partial-json.test.mjs   node --test for the parser
│   ├── render.test.mjs         node --test for the renderers
│   └── sandbox.test.mjs        node --test for the CSP injection and the event shape
├── test_step.py      offline pytest: html mode, the sandbox, the token count, the page
├── demo.py           the three modes headlessly; the token table, a click in the sandbox, demo.png
├── demo.png          the model's page mounted in the sandbox
├── package.json      npm test = node --test (no dependencies)
└── README.md         this file
```

## Open-ended generation

The State of Generative UI report's third mode gives the agent everything: it
can draw any layout, any style, any interaction, because it writes the code.
The price is on three fronts. Tokens: a page is text, and the text of a page
is long. Trust: the code came from a model and may do anything code does,
so it must run in a box. Consistency: nothing ties the page to the product's
components, so every reply looks different.

This step keeps the first two problems visible and solves the second one.
The sandbox is two layers. The iframe attribute `sandbox="allow-scripts"`
gives the document a unique origin and denies forms, popups and navigation
of the host. The CSP injected into the document denies fetches, scripts,
styles, images and connections from anywhere, so inline code can compute
but cannot load or send. What CSP does not govern is the iframe navigating
itself: a link or `location.href` can still take the sandbox to a URL of
the model's choosing, so the guarantee is the unique origin, not silence.
`sandboxed()` strips a `<meta http-equiv="refresh">`, the one way out that
needs no click. What the document can do is post a message to its parent,
and the host accepts exactly one shape.

## The code, piece by piece

`server.py`: the prompt. It is the same task as steps 01 and 02, with the
sandbox rules spelled out, because the model has to write code that works
inside them.

```python
HTML_PROMPT = """You build dashboards as one self-contained HTML document.
Write a complete document: <!doctype html>, <html>, <head> with one <style>, <body>,
and one <script> at the end. Everything inline: no external stylesheets, scripts,
fonts or images, because the page that hosts you blocks all network access.
Show three or four headline numbers, one table of detail and one chart drawn as
inline SVG. Invent plausible sample data when the user gives none.
Include at least one <button>. On click it must call
parent.postMessage({type: "event", name: "<what it does>", payload: {...}}, "*")
so the host page hears it. Output only the HTML, no code fence, no prose."""
```

`server.py`: html mode. The document streams as deltas like the JSON did,
then arrives whole. Every mode's `done` message now carries `raw`, the exact
text the model wrote, so the demo can count it.

```python
def open_ended_html(prompt):
    """Step 03: no catalog. The model's HTML as it streams, then the whole document."""
    messages = [{"role": "system", "content": HTML_PROMPT}, {"role": "user", "content": prompt}]
    for item in stream_text(messages):
        if isinstance(item, dict):
            yield item
            continue
        text, usage = item
        yield {"done": True, "mode": "html", "html": FENCE.sub("", text), "usage": usage, "raw": text}
```

`page/sandbox.mjs`: the box. The CSP goes into the document itself, first
thing in `<head>`, so it applies to the inline code that follows.

```js
export const CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:";

export const META = `<meta http-equiv="Content-Security-Policy" content="${CSP}">`;

export function sandboxed(html) {
  // Put the CSP meta tag first in <head>, or first in the document if there is no <head>.
  // \b: <header> is not <head>, and a CSP tag inside <body> is ignored by the browser.
  // A meta refresh is the one way a document can leave without a click; it goes.
  html = html.replace(/<meta[^>]*http-equiv\s*=\s*["']?refresh[^>]*>/gi, "");
  const head = /<head\b[^>]*>/i.exec(html);
  if (head) return html.slice(0, head.index + head[0].length) + META + html.slice(head.index + head[0].length);
  return META + html;
}

export function mount(iframe, html) {
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.srcdoc = sandboxed(html);
}

export function isEvent(data) {
  // The only shape the host accepts from the iframe: {type: "event", name, payload?}.
  return data !== null && typeof data === "object" && data.type === "event" && typeof data.name === "string";
}
```

`page/app.js`: the bridge. The listener checks the source window and the
shape of the data before it believes anything. A sandboxed iframe has an
opaque origin, so `event.origin` is `"null"` and cannot be used; the source
check does the same job.

```js
window.addEventListener("message", (event) => {
  // Only the mounted iframe, and only the one shape the host accepts.
  if (event.source !== frame.contentWindow || !isEvent(event.data)) return;
  inbox.push(event.data);
  inboxPanel.textContent += JSON.stringify(event.data) + "\n";
});
```

```js
      if (message.html !== undefined) mount(frame, message.html);
```

`tokens.py`: the count. tiktoken's `o200k_base` is the vocabulary of the
GPT-4.1 family, so its number matches the API's `completion_tokens` for the
text modes; for tool calls the API also bills the call framing, which is
why the static row differs by a dozen tokens.

```python
def count(text):
    """Tokens in the text, or None when no encoder is available."""
    enc = encoding()
    return len(enc.encode(text)) if enc else None
```

`demo.py`: the three modes run in the same page, then the first button in
the sandbox is clicked with Playwright and the host's inbox is read.

```python
        buttons = page.frame_locator("#frame").locator("button")
        clicked = buttons.count()
        if clicked:
            buttons.first.click()
            page.wait_for_timeout(300)
        inbox = page.evaluate("window.__inbox")
```

## Run it

Prerequisites: step 02's plus `tiktoken` (optional: the table falls back
to the API's counts without it).

```bash
python server.py            # http://127.0.0.1:8010, pick "open-ended" in the page
python demo.py              # the token table, the bridge event, demo.png
python -m pytest test_step.py
npm test
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."
python server.py
python demo.py
python -m pytest test_step.py
npm test
```

Expected output: in html mode the wire panel fills with the document for
20 to 40 seconds while the iframe stays blank, then the page mounts it and
the status line reads `32512 ms`. Clicking a button in the generated page
adds one `{"type": "event", ...}` line to the inbox panel. The quick demo
above prints the token table for the three modes.

If tiktoken cannot load its vocabulary (it is fetched once and cached), the
table falls back to the API's `completion_tokens` and says so.

## Error handling

- The model call fails, in any mode: the last frame is
  `{"done": true, "error": "..."}`, the status line shows it, the page
  reaches `data-state=done`; `demo.py` raises with the error text.
- The server is down or answers 4xx/5xx: the page records the error frame
  itself.
- The model wraps the document in a code fence: `FENCE` strips it from the
  finished text; `raw` keeps the fence so the token count is honest.
- The generated document throws: the error stays inside the iframe (its
  own console), the host is untouched.
- The iframe posts something that is not `{type: "event", name}`: dropped
  by `isEvent`; a message from any other window is dropped by the source
  check.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- The CSP covers loads and connections, not navigation. A generated `<a
  href="https://...">` still opens when the user clicks it, inside the
  sandbox; `location.href` does the same without a click. Only the meta
  refresh is stripped. Treat the sandbox as "cannot touch the host", not
  "cannot make a request".
- `sandboxed` needs to find `<head>` to put the policy where the browser
  reads it; without one the tag goes first in the document, which browsers
  also accept. A document with only a `<header>` gets the same treatment.
- The document is mounted once, complete. There is no partial render in
  html mode because a half-written document is not a document.
- The prompt asks for no external resources because the CSP blocks them;
  a model that ignores the prompt gets a page with missing fonts and
  images, not a network request.

## What to notice

- 10x is real. The same dashboard cost 328 tokens as a flat element map and
  3013 as HTML, and the HTML took eight times longer to arrive. The report's
  range is 5 to 10; three runs here landed at 9.2, 9.8 and 10.4.
- The HTML mode has no partial rendering. A half-written document cannot be
  mounted, so the user waits for the whole thing. The JSON modes painted
  their first component after about a second.
- The generated page looks nothing like steps 01 and 02. That is the
  consistency cost: the model chose yellow.
- The bridge is the whole contract between the two sides. The iframe can
  post anything; the host keeps only `{type: "event", name, payload}` from
  the one window it mounted. Step 04 turns those events into the next
  model turn.
- `sandbox="allow-scripts"` without `allow-same-origin` is the important
  half. With both, the document could reach the host's cookies and DOM.

## What the next step adds

The hybrid: the step 02 catalog plus one `GeneratedView` component whose
prop is model-written HTML rendered in this step's sandbox, and a `Button`
whose click becomes the next model turn.

## Diff from the previous step

```bash
diff -r ../step_02_declarative_tree .
```

New: `tokens.py`, `page/sandbox.mjs`, `tests/sandbox.test.mjs`. Changed:
`server.py` (`html` mode, `HTML_PROMPT`, `stream_text`, `raw` in every
`done`), `page/app.js` (iframe mount, message listener, `__inbox`),
`page/index.html` (the iframe, the inbox panel, the html option),
`demo.py` (three modes, the token table, the click). `catalog.py`,
`partial_json.py`, `progress.py`, `llm.py` and `page/render.mjs` are the
step 02 files.
