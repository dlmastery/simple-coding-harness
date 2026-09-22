/** Step 45 - the plan.
 *
 * The harness keeps a list of every task the agent wants to save. Each task
 * carries a status: pending, in_progress or completed. Every write_todos call
 * replaces the whole list, so there is exactly one current plan.
 *
 * The list lives here, not in the transcript. The late injection shows it to
 * the model on every call, so the plan is always in front of the model.
 */

import type { Todo, ToolSchema } from "./types.ts";

export const MARKS: Record<Todo["status"], string> = { pending: "[ ]", in_progress: "[~]", completed: "[x]" };

export const TODOS: Todo[] = [];

/** What is wrong with a todo list, or null. Checked before the list replaces the old one. */
export function problem(todos: unknown): string | null {
  if (!Array.isArray(todos)) return "Error: todos must be a list.";
  for (const [i, todo] of todos.entries()) {
    if (typeof todo !== "object" || todo === null) return `Error: item ${i} is not an object.`;
    for (const key of ["content", "activeForm", "status"] as const) {
      if (typeof todo[key] !== "string" || !todo[key].trim()) return `Error: item ${i} needs a non-empty '${key}'.`;
    }
    if (!(todo.status in MARKS)) return `Error: item ${i} has status '${todo.status}'; use one of ${Object.keys(MARKS).join(", ")}.`;
  }
  const active = todos.filter((t) => t.status === "in_progress");
  if (active.length > 1) return `Error: ${active.length} tasks are in_progress. At most one may be.`;
  return null;
}

/** Replace the whole list. At most one task may be in_progress. A bad list leaves the old one in place. */
export function writeTodos({ todos }: { todos: Todo[] }): string {
  const wrong = problem(todos);
  if (wrong !== null) {
    return wrong;
  }
  TODOS.splice(0, TODOS.length, ...todos);
  return todosPrompt() || "Todo list cleared.";
}

export function todosPrompt(): string {
  return TODOS.map((t) => `${MARKS[t.status]} ${t.content}`).join("\n");
}

/** What the agent is doing right now, for the spinner. */
export function activeForm(): string {
  for (const todo of TODOS) {
    if (todo.status === "in_progress") return todo.activeForm;
  }
  return "thinking";
}

export const TODO_SCHEMA: ToolSchema = {
  type: "function",
  function: {
    name: "write_todos",
    description:
      "Record the plan for a multi-step task. Send the whole list every " +
      "time. Keep at most one task in_progress and update it as you go.",
    parameters: {
      type: "object",
      properties: {
        todos: {
          type: "array",
          items: {
            type: "object",
            properties: {
              content: { type: "string", description: "The task, imperative: 'Fix the parser'" },
              activeForm: { type: "string", description: "Present continuous: 'Fixing the parser'" },
              status: { type: "string", enum: ["pending", "in_progress", "completed"] },
            },
            required: ["content", "activeForm", "status"],
          },
        },
      },
      required: ["todos"],
    },
  },
};
