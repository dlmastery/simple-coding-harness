/** Step 45 - one model call, and the system prompt.
 *
 * The openai package is imported on the first real call, not at the top,
 * so the tests run with no packages installed: they hand the loop a fake
 * client through setClient() and the import never happens.
 */

import * as config from "./config.ts";
import { skillsPrompt } from "./skills.ts";
import { TOOL_SCHEMAS } from "./tools.ts";
import type { Client, Message, Reply, ToolSchema, Usage } from "./types.ts";

let client: Client | null = null;

/** Replace the client. The tests inject a fake; null goes back to the real one. */
export function setClient(replacement: Client | null): void {
  client = replacement;
}

async function getClient(): Promise<Client> {
  if (client === null) {
    const { default: OpenAI } = await import("openai");
    client = new OpenAI({ baseURL: config.BASE_URL, apiKey: config.API_KEY }) as unknown as Client;
  }
  return client;
}

export const MODEL = config.MODEL;

export const SYSTEM_PROMPT = `
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Use write_file to create files and str_replace to edit them.
Answer back to the user once exploration is done.

For any task that takes more than one step, call write_todos first and plan it
out. Send the whole list every time you call it - it replaces the old one.
Keep exactly one task in_progress, mark it completed the moment it is finished,
and move the next one to in_progress in the same call. Skip the tool entirely
for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.

When you need to understand how something works - where a feature lives, how
data flows, what calls what - send a task subagent instead of grepping your
way there yourself. It explores in its own context window and hands you back
just the findings, so the search does not fill yours. It cannot see this
conversation, so write the question so it stands alone. Do all editing
yourself; the subagent only reads.

Long tool output is cut short, and the whole thing is written to a temp file
whose path is given at the cut. Page through it with head, tail, sed -n or
grep rather than asking for it again. That file only exists for the current
turn, so read it now or re-run the command later.

Your current working directory is: ${process.cwd()}

You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

${skillsPrompt()}
`;

/** tools undefined means the full registry; tools=[] means no tools (the compaction agent). */
export async function callLlm(messages: Message[], tools?: ToolSchema[] | null): Promise<{ message: Reply; usage: Usage }> {
  const request: Record<string, unknown> = { model: MODEL, messages };
  const schemas = tools == null ? TOOL_SCHEMAS : tools;
  if (schemas.length) {
    request.tools = schemas;
  }
  const response = await (await getClient()).chat.completions.create(request);

  if (!response.choices?.length) {
    // some servers answer 200 with an error object and no choices: say so instead of reading undefined
    const error = (response as { error?: { message?: string } }).error;
    throw new Error(error?.message ?? (error ? JSON.stringify(error) : "empty reply: the response carried no choices"));
  }
  const message = response.choices[0].message;

  const usage: Usage = {
    prompt_tokens: response.usage?.prompt_tokens ?? null,
    completion_tokens: response.usage?.completion_tokens ?? null,
    reasoning_tokens: response.usage?.completion_tokens_details?.reasoning_tokens ?? null,
    cached_tokens: response.usage?.prompt_tokens_details?.cached_tokens ?? null,
  };

  return { message, usage };
}

/** The transcript entry for a reply: role, content, and the tool calls when there are any.
 *
 * Three keys and nothing else, whatever the server sent along. The client
 * returns a plain object with explicit nulls and extras - `refusal`,
 * `annotations`, a reasoning model's `reasoning` - and none of that may be
 * echoed back on the next request, so the shape is pinned here, the way
 * the Python StreamedMessage.model_dump pins it. `content` stays, null
 * included: the entry on disk has the shape the API sends.
 */
export function entry(message: Reply): Message {
  const out: Message = { role: "assistant", content: message.content ?? null };
  if (message.tool_calls?.length) {
    out.tool_calls = message.tool_calls.map((call) => ({
      id: call.id,
      type: "function",
      function: { name: call.function.name, arguments: call.function.arguments },
    }));
  }
  return out;
}
