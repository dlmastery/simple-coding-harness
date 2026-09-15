// Build the Generative UI codelab slide deck from the content files in content/.
//   node genui/slides/build_deck.js [--out file.pptx] [--only 03.json]   -> genui/generative_ui_zero_to_hero.pptx
// Data-driven: every slide is described in content/*.json; code snippets are read
// from the step sources at build time so the deck never drifts from the code.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const HERE = __dirname;
const GENUI = path.join(HERE, "..");
const argv = process.argv.slice(2);
const outArg = argv.indexOf("--out");
const onlyArg = argv.indexOf("--only");
const OUT = outArg >= 0 ? path.resolve(argv[outArg + 1]) : path.join(GENUI, "generative_ui_zero_to_hero.pptx");
const ONLY = onlyArg >= 0 ? argv[onlyArg + 1] : null; // build one content file, e.g. --only 03.json

// palette: electric blue on white for the catalog, amber for open-ended, navy for dark slides
const NAVY = "141B3D", INK = "1F2937", SOFT = "4B5563", MUTE = "8B93A7";
const BLUE = "2F3CFF", BLUE_TINT = "EEF0FF", AMBER = "D97706", AMBER_TINT = "FFF4E5";
const GREEN = "15803D", GREEN_TINT = "ECFDF5", ROSE = "BE123C", ROSE_TINT = "FFF1F2";
const PAPER = "F6F7FB", LINE = "D7DAE5", CODE_BG = "0F172A", CODE_FG = "E2E8F0", CODE_DIM = "64748B";
const HEAD = "Cambria", BODY = "Calibri", MONO = "Courier New";
const KIND = {
  model: [BLUE, BLUE_TINT], catalog: [BLUE, BLUE_TINT], spec: [NAVY, PAPER], page: [GREEN, GREEN_TINT],
  server: [NAVY, PAPER], open: [AMBER, AMBER_TINT], host: [GREEN, GREEN_TINT], iframe: [AMBER, AMBER_TINT],
  user: [SOFT, PAPER], data: [ROSE, ROSE_TINT], plain: [SOFT, "FFFFFF"],
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.author = "simple-coding-harness";
pres.title = "Zero to Hero: Generative UI";

let n = 0;
const W = 13.33;

// ----------------------------------------------------------------- primitives
function base(kicker, title, opts = {}) {
  const s = pres.addSlide();
  s.background = { color: opts.dark ? NAVY : "FFFFFF" };
  n += 1;
  const ink = opts.dark ? "FFFFFF" : INK;
  if (kicker) s.addText(kicker.toUpperCase(), { x: 0.6, y: 0.32, w: 11, h: 0.3, fontFace: BODY, fontSize: 11, color: opts.dark ? "AAB4FF" : BLUE, bold: true, charSpacing: 2, margin: 0 });
  const size = !title ? 30 : title.length <= 58 ? 30 : title.length <= 66 ? 26 : title.length <= 76 ? 23 : 20;
  const wraps = !!title && (title.length * size * 0.5) / 72 > 12.1;
  if (title) s.addText(title, { x: 0.6, y: 0.6, w: 12.1, h: wraps ? 1.15 : 0.85, fontFace: HEAD, fontSize: size, color: ink, bold: true, margin: 0, valign: "top" });
  s.addText(String(n), { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTE, align: "right", margin: 0 });
  s._top = wraps ? 1.9 : 1.55; // where content may start
  return s;
}
function bullets(items, size = 14, color = INK) {
  // each item becomes one bulleted paragraph; **bold** spans become bold runs
  const runs = [];
  items.forEach((t, i) => {
    let parts = t.split(/(\*\*[^*]+\*\*|`[^`]+`)/).filter(Boolean);
    if (parts[0].startsWith("`") || parts[0].startsWith("**")) parts = ["​", ...parts]; // the bullet glyph takes the first run's style
    parts.forEach((p, j) => {
      const bold = p.startsWith("**"), code = p.startsWith("`");
      const opts = { fontFace: code ? MONO : BODY, fontSize: code ? size - 1 : size, color: bold ? NAVY : code ? ROSE : color, bold };
      if (j === 0) Object.assign(opts, { bullet: { indent: 14 }, paraSpaceAfter: 6 });
      if (j === parts.length - 1 && i < items.length - 1) opts.breakLine = true;
      runs.push({ text: bold || code ? p.slice(bold ? 2 : 1, bold ? -2 : -1) : p, options: opts });
    });
  });
  return runs;
}
function rich(parts) {
  // "**bold** text" -> runs
  const runs = [];
  parts.split(/(\*\*[^*]+\*\*|`[^`]+`)/).forEach((p) => {
    if (!p) return;
    if (p.startsWith("**")) runs.push({ text: p.slice(2, -2), options: { bold: true, color: NAVY } });
    else if (p.startsWith("`")) runs.push({ text: p.slice(1, -1), options: { fontFace: MONO, color: ROSE } });
    else runs.push({ text: p, options: {} });
  });
  return runs;
}
function fitSize(text, w, size, factor = 0.55) {
  // the largest size (down to 8) at which text fits in w inches on at most two lines
  let pt = size;
  while (pt > 8 && (text.length * pt * factor) / 72 > w * 2) pt -= 0.5;
  return pt;
}
function box(s, x, y, w, h, label, sub, kind = "plain", opts = {}) {
  const [edge, tint] = KIND[kind] || KIND.plain;
  opts = { ...opts, size: fitSize(label, w - 0.16, opts.size || 12) };
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: tint }, line: { color: edge, width: 1.25, dashType: opts.dashed ? "dash" : "solid" }, rectRadius: 0.1 });
  const split = sub ? (h > 0.8 ? 0.5 : 0.55) : 1;
  s.addText(label, { x: x + 0.08, y: y + 0.04, w: w - 0.16, h: sub ? h * split - 0.02 : h - 0.08, fontFace: BODY, fontSize: opts.size || 12, bold: true, color: edge, align: "center", valign: sub ? "bottom" : "middle", margin: 0 });
  if (sub) s.addText(sub, { x: x + 0.08, y: y + h * split + 0.02, w: w - 0.16, h: h * (1 - split) - 0.06, fontFace: BODY, fontSize: Math.max(8, fitSize(sub, (w - 0.16) * 1.5, (opts.size || 12) - 2.5, 0.5)), color: SOFT, align: "center", valign: "top", margin: 0 });
}
function arrow(s, x1, y1, x2, y2, color = SOFT) {
  s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.01, h: Math.abs(y2 - y1) || 0.01, line: { color, width: 1.5, endArrowType: "triangle" }, flipH: x2 < x1, flipV: y2 < y1 });
}
function badge(s, x, y, num, col = BLUE, d = 0.36) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: col }, line: { color: col } });
  s.addText(String(num), { x, y, w: d, h: d, fontFace: BODY, fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
}
function stat(s, x, y, w, value, label, col = BLUE) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h: 1.3, fill: { color: PAPER }, line: { color: PAPER }, rectRadius: 0.1 });
  s.addText(String(value), { x: x + 0.15, y: y + 0.06, w: w - 0.3, h: 0.62, fontFace: HEAD, fontSize: 28, bold: true, color: col, margin: 0, valign: "middle" });
  s.addText(label, { x: x + 0.15, y: y + 0.68, w: w - 0.3, h: 0.58, fontFace: BODY, fontSize: 10.5, color: SOFT, margin: 0, valign: "top" });
}
function note(s, text) { if (text) s.addNotes(text); }

