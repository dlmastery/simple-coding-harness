// Server-sent events, the reading side. fetch() gives a byte stream; this
// turns it into JSON events. One event is the `data:` lines up to a blank
// line. AG-UI puts one whole JSON event on each data line.

export async function* readEvents(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n"); // the spec allows either ending
    let cut;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const event = parseBlock(block);
      if (event) yield event;
    }
  }
  const last = parseBlock(buffer);
  if (last) yield last;
}

export function parseBlock(block) {
  const data = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart());
  return data.length ? JSON.parse(data.join("\n")) : null;
}
