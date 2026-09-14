// Step 04 - the box the artifact document runs in.
//
// The OpenUI example mounts the model's document with
// `<iframe sandbox="allow-scripts" referrerpolicy="no-referrer" srcdoc=...>`
// and stops there. This file adds what its README lists as "before
// production": a Content Security Policy injected into the document, a
// validation pass over the document, and one accepted message shape.

// No network at all: no scripts, styles, fonts or images from a URL, no
// fetch, no WebSocket. Inline style and script stay allowed because that is
// what the prompt tells the model to write. Images may be data: URIs.
export const CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:";

export const META = `<meta http-equiv="Content-Security-Policy" content="${CSP}">`;

const CSP_META_RE = /<meta[^>]+http-equiv\s*=\s*["']?content-security-policy["']?[^>]*>/gi;

// Return the document with our CSP as the first thing in <head>. A CSP meta
// tag applies only to what comes after it, so it has to be first; and any
// CSP the model wrote itself is removed, so the document cannot loosen ours.
export function sandboxed(html) {
  const cleaned = html.replace(CSP_META_RE, "");
  const head = /<head[^>]*>/i.exec(cleaned);
  if (head) return cleaned.slice(0, head.index + head[0].length) + META + cleaned.slice(head.index + head[0].length);
  return META + cleaned;
}

export const MAX_DOCUMENT_CHARS = 200_000;

// A validation pass over the document. It returns a list of findings; the
// page shows them next to the artifact. The CSP already blocks every one of
// them, so this is for the reader and the logs, not the only line of defence.
export function checkDocument(html) {
  const problems = [];
  if (html.length > MAX_DOCUMENT_CHARS) problems.push(`document is ${html.length} characters, limit ${MAX_DOCUMENT_CHARS}`);
  for (const match of html.matchAll(/\b(?:src|href)\s*=\s*["']?((?:https?:)?\/\/[^"'\s>]+)/gi)) problems.push(`external resource: ${match[1]}`);
  if (/\bfetch\s*\(|XMLHttpRequest|WebSocket|navigator\.sendBeacon|\bimport\s*\(/.test(html)) problems.push("network call in script");
  if (/<meta[^>]+http-equiv\s*=\s*["']?refresh/i.test(html)) problems.push("meta refresh");
  return problems;
}

// The only shape the host accepts from the iframe: {type: "event", name, payload?}.
// Anything else posted by the document is dropped before it reaches the app.
export function isEvent(data) {
  return data !== null && typeof data === "object" && data.type === "event" && typeof data.name === "string";
}
