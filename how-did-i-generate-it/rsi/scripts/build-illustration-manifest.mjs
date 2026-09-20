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
  ['meta-harness-v2','exec-c8fe1146-1b80-41ba-9834-45c5550eeb6d.png',true],
  ['graph-ontology-v1','exec-154a7383-143f-49de-8b39-45f30ac6991d.png',true],
  ['self-star-v1','exec-786ba075-a5ab-46ae-8058-f97a888049ab.png',false],
  ['self-star-v2','exec-3b9379c2-0515-473f-8035-017e6bedac22.png',true],
  ['inherited-improver-v1','exec-4450e321-9dbb-4db6-8d12-a82e01ee2c89.png',true],
  ['replay-boundary-v1','exec-a9f26ca9-51b3-43c0-9534-96711a0e0b3e.png',false],
  ['replay-boundary-v2','exec-e21a62ff-2908-4165-9775-e24bef03a33c.png',true],
  ['model-harness-v1','exec-d711210f-c637-48b6-96b0-a17c54576d1e.png',false],
  ['model-harness-v2','exec-e8221bb5-62a1-49ce-ac41-fb7c15980a17.png',false],
  ['model-harness-v3','exec-b9246c30-27c2-427e-ad3b-c6f7b9986fc5.png',false],
  ['model-harness-v4','exec-3c790a4e-c32e-480f-ab88-a174125e065c.png',true],
  ['actor-memory-v1','exec-35cdcc66-4edb-450f-b032-a7465ae575de.png',false],
  ['actor-memory-v2','exec-295e9fa9-8587-4632-b38b-b374e4f5b3c6.png',true],
  ['compute-contract-v1','exec-23bff6ac-66bf-4930-b243-d8b335fba9f7.png',false],
  ['compute-contract-v2','exec-76e9a404-6644-46d2-9fe7-4cc858c44441.png',true],
  ['nested-research-v1','exec-4fd9424b-b04d-4d71-ba20-9d5b94b97631.png',false],
  ['nested-research-v2','exec-36cafda0-7046-4511-a911-b15f850053b0.png',true],
  ['scientific-claim-v1','exec-fc49a94b-69cd-4821-a8c0-2ec1d1e53788.png',false],
  ['scientific-claim-v2','exec-83c64a76-0655-4628-a99a-198d564aeb37.png',true],
  ['data-science-process-v1','exec-b178eeb0-7f43-45e3-b10d-cfc948498221.png',false],
  ['data-science-process-v2','exec-c7bd4200-6fb7-4a3e-aa01-a207af53433c.png',false],
  ['data-science-process-v3','exec-25b01f66-df36-4dab-8b11-7bafcd9cd782.png',false],
  ['data-science-process-v4','exec-31c077dd-4c15-49a2-9e84-7814d2ad481d.png',true],
  ['modular-harness-v1','exec-cb2e8854-06c3-4d48-81d4-9f1c84d303cb.png',false],
  ['modular-harness-v2','exec-e125e687-f34f-4001-ad1c-980eb9f92af6.png',true],
  ['meta-skill-schedules-v1','exec-f369ff93-ff85-4773-a196-6f4d67121165.png',false],
  ['meta-skill-schedules-v2','exec-ef836f7e-ec20-43a8-a82a-6b3b7dbed7f5.png',false],
  ['meta-skill-schedules-v3','exec-716d81b6-be8d-466f-a52d-a7aebbf18840.png',true],
  ['system-coordination-v1','exec-0ac5c449-34fc-4b2d-8f5d-55c38848dbff.png',false],
  ['system-coordination-v2','exec-352b5076-052e-4ba0-b9f4-7b5abc0698fe.png',false],
  ['system-coordination-v3','exec-0e531d96-5253-4c2d-b390-a4fbb6040ce0.png',true]
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
