/** Step 45 - skills: the same SKILL.md files the Python harness reads.
 *
 * The front matter is read with a small key: value reader, not a YAML
 * library. Every shipped skill keeps name and description on one line each,
 * and that is all the index needs.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const SKILL_DIRS = [
  join(homedir(), ".agents", "skills"), // your skills
  join(process.cwd(), ".agents", "skills"), // this project's skills
];

export type Skill = { description: string; path: string };

/** key: value lines, with indented continuation lines folded into the value above. */
export function frontmatter(text: string): Record<string, string> {
  const meta: Record<string, string> = {};
  let last: string | null = null;
  for (const line of text.split(/\r?\n/)) {
    const match = /^([A-Za-z_][\w-]*):\s*(.*)$/.exec(line);
    if (match) {
      last = match[1];
      meta[last] = match[2].replace(/^["'](.*)["']$/, "$1").replace(/^[>|]-?$/, "");
    } else if (last !== null && /^\s+\S/.test(line)) {
      meta[last] = `${meta[last]} ${line.trim()}`.trim();
    }
  }
  return meta;
}

/** Read SKILL.md under every skill dir; name -> {description, path}. */
export function findSkills(): Record<string, Skill> {
  const skills: Record<string, Skill> = {};
  for (const directory of SKILL_DIRS) {
    if (!existsSync(directory)) continue;
    for (const name of readdirSync(directory).sort()) {
      const path = join(directory, name, "SKILL.md");
      if (!existsSync(path)) continue;
      const text = readFileSync(path, "utf-8");
      if (!text.startsWith("---")) continue;
      const meta = frontmatter(text.split("---")[1] ?? "");
      if (!meta.name) continue;
      const description = (meta.description ?? "").split(/\s+/).join(" ").trim();
      skills[meta.name] = { description, path };
    }
  }
  return skills;
}

export const SKILLS = findSkills();

/** One line per skill: the index that goes into the system prompt. */
export function skillsPrompt(): string {
  return Object.entries(SKILLS)
    .map(([name, s]) => `- ${name}: ${s.description}`)
    .join("\n");
}

/** Open a skill and return its full instructions. */
export function readSkill({ name }: { name: string }): string {
  if (!(name in SKILLS)) return `No skill named '${name}'.`;
  return readFileSync(SKILLS[name].path, "utf-8");
}
