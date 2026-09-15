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

export function sandboxed(html) {
  // Put the CSP meta tag first in <head>, or first in the document if there is no <head>.
  const head = /<head[^>]*>/i.exec(html);
  if (head) return html.slice(0, head.index + head[0].length) + META + html.slice(head.index + head[0].length);
  return META + html;
}

export function mount(iframe, html) {
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.srcdoc = sandboxed(html);
}

export function isEvent(data) {
  // The only shape the app accepts from the inner frame: {type: "event", name, payload?}.
  return data !== null && typeof data === "object" && data.type === "event" && typeof data.name === "string";
}
