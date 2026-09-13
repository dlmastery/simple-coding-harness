/** Step 45 - which tool calls need a human.
 *
 * An allow list names the commands the agent may run on its own: ls, pwd,
 * echo and other read-only commands it uses to gather information. Every
 * other command stops and asks the user. If the user approves, the tool call
 * runs.
 *
 * A third verdict, deny, covers the handful of commands no answer at the
 * prompt should unlock: rm, sudo, chmod, chown, curl and the like. The last
 * matching rule wins, so the catch-all goes first. The rules are the ones in
 * harness/permissions.py, in the same order.
 */

import { resolve, sep } from "node:path";

import type { Action, Args } from "./types.ts";

export let PROJECT = resolve(process.cwd());

/** The tests point the fence at a temp directory. */
export function setProject(path: string): void {
  PROJECT = resolve(path);
}

export const BASH_RULES: [string, Action][] = [
  ["*", "ask"],
  // read-only: let them through
  ["ls*", "allow"], ["pwd", "allow"], ["cd *", "allow"], ["echo *", "allow"],
  ["sort*", "allow"], ["uniq*", "allow"], ["cut *", "allow"], ["basename *", "allow"], ["dirname *", "allow"],
  ["date*", "allow"], ["env", "allow"], ["cat *", "allow"], ["head *", "allow"], ["tail *", "allow"],
  ["wc *", "allow"], ["file *", "allow"], ["which *", "allow"], ["grep *", "allow"], ["rg *", "allow"],
  ["find *", "allow"], ["tree*", "allow"],
  ["git status*", "allow"], ["git diff*", "allow"], ["git log*", "allow"], ["git show*", "allow"], ["git ls-files*", "allow"],
  ["pytest*", "allow"], ["python -m pytest*", "allow"],
  // risky: never, even if the user says yes
  ["rm *", "deny"], ["sudo *", "deny"], ["chmod *", "deny"], ["chown *", "deny"],
  ["curl *", "deny"], ["wget *", "deny"],
  ["git push*", "deny"], ["git reset*", "deny"], ["git clean*", "deny"],
];

/** Python's fnmatch: * ? [seq] [!seq], the rest literal. Case folds on Windows, as fnmatch does there. */
export function fnmatch(text: string, pattern: string): boolean {
  let source = "";
  for (let i = 0; i < pattern.length; i++) {
    const ch = pattern[i];
    if (ch === "*") {
      source += ".*";
    } else if (ch === "?") {
      source += ".";
    } else if (ch === "[") {
      const close = pattern.indexOf("]", i + 2);
      if (close === -1) {
        source += "\\[";
      } else {
        let inner = pattern.slice(i + 1, close).replace(/\\/g, "\\\\");
        if (inner.startsWith("!")) inner = "^" + inner.slice(1);
        source += `[${inner}]`;
        i = close;
      }
    } else {
      source += ch.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
    }
  }
  const flags = process.platform === "win32" ? "si" : "s";
  return new RegExp(`^${source}$`, flags).test(text);
}

/** Split a compound command on |, ||, ;, &, && - but not inside quotes. */
export function splitCommand(command: string): string[] {
  const parts: string[] = [];
  let current: string[] = [];
  let quote: string | null = null;
  let i = 0;
  while (i < command.length) {
    const ch = command[i];
    if (quote) {
      current.push(ch);
      quote = ch === quote ? null : quote;
    } else if (ch === "\\" && i + 1 < command.length) {
      current.push(ch, command[i + 1]);
      i += 1;
    } else if (ch === '"' || ch === "'") {
      quote = ch;
      current.push(ch);
    } else if ("&|;".includes(ch)) {
      parts.push(current.join(""));
      current = [];
      while (i + 1 < command.length && "&|".includes(command[i + 1])) {
        i += 1;
      }
    } else {
      current.push(ch);
    }
    i += 1;
  }
  parts.push(current.join(""));
  return parts.map((p) => p.trim()).filter((p) => p);
}

/** Rate every part of a compound command; the strictest verdict wins. */
export function decide(command: string): Action {
  const verdicts: Action[] = [];
  for (const part of splitCommand(command)) {
    let action: Action = "ask";
    for (const [pattern, rule] of BASH_RULES) {
      if (fnmatch(part, pattern)) action = rule;
    }
    verdicts.push(action);
  }
  for (const strictest of ["deny", "ask"] as const) {
    if (verdicts.includes(strictest)) return strictest;
  }
  return "allow";
}

export function insideProject(path: string): boolean {
  // Windows paths compare without case, the way Path.resolve() compares them.
  const fold = (p: string) => (process.platform === "win32" ? p.toLowerCase() : p);
  const resolved = fold(resolve(path));
  const project = fold(PROJECT);
  return resolved === project || resolved.startsWith(project + sep);
}

/** Return [action, reason]. Action is allow, ask or deny. */
export function check(name: string, args: Args): [Action, string | null] {
  if (name === "bash") {
    return [decide(args.command), `run: ${args.command}`];
  }
  if ((name === "write_file" || name === "str_replace") && !insideProject(args.path)) {
    return ["ask", `${name} outside ${PROJECT}: ${args.path}`];
  }
  return ["allow", null];
}
