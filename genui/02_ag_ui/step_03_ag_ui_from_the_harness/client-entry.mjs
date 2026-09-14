// The one line esbuild bundles into vendor/ag-ui-client.js. @ag-ui/client
// is published as an ES module that imports rxjs, zod and friends by bare
// name, which a browser cannot resolve without a bundler or an import map
// for every dependency. One esbuild call flattens it into a single file.
export { HttpAgent } from "@ag-ui/client";