// ----------------------------------------------------------------- diagrams
// Every diagram draws inside the rectangle (x, y, w, h).
const DIAGRAMS = {
  flow(s, d, x, y, w, h) {
    const nodes = d.nodes;
    const vertical = d.direction === "down" || (nodes.length > 3 && w < 9); // a narrow column cannot hold four boxes side by side
    const gap = 0.35;
    if (!vertical) {
      const bw = (w - gap * (nodes.length - 1)) / nodes.length;
      const bh = Math.min(1.1, h);
      const by = y + (h - bh) / 2;
      nodes.forEach((nd, i) => {
        const bx = x + i * (bw + gap);
        box(s, bx, by, bw, bh, nd.label, nd.sub, nd.kind, { dashed: nd.dashed, size: nd.size || 12 });
        if (i < nodes.length - 1) arrow(s, bx + bw + 0.03, by + bh / 2, bx + bw + gap - 0.03, by + bh / 2);
      });
    } else {
      const bh = Math.min(0.9, (h - gap * (nodes.length - 1)) / nodes.length);
      const bw = Math.min(w, 4.2);
      const bx = x + (w - bw) / 2;
      nodes.forEach((nd, i) => {
        const by = y + i * (bh + gap);
        box(s, bx, by, bw, bh, nd.label, nd.sub, nd.kind, { dashed: nd.dashed });
        if (i < nodes.length - 1) arrow(s, bx + bw / 2, by + bh + 0.03, bx + bw / 2, by + bh + gap - 0.03);
      });
    }
    if (d.caption) s.addText(d.caption, { x, y: y + h + 0.05, w, h: 0.35, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE, align: "center", margin: 0 });
  },
  chips(s, d, x, y, w, h) {
    // a vertical list of event / message chips with a short note each
    const rows = d.items;
    const rh = Math.min(0.52, (h - 0.1 * (rows.length - 1)) / rows.length);
    rows.forEach((it, i) => {
      const ry = y + i * (rh + 0.1);
      const [edge, tint] = KIND[it.kind || "spec"];
      s.addShape(pres.ShapeType.roundRect, { x, y: ry, w: 2.6, h: rh, fill: { color: tint }, line: { color: edge, width: 1 }, rectRadius: 0.08 });
      s.addText(it.label, { x: x + 0.1, y: ry, w: 2.4, h: rh, fontFace: MONO, fontSize: 10.5, bold: true, color: edge, valign: "middle", margin: 0 });
      s.addText(it.note || "", { x: x + 2.75, y: ry, w: w - 2.75, h: rh, fontFace: BODY, fontSize: 11.5, color: INK, valign: "middle", margin: 0 });
    });
    if (d.caption) s.addText(d.caption, { x, y: y + h + 0.05, w, h: 0.35, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE, margin: 0 });
  },
  layers(s, d, x, y, w, h) {
    const L = d.items;
    const lh = Math.min(0.85, (h - 0.12 * (L.length - 1)) / L.length);
    L.forEach((it, i) => {
      const ly = y + i * (lh + 0.12);
      const inset = (d.nested ? i * 0.35 : 0);
      box(s, x + inset, ly, w - 2 * inset, lh, it.label, it.sub, it.kind || "spec", { dashed: it.dashed, size: 13 });
    });
    if (d.caption) s.addText(d.caption, { x, y: y + h + 0.05, w, h: 0.35, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE, align: "center", margin: 0 });
  },
  hybrid(s, d, x, y, w, h) {
    // the report's diagram: catalog primitives on the left, one dashed generated view on the right
    s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: "FFFFFF" }, line: { color: LINE, width: 1.25 }, rectRadius: 0.12 });
    [0, 1, 2].forEach((i) => s.addShape(pres.ShapeType.ellipse, { x: x + 0.2 + i * 0.22, y: y + 0.15, w: 0.12, h: 0.12, fill: { color: BLUE }, line: { color: BLUE } }));
    const left = (d.left || ["Heading", "Card", "BarChart", "Button"]);
    const colW = (w - 0.6) * 0.48, rowH = (h - 0.7) / left.length - 0.12;
    left.forEach((lab, i) => box(s, x + 0.2, y + 0.45 + i * (rowH + 0.12), colW, rowH, lab, "catalog primitive", "catalog", { size: 12 }));
    const gx = x + 0.4 + colW, gw = w - 0.6 - colW;
    box(s, gx, y + 0.45, gw, h - 0.65, d.right || "GeneratedView", d.rightSub || "sandboxed iframe: open-ended only where the catalog does not reach", "open", { dashed: true, size: 13 });
    if (d.caption) s.addText(d.caption, { x, y: y + h + 0.05, w, h: 0.35, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE, align: "center", margin: 0 });
  },
  bridge(s, d, x, y, w, h) {
    // two boxes (left/right) and labelled arrows between them, alternating directions
    const bw = w < 9 ? w * 0.27 : 2.6, bh = h;
    box(s, x, y, bw, bh, d.left.label, d.left.sub, d.left.kind || "host", { size: 13 });
    box(s, x + w - bw, y, bw, bh, d.right.label, d.right.sub, d.right.kind || "iframe", { dashed: d.right.dashed, size: 13 });
    const msgs = d.messages;
    const step = (h - 0.4) / Math.max(1, msgs.length - 1);
    msgs.forEach((m, i) => {
      const my = y + 0.2 + i * step;
      const x1 = x + bw + 0.1, x2 = x + w - bw - 0.1;
      if (m.dir === "right") arrow(s, x1, my, x2, my, m.kind === "open" ? AMBER : BLUE); else arrow(s, x2, my, x1, my, m.kind === "open" ? AMBER : BLUE);
      s.addText(m.label, { x: x1, y: my - 0.3, w: x2 - x1, h: 0.28, fontFace: MONO, fontSize: fitSize(m.label, x2 - x1, 9.5, 0.6), color: INK, align: "center", margin: 0 });
    });
    if (d.caption) s.addText(d.caption, { x, y: y + h + 0.05, w, h: 0.35, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE, align: "center", margin: 0 });
  },
  grid(s, d, x, y, w, h) {
    // a 2-axis matrix: cols x rows of cells with a label each; axis titles top and left
    const cols = d.cols, rows = d.rows;
    const lx = x + 1.3, ty = y + 0.45;
    const cw = (w - 1.3) / cols.length, rh = (h - 0.45) / rows.length;
    cols.forEach((c, i) => s.addText(c, { x: lx + i * cw, y, w: cw, h: 0.4, fontFace: BODY, fontSize: 11, bold: true, color: SOFT, align: "center", margin: 0 }));
    rows.forEach((r, j) => s.addText(r, { x, y: ty + j * rh, w: 1.25, h: rh, fontFace: BODY, fontSize: 11, bold: true, color: SOFT, valign: "middle", margin: 0 }));
    d.cells.forEach((cell, k) => {
      const i = k % cols.length, j = Math.floor(k / cols.length);
      box(s, lx + i * cw + 0.06, ty + j * rh + 0.06, cw - 0.12, rh - 0.12, cell.label, cell.sub, cell.kind || "spec", { size: 11.5, dashed: cell.dashed });
    });
  },
  tiles(s, d, x, y, w, h) {
    const t = d.items, per = Math.min(3, t.length), tw = (w - 0.25 * (per - 1)) / per;
    t.forEach((it, i) => stat(s, x + (i % per) * (tw + 0.25), y + Math.floor(i / per) * 1.45, tw, it.value, it.label, it.color === "amber" ? AMBER : it.color === "green" ? GREEN : BLUE));
  },
  skeleton(s, d, x, y, w, h) {
    // OpenUI Lang: statements on the left, the page skeleton on the right with pending slots
    const lines = d.lines;
    const lh = 0.34;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: w * 0.55, h, fill: { color: CODE_BG }, line: { color: CODE_BG }, rectRadius: 0.1 });
    s.addText(lines.map((l, i) => ({ text: l, options: { breakLine: i < lines.length - 1, fontFace: MONO, fontSize: 10.5, color: i < (d.arrived ?? lines.length) ? CODE_FG : CODE_DIM } })), { x: x + 0.15, y: y + 0.12, w: w * 0.55 - 0.3, h: h - 0.24, margin: 0, valign: "top", lineSpacingMultiple: 1.1 });
    const px = x + w * 0.58, pw = w * 0.42;
    s.addShape(pres.ShapeType.roundRect, { x: px, y, w: pw, h, fill: { color: "FFFFFF" }, line: { color: LINE }, rectRadius: 0.1 });
    (d.slots || []).forEach((sl, i) => {
      const sh = (h - 0.3) / d.slots.length - 0.1;
      box(s, px + 0.15, y + 0.15 + i * (sh + 0.1), pw - 0.3, sh, sl.label, sl.pending ? "waiting for its statement" : "", sl.pending ? "open" : "catalog", { dashed: sl.pending, size: 11 });
    });
    if (d.caption) s.addText(d.caption, { x, y: y + h + 0.05, w, h: 0.35, fontFace: BODY, fontSize: 10.5, italic: true, color: MUTE, align: "center", margin: 0 });
  },
};

