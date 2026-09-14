// Print the catalog as JSON Schema, one entry per component, so the Python
// server can check a spec against the same catalog the page renders.
import { z } from "zod";
import { catalog } from "./catalog.mjs";

const components = {};
for (const [name, definition] of Object.entries(catalog.data.components)) {
  components[name] = {
    description: definition.description,
    props: z.toJSONSchema(definition.props),
  };
}
process.stdout.write(JSON.stringify({ components }, null, 2));
