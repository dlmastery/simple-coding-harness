// Recorded editorial migration. Each replacement is checked, and reruns are harmless.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {renderDiagram} from './lesson-diagrams.mjs';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
function replace(file,old,next){
  const path=resolve(repo,file),text=readFileSync(path,'utf8');
  if(text.includes(next)) return;
  if(!text.includes(old)) throw new Error(`Missing editorial source in ${file}`);
  writeFileSync(path,text.replace(old,next));
}
const lessons='how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs';
replace(lessons,'Let two roles challenge each other while keeping correctness grounded in an external check.','Use a small game to observe experience, feedback, and a retained self-play learning update.');
replace(lessons,'The evaluator measures outcomes under fixed rules. Recursion concerns','The external evaluator measures outcomes under fixed rules. An improver may change its internal proposal-ranking or promotion rule; that changed procedure is still judged by the unchanged external comparison. Recursion concerns');
replace(lessons,'Move the promotion rule into the editable candidate surface in a labelled diagram. Explain how this can inflate acceptance without improving capability.','In a labelled diagram, let a candidate change the external final metric after seeing its result. Explain why that invalidates the comparison. Contrast it with a candidate improver changing its internal proposal-selection rule while the external metric, final cases, and resource budget stay fixed.');
replace(lessons,'Otherwise a system can appear better by changing the measurement or acceptance rule.','Otherwise a system can appear better by changing the external measurement or final acceptance criterion. Internal candidate-selection rules may change if the unchanged external evaluator judges the resulting procedure.');
replace(lessons,'This changes the procedure for improving task skills. The proposal remains a hypothesis','This changes the procedure for improving task skills. Its internal promotion rule is a legitimate target; the external cases, metric, and comparison budget used to judge that change stay fixed. The proposal remains a hypothesis');
replace('how-did-i-generate-it/rsi/scripts/lesson-content.mjs','Each lab changes one property of the same small research workflow. Ask what persists and what observation would establish a benefit.','Most labs use the small ML workflow. Queue simulations expose organization and emergence; a tiny game exposes actual self-play learning. Ask what persists and what observation would establish a benefit.');
replace('how-did-i-generate-it/rsi/scripts/publish-diagrams.mjs',"'07.07':['v4',1]","'07.07':['v5',1]");
replace('how-did-i-generate-it/rsi/scripts/publish-diagrams.mjs',"'rendered-gallery-v4.md']","'rendered-gallery-v4.md','rendered-gallery-v5.md']");
const dir=resolve(repo,'how-did-i-generate-it/rsi/visuals/rendered-v5');
mkdirSync(dir,{recursive:true});
// A vertical layout keeps the new learning mechanism readable on a narrow page.
const source=renderDiagram('07.07').match(/```mermaid\n([\s\S]*?)\n```/)[1].replace('flowchart LR','flowchart TD');
writeFileSync(resolve(dir,'self-play.mmd'),source+'\n');
writeFileSync(resolve(dir,'../rendered-gallery-v5.md'),'# Self-play learning diagram revision\n\nLab 07.07 now executes tabular learning. This replaces the earlier interaction-only diagram. Fixed rules produce actual table updates; frozen evaluation remains outside training. Rendered with Mermaid CLI on white, not Imagen. Earlier revisions remain available.\n\n![Learning and frozen evaluation](rendered-v5/rendered-gallery-v5-1.png)\n');
console.log('Updated self-play and evaluator boundaries; prepared v5 diagram source.');