// ----------------------------------------------------------------- code
function readSnippet(spec) {
  const file = path.join(GENUI, spec.file);
  const all = fs.readFileSync(file, "utf8").replace(/\r\n/g, "\n").split("\n");
  let start = 0;
  if (spec.from) {
    start = all.findIndex((l) => l.includes(spec.from));
    if (start < 0) throw new Error(`snippet anchor not found: ${spec.from} in ${spec.file}`);
  }
  let end = start + (spec.count || 14);
  if (spec.to) {
    const t = all.findIndex((l, i) => i >= start && l.includes(spec.to));
    if (t >= 0) end = t + 1;
  }
  let lines = all.slice(start, Math.min(end, all.length));
  if (spec.skip) lines = lines.filter((l) => !spec.skip.some((sk) => l.includes(sk)));
  const indent = Math.min(...lines.filter((l) => l.trim()).map((l) => l.match(/^ */)[0].length));
  lines = lines.map((l) => l.slice(indent));
  if (spec.maxWidth) lines = lines.map((l) => (l.length > spec.maxWidth ? l.slice(0, spec.maxWidth - 1) + "…" : l));
  return { lines, startLine: start + 1, longest: Math.max(...lines.map((l) => l.length)) };
}
function codeMetrics(snippet, w) {
  // font size and wrapped-line count for a code box of width w
  for (const pt of [10.5, 10, 9.5, 9]) {
    const cap = Math.floor(((w - 0.85) * 72) / (pt * 0.6));
    const rows = snippet.lines.reduce((acc, l) => acc + Math.max(1, Math.ceil((l.length + 4) / cap)), 0);
    if (rows <= 22 || pt === 9) return { pt, rows, lineH: (pt * 1.22) / 72 };
  }
  return { pt: 9, rows: snippet.lines.length, lineH: (9 * 1.22) / 72 };
}
function codeBlock(s, x, y, w, h, snippet, callouts = []) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: CODE_BG }, line: { color: CODE_BG }, rectRadius: 0.1 });
  const marks = new Map(callouts.map((c, i) => [c.line, i + 1]));
  const { pt } = codeMetrics(snippet, w);
  const runs = [];
  snippet.lines.forEach((l, i) => {
    const num = i + 1;
    const mark = marks.get(num);
    // the gutter carries the callout number in amber instead of the line number, so nothing overlaps
    runs.push({ text: (mark ? "[" + mark + "]" : String(num).padStart(3, " ")) + " ", options: { fontFace: MONO, fontSize: pt, bold: !!mark, color: mark ? "FBBF24" : CODE_DIM } });
    runs.push({ text: l || " ", options: { fontFace: MONO, fontSize: pt, color: mark ? "FDE68A" : CODE_FG, bold: !!mark, breakLine: i < snippet.lines.length - 1 } });
  });
  s.addText(runs, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h - 0.3, margin: 0, valign: "top", lineSpacingMultiple: 1.08 });
}

