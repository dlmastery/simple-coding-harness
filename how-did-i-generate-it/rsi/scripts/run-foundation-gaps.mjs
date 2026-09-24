// Bounded author activities, not a native coding-agent or learner acceptance test.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const out=resolve(repo,'../rsi-work-2026-09-21-foundation-gaps');
if(existsSync(out))throw Error('Preserve existing workspace');
mkdirSync(out);
const save=(p,s)=>{mkdirSync(dirname(resolve(out,p)),{recursive:true});writeFileSync(resolve(out,p),s.trimEnd()+'\n');};
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
copyFileSync(script,resolve(out,'run-foundation-gaps.mjs'));
copyFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/FOUNDATION-GAPS-PROTOCOL.md'),resolve(out,'PROTOCOL.md'));
const baseTool=resolve(repo,'rsi/tools/lab.py'),baseHash=hash(baseTool),cost=[];
copyFileSync(baseTool,resolve(out,'lab-tool-snapshot.py'));
save('ENVIRONMENT.md','# Author environment\n\nNode: '+process.version+'; '+process.platform+' '+process.arch+'\nPython executable: repository .venv/Scripts/python.exe\nSource SHA-256: '+hash(script)+'\nBase tool SHA-256: '+baseHash+'\n\nStudent interface: natural language; all implementation is agent-written.');
// Lab 03.03: four cases, with the delayed-result extension inside the missing case.
save('03-03/PLAN.md','# Join contract\n\nRequested candidate A; contract v1. Require data and resource passes with matching identities. Stop the missing case at synthetic tick 1. A result arriving at tick 2 is archived without reopening the decision. Resource numbers are declared fixtures, not host measurements.');
const inputs=[
 {name:'matching',data:{candidate:'A',contract:'v1',values:[1,2]},resource:{candidate:'A',contract:'v1',requested:2,allowed:4},expected:'proceed'},
 {name:'missing',data:{candidate:'A',contract:'v1',values:[1,2]},resource:null,expected:'incomplete'},
 {name:'wrong-candidate',data:{candidate:'A',contract:'v1',values:[1,2]},resource:{candidate:'B',contract:'v1',requested:2,allowed:4},expected:'reject identity'},
 {name:'wrong-contract',data:{candidate:'A',contract:'v1',values:[1,2]},resource:{candidate:'A',contract:'v2',requested:2,allowed:4},expected:'reject contract'}
];
const dataCheck=x=>({kind:'data',candidate:x.candidate,contract:x.contract,status:x.values.every(Number.isFinite)?'pass':'fail'});
const resourceCheck=x=>({kind:'resource',candidate:x.candidate,contract:x.contract,status:x.requested<=x.allowed?'pass':'fail'});
function join(records){
 const data=records.filter(x=>x.kind==='data'),resource=records.filter(x=>x.kind==='resource');
 if(data.length!==1||resource.length!==1)return 'incomplete';
 if(records.some(x=>x.candidate!=='A'))return 'reject identity';
 if(records.some(x=>x.contract!=='v1'))return 'reject contract';
 return records.every(x=>x.status==='pass')?'proceed':'reject failed check';
}
const joinRows=[];
for(const fixture of inputs){
 const dir='03-03/'+fixture.name;
 save(dir+'/INPUT.md','# Teaching fixture\n\nData candidate: '+fixture.data.candidate+'\nData contract: '+fixture.data.contract+'\nValues: '+fixture.data.values.join(', ')+'\nResource: '+(fixture.resource?fixture.resource.candidate+' / '+fixture.resource.contract+' / requested '+fixture.resource.requested+' / allowed '+fixture.resource.allowed:'not arrived by tick 1')+'\nExpected join: '+fixture.expected);
 const start=performance.now(),records=[dataCheck(fixture.data)];if(fixture.resource)records.push(resourceCheck(fixture.resource));
 save(dir+'/CHECKS.csv','kind,candidate,contract,status\n'+records.map(x=>[x.kind,x.candidate,x.contract,x.status].join(',')).join('\n'));
 const verdict=join(records);if(verdict!==fixture.expected)throw Error('Join differs from declared outcome');
 save(dir+'/VERDICT.md','# Join result\n\n'+verdict+'\n\nSequential checks on teaching inputs; no resource measurement.');
 joinRows.push([fixture.name,fixture.expected,verdict]);cost.push(['03.03',fixture.name,(performance.now()-start).toFixed(3)]);
 if(fixture.name==='missing'){
  const late=resourceCheck({candidate:'A',contract:'v1',requested:2,allowed:4});
  save(dir+'/LATE-RESOURCE.csv','kind,candidate,contract,status\n'+[late.kind,late.candidate,late.contract,late.status].join(','));
  save(dir+'/DELAY-TRACE.md','# Simulated delivery\n\nTick 0: data result arrives.\nTick 1: stop limit reached; join returns incomplete.\nTick 2: resource result arrives and is archived. The stopped decision stays incomplete; no second join or model action is authorized.\n\nSynthetic ticks; no actual concurrent workers or timed sleep.');
 }
}
save('03-03/JOIN-REPORT.md','# Four observed scenarios\n\n| Case | Expected | Actual |\n|---|---|---|\n'+joinRows.map(r=>'| '+r.join(' | ')+' |').join('\n')+'\n\nOnly the complete matching pair proceeds. The delayed result is retained in the missing case without reopening its stopped decision.');
// Lab 04.03: all six tables are saved before any base-tool execution.
const table=rows=>'# Domain facts\n\n| Subject | Relation | Object |\n|---|---|---|\n'+rows.map(r=>'| '+r.join(' | ')+' |').join('\n');
const baseCases=[
 ['feature-pass',[['model','uses feature','hr']],0],
 ['feature-fail',[['model','uses feature','total_users'],['total_users','derived from','target']],1],
 ['transform-pass',[['scaler','fit on','train']],0],
 ['transform-fail',[['scaler','fit on','final']],1],
 ['selection-pass',[['search','selects on','selection']],0],
 ['selection-fail',[['search','selects on','final']],1]
];
save('04-03/RULES.md','# Three invariants\n\n1. An input with a declared direct derivation from target must not be used as a feature.\n2. A fitted transform uses train only.\n3. Search must not select on final.\n\nThese are declared-fact checks, not inference about omitted facts. Unknown relation names are rejected by the supplied implementation; a separate unknown-relation case is outside this run allowance.');
for(const [name,rows] of baseCases)save('04-03/'+name+'/DOMAIN.md',table(rows));
// Lab 04.04: original, corrected, and consistently renamed tables are separate.
const bad=[['model','uses feature','total_users'],['total_users','derived from','target'],['scaler','fit on','final'],['search','selects on','final']];
save('04-04/original/DOMAIN.md',table(bad));
save('04-04/corrected/DOMAIN.md',table([['model','uses feature','hr'],['scaler','fit on','train'],['search','selects on','selection']]));
save('04-04/renamed/DOMAIN.md',table(bad.map(row=>row.map(cell=>cell==='total_users'?'harmless_feature':cell))));
const frozenInputs=[...baseCases.map(([name])=>'04-03/'+name+'/DOMAIN.md'),...['original','corrected','renamed'].map(name=>'04-04/'+name+'/DOMAIN.md')];
const identities=new Map(frozenInputs.map(p=>[p,hash(resolve(out,p))]));
save('DOMAIN-INPUT-FREEZE.md','# Before domain execution\n\n'+[...identities].map(([p,h])=>p+': '+h).join('\n')+'\nBase tool: '+baseHash);
let domainCalls=0;
function domain(folder,count){
 if(++domainCalls>9)throw Error('Domain check allowance exhausted');
 const start=performance.now();
 const result=spawnSync(resolve(repo,'.venv/Scripts/python.exe'),[baseTool,'audit-domain','--input',resolve(out,folder,'DOMAIN.md'),'--output',resolve(out,folder,'DOMAIN-CHECK.md')],{cwd:repo,encoding:'utf8',timeout:60000});
 save(folder+'/EXECUTION.md','# Domain execution\n\nExit: '+result.status+'\nStdout:\n'+result.stdout+'\nStderr:\n'+(result.stderr||'(empty)'));
 cost.push([folder.split('/')[0].replace('-','.'),folder.split('/')[1],(performance.now()-start).toFixed(3)]);
 if(result.error||result.status!==(count?1:0))throw Error('Unexpected domain subprocess outcome');
 const actual=(readFileSync(resolve(out,folder,'DOMAIN-CHECK.md'),'utf8').match(/^- FAIL:/gm)||[]).length;
 if(actual!==count)throw Error('Unexpected invariant failure count');
 return actual;
}
const ruleRows=[];
for(const [name,,expected] of baseCases)ruleRows.push([name,expected,domain('04-03/'+name,expected)]);
save('04-03/RULE-TESTS.md','# Observed base-rule results\n\n| Case | Expected violations | Actual violations |\n|---|---:|---:|\n'+ruleRows.map(r=>'| '+r.join(' | ')+' |').join('\n'));
// Units is a workspace extension, separate from the original relation checker.
save('04-03/units-check.mjs',`import {readFileSync} from 'node:fs';
const text=readFileSync(process.argv[2],'utf8');
const metric=/^Metric: (.*)$/m.exec(text)?.[1]?.trim();
const units=/^Units: (.*)$/m.exec(text)?.[1]?.trim();
const ok=metric==='MAE'&&Boolean(units);
console.log(ok?'PASS: MAE has a nonempty unit label':'FAIL: this MAE fixture needs a nonempty unit label');
process.exitCode=ok?0:1;`);
save('04-03/units-present.md','Metric: MAE\nValue: 12.5\nUnits: rentals per hour');
save('04-03/units-missing.md','Metric: MAE\nValue: 12.5');
const unitFiles=['04-03/units-check.mjs','04-03/units-present.md','04-03/units-missing.md'];
const unitsFrozen=new Map(unitFiles.map(p=>[p,hash(resolve(out,p))]));
save('04-03/UNITS-FREEZE.md','# Before extension checks\n\n'+[...unitsFrozen].map(([p,h])=>p+': '+h).join('\n')+'\n\nOnly nonempty units are checked. Dimensional validity and metric recomputation are outside this extension.');
for(const [name,expected] of [['units-present',0],['units-missing',1]]){
 const start=performance.now(),result=spawnSync(process.execPath,[resolve(out,'04-03/units-check.mjs'),resolve(out,'04-03/'+name+'.md')],{encoding:'utf8',timeout:60000});
 save('04-03/'+name+'-RESULT.md','# Units check\n\nExit: '+result.status+'\n\n'+result.stdout+'\nStderr: '+(result.stderr||'(empty)'));
 cost.push(['04.03',name,(performance.now()-start).toFixed(3)]);
 if(result.error||result.status!==expected)throw Error('Unexpected extension result');
}
const contradictionRows=[];
for(const [name,expected] of [['original',3],['corrected',0],['renamed',3]])contradictionRows.push([name,expected,domain('04-04/'+name,expected)]);
save('04-04/REPAIR-REPORT.md','# Observed relation checks\n\n| Table | Expected violations | Actual violations |\n|---|---:|---:|\n'+contradictionRows.map(r=>'| '+r.join(' | ')+' |').join('\n')+'\n\nThe renamed copy still fails because its derivation fact remains. A real leaked experiment would need corrected features, a train-only transform refit, and renewed comparison under a valid split protocol. A consumed final set cannot become unseen by rewriting a table; retain exposure history and establish an appropriate new final evaluation. No training was performed here.');
for(const [p,h] of [...identities,...unitsFrozen])if(hash(resolve(out,p))!==h)throw Error('Frozen artifact changed: '+p);
if(hash(baseTool)!==baseHash)throw Error('Supplied tool changed');
save('COST.csv','lab,case,wall_ms\n'+cost.map(r=>r.join(',')).join('\n'));
save('PROGRESS.md','# Author progress\n\n03.03: four join scenarios complete, delayed arrival recorded within the missing case.\n04.03: six base cases and two extension cases complete.\n04.04: original, corrected, and consistently renamed checks complete.\nZero model fits. No activity allowance remains. Learner prediction, teach-back, and quiz untested. Inference costs unknown. Sequential teaching fixtures do not establish agent-context isolation or measured cluster resources.');
const files=[];function walk(dir=''){for(const e of readdirSync(resolve(out,dir),{withFileTypes:true})){const p=dir?dir+'/'+e.name:e.name;if(e.isDirectory())walk(p);else files.push(p);}}walk();
save('MANIFEST.csv','file,sha256\n'+files.sort().map(p=>p+','+hash(resolve(out,p))).join('\n'));
console.log('Four joins, nine domain checks, two extension checks completed. Workspace: '+out);
