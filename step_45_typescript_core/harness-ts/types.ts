/** Step 45 - the shapes shared by every module of the TypeScript port.
 *
 * The Python harness passes plain dicts and the objects the openai client
 * returns. Here the same shapes get names, so each file can say what it
 * takes and what it gives back. Nothing in this file runs.
 */

export type Role = "system" | "user" | "assistant" | "tool";

export interface ToolCall {
  id: string;
  type: "function";
  function: { name: string; arguments: string };
}

/** One transcript entry - exactly what goes on the wire and into the session log. */
export interface Message {
  role: Role;
  content?: string | null;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  [extra: string]: unknown;
}

/** choices[0].message as the client returns it, before it becomes a Message. */
export interface Reply {
  content?: string | null;
  tool_calls?: ToolCall[] | null;
  [extra: string]: unknown;
}

export interface Usage {
  prompt_tokens: number | null;
  completion_tokens: number | null;
  reasoning_tokens: number | null;
  cached_tokens: number | null;
}

export interface ToolSchema {
  type: "function";
  function: { name: string; description: string; parameters: Record<string, unknown> };
}

export interface Completion {
  choices: { message: Reply }[];
  usage?: {
    prompt_tokens?: number | null;
    completion_tokens?: number | null;
    completion_tokens_details?: { reasoning_tokens?: number | null } | null;
    prompt_tokens_details?: { cached_tokens?: number | null } | null;
  } | null;
}

/** The slice of the openai client the loop uses. A fake in the tests has the same shape. */
export interface Client {
  chat: { completions: { create(request: Record<string, unknown>): Promise<Completion> } };
}

export type Args = Record<string, any>;
export type Tool = (args: Args) => string | Promise<string>;
export type Action = "allow" | "ask" | "deny";
export type Todo = { content: string; activeForm: string; status: "pending" | "in_progress" | "completed" };
