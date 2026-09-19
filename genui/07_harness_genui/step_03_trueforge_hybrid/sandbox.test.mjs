// The CSP injection in web/sandbox.mjs must match artifact.py's.
import { test } from "node:test";
import assert from "node:assert/strict";
import { CSP, META, MAX_DOCUMENT_CHARS, checkDocument, sandboxed } from "./web/sandbox.mjs";

test("the CSP meta tag goes right after the doctype, before any element", () => {
  const doc = '<!doctype html><html><head><meta charset="utf-8"><title>x</title></head><body>hi</body></html>';
  assert.ok(sandboxed(doc).startsWith("<!doctype html>" + META + "<html><head>"));
  assert.ok(sandboxed('<HTML><HEAD lang="en"><title>x</title></HEAD></HTML>').startsWith(META + "<HTML>"));
  const early = sandboxed("<!doctype html><script>fetch('https://x')</script><head></head>");
  assert.ok(early.indexOf(META) < early.indexOf("<script>"));  // a script before <head> still runs under the policy
  assert.ok(!/refresh/i.test(sandboxed('<meta http-equiv="refresh" content="0;url=https://x">')));
});

test("a CSP the model wrote is removed, a fragment gets the tag in front", () => {
  const loosened = '<html><head><meta http-equiv="Content-Security-Policy" content="default-src *"></head><body></body></html>';
  const out = sandboxed(loosened);
  assert.equal(out.split("Content-Security-Policy").length - 1, 1);
  assert.ok(!out.includes("default-src *"));
  assert.equal(sandboxed("<p>fragment</p>"), META + "<p>fragment</p>");
  assert.ok(CSP.includes("default-src 'none'") && CSP.includes("script-src 'unsafe-inline'") && CSP.includes("img-src data:"));
});

test("checkDocument lists what the CSP will block", () => {
  assert.deepEqual(checkDocument("<p>fine</p><script>document.title='x'</script>"), []);
  const bad = '<script src="https://cdn.example/x.js"></script><script>fetch("/x")</script><meta http-equiv="refresh" content="0">';
  assert.deepEqual(checkDocument(bad), ["external resource: https://cdn.example/x.js", "network call in script", "meta refresh"]);
  assert.ok(checkDocument("x".repeat(MAX_DOCUMENT_CHARS + 1))[0].startsWith("document is 200001 characters"));
});
