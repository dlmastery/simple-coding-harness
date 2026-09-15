# Writing content files for the deck

`build_deck.js` renders every `content/*.json` in filename order. Each file is
`{"slides": [ ... ]}`. Paths in `file` and `image` are relative to `genui/`.
Build with `node genui/slides/build_deck.js` from the repo root (it prints the
slide count per file and fails loudly on a bad snippet anchor or unknown type).

## Slide types

```json
{"type": "section", "kicker": "Sub-theme 02", "title": "AG-UI, the transport",
 "lead": "60-90 words: what this sub-theme is, in the report's terms.",
 "steps": [{"id": "02.1", "title": "An AG-UI server"}, {"id": "02.2", "title": "..."}],
 "notes": "speaker notes"}

{"type": "theory", "kicker": "Step 02.1 · Level 5 of 21 · your own product",
 "title": "A run is a request; the reply is a stream of typed events",
 "headline": "One sentence with **bold** for the key term.",
 "bullets": ["4-6 short bullets, 8-16 words each, the theory behind the step"],
 "diagram": {...},                 // optional, see below
 "takeaway": "one sentence",
 "notes": "speaker notes, 60-120 words: what to say on this slide"}

{"type": "code", "kicker": "Step 02.1 · code walkthrough",
 "title": "The agent is a generator; the endpoint encodes it",
 "snippet": {"file": "02_ag_ui/step_01_ag_ui_server/agent.py", "from": "def run(", "count": 14,
             "to": "yield RunFinishedEvent", "skip": ["# noqa"], "maxWidth": 96},
 "callouts": [{"line": 2, "text": "Line numbers are 1-based **within the snippet**. 1-3 callouts, 10-25 words each."}],
 "caption": "one sentence under the code",
 "notes": "..."}

{"type": "result", "kicker": "Step 02.1 · quick demo",
 "title": "What the recorded run showed",
 "image": "02_ag_ui/step_01_ag_ui_server/demo.png",     // or "output": ["line", "line", ...] for text demos (max 20 lines)
 "imageWidth": 7.2, "imageHeight": 4.9,                  // optional; keep the image's aspect ratio in mind (default box 7.2 x 4.9 in, contain)
 "stats": [{"value": "18", "label": "TEXT_MESSAGE_CONTENT events"}, {"value": "1,148", "label": "prompt tokens", "color": "amber"}],   // 0-3 stats
 "notice": ["2-4 bullets: what to look at in the picture"],
 "caption": "optional one line",
 "notes": "..."}

{"type": "chart", "kicker": "...", "title": "...", "chartType": "bar", "horizontal": false,
 "labels": ["OpenUI Lang", "YAML", "C1 JSON", "patches"],
 "series": [{"name": "tokens", "values": [4800, 9122, 9948, 10180]}],
 "valueTitle": "tokens (o200k_base)", "bullets": ["optional bullets on the right"], "caption": "...", "notes": "..."}

{"type": "table", "kicker": "...", "title": "...", "columns": ["If", "Then", "Step"],
 "rows": [["...", "...", "..."]], "colW": [3.5, 6.1, 2.5], "caption": "...", "notes": "..."}

{"type": "diagram", "kicker": "...", "title": "...", "lead": "one sentence", "diagram": {...}, "takeaway": "...", "notes": "..."}
```

## Diagram specs (`diagram` field)

Node kinds colour the boxes: `model` and `catalog` (blue), `spec` and
`server` (navy on grey), `page` and `host` (green), `open` and `iframe`
(amber), `data` (rose), `user` (grey). `"dashed": true` draws a dashed
border (use it for open-ended or pending parts).

```json
{"type": "flow", "direction": "right", "nodes": [{"label": "model", "sub": "tool calls", "kind": "model"}, {"label": "server", "sub": "one SSE message per call", "kind": "server"}, {"label": "page", "sub": "three renderers", "kind": "page"}], "caption": "..."}
{"type": "flow", "direction": "down", "nodes": [...]}                              // vertical, up to 5 nodes
{"type": "chips", "items": [{"label": "RUN_STARTED", "note": "the run has an id", "kind": "spec"}, ...], "caption": "..."}   // up to 8 rows: event or message lists
{"type": "layers", "nested": true, "items": [{"label": "A2A", "sub": "agent to agent"}, {"label": "AG-UI", "sub": "..."}, {"label": "A2UI", "sub": "...", "kind": "catalog"}]}
{"type": "hybrid", "left": ["Heading", "Card", "BarChart", "Button"], "right": "GeneratedView", "rightSub": "sandboxed iframe", "caption": "..."}
{"type": "bridge", "left": {"label": "host page", "sub": "...", "kind": "host"}, "right": {"label": "iframe", "sub": "...", "kind": "iframe", "dashed": true},
 "messages": [{"label": "ui/initialize", "dir": "left"}, {"label": "tool-result", "dir": "right"}, {"label": "tools/call", "dir": "left", "kind": "open"}]}   // 3-6 messages; dir is the arrow direction
{"type": "grid", "cols": ["static", "declarative", "open-ended"], "rows": ["your product", "third-party host"], "cells": [{"label": "...", "sub": "...", "kind": "catalog"}, ...]}  // cells row-major
{"type": "tiles", "items": [{"value": "9-10x", "label": "tokens, HTML vs flat spec", "color": "amber"}, ...]}   // up to 6 big-number tiles
{"type": "skeleton", "lines": ["root = Stack([title, kpis])", "title = Text(\"...\")", "kpis = Stack([a, b])"], "arrived": 2, "slots": [{"label": "title"}, {"label": "kpis", "pending": true}], "caption": "..."}
```

## Per step, produce this sequence

1. `theory` (with a diagram): the idea, in the report's terms, and why it comes now.
2. `code` (one or two): the most teaching snippet(s), anchored in the real file, with 1-3 callouts. Snippets are read from the source at build time, so the anchor text must exist. Keep to 8-16 lines; use `to` to stop early and `skip` to drop noise lines.
3. `result`: the recorded demo (the step README's Quick demo has the real numbers; embed every `demo*.png` the step has, one `result` slide per image, or use `output` for text-only demos).

Numbers only from the step READMEs' recorded demos. Prose: short sentences, active voice, no first person, no idioms, no references to any video or author. Say "the report" for the State of Generative UI report. Speaker notes on every slide (they are what a presenter says; 60-120 words).

Slide titles are the message, not a label: "A flat element map paints at chunk 33; a tree waits for chunk 408", not "Results".
