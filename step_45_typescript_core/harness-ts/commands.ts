/** Step 45 - the slash commands: /rewind, /sessions, /compact.
 */

import * as compaction from "./compact.ts";
import * as sandbox from "./sandbox.ts";
import * as session from "./session.ts";
import type { Message } from "./types.ts";
import { ui } from "./ui.ts";

export const COMMANDS: Record<string, string> = {
  "/rewind": "jump back to an earlier point in this chat",
  "/sessions": "open a past chat",
  "/compact": "summarise the history so far and free up the context window",
};

export function preview(message: Message): string {
  if (message.tool_calls?.length) {
    return "-> " + message.tool_calls[0].function.name;
  }
  return String(message.content ?? "").split(/\s+/).join(" ").trim().slice(0, 70);
}

/** The screen no longer matches the history, so wipe it and draw again. */
export function redraw(messages: Message[], label: string): Message[] {
  ui.clear();
  ui.banner(sandbox.name());
  ui.resumed(messages, label);
  ui.replay(messages);
  return messages;
}

export async function rewind(messages: Message[]): Promise<Message[]> {
  const rows = messages.map((m) => `${m.role.padEnd(9)} ${preview(m)}`);
  const choice = await ui.pick("rewind to", rows);
  if (choice === null) return messages;
  session.rewindTo(choice + 1);
  return redraw(messages.slice(0, choice + 1), "rewound");
}

export async function sessions(messages: Message[]): Promise<Message[]> {
  const saved = session.allSessions();
  if (!saved.length) {
    ui.note("no saved chats yet");
    return messages;
  }
  const rows = saved.map((s) => `${s.id}  ${s.title}`);
  const choice = await ui.pick("open chat", rows);
  if (choice === null) return messages;
  return redraw(session.openSession(saved[choice].id), "opened");
}

export async function compact(messages: Message[]): Promise<Message[]> {
  const before = messages.length;
  let compacted: Message[];
  const done = ui.working("compacting");
  try {
    compacted = await compaction.compact(messages);
  } catch (failure) {
    // One more API call, fired when the window is nearly full - the worst
    // moment to lose the session over a rate limit. Keep going as we are.
    ui.note(`compaction failed (${(failure as Error)?.constructor?.name ?? "Error"}); transcript kept as is`);
    return messages;
  } finally {
    done();
  }
  if (compacted.length === before) {
    ui.note("nothing old enough to compact yet");
    return messages;
  }
  session.compacted(compacted);
  ui.compacted(before, compacted);
  return compacted;
}

export async function handle(command: string, messages: Message[]): Promise<Message[]> {
  if (command === "/compact") return compact(messages);
  if (command === "/rewind") return rewind(messages);
  if (command === "/sessions") return sessions(messages);
  ui.note(Object.entries(COMMANDS).map(([name, help]) => `${name}  -  ${help}`).join("\n"));
  return messages;
}
