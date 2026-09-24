// Add explicit orientation without replacing the existing lesson explanations.
import {readFileSync, writeFileSync, readdirSync} from 'node:fs';
import {resolve, relative, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../genui');
const themes = readdirSync(root).filter(name => /^\d\d_/.test(name)).sort();
const diagrams = [
  ['The agent chooses; the application renders.', 'A[Agent output] --> V[Validate component and props]\nV --> R[Application renderer]\nR --> P[Visible card or layout]'],
  ['Events carry a run; state determines what the page displays.', 'A[Agent run] --> E[Events and state patches]\nE --> C[Client applies updates]\nC --> P[Page renders state]\nP -->|user action| A'],
  ['Component structure and application data meet at the renderer.', 'S[Surface components] --> R[Catalog renderer]\nD[Data model] --> R\nR --> U[Visible interface]\nU -->|action and values| A[Application]'],
  ['Parsing and reference resolution happen before components are rendered.', 'L[UI language stream] --> P[Parser]\nP --> V[Resolve and validate references]\nV --> R[Component renderer]'],
  ['A catalog defines the allowed UI; patches change its state over time.', 'C[Component catalog] --> V[Validate spec]\nS[Spec and patches] --> V\nV --> R[Target renderer]\nR --> A[Named user action]'],
  ['The host controls the bridge to an embedded app.', 'T[Tool result] --> H[Host reads UI resource]\nH --> F[Sandboxed app frame]\nF --> B[Host bridge]\nB --> G[Allowed host operations]'],
  ['The interface becomes one part of a complete agent workflow.', 'A[Agent loop] --> T[Render tool or UI output]\nT --> V[Validate and render]\nV --> U[User action]\nU --> G[Application checks action]\nG --> A'],
];
const all = themes.flatMap(theme => readdirSync(resolve(root, theme)).filter(n => n.startsWith('step_')).sort().map(step => ({theme,step,path:resolve(root,theme,step,'README.md')})));
const link = (from,to) => relative(dirname(from),to).replaceAll('\\','/');
function insert(path, body) {
  const text = readFileSync(path,'utf8');
  if (text.includes('<!-- genui-orientation -->')) return;
  const firstBreak = text.indexOf('\n');
  writeFileSync(path,text.slice(0,firstBreak+1)+'\n<!-- genui-orientation -->\n'+body+'\n<!-- /genui-orientation -->\n'+text.slice(firstBreak+1));
}
themes.forEach((theme,index) => {
  const path=resolve(root,theme,'README.md');
  const nav=['[Course map](../README.md#see-the-learning-path)', '[Recorded walkthrough](../WALKTHROUGH.md)'];
  if(index>0) nav.push(`[Previous theme](../${themes[index-1]}/README.md)`);
  if(index<themes.length-1) nav.push(`[Next theme](../${themes[index+1]}/README.md)`);
  const [caption, diagram]=diagrams[index];
  insert(path,`**You are here: theme ${index+1} of 7.** ${nav.join(' · ')}\n\n\`\`\`mermaid\nflowchart LR\n${diagram}\n\`\`\`\n\n*${caption}*\n`);
});
all.forEach((lesson,index) => {
  const nav=['[Course](../../README.md)', '[Theme](../README.md)'];
  if(index>0) nav.push(`[Previous lesson](${link(lesson.path,all[index-1].path)})`);
  if(index<all.length-1) nav.push(`[Next lesson](${link(lesson.path,all[index+1].path)})`);
  insert(lesson.path,`**Lesson ${index+1} of ${all.length}.** ${nav.join(' · ')}\n`);
});
console.log(`Oriented ${themes.length} themes and ${all.length} lessons.`);
