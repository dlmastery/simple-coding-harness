// Prints the tree for a program file as JSON, so test_step.py can compare it
// with the Python parser's tree.
import { readFileSync } from "node:fs";
import { parse, catalogFromSchema } from "./openui-parse.mjs";

const [, , programPath, catalogPath] = process.argv;
const catalog = catalogFromSchema(JSON.parse(readFileSync(catalogPath, "utf-8")));
const result = parse(readFileSync(programPath, "utf-8"), catalog);
console.log(JSON.stringify({ root: result.root, unresolved: result.unresolved, errors: result.errors }));
