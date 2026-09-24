// A retained visual-review artifact; not part of the student run path.
import {writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {lessons} from './lesson-content.mjs';
import {renderDiagram} from './lesson-diagrams.mjs';
const filename=process.argv[2] || 'diagram-gallery.md';
if (!/^diagram-gallery(?:-v\d+)?\.md$/.test(filename)) throw new Error('Use a versioned diagram-gallery filename.');
const output=resolve(dirname(fileURLToPath(import.meta.url)), '../visuals',filename);
if(existsSync(output)) throw new Error('Preserve the existing gallery. Supply a new versioned filename.');
mkdirSync(dirname(output), {recursive:true});
const requested=process.argv[3]?.split(',');
const selected=requested?lessons.filter(l=>requested.includes(l.id)):lessons;
if(requested && selected.length!==requested.length) throw new Error('Unknown or duplicate requested lesson ID.');
writeFileSync(output, '# Technical schematic review gallery\n\nOriginal Mermaid diagrams. These are not Imagen-generated illustrations.\n\n'+
  selected.map(l=>`## ${l.id} · ${l.title}\n\n${renderDiagram(l.id)}`).join('\n\n')+'\n');
console.log(`Prepared ${selected.length} diagrams for rendering.`);
