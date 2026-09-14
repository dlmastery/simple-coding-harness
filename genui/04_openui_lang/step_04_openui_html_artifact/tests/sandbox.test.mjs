import { test } from "node:test";
import assert from "node:assert/strict";
import { CSP, META, checkDocument, isEvent, sandboxed } from "../sandbox.mjs";
import { blocks, inline, renderMarkdown } from "../markdown.mjs";
import { renderToStaticMarkup } from "react-dom/server";

test("the CSP allows only inline style and script and data: images", () => {
  assert.equal(CSP, "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:");
  assert.ok(META.startsWith('<meta http-equiv="Content-Security-Policy"'));
});

test("sandboxed() puts the CSP meta first in <head>", () => {
  const html = "<!doctype html><html><head><title>x</title></head><body>hi</body></html>";
  const out = sandboxed(html);
  assert.ok(out.startsWith("<!doctype html><html><head>" + META + "<title>x</title>"));
});

test("sandboxed() prepends the meta when there is no <head>, and drops a CSP the model wrote", () => {
  assert.ok(sandboxed("<p>fragment</p>").startsWith(META + "<p>fragment</p>"));
  const loose = '<html><head><meta http-equiv="Content-Security-Policy" content="default-src *"></head></html>';
  const out = sandboxed(loose);
  assert.equal(out.match(/Content-Security-Policy/g).length, 1);
  assert.ok(out.includes(CSP) && !out.includes("default-src *"));
});

test("checkDocument() reports external resources and network calls", () => {
  assert.deepEqual(checkDocument("<p>ok</p><script>let a=1</script>"), []);
  const bad = "<script src='https://cdn.example/x.js'></script><img src=\"//img.example/a.png\"><script>fetch('/api')</script>";
  assert.deepEqual(checkDocument(bad), [
    "external resource: https://cdn.example/x.js",
    "external resource: //img.example/a.png",
    "network call in script",
  ]);
});

test("isEvent() accepts one message shape only", () => {
  assert.equal(isEvent({ type: "event", name: "calculated" }), true);
  assert.equal(isEvent({ type: "event" }), false);
  assert.equal(isEvent("event"), false);
  assert.equal(isEvent(null), false);
});

test("the Markdown subset renders to elements, never to an HTML string", () => {
  assert.deepEqual(blocks("a\n\n\nb"), ["a", "b"]);
  assert.equal(renderToStaticMarkup(inline("x **b** `c`")), "x <strong>b</strong> <code>c</code>");
  const html = renderToStaticMarkup(renderMarkdown("# Title\n\n- one\n- two\n\n<img src=x onerror=alert(1)>"));
  assert.ok(html.includes('<h2 class="md-heading">Title</h2>'));
  assert.ok(html.includes("<li>one</li><li>two</li>"));
  assert.ok(html.includes("&lt;img src=x onerror=alert(1)&gt;"), html);
});
