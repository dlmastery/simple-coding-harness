// Generative UI step 03 - the box an HtmlArtifact document runs in.
//
// The document is model-written HTML, CSS and JavaScript. It runs in an
// <iframe sandbox="allow-scripts" referrerpolicy="no-referrer" srcdoc=...>
// with a Content Security Policy injected as the first thing in <head>, so
// scripts and styles inline in the document work and nothing else does: no
// network, no frames, no forms posted anywhere. Same idea as sub-theme 04's
// html-artifact step, written again here for this renderer.

// No network at all: no scripts, styles, fonts or images from a URL, no
// fetch, no WebSocket. Inline style and script stay allowed because that is
// what the instructions tell the agent to write. Images may be data: URIs.
export const CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:";

export const META = `<meta http-equiv="Content-Security-Policy" content="${CSP}">`;

const CSP_META_RE = /<meta[^>]+http-equiv\s*=\s*["']?content-security-policy["']?[^>]*>/gi;
const REFRESH_META_RE = /<meta[^>]+http-equiv\s*=\s*["']?refresh["']?[^>]*>/gi;
const DOCTYPE_RE = /^\s*<!doctype[^>]*>/i;

// The document with our CSP right after the doctype, before any element. A
// CSP meta tag applies only to what comes after it; searching for the
// document's own <head> is not safe, because a script written before <head>,
// or a <head> inside a comment, would run ahead of the policy. A <meta>
// before <html> is legal HTML: the parser opens <html> and <head> for it.
// The model's own CSP and any meta refresh (a navigation the policy cannot
// block) are removed first.
export function sandboxed(html) {
  const cleaned = html.replace(CSP_META_RE, "").replace(REFRESH_META_RE, "");
  const doctype = DOCTYPE_RE.exec(cleaned);
  const at = doctype ? doctype[0].length : 0;
  return cleaned.slice(0, at) + META + cleaned.slice(at);
}

export const MAX_DOCUMENT_CHARS = 200_000;

// Findings about the document, for the page to show next to the artifact.
// The CSP already blocks every one of them; this is for the reader.
export function checkDocument(html) {
  const problems = [];
  if (html.length > MAX_DOCUMENT_CHARS) problems.push(`document is ${html.length} characters, limit ${MAX_DOCUMENT_CHARS}`);
  for (const match of html.matchAll(/\b(?:src|href)\s*=\s*["']?((?:https?:)?\/\/[^"'\s>]+)/gi)) problems.push(`external resource: ${match[1]}`);
  if (/\bfetch\s*\(|XMLHttpRequest|WebSocket|navigator\.sendBeacon|\bimport\s*\(/.test(html)) problems.push("network call in script");
  if (/<meta[^>]+http-equiv\s*=\s*["']?refresh/i.test(html)) problems.push("meta refresh");
  return problems;
}
