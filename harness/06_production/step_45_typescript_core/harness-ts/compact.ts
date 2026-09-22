/** Step 45 - the compaction agent.
 *
 * When the prompt reaches 85% of the context window, the harness cuts it back
 * to 35%. It does not drop the oldest messages, because that would break the
 * KV cache. Instead it compacts: a summary of everything that happened in the
 * session replaces the messages about to be deleted.
 *
 * A second agent with one job and no tools writes that handoff note. The note
 * is folded into the system prompt. The transcript then has to fill from 35%
 * back to 85% before the next compaction, so the system prompt stays the same
 * in between and the cached prefix survives.
 */

import * as config from "./config.ts";
import { SUMMARY, estimate, strip } from "./history.ts";
import * as llm from "./llm.ts";
import type { Message, Usage } from "./types.ts";

export const SYSTEM_PROMPT = `
You are compacting the transcript of a coding session. The session is out of
context window. Write the handoff note that lets a fresh agent pick the work up
without re-reading anything.

Use these sections, in this order. Skip any that would be empty.

## Goal
What the user asked for. Quote them where the exact wording matters.

## What happened
Decisions taken and the reasoning behind them. Include approaches that were
tried and abandoned, and why - those are the expensive lessons, and an agent
without them will try the same dead end again.

## Files
Every file touched: path, and what changed in it.

## State
What works, what is broken, what was left half-finished.

## Next
The immediate next step.

Rules:
- Be specific. Real paths, function names, error text, exact commands.
- Keep anything the user explicitly asked for, corrected, or rejected.
- Never invent progress. If something was not finished, say it was not.
- No preamble and no sign-off. Start at the first heading.
`;

export const HANDOFF = SUMMARY + `
Everything before this point has been compacted out of the context window to
free up room. This is the record of it - treat it as your own memory of the
work so far, not as something the user told you.

{summary}
</summary>`;

export const SUMMARY_BLOCK = /\n*<summary>[\s\S]*?<\/summary>/g;
export const ROLES: Record<string, string> = { user: "USER", assistant: "ASSISTANT", tool: "TOOL RESULT" };

/** Has the last request grown past the point where we rebuild? */
export function needed(usage: Usage): boolean {
  return (usage.prompt_tokens ?? 0) > config.CONTEXT_WINDOW * config.COMPACT_AT;
}

/** The handoff note a previous compaction left in the system prompt, if any. */
export function previousSummary(systemContent: string): string {
  const match = systemContent.match(SUMMARY_BLOCK);
  return match ? match[0].trim() : "";
}

/** The system prompt without any earlier handoff note. */
export function basePrompt(systemContent: string): string {
  return systemContent.replace(SUMMARY_BLOCK, "").trimEnd();
}

/** Flatten the transcript into something the summariser can read. */
export function render(messages: Message[], previous = ""): string {
  const lines: string[] = [];
  if (previous) {
    lines.push(`PREVIOUS HANDOFF NOTE (carry forward what still matters):\n${previous}`);
  }
  for (const message of messages) {
    if (message.role === "system") continue;
    let content = message.content ?? "";
    for (const call of message.tool_calls ?? []) {
      content += `\n[called ${call.function.name}: ${call.function.arguments}]`;
    }
    lines.push(`${ROLES[message.role] ?? message.role}: ${content}`);
  }
  return lines.join("\n\n");
}

/** One model call, no tools. Returns the handoff note. */
export async function summarize(messages: Message[], previous = ""): Promise<string> {
  const { message } = await llm.callLlm(
    [{ role: "system", content: SYSTEM_PROMPT }, { role: "user", content: render(messages, previous) }],
    [],
  );
  return message.content || "(the summariser returned nothing)";
}

/** First index at or after `start` where cutting cannot orphan a tool call.
 *
 * A tool result has to keep the assistant message that asked for it, so the
 * only safe cut points are the messages that open a fresh exchange.
 */
export function safeBoundary(messages: Message[], start: number): number {
  for (let index = Math.max(start, 1); index < messages.length; index++) {
    const previous = messages[index - 1];
    if (messages[index].role === "tool" || previous.tool_calls?.length) continue;
    return index;
  }
  return messages.length;
}

/** Walk back from the end, taking messages until the tail fills `budget`. */
export function tailStart(messages: Message[], budget: number): number {
  let total = 0;
  for (let index = messages.length - 1; index > 0; index--) {
    total += estimate([messages[index]]);
    if (total > budget) return safeBoundary(messages, index);
  }
  return safeBoundary(messages, 1);
}

/** [system + summary, ...recent tail]. Unchanged if nothing is old enough. */
export async function compact(messages: Message[], budget: number = config.CONTEXT_WINDOW * config.COMPACT_TO): Promise<Message[]> {
  const cut = tailStart(messages, budget);
  if (cut <= 1) return messages;

  const system = messages[0].content ?? "";
  const summary = await summarize(messages.slice(1, cut), previousSummary(system));
  const kept: Message[] = [
    { role: "system", content: basePrompt(system) + "\n\n" + HANDOFF.replace("{summary}", () => summary) },
    ...messages.slice(cut),
  ];
  strip(kept); // the tail is old news too; shrink it now, while the prefix is already rebuilt
  return kept;
}
