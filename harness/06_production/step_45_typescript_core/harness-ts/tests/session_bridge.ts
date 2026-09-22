/** Step 45 - the other side of the cross-language session test.
 *
 * test_step.py runs this script with node:
 *
 *   session_bridge.ts write <dir> <id>   writes a small session with the TypeScript session module
 *   session_bridge.ts load  <dir> <id>   loads one and prints the messages as JSON
 *
 * The Python test then loads what "write" produced with harness.session.load,
 * and compares what "load" printed with what Python wrote.
 */

import * as session from "../session.ts";
import type { Message } from "../types.ts";

const [mode, dir, id] = process.argv.slice(2);
session.state.dir = dir;
session.state.current = id;
session.state.written = 0;

if (mode === "write") {
  const messages = [
    { role: "system", content: "You are a coding agent." },
    { role: "user", content: "list the files" },
    { role: "assistant", tool_calls: [{ id: "call_1", type: "function", function: { name: "bash", arguments: '{"command":"ls"}' } }] },
    { role: "tool", tool_call_id: "call_1", content: "README.md\nharness\n" },
    { role: "assistant", content: "Two entries: README.md and harness/." },
  ] as Message[];
  session.save(messages);
  session.rewindTo(2);
  session.save([...messages.slice(0, 2), { role: "assistant", content: "héllo from TypeScript" }]);
} else if (mode === "load") {
  process.stdout.write(JSON.stringify(session.load(id)));
} else {
  console.error("usage: session_bridge.ts write|load <dir> <id>");
  process.exit(2);
}