// ----------------------------------------------------------------- slide types
const SLIDES = {
  title(sl) {
    const s = pres.addSlide(); n += 1;
    s.background = { color: NAVY };
    s.addText(sl.kicker || "", { x: 0.8, y: 1.2, w: 11, h: 0.4, fontFace: BODY, fontSize: 13, color: "AAB4FF", bold: true, charSpacing: 3, margin: 0 });
    s.addText(sl.title, { x: 0.8, y: 1.7, w: 11.5, h: 1.6, fontFace: HEAD, fontSize: 48, bold: true, color: "FFFFFF", margin: 0, valign: "top" });
    s.addText(sl.subtitle || "", { x: 0.8, y: 3.4, w: 10.5, h: 1.0, fontFace: BODY, fontSize: 20, color: "CADCFC", margin: 0, valign: "top" });
    // the motif: four catalog cards and one dashed generated view
    const bx = 0.8, by = 4.9;
    ["Heading", "Card", "BarChart", "Button"].forEach((l, i) => {
      s.addShape(pres.ShapeType.roundRect, { x: bx + i * 1.55, y: by, w: 1.4, h: 0.75, fill: { color: "1E2761" }, line: { color: "AAB4FF", width: 1 }, rectRadius: 0.1 });
      s.addText(l, { x: bx + i * 1.55, y: by, w: 1.4, h: 0.75, fontFace: BODY, fontSize: 12, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    });
    s.addShape(pres.ShapeType.roundRect, { x: bx + 4 * 1.55 + 0.2, y: by, w: 3.2, h: 0.75, fill: { color: "1E2761" }, line: { color: "FBBF24", width: 1.25, dashType: "dash" }, rectRadius: 0.1 });
    s.addText("GeneratedView · sandboxed iframe", { x: bx + 4 * 1.55 + 0.2, y: by, w: 3.2, h: 0.75, fontFace: BODY, fontSize: 12, color: "FDE68A", align: "center", valign: "middle", margin: 0 });
    s.addText(sl.footer || "", { x: 0.8, y: 6.5, w: 11, h: 0.4, fontFace: BODY, fontSize: 12, color: "AAB4FF", margin: 0 });
    note(s, sl.notes);
  },
  section(sl) {
    const s = pres.addSlide(); n += 1;
    s.background = { color: NAVY };
    s.addText(sl.kicker || "", { x: 0.8, y: 0.9, w: 11, h: 0.4, fontFace: BODY, fontSize: 13, color: "AAB4FF", bold: true, charSpacing: 3, margin: 0 });
    s.addText(sl.title, { x: 0.8, y: 1.4, w: 11.5, h: 1.3, fontFace: HEAD, fontSize: 40, bold: true, color: "FFFFFF", margin: 0, valign: "top" });
    s.addText(sl.lead || "", { x: 0.8, y: 2.8, w: 7.2, h: 2.2, fontFace: BODY, fontSize: 16, color: "CADCFC", margin: 0, valign: "top" });
    (sl.steps || []).forEach((st, i) => {
      const y = 2.85 + i * 0.78;
      s.addShape(pres.ShapeType.roundRect, { x: 8.4, y, w: 4.3, h: 0.66, fill: { color: "1E2761" }, line: { color: "3B4A8A", width: 1 }, rectRadius: 0.08 });
      s.addText([{ text: st.id + "  ", options: { bold: true, color: "FDE68A" } }, { text: st.title, options: { color: "FFFFFF" } }], { x: 8.55, y, w: 4.05, h: 0.66, fontFace: BODY, fontSize: 12.5, valign: "middle", margin: 0 });
    });
    s.addText(String(n), { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 10, color: "6B7AB8", align: "right", margin: 0 });
    note(s, sl.notes);
  },
  theory(sl) {
    const s = base(sl.kicker, sl.title);
    const leftW = sl.diagram ? 5.6 : 12.1;
    const top = s._top;
    if (sl.headline) s.addText(rich(sl.headline), { x: 0.6, y: top, w: leftW, h: 0.9, fontFace: BODY, fontSize: 16, color: NAVY, margin: 0, valign: "top" });
    const by = sl.headline ? top + 0.95 : top + 0.05;
    const bottom = sl.takeaway ? 6.3 : 6.8;
    const btext = (sl.bullets || []).join(" ");
    let bsize = 13.5;
    const blines = (pt) => Math.ceil(btext.length / ((leftW * 72) / (pt * 0.5))) + (sl.bullets || []).length;
    while (bsize > 11 && blines(bsize) * ((bsize * 1.3) / 72) > bottom - by) bsize -= 0.5;
    s.addText(bullets(sl.bullets || [], bsize), { x: 0.6, y: by, w: leftW, h: bottom - by, margin: 0, valign: "top" });
    if (sl.diagram) DIAGRAMS[sl.diagram.type](s, sl.diagram, 6.6, top + 0.2, 6.1, Math.min(sl.diagram.height || 4.2, (sl.takeaway ? 6.0 : 6.5) - top - (sl.diagram.caption ? 0.4 : 0)));
    if (sl.takeaway) {
      s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 6.45, w: 12.1, h: 0.55, fill: { color: BLUE_TINT }, line: { color: BLUE_TINT }, rectRadius: 0.08 });
      s.addText([{ text: "Takeaway  ", options: { bold: true, color: BLUE } }, { text: sl.takeaway, options: { color: INK } }], { x: 0.8, y: 6.45, w: 11.7, h: 0.55, fontFace: BODY, fontSize: 12.5, valign: "middle", margin: 0 });
    }
    note(s, sl.notes);
  },
  code(sl) {
    const s = base(sl.kicker, sl.title);
    const snip = readSnippet(sl.snippet);
    const callouts = sl.callouts || [];
    const top = s._top;
    const codeW = callouts.length ? 8.1 : 12.1;
    const { rows, lineH } = codeMetrics(snip, codeW);
    const codeH = Math.min(6.3 - top, 0.45 + rows * lineH);
    codeBlock(s, 0.6, top, codeW, codeH, snip, callouts);
    s.addText(sl.snippet.file, { x: 0.6, y: top + codeH + 0.05, w: codeW, h: 0.3, fontFace: MONO, fontSize: 9.5, color: MUTE, margin: 0 });
    if (callouts.length) {
      const avail = 6.35 - top;
      callouts.forEach((c, i) => {
        const y = top + 0.05 + i * (avail / callouts.length);
        badge(s, 8.95, y, i + 1, AMBER, 0.32);
        s.addText(rich(c.text), { x: 9.4, y: y - 0.04, w: 3.35, h: avail / callouts.length - 0.1, fontFace: BODY, fontSize: 12, color: INK, margin: 0, valign: "top" });
      });
    }
    if (sl.caption) s.addText(rich(sl.caption), { x: 0.6, y: 6.45, w: 12.1, h: 0.6, fontFace: BODY, fontSize: 12.5, color: SOFT, margin: 0, valign: "middle" });
    note(s, sl.notes);
  },
  result(sl) {
    const s = base(sl.kicker, sl.title);
    let rightX = 0.6, rightW = 12.1;
    if (sl.image) {
      const img = path.join(GENUI, sl.image);
      const ih = sl.imageHeight || 4.9, iw = sl.imageWidth || 7.2;
      s.addImage({ path: img, x: 0.6, y: s._top, w: iw, h: ih, sizing: { type: "contain", w: iw, h: ih } });
      s.addShape(pres.ShapeType.rect, { x: 0.6, y: s._top, w: iw, h: ih, fill: { type: "none" }, line: { color: LINE, width: 1 } });
      rightX = 0.6 + iw + 0.4; rightW = W - rightX - 0.6;
    } else if (sl.output) {
      const lines = sl.output;
      s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: s._top, w: 7.2, h: 4.9, fill: { color: CODE_BG }, line: { color: CODE_BG }, rectRadius: 0.1 });
      s.addText(lines.map((l, i) => ({ text: l, options: { breakLine: i < lines.length - 1, fontFace: MONO, fontSize: lines.length > 18 ? 9 : 10, color: CODE_FG } })), { x: 0.8, y: s._top + 0.15, w: 6.8, h: 4.6, margin: 0, valign: "top" });
      rightX = 8.2; rightW = 4.5;
    }
    let y = s._top;
    const stats = (sl.stats || []).slice(0, sl.notice && sl.notice.length > 2 ? 2 : 3);
    stats.forEach((st) => { stat(s, rightX, y, rightW, st.value, st.label, st.color === "amber" ? AMBER : st.color === "green" ? GREEN : BLUE); y += 1.4; });
    if (sl.notice) {
      const room = (sl.caption ? 6.4 : 6.9) - y;
      const text = sl.notice.join(" ");
      let size = 12.5;
      const linesAt = (pt) => Math.ceil(text.length / ((rightW * 72) / (pt * 0.5))) + sl.notice.length;
      while (size > 10 && linesAt(size) * ((size * 1.25) / 72) > room) size -= 0.5;
      s.addText(bullets(sl.notice, size), { x: rightX, y: y + 0.05, w: rightW, h: room, margin: 0, valign: "top" });
    }
    if (sl.caption) s.addText(rich(sl.caption), { x: 0.6, y: 6.55, w: 12.1, h: 0.5, fontFace: BODY, fontSize: 12, color: SOFT, margin: 0, valign: "middle" });
    note(s, sl.notes);
  },
  chart(sl) {
    const s = base(sl.kicker, sl.title);
    const colors = [BLUE, AMBER, GREEN, ROSE, NAVY];
    s.addChart(pres.ChartType[sl.chartType || "bar"], sl.series.map((se) => ({ name: se.name, labels: sl.labels, values: se.values })), {
      x: 0.6, y: s._top, w: sl.bullets ? 7.6 : 12.1, h: 6.3 - s._top, barDir: sl.horizontal ? "bar" : "col", barGrouping: "clustered",
      chartColors: colors, showTitle: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: SOFT,
      catAxisLabelColor: SOFT, valAxisLabelColor: MUTE, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
      valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" }, showLegend: sl.series.length > 1, legendPos: "b", legendFontSize: 11,
      valAxisTitle: sl.valueTitle || "", showValAxisTitle: !!sl.valueTitle, valAxisTitleColor: SOFT, valAxisTitleFontSize: 10,
    });
    if (sl.bullets) s.addText(bullets(sl.bullets, 12.5), { x: 8.5, y: s._top + 0.1, w: 4.2, h: 6.2 - s._top, margin: 0, valign: "top" });
    if (sl.caption) s.addText(rich(sl.caption), { x: 0.6, y: 6.5, w: 12.1, h: 0.5, fontFace: BODY, fontSize: 12, color: SOFT, margin: 0, valign: "middle" });
    note(s, sl.notes);
  },
  table(sl) {
    const s = base(sl.kicker, sl.title);
    const head = sl.columns.map((c) => ({ text: c, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontFace: BODY, fontSize: 11.5 } }));
    const rows = sl.rows.map((r, i) => r.map((c, j) => ({ text: c, options: { fontFace: BODY, fontSize: 11, color: INK, bold: j === 0, fill: { color: i % 2 ? PAPER : "FFFFFF" } } })));
    s.addTable([head, ...rows], { x: 0.6, y: s._top, w: 12.1, colW: sl.colW, rowH: 0.36, border: { type: "solid", color: LINE, pt: 0.5 }, margin: 0.06, valign: "middle" });
    if (sl.caption) s.addText(rich(sl.caption), { x: 0.6, y: 6.55, w: 12.1, h: 0.5, fontFace: BODY, fontSize: 12, color: SOFT, margin: 0, valign: "middle" });
    note(s, sl.notes);
  },
  diagram(sl) {
    const s = base(sl.kicker, sl.title);
    if (sl.lead) s.addText(rich(sl.lead), { x: 0.6, y: s._top, w: 12.1, h: 0.6, fontFace: BODY, fontSize: 15, color: NAVY, margin: 0 });
    const dy = sl.lead ? s._top + 0.7 : s._top + 0.05;
    DIAGRAMS[sl.diagram.type](s, sl.diagram, 0.6, dy, 12.1, Math.min(sl.diagram.height || 3.9, (sl.takeaway ? 6.2 : 6.7) - dy));
    if (sl.takeaway) {
      s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 6.45, w: 12.1, h: 0.55, fill: { color: BLUE_TINT }, line: { color: BLUE_TINT }, rectRadius: 0.08 });
      s.addText([{ text: "Takeaway  ", options: { bold: true, color: BLUE } }, { text: sl.takeaway, options: { color: INK } }], { x: 0.8, y: 6.45, w: 11.7, h: 0.55, fontFace: BODY, fontSize: 12.5, valign: "middle", margin: 0 });
    }
    note(s, sl.notes);
  },
};

// ----------------------------------------------------------------- build
const files = fs.readdirSync(path.join(HERE, "content")).filter((f) => f.endsWith(".json") && (!ONLY || f === ONLY)).sort();
let count = 0;
for (const f of files) {
  const doc = JSON.parse(fs.readFileSync(path.join(HERE, "content", f), "utf8"));
  for (const sl of doc.slides) {
    if (!SLIDES[sl.type]) throw new Error(`${f}: unknown slide type ${sl.type}`);
    SLIDES[sl.type](sl);
    count += 1;
  }
  console.log(`${f}: ${doc.slides.length} slides`);
}
pres.writeFile({ fileName: OUT }).then(() => console.log(`wrote ${OUT} (${count} slides)`));
