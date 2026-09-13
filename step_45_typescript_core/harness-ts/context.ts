/** Step 45 - context: the late injection appended to every request.
 *
 * The same three parts as harness/context.py: the environment block, the
 * todo list, and the files git has seen change since the previous call.
 */

import { spawnSync } from "node:child_process";

import { todosPrompt } from "./todos.ts";
import type { Message } from "./types.ts";

export const LABELS: Record<string, string> = { M: "modified", D: "deleted", A: "added", "??": "new" };

export function git(command: string): string {
  const result = spawnSync(`git ${command}`, { shell: true, encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] });
  return result.stdout ?? "";
}

/** path -> status code, straight from git. */
export function gitStatus(): Record<string, string> {
  const status: Record<string, string> = {};
  for (const line of git("status --porcelain").split(/\r?\n/)) {
    if (line) status[line.slice(3)] = line.slice(0, 2).trim();
  }
  return status;
}

export let LAST_STATUS = gitStatus();

/** What git sees as different since the previous call. */
export function fileChanges(): Record<string, string> {
  const now = gitStatus();
  const changed: Record<string, string> = {};
  for (const [path, code] of Object.entries(now)) {
    if (LAST_STATUS[path] !== code) changed[path] = code;
  }
  LAST_STATUS = now;
  return changed;
}

export function changesNote(): string {
  const changed = fileChanges();
  const lines = Object.entries(changed).map(([path, code]) => `${LABELS[code] ?? code}: ${path}`);
  if (!lines.length) return "";
  return (
    "\n<system-reminder>\n" +
    "These files changed since your last turn. Read them again before " +
    "editing:\n" + lines.join("\n") + "\n</system-reminder>"
  );
}

export function todosNote(): string {
  const plan = todosPrompt();
  return plan ? `\n<todos>\n${plan}\n</todos>` : "";
}

function now(): string {
  const two = (n: number) => String(n).padStart(2, "0");
  const d = new Date();
  return `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())} ${two(d.getHours())}:${two(d.getMinutes())}`;
}

/** The block we append to the request on every call. */
export function reminder(): Message & { content: string } {
  return {
    role: "user",
    content:
      "<env>\n" +
      `time: ${now()}\n` +
      `git branch: ${git("branch --show-current").trim() || "(detached)"}\n` +
      "</env>" + todosNote() + changesNote(),
  };
}
