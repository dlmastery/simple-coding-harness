/** Step 45 - the screen, in plain console output.
 *
 * The Python harness draws with rich: panels, rules, a spinner, markdown.
 * This port keeps the same method names and the same information on screen,
 * with ANSI colours when stdout is a terminal and plain text when it is not.
 * No dependencies. Reading input goes through node:readline, so ask(),
 * approve() and pick() return promises.
 */

import { createInterface } from "node:readline";

import { MARKS } from "./todos.ts";
import type { Args, Message, Todo, ToolCall, Usage } from "./types.ts";

const TTY = process.stdout.isTTY === true;

export const ACCENT = "34"; // blue
export const USER = "32"; // green
export const TOOL = "33"; // yellow
export const MUTED = "90"; // grey
const BOLD = "1";

export const MAX_TOOL_OUTPUT_LINES = 12;

function paint(text: string, ...codes: string[]): string {
  return TTY ? `\x1b[${codes.join(";")}m${text}\x1b[0m` : text;
}

function indent(text: string, columns = 2): string {
  const pad = " ".repeat(columns);
  return text.split("\n").map((line) => pad + line).join("\n");
}

function box(lines: string[], columns = 2): string {
  const width = Math.min(Math.max(...lines.map((l) => l.length), 10), 100);
  const bar = "─".repeat(width + 2);
  const clip = (l: string) => (l.length > width ? l.slice(0, width - 1) + "…" : l);
  const body = lines.map((l) => `│ ${clip(l).padEnd(width)} │`);
  return indent([`┌${bar}┐`, ...body, `└${bar}┘`].join("\n"), columns);
}

export class UI {
  totals: Record<string, number> = {};

  /** One line from the keyboard, or null on end of file / ctrl-c. */
  read(promptText: string): Promise<string | null> {
    return new Promise((resolve) => {
      const rl = createInterface({ input: process.stdin, output: process.stdout });
      let answered = false;
      rl.question(promptText, (answer) => {
        answered = true;
        rl.close();
        resolve(answer);
      });
      rl.on("SIGINT", () => rl.close());
      rl.on("close", () => {
        if (!answered) resolve(null);
      });
    });
  }

  // ---------------------------------------------------------------- input

  banner(sandboxName = "none"): void {
    console.log();
    console.log(paint("── coding agent ", BOLD, ACCENT) + paint("─".repeat(40), MUTED));
    console.log(indent(paint(`sandbox: ${sandboxName}  ·  /sessions  /rewind  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave`, MUTED)));
  }

  clear(): void {
    console.clear();
  }

  resumed(messages: Message[], label = "resumed"): void {
    const turns = messages.filter((m) => m.role === "user").length;
    console.log(indent(paint(`${label} · ${messages.length} messages · ${turns} turns`, MUTED)));
  }

  /** The arguments of a logged call, for drawing: broken JSON is shown as it is, never parsed twice. */
  static argsOf(call: ToolCall): Args {
    try {
      const args = JSON.parse(call.function.arguments || "{}");
      if (typeof args === "object" && args !== null && !Array.isArray(args)) return args;
    } catch {
      // fall through: the raw string is the best picture of what the model sent
    }
    return { raw: call.function.arguments };
  }

  /** Redraw a loaded transcript so the screen matches the history. */
  replay(messages: Message[]): void {
    const results: Record<string, string> = {};
    for (const m of messages) {
      if (m.role === "tool" && m.tool_call_id) results[m.tool_call_id] = m.content ?? "";
    }
    for (const message of messages) {
      if (message.role === "user") {
        this.user(message.content ?? "");
      } else if (message.role === "assistant") {
        if (message.content) this.agent(message.content);
        for (const call of message.tool_calls ?? []) {
          this.tool(call.function.name, UI.argsOf(call), results[call.id] ?? "");
        }
      }
    }
  }

  /** Numbered list; returns the chosen index or null. */
  async pick(title: string, rows: string[]): Promise<number | null> {
    console.log();
    console.log(indent(paint(title, BOLD, ACCENT)));
    rows.forEach((row, i) => console.log(indent(paint(`${String(i).padStart(3)}  ${row}`, MUTED))));
    const answer = (await this.read("  number> "))?.trim();
    if (answer === undefined || !/^\d+$/.test(answer)) return null;
    const index = Number(answer);
    return index < rows.length ? index : null;
  }

