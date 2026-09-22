/** Step 45 - exploration subagents.
 *
 * A task tool hands a self-contained exploration question to a fresh agent
 * that has its own context window. The subagent reuses callLlm: it takes a
 * list of messages and a tool set and returns one response.
 *
 * Four rules, and the code below is really just these:
 *
 *   1. it starts from an empty history           - none of the chat context
 *      the user had with the main agent is shared with the subagent
 *   2. it holds every tool but four              - task, write_todos,
 *      str_replace and write_file are withheld; no recursion, one subagent deep
 *   3. it runs the same loop as the main agent   - callLlm, append, tools
 *   4. only its final message.content comes back - none of the subagent's
 *      tool calls ever return to the main agent
 */

import { fit } from "./history.ts";
import type { Message, ToolSchema } from "./types.ts";
import { ui } from "./ui.ts";

export let MAX_TURNS = 12; // a runaway explorer is worse than a missing answer

/** The tests lower the limit. */
export function setMaxTurns(turns: number): void {
  MAX_TURNS = turns;
}

export const WITHHELD = new Set(["task", "write_todos", "str_replace", "write_file"]);

export const SYSTEM_PROMPT = `
You are an exploration subagent. You were given one question by a lead agent
and you answer it. That is the whole job.

You cannot see the conversation that spawned you, and the lead agent cannot
see anything you do here. Only your final message crosses back, so it has to
stand on its own.

You are working in ${process.cwd()}. Search inside it. Never search from / or
from the home directory - that scans the whole machine and will time out.

How to work:
- Use bash, read_file and read_skill to find out what is actually true.
  Prefer rg, grep and find to guess at where things live.
- You are here to read and report, not to change anything.
- Search in batches. Several greps in one turn beats one grep per turn.
- Stop as soon as you can answer. Do not keep looking to be thorough.

Your final message is the entire report, and it is the only thing that costs
the lead agent anything - so keep it short. Aim for under 150 words. Findings
only: file paths with line numbers, names, values. Say plainly what you could
not find; a gap is useful, a guess is not.
`;

/** Every tool schema except the withheld ones. */
export async function toolset(): Promise<ToolSchema[]> {
  const { TOOL_SCHEMAS } = await import("./tools.ts");

  return TOOL_SCHEMAS.filter((s) => !WITHHELD.has(s.function.name));
}

/** Run a fresh agent on one question and return only its final answer. */
export async function task({ description }: { description: string }): Promise<string> {
  // Imported here, not at the top: tools imports us, and we need tools. A
  // top-level import would run before TASK_SCHEMA exists on that side.
  const { callLlm, entry } = await import("./llm.ts");
  const { execute } = await import("./tools.ts");

  // rule 1: two messages, born here, dead at the return
  const messages: Message[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: description },
  ];
  ui.subagent(description);
  let report: string | null = null; // newest thing it has said, kept in case we run out of turns

  // rule 3: the loop from agent.ts, pointed at a different list
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    fit(messages); // its context can overflow too, and nobody compacts it

    const done = ui.working("subagent exploring");
    let message, usage;
    try {
      ({ message, usage } = await callLlm(messages, await toolset())); // rule 2
    } finally {
      done();
    }
    messages.push(entry(message));
    ui.usage(usage);
    report = message.content || report;

    // rule 4: no tool calls means it has stopped looking and started answering
    if (!message.tool_calls?.length) {
      return report || "(the subagent came back with nothing)";
    }

    for (const toolCall of message.tool_calls) {
      // the same executor as the main loop: same permissions, same sandbox
      const [args, result] = await execute(toolCall);
      ui.tool(toolCall.function.name, args, result, true);
      messages.push({ role: "tool", tool_call_id: toolCall.id, content: result });
    }
  }

  if (report) {
    return `(stopped after ${MAX_TURNS} turns, before finishing. Partial findings below.)\n\n${report}`;
  }
  return `(stopped after ${MAX_TURNS} turns with nothing to report.)`;
}

export const TASK_SCHEMA: ToolSchema = {
  type: "function",
  function: {
    name: "task",
    description:
      "Hand a self-contained exploration question to a fresh agent that " +
      "has its own context window, and get back its findings. Use this " +
      "to learn how the codebase works - tracing behaviour, locating " +
      "where something is implemented, surveying files - so the search " +
      "costs you one answer instead of dozens of tool results. It cannot " +
      "see this conversation, so include every detail it needs. It reads " +
      "and reports; it never edits. Do your own editing.",
    parameters: {
      type: "object",
      properties: {
        description: {
          type: "string",
          description:
            "The question, written to stand alone: what to find " +
            "out, where to start looking, and what the answer " +
            "should contain.",
        },
      },
      required: ["description"],
    },
  },
};
