/** Step 45 - settings. Real environment variables win; ~/.simple-harness/env fills gaps.
 *
 * The same file and the same names as harness/config.py, so one key serves
 * both harnesses. One KEY=VALUE per line.
 */

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const HOME = join(homedir(), ".simple-harness");
export const ENV_FILE = join(HOME, "env");

if (existsSync(ENV_FILE)) {
  for (const line of readFileSync(ENV_FILE, "utf-8").split(/\r?\n/)) {
    if (line.includes("=") && !line.trimStart().startsWith("#")) {
      const cut = line.indexOf("=");
      const key = line.slice(0, cut).trim();
      process.env[key] ??= line.slice(cut + 1).trim();
    }
  }
}

export const BASE_URL = process.env.BASE_URL ?? "https://openrouter.ai/api/v1";
export const API_KEY = process.env.API_KEY ?? "";
export const MODEL = process.env.MODEL ?? "deepseek/deepseek-v4-flash";

// How much room the model has, and how we spend it (85% -> 35%).
export const CONTEXT_WINDOW = Number(process.env.CONTEXT_WINDOW ?? 128_000);
export const COMPACT_AT = 0.85; // compact once the prompt crosses this fraction of the window
export const COMPACT_TO = 0.35; // and cut back to this fraction, so it does not retrigger soon
