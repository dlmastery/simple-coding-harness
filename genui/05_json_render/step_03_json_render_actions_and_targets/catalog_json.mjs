// Print the catalog as JSON Schema, one entry per component, plus the action
// names (the catalog's own and the schema's built-ins), so the Python server
// can check a spec against the same catalog the page renders.
import { z } from "zod";
import { catalog } from "./catalog.mjs";

const components = {};
for (const [name, definition] of Object.entries(catalog.data.components)) {
  components[name] = {
    description: definition.description,
    props: z.toJSONSchema(definition.props),
  };
}
const actions = {};
for (const [name, definition] of Object.entries(catalog.data.actions)) {
  actions[name] = {
    description: definition.description,
    params: z.toJSONSchema(definition.params),
  };
}
const builtInActions = catalog.schema.builtInActions.map((action) => action.name);
process.stdout.write(JSON.stringify({ components, actions, builtInActions }, null, 2));
