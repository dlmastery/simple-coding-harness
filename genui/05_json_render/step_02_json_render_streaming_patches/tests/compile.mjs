// Compile a JSONL file with the library's stream compiler and print the spec.
// test_step.py runs this and compares the result with json_patch.SpecStream.
import { readFileSync } from "node:fs";
import { createSpecStreamCompiler } from "@json-render/core";

const text = readFileSync(process.argv[2], "utf-8");
const compiler = createSpecStreamCompiler();
compiler.push(text);
process.stdout.write(JSON.stringify(compiler.getResult()));
