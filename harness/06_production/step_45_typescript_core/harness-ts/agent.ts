/** Step 45 - the loop. One turn: append the user's message, call the model,
 * run every tool call it asks for, feed the results back, repeat until a
 * reply has no tool calls. main() wraps it in the input loop.
 *
 * Every await here is where the Python loop blocks: the model call, the
 * tool call, the prompt. The order of events is the same.
 */

import { parseArgs } from "node:util";
import { pathToFileURL } from "node:url";

import * as commands from "./commands.ts";
import * as compact from "./compact.ts";
import { reminder } from "./context.ts";
import * as history from "./history.ts";
import { SYSTEM_PROMPT, callLlm, entry } from "./llm.ts";
import * as sandbox from "./sandbox.ts";
import * as session from "./session.ts";
import { activeForm } from "./todos.ts";
import { execute } from "./tools.ts";
import type { Message, Usage } from "./types.ts";
import { ui } from "./ui.ts";

const NO_USAGE: Usage = { prompt_tokens: null, completion_tokens: null, reasoning_tokens: null, cached_tokens: null };

/** One user turn. Returns the (possibly compacted) message list. */
export async function turn(messages: Message[], userInput: string, debug = false): Promise<Message[]> {
  messages.push({ role: "user", content: userInput });
  let usage = NO_USAGE;

  while (true) {
    const injection = reminder();
    ui.injection(injection.content);

    if (history.fit(messages)) {
      ui.note("dropped old tool output to make this request fit");
    }

    const done = ui.working(activeForm());
    let message;
    try {
      ({ message, usage } = await callLlm([...messages, injection]));
    } finally {
      done();
    }

    messages.push(entry(message));
    session.save(messages);
    ui.usage(usage);

    if (debug) {
      ui.debug(entry(message));
    }

    if (message.content) {
      ui.agent(message.content);
    }

    if (!message.tool_calls?.length) {
      break;
    }

    for (const toolCall of message.tool_calls) {
      const [args, result] = await execute(toolCall);
      ui.tool(toolCall.function.name, args, result);

      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: result,
      });
      session.save(messages); // after every message, so a crash loses nothing
    }
  }

  history.sweep(); // the turn is over: bin its temp files...
  history.strip(messages); // ...and shrink the tool output it produced

  if (compact.needed(usage)) {
    messages = await commands.compact(messages);
  }
  return messages;
}

export async function main(): Promise<void> {
  const { values: cli } = parseArgs({
    options: {
      resume: { type: "boolean", default: false }, // continue the last session
      debug: { type: "boolean", default: false }, // show the raw model response
    },
  });

  ui.banner(sandbox.name());

  let messages: Message[] = [{ role: "system", content: SYSTEM_PROMPT }];
  if (cli.resume) {
    const saved = session.allSessions();
    if (saved.length) {
      messages = session.openSession(saved[0].id);
      history.strip(messages);
      ui.resumed(messages);
      ui.replay(messages);
    }
  }

  while (true) {
    const userInput = await ui.ask();
    if (userInput === null || userInput === "/exit" || userInput === "/quit") {
      break; // ctrl-d, ctrl-c at the prompt, or the command: the transcript is saved
    }
    if (!userInput) {
      continue; // an empty line is not a message
    }

    if (userInput.startsWith("/")) {
      messages = await commands.handle(userInput, messages);
      session.save(messages);
      continue;
    }

    messages = await turn(messages, userInput, cli.debug);
  }

  ui.summary();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((failure) => {
    // a model call that failed for good, or anything else the loop did not expect:
    // one line, exit 1, and the transcript on disk is whole - --resume picks it up
    console.error(`harness: ${failure?.message ?? failure}`);
    process.exit(1);
  });
}
