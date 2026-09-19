import { test } from "node:test";
import assert from "node:assert/strict";

import { sandboxed, mount, isEvent, CSP, META } from "../page/sandbox.mjs";

test("the CSP meta tag goes first in <head>", () => {
  const html = "<!doctype html><html><head><title>x</title></head><body></body></html>";
  const out = sandboxed(html);
  assert.ok(out.startsWith("<!doctype html><html><head>" + META));
  assert.match(out, /<title>x<\/title>/);
});

test("a document without <head> gets the tag prepended", () => {
  assert.ok(sandboxed("<div>hi</div>").startsWith(META));
  assert.ok(sandboxed("<HEAD lang='en'>x").includes("<HEAD lang='en'>" + META + "x"));
});

test("the policy allows only inline style and script and data images", () => {
  assert.match(CSP, /default-src 'none'/);
  assert.match(CSP, /script-src 'unsafe-inline'/);
  assert.doesNotMatch(CSP, /connect-src|https?:/);
});

test("mount sets sandbox=allow-scripts and srcdoc", () => {
  const attrs = {};
  const iframe = { setAttribute: (k, v) => (attrs[k] = v), srcdoc: "" };
  mount(iframe, "<head></head><p>x</p>");
  assert.equal(attrs.sandbox, "allow-scripts");
  assert.ok(iframe.srcdoc.includes(META));
});

test("only {type: 'event', name} messages count as events", () => {
  assert.equal(isEvent({ type: "event", name: "refresh", payload: { a: 1 } }), true);
  assert.equal(isEvent({ type: "event" }), false);
  assert.equal(isEvent({ type: "navigate", name: "x" }), false);
  assert.equal(isEvent("event"), false);
  assert.equal(isEvent(null), false);
});

test("<header> is not <head>: the tag still goes before the body", () => {
  const out = sandboxed("<!doctype html><html><body><header>x</header></body></html>");
  assert.ok(out.startsWith(META), "a CSP tag inside <body> would be ignored by the browser");
  assert.doesNotMatch(out, /<header><meta/);
});

test("a meta refresh is stripped: it is the one way out that needs no click", () => {
  const out = sandboxed('<head><meta http-equiv="refresh" content="0;url=https://evil.example/"></head><p>x</p>');
  assert.doesNotMatch(out, /refresh/);
  assert.match(out, /<head><meta http-equiv="Content-Security-Policy"/);
});
