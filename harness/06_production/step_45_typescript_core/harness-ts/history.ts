/** Step 45 - keeping the transcript small enough to send.
 *
 * Tool call output is the main reason a transcript explodes. Three
 * mechanisms, cheapest first. Only the first two live here; the expensive one
 * (the compaction agent) is compact.ts.
 *
 * 1. cap    a fresh tool result is trimmed at 10,000 characters and the full
 *           text parked in a temp file the agent can page through with head,
 *           tail, sed or grep. The file lives only until the turn ends; then
 *           it is deleted.
 * 2. strip  once a turn is over, its tool results shrink to a stub. Strip
 *           touches past turns only. The edit lands at the tail, so the
 *           cached prefix in front of it survives.
 * 3. fit    a single request is still too big: throw tool results away whole,
 *           oldest first, until it fits. The panic button.
 */

import { randomBytes } from "node:crypto";
import { rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import * as config from "./config.ts";
import type { Message } from "./types.ts";

export const CAP = 10_000; // chars of a fresh tool result the agent sees inline
export const STUB = 300; // chars kept once the turn that produced it is over

export const TRIMMED = "[output trimmed:"; // marker, so stripping twice is a no-op
export const SUMMARY = "<summary>"; // marks the handoff note compaction leaves in the system prompt
export const SPILLS: string[] = []; // temp files belonging to the current turn

// --- 1. cap ------------------------------------------------------------------

/** Park the full output on disk for the rest of this turn. */
export function spill(text: string): string {
  const path = join(tmpdir(), `harness-${randomBytes(6).toString("hex")}.txt`);
  writeFileSync(path, text, "utf-8");
  SPILLS.push(path);
  return path;
}

/** Trim a fresh tool result, leaving a pointer to the whole thing. */
export function cap(text: string): string {
  if (text.length <= CAP) return text;
  let path: string;
  try {
    path = spill(text);
  } catch {
    return text.slice(0, CAP) + `\n\n${TRIMMED} ${text.length - CAP} chars cut and could not be saved.]`;
  }
  return (
    text.slice(0, CAP) +
    `\n\n${TRIMMED} ${text.length - CAP} of ${text.length} chars cut. ` +
    `The whole output is at ${path} - page through it with head, tail, ` +
    "sed -n or grep. It is deleted when this turn ends.]"
  );
}

/** Delete this turn's temp files. Their paths die with the tool results. */
export function sweep(): void {
  for (const path of SPILLS) {
    rmSync(path, { force: true });
  }
  SPILLS.length = 0;
}

// --- 2. strip ----------------------------------------------------------------

/** Shrink every tool result from finished turns. Returns how many shrank.
 *
 * Called after a turn ends, so "everything in the list" and "everything the
 * model no longer needs in full" are the same set.
 */
export function strip(messages: Message[]): number {
  let shrunk = 0;
  for (const message of messages) {
    const content = message.content ?? "";
    if (message.role !== "tool" || content.includes(TRIMMED) || content.length <= STUB) {
      continue;
    }
    message.content =
      content.slice(0, STUB) +
      `\n\n${TRIMMED} ${content.length - STUB} more chars. ` +
      "Run the command again if you need them.]";
    shrunk += 1;
  }
  return shrunk;
}

// --- 3. fit ------------------------------------------------------------------

/** Rough token count - good enough to decide whether to panic. */
export function estimate(messages: Message[]): number {
  return Math.floor(messages.reduce((total, m) => total + JSON.stringify(m).length, 0) / 4);
}

/** Last resort: discard whole tool results, oldest first, until it fits. */
export function fit(messages: Message[], budget: number = config.CONTEXT_WINDOW * config.COMPACT_AT): number {
  let dropped = 0;
  for (const message of messages) {
    if (estimate(messages) <= budget) break;
    if (message.role === "tool" && !(message.content ?? "").includes(TRIMMED)) {
      message.content = `${TRIMMED} dropped to fit the context window.]`;
      dropped += 1;
    }
  }
  return dropped;
}
