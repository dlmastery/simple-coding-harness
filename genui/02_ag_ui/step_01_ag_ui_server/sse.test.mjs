import { test } from "node:test";
import assert from "node:assert/strict";
import { parseBlock, readEvents } from "./sse.mjs";

function responseFrom(chunks) {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  return new Response(body);
}

test("parseBlock reads one data line", () => {
  assert.deepEqual(parseBlock('data: {"type":"RUN_STARTED","runId":"r1"}'), { type: "RUN_STARTED", runId: "r1" });
  assert.equal(parseBlock(": a comment"), null);
});

test("readEvents joins chunks that split an event", async () => {
  const wire =
    'data: {"type":"TEXT_MESSAGE_START","messageId":"m"}\n\n' +
    'data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"m","delta":"hi"}\n\n';
  const events = [];
  for await (const event of readEvents(responseFrom([wire.slice(0, 20), wire.slice(20, 70), wire.slice(70)]))) {
    events.push(event.type);
  }
  assert.deepEqual(events, ["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT"]);
});
