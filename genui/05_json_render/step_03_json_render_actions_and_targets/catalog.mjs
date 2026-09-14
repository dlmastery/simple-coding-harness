// The catalog: the six components from step 1, a Button, and two actions the
// model may bind to it. json-render turns this one object into the system
// prompt (catalog.prompt()) and, through defineRegistry, into a typed
// component map for the Renderer. The same catalog feeds the ink renderer.
// The React schema fixes the spec shape: { root, elements: { id: { type, props, children } } }.
import { z } from "zod";
import { defineCatalog } from "@json-render/core";
import { schema } from "@json-render/react/schema";

export const catalog = defineCatalog(schema, {
  components: {
    Card: {
      props: z.object({
        title: z.string(),
        subtitle: z.string().nullable(),
      }),
      description: "A titled container. Put related elements inside it.",
    },
    Row: {
      props: z.object({
        gap: z.enum(["small", "large"]).nullable(),
      }),
      description: "Lays its children out side by side.",
    },
    Text: {
      props: z.object({
        text: z.string(),
        tone: z.enum(["normal", "muted", "strong"]).nullable(),
      }),
      description: "One paragraph of text.",
    },
    Metric: {
      props: z.object({
        label: z.string(),
        value: z.string(),
        delta: z.string().nullable(),
      }),
      description: "One key number with a label and an optional change such as '+12%'.",
    },
    Table: {
      props: z.object({
        columns: z.array(z.string()),
        rows: z.array(z.array(z.string())),
      }),
      description: "A table. Every row has one cell per column.",
    },
    Chart: {
      props: z.object({
        kind: z.enum(["bar", "line"]),
        labels: z.array(z.string()),
        values: z.array(z.number()),
      }),
      description: "A small bar or line chart. labels and values have the same length.",
    },
    Button: {
      props: z.object({
        label: z.string(),
        variant: z.enum(["primary", "secondary"]).nullable(),
      }),
      description: "A button. Bind its press event to an action with the on field.",
    },
  },
  actions: {
    refresh_numbers: {
      params: z.object({}),
      description: "Reload this week's numbers from the stand. The agent answers with patches that replace the values.",
    },
    show_details: {
      params: z.object({ metric: z.string() }),
      description: "Ask the agent for a details card about one metric. params.metric is the metric's label.",
    },
  },
});

// The prompt the server sends as the system message: the library's JSONL
// format, plus rules that make the demo exercise both kinds of action.
export const PROMPT = catalog.prompt({
  system: "You are a dashboard builder. You turn a request into a UI spec.",
  customRules: [
    "Use short element ids such as card-1, row-1, metric-1.",
    "Include one Button bound to refresh_numbers and one Button bound to show_details for the main metric.",
    "Include one Button that toggles a Card of notes with setState on /showNotes; give that Card visible: {\"$state\": \"/showNotes\"}.",
  ],
});
