// Step 02 - print the system prompt the catalog generates.
//
//     node prompt.mjs > prompt.txt
//
// library.prompt() turns the Zod schemas into one signature line per
// component plus the language rules. server.py caches the output in
// prompt.txt and sends it as the system message.
import { library, PROMPT_OPTIONS } from "./library.mjs";

process.stdout.write(library.prompt(PROMPT_OPTIONS));
