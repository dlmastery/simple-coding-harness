/** Step 45 - the tools, and execute(), the one permission-checked entry point
 * the main loop and the subagent both use.
 *
 * Every tool takes one object of named arguments, parsed from the model's
 * JSON. Python spreads that dict as keyword arguments; here the object is
 * passed whole and destructured in the signature.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

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
      // to take the session down. Hand the failure back as a result, with
      // what the command printed before it was killed.
      return history.cap(`Timed out after ${failure.timeout}s and was killed. Output so far:\n${failure.output}`);
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
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content, "utf-8");
  return `Wrote ${path}`;
}

/** Swap exact text in a file. old_str must match exactly once. */
export function strReplace({ path, old_str, new_str, allow_multi_edit = false }: {
  path: string; old_str: string; new_str: string; allow_multi_edit?: boolean;
}): string {
  if (!old_str) {
    return "Error: old_str is empty; give the exact text to replace";
  }
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

/** The arguments of a tool call as an object, or [{}, why] when they are not one. */
export function parseArgs(toolCall: ToolCall): [Args, string | null] {
  let args: unknown;
  try {
    args = JSON.parse(toolCall.function.arguments || "{}");
  } catch (failure) {
    return [{}, (failure as Error).message];
  }
  if (typeof args !== "object" || args === null || Array.isArray(args)) {
    return [{}, `got ${Array.isArray(args) ? "array" : typeof args}, not an object`];
  }
  return [args as Args, null];
}

/** Run one tool call through the permission layer. Returns [args, result].
 *
 * Shared by the main loop and by subagents, so a subagent is fenced in by
 * exactly the same rules - it is not a way around them. Nothing rejects
 * out of here: arguments that are not a JSON object, a tool name the
 * registry does not have and an exception inside the tool all come back
 * as an Error: result the model can read, the way a failed command does.
 * Every tool call gets exactly one result, so the transcript stays valid.
 */
export async function execute(toolCall: ToolCall): Promise<[Args, string]> {
  const name = toolCall.function.name;
  const [args, problem] = parseArgs(toolCall);
  if (problem !== null) {
    return [args, `Error: the arguments of ${name} are not a JSON object: ${problem}`];
  }
  const fn = TOOLS[name];
  if (fn === undefined) {
    return [args, `Error: no tool named '${name}'.`];
  }
  const [action, reason] = check(name, args);
  if (action === "deny") {
    return [args, `Blocked by policy: ${reason}`];
  }
  if (action === "ask" && !(await ui.approve(reason))) {
    return [args, "The user denied this tool call."];
  }
  try {
    return [args, await fn(args)];
  } catch (failure) {
    // a missing file or a wrong argument is the model's problem to fix
    const error = failure as Error;
    return [args, `Error: ${error?.name ?? "Error"}: ${error?.message ?? String(failure)}`];
  }
}
