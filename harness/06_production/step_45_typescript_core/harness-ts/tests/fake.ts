/** Step 45 - test helpers: a scripted fake client, and a temp workspace.
 *
 * The fake has the one method the loop calls, chat.completions.create. It
 * records every request and answers from a list of scripted replies, so a
 * test can say what the model will do and then check what the loop did.
 */

import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import * as permissions from "../permissions.ts";
import * as session from "../session.ts";
import type { Client, Completion, Reply, ToolCall } from "../types.ts";
import { ui } from "../ui.ts";

export const USAGE = { prompt_tokens: 10, completion_tokens: 4, completion_tokens_details: { reasoning_tokens: null }, prompt_tokens_details: { cached_tokens: 3 } };

export type Request = Record<string, any>;

export function fakeClient(replies: Reply[], requests: Request[] = []): Client {
  return {
    chat: {
      completions: {
        async create(request: Request): Promise<Completion> {
          requests.push({ ...request, messages: structuredClone(request.messages) }); // a snapshot: the loop mutates its list
          const message = replies.shift() ?? { content: "(out of scripted replies)", tool_calls: null };
          return { choices: [{ message }], usage: USAGE };
        },
      },
    },
  };
}

export function call(id: string, name: string, args: Record<string, unknown>): ToolCall {
  return { id, type: "function", function: { name, arguments: JSON.stringify(args) } };
}

export function say(text: string): Reply {
  return { content: text, tool_calls: null, refusal: null };
}

export function use(...calls: ToolCall[]): Reply {
  return { content: null, tool_calls: calls, refusal: null };
}

/** A temp workspace: the permission fence, the session store and cwd all point at it. */
export function workspace(): string {
  const dir = mkdtempSync(join(tmpdir(), "harness-ts-"));
  process.chdir(dir);
  permissions.setProject(dir);
  session.state.dir = join(dir, "sessions");
  mkdirSync(session.state.dir);
  session.state.current = "test-session";
  session.state.written = 0;
  ui.approve = async () => true;
  return dir;
}
