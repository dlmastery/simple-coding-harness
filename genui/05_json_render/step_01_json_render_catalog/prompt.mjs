// Print the system prompt json-render generates from the catalog.
// The Python side runs this once and caches the text in prompt.txt.
import { PROMPT } from "./catalog.mjs";

process.stdout.write(PROMPT);
