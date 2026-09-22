/** Step 45 - session: the same JSONL log as harness/session.py.
 *
 * One JSON object per line. A message entry has a role. A rewind is
 * {"rewind_to": n}; a compaction is {"compacted": [...]}. The directory is
 * ~/.simple-harness/sessions/<project>/, where <project> is the working
 * directory with every non-alphanumeric character turned into a dash - the
 * same name the Python harness computes, so both find the same files.
 *
 * The Python module keeps CURRENT and WRITTEN as module globals. ES modules
 * do not let an importer assign to an export, so the same two values live
 * on one exported state object here.
 */

import { appendFileSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join, resolve } from "node:path";

import type { Message } from "./types.ts";

export const PROJECT = [...resolve(process.cwd())].map((c) => (/^[\p{L}\p{N}]$/u.test(c) ? c : "-")).join("");
export const SESSION_DIR = join(homedir(), ".simple-harness", "sessions", PROJECT);

function stamp(now = new Date()): string {
  const two = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}${two(now.getMonth() + 1)}${two(now.getDate())}-${two(now.getHours())}${two(now.getMinutes())}${two(now.getSeconds())}`;
}

export const state = {
  dir: SESSION_DIR,
  current: stamp(),
  written: 0, // how many messages are already on disk
};

export function pathFor(sessionId: string): string {
  return join(state.dir, `${sessionId}.jsonl`);
}

function append(entry: unknown): void {
  mkdirSync(state.dir, { recursive: true });
  appendFileSync(pathFor(state.current), JSON.stringify(entry) + "\n", "utf-8");
}

/** Append what is new. Never rewrite what is already on disk. */
export function save(messages: Message[]): void {
  for (const message of messages.slice(state.written)) {
    append(message);
  }
  state.written = messages.length;
}

/** Record a rewind as an entry, so the old messages stay in the file. */
export function rewindTo(count: number): void {
  append({ rewind_to: count });
  state.written = count;
}

/** Compaction rewrites history, so record the result and start from it. */
export function compacted(messages: Message[]): void {
  append({ compacted: messages });
  state.written = messages.length;
}

/** Replay the log: messages accumulate, rewinds cut them back, a compaction replaces them. */
export function load(sessionId: string): Message[] {
  let messages: Message[] = [];
  for (const line of readFileSync(pathFor(sessionId), "utf-8").split(/\r?\n/)) {
    let entry: Record<string, unknown>;
    try {
      entry = JSON.parse(line);
    } catch {
      continue; // a blank line, or a half-written last line from a kill mid-save
    }
    // Step 44 of the Python harness stamps every entry with `ts` and adds
    // {"usage": ...} entries after each model call. The model never saw
    // either, so they come off here, and a Python log of any step loads.
    delete entry.ts;
    if ("usage" in entry) {
      continue;
    }
    if ("rewind_to" in entry) {
      messages.splice(entry.rewind_to as number);
    } else if ("compacted" in entry) {
      messages = [...(entry.compacted as Message[])];
    } else if ("role" in entry) {
      messages.push(entry as Message);
    }
    // Any other marker (a handoff from step 40) is outside the stage 15 feature set and is skipped.
  }
  return messages;
}

/** Switch to a past chat and become it. */
export function openSession(sessionId: string): Message[] {
  state.current = sessionId;
  const messages = load(sessionId);
  state.written = messages.length;
  return messages;
}

export function title(messages: Message[]): string {
  for (const message of messages) {
    if (message.role === "user") {
      return String(message.content ?? "").split(/\s+/).join(" ").trim().slice(0, 60);
    }
  }
  return "(empty)";
}

/** Newest first. */
export function allSessions(): { id: string; title: string }[] {
  if (!existsSync(state.dir)) return [];
  const files = readdirSync(state.dir)
    .filter((f) => f.endsWith(".jsonl"))
    .map((f) => join(state.dir, f))
    .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
  return files.map((p) => {
    const id = basename(p, ".jsonl");
    return { id, title: title(load(id)) };
  });
}