  /** Stop and ask before a tool call the rules rate as 'ask'. */
  async approve(reason: string | null): Promise<boolean> {
    console.log();
    console.log(indent(paint(reason ?? "", BOLD, TOOL)));
    const answer = await this.read("  allow? (y/n)> ");
    return answer !== null && answer.trim().toLowerCase().startsWith("y");
  }

  /** The next line from the user: "" for an empty line, null when they want out (ctrl-d, ctrl-c). */
  async ask(): Promise<string | null> {
    console.log();
    const answer = await this.read("> ");
    if (answer === null) {
      console.log();
      return null;
    }
    return answer.trim();
  }

  // --------------------------------------------------------------- output

  user(text: string): void {
    console.log();
    console.log(indent(paint(text.trim(), BOLD, USER)));
  }

  agent(text: string): void {
    console.log();
    console.log(indent(paint("agent", BOLD, ACCENT)));
    console.log();
    console.log(indent(text.trim()));
  }

  tool(name: string, args: Args, result: string, nested = false): void {
    if (name === "write_todos" && Array.isArray(args.todos) && !result.startsWith("Error")) {
      this.todos(args.todos); // a list the tool accepted is drawn as the checklist; a refused one shows the error
      return;
    }
    const header = `${name} ${this.formatArgs(args)}`;
    console.log();
    console.log(box([header, "", ...this.formatResult(result)], nested ? 6 : 2));
  }

  /** Shown to you, never to the main agent - it only gets the report. */
  subagent(description: string): void {
    console.log();
    console.log(box(["subagent · own context", "", ...description.trim().split("\n")], 4));
  }

  /** The plan as a checklist. The raw tool output is never worth showing. */
  todos(todos: Todo[]): void {
    const done = todos.filter((t) => t.status === "completed").length;
    const rows = todos.map((t) => `${MARKS[t.status] ?? "[?]"} ${t.content}`);
    console.log();
    console.log(box([`todos ${done}/${todos.length}`, "", ...rows]));
  }

  /** Show the handoff note compaction folded into the system prompt. */
  compacted(before: number, messages: Message[]): void {
    const system = messages[0].content ?? "";
    const body = system.slice(system.indexOf("<summary>")).replace("<summary>", "").replace("</summary>", "");
    console.log();
    console.log(box([`compacted · ${before} → ${messages.length} messages`, "", ...body.trim().split("\n")]));
  }

  note(text: string): void {
    console.log();
    console.log(indent(paint(text, MUTED)));
  }

  /** The late block, dimmed, so you can see what the model sees. */
  injection(text: string): void {
    console.log();
    console.log(paint(box(["late injection", "", ...text.trim().split("\n")]), MUTED));
  }

  debug(data: unknown): void {
    console.log();
    console.log(box(["raw response", "", ...JSON.stringify(data, null, 2).split("\n")]));
  }

  /** Show what the agent is doing; call the returned function when it is done. */
  working(label = "thinking"): () => void {
    if (!TTY) return () => {};
    process.stdout.write(indent(paint(`… ${label}`, MUTED)));
    return () => process.stdout.write("\r\x1b[2K");
  }

  // ---------------------------------------------------------------- usage

  usage(stats: Usage): void {
    const parts: string[] = [];
    for (const [key, value] of Object.entries(stats)) {
      this.totals[key] = (this.totals[key] ?? 0) + (value ?? 0);
      if (value) parts.push(`${value.toLocaleString("en-US")} ${key.replace("_tokens", "")}`);
    }
    console.log();
    console.log(indent(paint(parts.join(" · "), MUTED)));
  }

  summary(): void {
    if (!Object.keys(this.totals).length) return;
    console.log();
    for (const [key, value] of Object.entries(this.totals)) {
      console.log(indent(`${paint(key.replace(/_/g, " ").padEnd(20), MUTED)}${paint(value.toLocaleString("en-US"), BOLD, ACCENT)}`));
    }
    console.log(paint("─".repeat(56), MUTED));
    console.log();
  }

  // -------------------------------------------------------------- helpers

  formatArgs(args: Args): string {
    const values = Object.values(args);
    if (values.length === 1) return String(values[0]);
    return JSON.stringify(args);
  }

  formatResult(result: string): string[] {
    const lines = result.trim() ? result.trim().split("\n") : ["(no output)"];
    const shown = lines.slice(0, MAX_TOOL_OUTPUT_LINES);
    const hidden = lines.length - shown.length;
    if (hidden > 0) shown.push(`… ${hidden} more lines`);
    return shown;
  }
}

export const ui = new UI();
