// Step 03 - the inner boundary: the box the model-written region runs in.
//
// The app itself already runs in the host's sandboxed iframe under the
// policy the resource declared (step 01). The generated region goes one
// level deeper: a nested iframe with `sandbox="allow-scripts"` and nothing
// else, and this CSP injected first in its head. A srcdoc frame inherits
// the app's policy too, so both apply; this one is the stricter of the two.
// No 'self', no frames, no connections: inline style and script only.

export const CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:";

export const META = `<meta http-equiv="Content-Security-Policy" content="${CSP}">`;

const REFRESH_META_RE = /<meta[^>]+http-equiv\s*=\s*["']?refresh["']?[^>]*>/gi;

export function sandboxed(html) {
  // The CSP meta tag right after the doctype, before any element: a script written before <head>,
  // or a <head> inside a comment, would otherwise run ahead of the policy. A meta refresh is a
  // navigation the policy cannot block, so it is removed.
  const cleaned = html.replace(REFRESH_META_RE, "");
  const doctype = /^\s*<!doctype[^>]*>/i.exec(cleaned);
  const at = doctype ? doctype[0].length : 0;
  return cleaned.slice(0, at) + META + cleaned.slice(at);
}

export function mount(iframe, html) {
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.srcdoc = sandboxed(html);
}

export function isEvent(data) {
  // The only shape the app accepts from the inner frame: {type: "event", name, payload?}.
  return data !== null && typeof data === "object" && data.type === "event" && typeof data.name === "string";
}
