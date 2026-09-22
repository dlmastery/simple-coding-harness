// Author walkthrough. Students ask the agent to create and run their implementation.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const out=resolve(repo,'../rsi-work-2026-09-21-procedure-graph');
if(existsSync(out))throw Error('Preserve previous workspace; choose a new declared run.');
mkdirSync(out);
const save=(p,s)=>{mkdirSync(dirname(resolve(out,p)),{recursive:true});writeFileSync(resolve(out,p),s.trimEnd()+'\n');};
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const original=hash(resolve(repo,'rsi/tools/lab.py'));
copyFileSync(script,resolve(out,'run-procedure-graph.mjs'));
copyFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/PROCEDURE-GRAPH-PROTOCOL.md'),resolve(out,'PROTOCOL.md'));
save('ENVIRONMENT.md', '# Environment\n\nNode '+process.version+'; '+process.platform+' '+process.arch+'.\n\nTool SHA-256: '+original+'\nSource driver SHA-256: '+hash(script)+'\n');
const parent='# Procedure graph\n\n| Node | Outcome | Next |\n|---|---|---|\n| inspect | valid | domain |\n| inspect | invalid | fit |\n| domain | valid | fit |\n| domain | invalid | diagnose |\n| fit | done | report |\n| report | done | stop |\n| diagnose | done | stop |';
save('parent.md',parent);
save('DOMAIN.md','# Domain facts\n\n| Subject | Relation | Object |\n|---|---|---|\n| experiment | uses feature | hr |\n| experiment | uses feature | weekday |');
const guide={inspect:['Check that every feature value is finite numeric.','valid or invalid'],domain:['Run the unchanged domain checker on declared facts.','valid or invalid'],fit:['Record a stub invocation. Do not train anything.','done'],report:['Record that the graph reached reporting, not a measured model result.','done'],diagnose:['Preserve the invalid case and stop this path.','done']};
const parse=file=>readFileSync(file,'utf8').split('\n').filter(x=>x.startsWith('|')&&!x.includes('---')).slice(1).map(x=>x.split('|').slice(1,-1).map(x=>x.trim()));
let traversals=0;
const rows=[];
function run(label,graph,fixture){
 traversals++; if(traversals>6)throw Error('Traversal budget exhausted.');
 const started=performance.now(),edges=parse(resolve(out,graph)); let state='inspect',fitCalls=0;
 const trace=[],folder=label;save(folder+'/INPUT.md','# Fixture\n\n'+fixture.description+'\n\n'+Object.entries(fixture.features).map(([k,v])=>k+': '+String(v)).join('\n'));
 save(folder+'/DOMAIN.md',fixture.facts||readFileSync(resolve(out,'DOMAIN.md'),'utf8'));
 for(let step=1;state!=='stop';step++){
  if(step>6)throw Error('Graph step budget exhausted');
  const routes=edges.filter(x=>x[0]===state),[action,completion]=guide[state];
  save(folder+'/step-'+step+'-before.md','# Before node '+state+'\n\nInput: INPUT.md and DOMAIN.md\n\nAction: '+action+'\n\nCompletion: '+completion+'\n\nAvailable edges:\n'+routes.map(x=>x.join(' → ')).join('\n')+'\n\nGraph SHA-256: '+hash(resolve(out,graph)));
  let outcome;
  if(state==='inspect')outcome=Object.values(fixture.features).every(x=>typeof x==='number'&&Number.isFinite(x))?'valid':'invalid';
  else if(state==='domain'){
   const result=spawnSync(resolve(repo,'.venv/Scripts/python.exe'),[resolve(repo,'rsi/tools/lab.py'),'audit-domain','--input',resolve(out,folder,'DOMAIN.md'),'--output',resolve(out,folder,'DOMAIN-CHECK.md')],{encoding:'utf8',timeout:60000,cwd:repo});
   save(folder+'/AUDIT-EXECUTION.md','# Domain subprocess\n\nExit: '+result.status+'\n\n'+result.stdout+'\n'+result.stderr);
   if(result.error||![0,1].includes(result.status))throw Error('Domain tool failed: '+result.error);
   outcome=result.status===0?'valid':'invalid';
  } else {outcome='done';if(state==='fit')fitCalls++;}
  const edge=routes.find(x=>x[1]===outcome);if(!edge)throw Error('No edge');
  trace.push([step,state,outcome,edge[2]].join(','));state=edge[2];
 }
 const path=trace.map(x=>x.split(',')[1]).join(' → ')+' → stop';
 save(folder+'/TRACE.csv','step,node,outcome,next\n'+trace.join('\n'));
 save(folder+'/RESULT.md','# Traversal result\n\nPath: '+path+'\n\nStub calls: '+fitCalls+'\nModel fits: 0\n');
 rows.push([label,graph,fitCalls,0,(performance.now()-started).toFixed(3)]);
 return {path,fitCalls};
}
const bad={description:'Constructed selection failure: hour is not numeric.',features:{hr:'unknown',weekday:2}};
const good={description:'Constructed regression control: permitted numeric calendar fields.',features:{hr:8,weekday:2}};
save('SELECTION-PLAN.md','# Selection cases\n\nInvalid hour must reach diagnosis with no fit stub. Valid calendar input must still reach reporting. Compare parent and child on both cases.');
const pbad=run('selection-invalid-parent','parent.md',bad),pgood=run('selection-valid-parent','parent.md',good);
if(pbad.fitCalls!==1||!pgood.path.includes('report'))throw Error('Parent fixtures do not expose the declared bug.');
save('CHANGE-PROPOSAL.md','# One transition edit\n\nObserved: invalid input reached the fit stub in the parent. Change inspect / invalid from fit to diagnose. Keep all other edges and domain rules unchanged. Require the two declared selection checks before retention.');
const child=parent.replace('| inspect | invalid | fit |','| inspect | invalid | diagnose |');
save('child.md',child);
const cbad=run('selection-invalid-child','child.md',bad),cgood=run('selection-valid-child','child.md',good);
if(cbad.fitCalls!==0||!cbad.path.includes('diagnose')||cgood.fitCalls!==1||!cgood.path.includes('report'))throw Error('Selection rejected; preserve all records.');
save('SELECTION-DECISION.md','# Selection decision\n\nRetain the child: the target failure is diagnosed, and the valid control still reaches reporting. Exactly one edge differs. No alternate candidate was proposed; there is no invented rejected edit.');
const frozen=hash(resolve(out,'child.md'));save('FREEZE.md','# Frozen graph\n\nchild.md SHA-256: '+frozen+'\n\nNo changes after this decision.');
const fresh=run('later-calendar','child.md',{description:'Distinct calendar fixture constructed after freezing; author-known, not blinded.',features:{hr:23,weekday:6}});
const semantic=run('later-semantic','child.md',{description:'Numeric target component passes types but violates the declared domain rule.',features:{casual:3},facts:'# Domain facts\n\n| Subject | Relation | Object |\n|---|---|---|\n| experiment | uses feature | casual |\n| casual | derived from | target |'});
if(fresh.fitCalls!==1||!fresh.path.includes('report')||semantic.fitCalls!==0||!semantic.path.includes('domain → diagnose'))throw Error('Frozen checks failed.');
if(hash(resolve(out,'child.md'))!==frozen||hash(resolve(repo,'rsi/tools/lab.py'))!==original)throw Error('Frozen artifact changed.');
save('COST.csv','traversal,graph,stub_calls,model_fits,wall_ms\n'+rows.map(x=>x.join(',')).join('\n'));
save('CHECKS.md','# Four fixture checks\n\n| Check | Observation |\n|---|---|\n| Target selection pair | Parent calls fit stub; child diagnoses without fitting |\n| Regression selection pair | Both retain the valid reporting route |\n| Frozen later calendar case | Reaches reporting; hash unchanged |\n| Frozen semantic case | Type check passes; domain audit rejects; no fit stub |\n\nSix traversals, one edge edit, zero model fits. All declared checks passed. This is a deterministic author fixture exercise, not independent agent adaptation, blinded transfer, a paper reproduction, or learner assessment. Wall times include subprocess startup; agent inference cost is unknown.');
save('PROGRESS.md','# Author progress\n\nAll four declared fixture checks executed. No learner predictions or quiz answers collected. No remaining traversal allowance. Preserve the workspace.');
const files=[];
function walk(dir=''){for(const e of readdirSync(resolve(out,dir),{withFileTypes:true})){const p=dir?dir+'/'+e.name:e.name;if(e.isDirectory())walk(p);else files.push(p);}}walk();
save('MANIFEST.csv','file,sha256\n'+files.sort().map(p=>p+','+hash(resolve(out,p))).join('\n'));
console.log('Completed four fixture checks / six graph traversals / zero fits. Workspace: '+out);
