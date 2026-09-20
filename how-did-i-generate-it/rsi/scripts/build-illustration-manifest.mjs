// Agent-authored provenance check; students do not run this script.
import {readFileSync, writeFileSync, existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const repo=resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const folder=resolve(repo,'how-did-i-generate-it/rsi/visuals/generated');
const outputs=[
  ['main-overview-v1','exec-5bc0cf68-f09e-414a-bfaf-a34a2ff8d422.png',false],
  ['main-overview-v2','exec-a03901fb-38b7-448d-a3ef-65549e170b46.png',true],
  ['target-leakage-v1','exec-8bea4f88-87c8-4950-a229-c1339ebf05ac.png',false],
  ['target-leakage-v2','exec-6e99a51f-61a1-4b2e-85cd-33728bc3c6f8.png',true],
  ['bounded-loop-v1','exec-362f1817-ee12-4f7b-b15d-204687892372.png',true],
  ['meta-harness-v1','exec-614d8741-99e9-4126-b79b-a50dba8eb455.png',false],
  ['meta-harness-v2','exec-c8fe1146-1b80-41ba-9834-45c5550eeb6d.png',true]
];
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const rows=['artifact,prompt,tool,model,original_output,width,height,bytes,sha256,published_copy,status'];
for (const [stem,original,selected] of outputs) {
  const file=`${stem}.png`, prompt=`${stem}.prompt.md`;
  if (!existsSync(resolve(folder,prompt))) throw new Error(`Missing prompt: ${prompt}`);
  const bytes=readFileSync(resolve(folder,file));
  if (!bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))) throw new Error(`Not PNG: ${file}`);
  const published=selected ? `rsi/assets/illustrations/${file}` : '';
  if (selected && hash(readFileSync(resolve(repo,published)))!==hash(bytes)) throw new Error(`Changed copy: ${file}`);
  rows.push([file,prompt,'built-in image_gen','not exposed',original,bytes.readUInt32BE(16),bytes.readUInt32BE(20),bytes.length,hash(bytes),published,selected?'selected after full-size review':'superseded; retained'].join(','));
}
writeFileSync(resolve(folder,'MANIFEST.csv'),rows.join('\n')+'\n');
console.log(`Recorded ${outputs.length} generated PNGs and verified ${outputs.filter(x=>x[2]).length} published copies.`);
