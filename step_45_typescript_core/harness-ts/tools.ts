/** Step 45 - the tools, and execute(), the one permission-checked entry point
 * the main loop and the subagent both use.
 *
 * Every tool takes one object of named arguments, parsed from the model's
 * JSON. Python spreads that dict as keyword arguments; here the object is
 * passed whole and destructured in the signature.
 */

import { readFileSync, writeFileSync } from "node:fs";

import * as history from "./history.ts";
import * as sandbox from "./sandbox.ts";
import { check } from "./permissions.ts";
import { readSkill } from "./skills.ts";
import { TASK_SCHEMA, task } from "./subagent.ts";
import { TODO_SCHEMA, writeTodos } from "./todos.ts";
import type { Args, Tool, ToolCall, ToolSchema } from "./types.ts";
import { ui } from "./ui.ts";

/** Run a shell command and return its combined stdout and stderr. */
export async function bash({ command }: { command: string }): Promise<string> {
  let result: sandbox.Output;
  try {
    result = await sandbox.run(command);
  } catch (failure) {
    if (failure instanceof sandbox.TimedOut) {
      // A slow command is the model's problem to work around, not a reason
      // to take the session down. Hand the failure back as a result.
      return `Timed out after ${failure.timeout}s and was killed. Narrow it down.`;
    }
    throw failure;
  }
  return history.cap(result.stdout + result.stderr || "(no output)");
}

/** Read a file and return its contents. */
export function readFile({ path }: { path: string }): string {
  return history.cap(readFileSync(path, "utf-8"));
}

/** Create a file, or overwrite it if it already exists. */
export function writeFile({ path, content }: { path: string; content: string }): string {
  writeFileSync(path, content, "utf-8");
  return `Wrote ${path}`;
}

/** Swap exact text in a file. old_str must match exactly once. */
export function strReplace({ path, old_str, new_str, allow_multi_edit = false }: {
  path: string; old_str: string; new_str: string; allow_multi_edit?: boolean;
}): string {
  const content = readFileSync(path, "utf-8");

  const pieces = content.split(old_str);
  const count = pieces.length - 1;
  if (count === 0) {
    return `Error: old_str was not found in ${path}`;
  }
  if (count > 1 && !allow_multi_edit) {
    return (
      `Error: old_str matches ${count} times in ${path}. ` +
      "Add surrounding lines to make it unique, " +
      "or set allow_multi_edit to replace them all."
    );
  }

  writeFileSync(path, pieces.join(new_str), "utf-8");
  return `Replaced ${count} match(es) in ${path}`;
}

export const TOOL_SCHEMAS: ToolSchema[] = [
  {
    type: "function",
    function: {
      name: "bash",
      description: "Run a shell command and return its combined stdout and stderr.",
      parameters: {
        type: "object",
        properties: { command: { type: "string", description: "The shell command to run" } },
        required: ["command"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "read_file",
      description: "Read a file and return its contents.",
      parameters: {
        type: "object",
        properties: { path: { type: "string", description: "Path to the file to read" } },
        required: ["path"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "read_skill",
      description: "Open a skill by name and return its full instructions.",
      parameters: {
        type: "object",
        properties: { name: { type: "string", description: "Name of the skill to open" } },
        required: ["name"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "write_file",
      description: "Create a file, or overwrite it if it already exists.",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "File to write" },
          content: { type: "string", description: "The full contents" },
        },
        required: ["path", "content"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "str_replace",
      description:
        "Replace exact text in a file. old_str must appear exactly once, " +
        "so include surrounding lines if needed.",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "File to edit" },
          old_str: { type: "string", description: "Exact text to find" },
          new_str: { type: "string", description: "Text to put in its place" },
          allow_multi_edit: { type: "boolean", description: "Replace every match instead of failing" },
        },
        required: ["path", "old_str", "new_str"],
      },
    },
  },
  TODO_SCHEMA,
  TASK_SCHEMA,
];

export const TOOLS: Record<string, Tool> = {
  bash,
  read_file: readFile,
  write_file: writeFile,
  str_replace: strReplace,
  read_skill: readSkill,
  write_todos: writeTodos,
  task,
};

/** Run one tool call through the permission layer. Returns [args, result].
 *
 * Shared by the main loop and by subagents, so a subagent is fenced in by
 * exactly the same rules - it is not a way around them.
 */
export async function execute(toolCall: ToolCall): Promise<[Args, string]> {
  const args: Args = JSON.parse(toolCall.function.arguments);
  const [action, reason] = check(toolCall.function.name, args);
  if (action === "deny") {
    return [args, `Blocked by policy: ${reason}`];
  }
  if (action === "ask" && !(await ui.approve(reason))) {
    return [args, "The user denied this tool call."];
  }
  return [args, await TOOLS[toolCall.function.name](args)];
}
