// Step 04 - the HtmlArtifact component: OpenUI's open-ended escape hatch.
//
// The model writes a whole HTML/CSS/JS document as the second argument of
// one statement. While that string is still arriving the renderer shows a
// status line and the raw source; once the stream ends it switches to the
// Rendered tab, where the document runs in a sandboxed iframe with the CSP
// from sandbox.mjs injected first in its <head>. This is the shape of
// `src/html-artifact.tsx` in OpenUI's examples/miscellaneous/html-artifact,
// without the react-ui panel and with the hardening its comment asks for.

import { defineComponent, useIsStreaming } from "@openuidev/react-lang";
import { createElement as h, useEffect, useState } from "react";
import { z } from "zod";
import { checkDocument, sandboxed } from "./sandbox.mjs";

function HtmlArtifactRenderer({ props }) {
  const isStreaming = useIsStreaming();
  // Raw while the document streams in, Rendered once it is complete; the
  // reader can switch back to Raw with the tabs.
  const [view, setView] = useState(isStreaming ? "raw" : "rendered");
  useEffect(() => {
    if (!isStreaming) setView("rendered");
  }, [isStreaming]);
  const problems = checkDocument(props.document);
  const tab = (name, label) =>
    h("button", { type: "button", className: `tab ${view === name ? "active" : ""}`, "data-view": name, onClick: () => setView(name) }, label);

  return h("section", { className: "artifact", "data-state": isStreaming ? "streaming" : "ready", "data-view": isStreaming ? "raw" : view },
    h("div", { className: "artifact-head" },
      h("strong", null, props.title),
      isStreaming
        ? h("span", { className: "artifact-status" }, `Generating artifact ... ${props.document.length} characters so far`)
        : h("div", { className: "tabs" }, tab("raw", "Raw"), tab("rendered", "Rendered"))),
    isStreaming || view === "raw"
      ? h("pre", { className: "artifact-raw" }, props.document)
      : h("iframe", {
          title: props.title,
          className: "artifact-frame",
          sandbox: "allow-scripts",
          referrerPolicy: "no-referrer",
          srcDoc: sandboxed(props.document),
        }),
    problems.length
      ? h("ul", { className: "artifact-problems" }, problems.map((p, i) => h("li", { key: i }, p)))
      : null);
}

export const HtmlArtifact = defineComponent({
  name: "HtmlArtifact",
  description: "A self-contained interactive HTML/CSS/JavaScript document, run in a sandboxed iframe once it has fully arrived",
  props: z.object({
    title: z.string(),
    document: z.string().describe("a complete HTML document with inline CSS and JS"),
  }),
  component: HtmlArtifactRenderer,
});
