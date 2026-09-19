// Step 03 - the box the model's HTML runs in.
// The iframe gets `sandbox="allow-scripts"` and nothing else: a unique origin,
// no forms, no popups, no navigation of the host. The CSP below is injected
// into the document itself, so inline code cannot fetch, connect or load
// anything. What CSP does not cover is navigating the iframe itself (a link,
// location.href): the unique origin is the guarantee, not silence.

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
