// Read-only reconciliation of existing runs; no fitting or model loading.
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname, resolve, relative} from 'node:path';
import {fileURLToPath} from 'node:url';
const repo=resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const root=resolve(repo,'rsi/evidence/2026-09-20/clean-journey/09-05');
const out=resolve(repo,'how-did-i-generate-it/rsi/validation/rsi-reading-review');
mkdirSync(out,{recursive:true});
const read=p=>readFileSync(p,'utf8');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const checks=[], identities=[];
const check=(name,pass)=>checks.push({name,pass:Boolean(pass)});
const identify=p=>{const value=hash(p);identities.push([relative(repo,p).replaceAll('\\','/'),value]);return value;};
// The selected retained tables have simple, unquoted fields. Refuse other CSVs.
const table=name=>{const raw=read(resolve(root,name));if(raw.includes('"'))throw new Error('Unexpected quoted CSV');const [head,...rows]=raw.trim().split(/\r?\n/).map(x=>x.split(','));return rows.map(row=>{if(row.length!==head.length)throw new Error('Malformed table');return Object.fromEntries(head.map((key,i)=>[key,row[i]]));});};
const source=read(resolve(root,'SOURCE.md'));
const driver=identify(resolve(repo,'how-did-i-generate-it/rsi/scripts/run-matched-improver.py'));
check('historical driver identity',source.includes(driver));
const protocol=identify(resolve(root,'PROTOCOL.md'));
check('historical protocol identity',source.includes(protocol));
const versions={};
for(const version of ['v0','v1']) versions[version]=identify(resolve(root,`skills/IMPROVER-${version}.md`));
const skillHashes=['parent','child'].map(name=>identify(resolve(root,`skills/TASK-SKILL-${name}.md`)));
check('frozen decision bytes',identify(resolve(root,'FROZEN-DECISIONS.csv'))===read(resolve(root,'FROZEN-DECISIONS.sha256')).trim());
const fixtures=table('DIAGNOSTIC-FIXTURES.csv');
check('two diagnostic cases under both versions',fixtures.length===4&&new Set(fixtures.map(r=>r.fixture)).size===2);
check('diagnostic version binding',fixtures.every(r=>r.improver_sha256===versions[r.improver]));
check('diagnostic outcomes',fixtures.map(r=>r.promoted).join(',')==='True,False,True,True');
const decisions=table('FROZEN-DECISIONS.csv');
check('four task and version decisions',decisions.length===4&&new Set(decisions.map(r=>r.task+'/'+r.improver)).size===4);
check('eight historical fits',table('FIT-COSTS.csv').reduce((sum,r)=>sum+Number(r.fits),0)===8);
for(const task of ['regression','classification']){
 const dataHash=identify(resolve(root,`cases/${task}.csv`));
 check(`${task} data identity`,table('DATA-IDENTITIES.csv').filter(r=>r.task===task).every(r=>r.data_sha256===dataHash));
 for(const version of ['v0','v1']){
  const row=decisions.find(r=>r.task===task&&r.improver===version);
  const before=read(resolve(root,`rounds/${task}/${version}/BEFORE.md`));
  const decision=read(resolve(root,`rounds/${task}/${version}/DECISION.md`));
  check(`${task}/${version} identities`,row.improver_sha256===versions[version]&&[versions[version],dataHash,...skillHashes].every(h=>before.includes(h))&&decision.includes(versions[version]));
 }
 for(const candidate of ['parent','child']) for(const partition of ['training','selection']){
  const paths=['v0','v1'].map(v=>resolve(root,`rounds/${task}/${v}/${candidate}/${partition}-predictions.csv`));
  check(`${task}/${candidate}/${partition} matched predictions`,identify(paths[0])===identify(paths[1]));
 }
}
const regression=decisions.filter(r=>r.task==='regression');
check('observed regression decision difference',regression.find(r=>r.improver==='v0').retained==='child'&&regression.find(r=>r.improver==='v1').retained==='parent');
const pointerRows=['v1','v0'].map(version=>{
 const path=resolve(root,`skills/IMPROVER-${version}.md`), text=read(path);
 const found=['training','selection'].filter(part=>text.includes(`only if its ${part} score is strictly better`));
 if(found.length!==1)throw new Error('Ambiguous recorded rule');
 const partition=found[0], values=regression[0];
 const retained=Number(values['child_'+partition])<Number(values['parent_'+partition])?'child':'parent';
 return {version,partition,retained};
});
check('no-fit pointer replay matches saved decisions',pointerRows.every(row=>regression.find(r=>r.improver===row.version).retained===row.retained));
writeFileSync(resolve(out,'SOURCE-IDENTITIES.csv'),'path,sha256\n'+identities.map(row=>row.join(',')).join('\n')+'\n');
writeFileSync(resolve(out,'CHECKS.csv'),'check,passed\n'+checks.map(row=>`${row.name},${row.pass}`).join('\n')+'\n');
writeFileSync(resolve(out,'POINTER-REPLAY.md'),`# Swap the pointer without rerunning the experiment\n\nThis is a new deterministic replay of saved scores, not a new fit or an independent agent decision. Both procedure files are read. The active pointer is an in-memory selection; the historical workspace stays unchanged.\n\n| Selected version | Governing partition | Retained skill |\n|---|---|---|\n${pointerRows.map(r=>`| ${r.version} | ${r.partition} | ${r.retained} |`).join('\n')}\n\nUnder v0, the selection-based promotion requirement disappears. The task, external MAE, data, and final evaluation do not change. Both original procedures compute training and selection scores; the changed action is which score governs retention, not whether the other score exists.\n`);
const failed=checks.filter(c=>!c.pass);
console.log(`${checks.length-failed.length}/${checks.length} checks passed; ${identities.length} source identities; zero fits.`);
if(failed.length){console.error(failed);process.exitCode=1;}
