// Publish reviewed technical schematics as portable static images.
import {readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {lessons} from './lesson-content.mjs';
const repo=resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const provenance=resolve(repo, 'how-did-i-generate-it/rsi/visuals');
const destination=resolve(repo, 'rsi/assets/diagrams');
mkdirSync(destination,{recursive:true});
const records=[];
for(const [i,l] of lessons.entries()) {
  const overrides={'00.01':['v3',1], '07.07':['v5',1], '10.07':['v6',1]};
  const [revision,index]=overrides[l.id] || ['v2',i+1];
  const input=resolve(provenance,`rendered-${revision}/rendered-gallery-${revision}-${index}.png`);
  if(!existsSync(input)) throw new Error(`Rendering is incomplete: ${input}`);
  const bytes=readFileSync(input);
  if(bytes.subarray(0,8).toString('hex')!=='89504e470d0a1a0a') throw new Error('Expected PNG image.');
  const filename=`lab-${l.id.replace('.','-')}.png`;
  copyFileSync(input,resolve(destination,filename));
  const hash=createHash('sha256').update(bytes).digest('hex');
  records.push(`| ${l.id} | ${revision}, ${index} | ${bytes.readUInt32BE(16)} × ${bytes.readUInt32BE(20)} | ${hash} |`);
}
writeFileSync(resolve(destination,'README.md'),`# Technical schematics\n\nOriginal course diagrams rendered with Mermaid CLI 11.17.0 on a white background. These are schematic explanations, not measured results or Imagen-generated illustrations.\n\nThe [source and review record](../../../how-did-i-generate-it/rsi/visuals/REVIEW.md) retains the first and revised galleries. Each published image maps to its gallery revision and index below. Source code: [lesson-diagrams.mjs](../../../how-did-i-generate-it/rsi/scripts/lesson-diagrams.mjs).\n\n| Lab | Gallery revision and index | Pixels | SHA-256 |\n|---|---|---|---|\n${records.join('\n')}\n`);
// Mermaid CLI emits Windows separators in Markdown image targets. Normalize for GitHub.
for(const filename of ['rendered-gallery.md','rendered-gallery-v2.md','rendered-gallery-v3.md','rendered-gallery-v4.md','rendered-gallery-v5.md']) {
  const path=resolve(provenance,filename);
  writeFileSync(path,readFileSync(path,'utf8').replaceAll('\\','/'));
}
console.log(`Published ${records.length} static diagrams with source mappings and hashes.`);
