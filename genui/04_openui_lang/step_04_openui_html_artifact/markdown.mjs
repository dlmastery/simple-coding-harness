// Step 04 - a small Markdown renderer that builds React elements directly.
//
// The OpenUI example renders Markdown with its react-ui package. Here a
// dependency-free subset is enough: paragraphs, headings, bullet lists, and
// inline bold, italic and code. It never produces an HTML string, so model
// text cannot smuggle markup into the host page (no innerHTML anywhere).

import { createElement as h } from "react";

const INLINE_RE = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;

// "a **b** `c`" -> ["a ", <strong>b</strong>, " ", <code>c</code>]
export function inline(text) {
  return text.split(INLINE_RE).filter(Boolean).map((part, i) => {
    if (part.startsWith("**")) return h("strong", { key: i }, part.slice(2, -2));
    if (part.startsWith("`")) return h("code", { key: i }, part.slice(1, -1));
    if (part.startsWith("*")) return h("em", { key: i }, part.slice(1, -1));
    return part;
  });
}

// Split into blocks on blank lines; each block is a heading, a list or a paragraph.
export function blocks(text) {
  return text.replace(/\r\n/g, "\n").split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
}

export function renderMarkdown(text) {
  return blocks(text).map((block, i) => {
    const heading = /^(#{1,3})\s+(.*)$/.exec(block);
    if (heading) return h(`h${heading[1].length + 1}`, { key: i, className: "md-heading" }, inline(heading[2]));
    const lines = block.split("\n");
    if (lines.every((l) => /^[-*]\s+/.test(l))) {
      return h("ul", { key: i, className: "md-list" }, lines.map((l, j) => h("li", { key: j }, inline(l.replace(/^[-*]\s+/, "")))));
    }
    return h("p", { key: i, className: "md-p" }, inline(lines.join(" ")));
  });
}
