// A small AG-UI client: POST a RunAgentInput, read the SSE body, hand each
// event to a handler by its `type`. No DOM in here, so node --test covers it.

// Split an SSE buffer into complete frames; the remainder is kept for the next read.
// CRLF endings are folded to LF first; a frame with no data line (an SSE
// comment, which the server uses as a keepalive) yields nothing.
export function parseSse(buffer) {
  const events = [];
  buffer = buffer.replaceAll('\r\n', '\n');
  let end;
  while ((end = buffer.indexOf('\n\n')) >= 0) {
    const frame = buffer.slice(0, end);
    buffer = buffer.slice(end + 2);
    const data = frame.split('\n').filter((l) => l.startsWith('data: ')).map((l) => l.slice(6)).join('\n');
    if (data) events.push(JSON.parse(data));
  }
  return { events, rest: buffer };
}

let counter = 0;
export function newId(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${(counter++).toString(36)}`;
}

// The input AG-UI expects: thread, run, the chat so far, and forwardedProps for
// anything the transport must carry as metadata (A2UI actions and data models).
export function runAgentInput({ threadId, messages, forwardedProps = {} }) {
  return { threadId, runId: newId('run'), state: {}, messages, tools: [], context: [], forwardedProps };
}

// Resolves when the stream ends; rejects on a non-2xx answer (a 422 for a bad
// body has no frames, so the status and body are the only explanation).
export async function runAgent(url, input, onEvent, fetchImpl = fetch) {
  const response = await fetchImpl(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(input) });
  if (response.ok === false) throw new Error(`${response.status} ${await response.text()}`);
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let rest = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const parsed = parseSse(rest + value);
    rest = parsed.rest;
    for (const event of parsed.events) onEvent(event);
  }
}
