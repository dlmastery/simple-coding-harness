// Coverage inventory, not an automated judgment of teaching quality.
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, resolve, relative, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {lessons, themes} from './lesson-content.mjs';
import {examples} from './lesson-examples.mjs';
import {guidance} from './lesson-guidance.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const report=resolve(repo, 'how-did-i-generate-it/rsi/validation/README-GUIDANCE-COVERAGE.md');
const known=new Set(lessons.map(l=>l.id));
for (const [id,support] of Object.entries(guidance)) {
  if (!known.has(id)) throw new Error(`Unknown lesson support: ${id}`);
  if (!(support.example || examples[id]) || !support.recovery || !support.hint || !support.outputs?.length)
    throw new Error(`Incomplete teaching support: ${id}`);
  if (support.outputs.some(row=>row.length !== 2 || row.some(cell=>!cell.trim())))
    throw new Error(`Incomplete output description: ${id}`);
}
let curated=0, concrete=0;
const rows=lessons.map(l=>{
  const support=guidance[l.id], worked=Boolean(support?.example || examples[l.id]);
  if(support) curated++;
  if(worked) concrete++;
  const file=resolve(repo,'rsi',themes[l.theme].directory,l.group || '',`step_${l.id.slice(3)}_${l.slug}`,'README.md');
  const body=readFileSync(file,'utf8');
  if(support && (!body.includes(support.recovery) || !body.includes(support.hint) || !body.includes('### Open these outputs')))
    throw new Error(`Generated README is stale: ${l.id}`);
  const href=relative(dirname(report),file).split(sep).join('/');
  return `| [${l.id}](${href}) | ${worked?'present':'missing'} | ${support?'authored':'pending'} | ${support?'specific':'generic or pending'} | ${support?'specific':'generic or pending'} |`;
});
writeFileSync(report,`# README teaching-support coverage

Generated from the current lesson source and published READMEs. This inventory checks presence and source/publication agreement. It does not establish factual correctness, visual quality, runtime completion, or student learning.

${curated} of ${lessons.length} lessons have individually authored output guides, recovery advice, and hints in the current editorial pass. ${concrete} have a worked example. The remaining rows stay visibly pending; having a section heading is not counted as having the missing teaching content.

The [completion ledger](../COURSE-COMPLETION-LEDGER.md) retains the full scope. Editorial observations and actual execution evidence remain separate.

| Lab | Worked example | Output guide | Recovery | Quiz hint |
|---|---|---|---|---|
${rows.join('\n')}
`, 'utf8');
console.log(`Teaching support: ${curated}/${lessons.length}; worked examples: ${concrete}/${lessons.length}.`);
