// Author verification driver. Students request these actions through the tutor.
import {readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync, readdirSync, statSync} from 'node:fs';
import {resolve, dirname, relative, sep, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';

const script = fileURLToPath(import.meta.url);
const repo = resolve(dirname(script), '../../..');
const [phase, destination] = process.argv.slice(2);
if (!destination) throw Error('Supply phase and sibling output path');
const out = resolve(destination);
if (out === repo || out.startsWith(repo + sep)) throw Error('Use a sibling workspace');
const sha = p => createHash('sha256').update(readFileSync(p)).digest('hex');
const read = p => readFileSync(join(out,p), 'utf8');
const save = (p,s) => {mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const absent = p => {if(existsSync(join(out,p))) throw Error('Preserve existing phase: '+p);};
const fields = s => Object.fromEntries(s.split(/\r?\n/).filter(x=>x.includes(': ')).map(x=>{const i=x.indexOf(': ');return[x.slice(0,i),x.slice(i+2)];}));
const table = (p,cols,data) => save(p,[cols,...data].map(row=>row.map(String).map(v=>/[",\n]/.test(v)?'"'+v.replaceAll('"','""')+'"':v).join(',')).join('\n'));
const identity = p => sha(join(out,p));
const frozen = () => {if(identity('skills/META-SKILL-v0.md')!==fields(read('FREEZE.md'))['Updater SHA-256']) throw Error('Original updater changed');if(sha(script)!==fields(read('FREEZE.md'))['Driver SHA-256']) throw Error('Driver changed');};
const cases = {
  seconds: {rows:[['A',10,.8,'second'],['B',10,1,'second']],expected:'A'},
  milliseconds: {rows:[['A',10,800,'millisecond'],['B',10,1,'second']],expected:'A'},
  minutes: {rows:[['A',10,.02,'minute'],['B',10,.8,'second']],expected:'B'},
  microseconds: {rows:[['A',10,800,'microsecond'],['B',10,.001,'second']],expected:'A'},
  unknown: {rows:[['A',10,.001,'tick'],['B',10,1,'second']],expected:'refused'}
};
function decide(skill, fixture) {
  const data = fields(read(skill));
  const options=[];
  for(const [candidate,mae,duration,unit] of fixture.rows){
    const factor=data['Seconds per '+unit];
    if(factor===undefined && data['Unknown units']==='refuse') return {actual:'refused',converted:options,reason:'unsupported duration unit: '+unit};
    options.push([candidate,mae,duration*Number(factor??1),unit,factor===undefined?'assumed identity':'declared conversion']);
  }
  options.sort((a,b)=>a[1]-b[1]||a[2]-b[2]||a[0].localeCompare(b[0]));
  return {actual:options[0][0],converted:options,reason:'lowest MAE then normalized runtime then stable candidate ID'};
}
function check(label,skill,name,updater='skills/META-SKILL-v0.md'){
  absent(label+'/RESULT.md');frozen();
  const fixture=cases[name];
  table(label+'/INPUT.csv',['candidate','selection_mae','duration','unit'],fixture.rows);
  save(label+'/BEFORE.md',`# Before decision\n\nCase: ${name}\nTask skill: ${skill}\nTask SHA-256: ${identity(skill)}\nUpdater: ${updater}\nUpdater SHA-256: ${identity(updater)}\nExpected decision: ${fixture.expected}\nThese values are author-constructed fixtures; no model fitting occurs.`);
  const start=performance.now(), result=decide(skill,fixture), elapsed=performance.now()-start;
  table(label+'/CONVERSIONS.csv',['candidate','selection_mae','seconds','source_unit','basis'],result.converted);
  const pass=result.actual===fixture.expected;
  save(label+'/RESULT.md',`# Executed decision\n\nActual: ${result.actual}\nExpected: ${fixture.expected}\nPass: ${pass}\nDecision milliseconds: ${elapsed}\nReason: ${result.reason}\nModel fits: 0`);
  writeFileSync(join(out,'EXECUTIONS.csv'),`${label},${skill},${name},${result.actual},${fixture.expected},${pass},${elapsed},0\n`,{flag:'a'});
  return {pass,actual:result.actual,elapsed};
}
function round(label,parent,child,target,regression,updater){
  absent(label+'/ROUND.md');frozen();
  const m=fields(read(updater)), policy=m['Check policy'];
  if(!['target-and-regression','target-and-unknown'].includes(policy)) throw Error('Unsupported check policy');
  const second=policy==='target-and-regression'?regression:'unknown';
  save(label+'/ROUND.md',`# Before this task-skill round\n\nParent: ${parent}\nParent SHA-256: ${identity(parent)}\nChild: ${child}\nChild SHA-256: ${identity(child)}\nUpdater: ${updater}\nUpdater SHA-256: ${identity(updater)}\nRead check policy: ${policy}\nTarget case: ${target}\nSecond case selected by updater: ${second}\nTwo checks; zero fits. Child content is agent-authored before this round.`);
  const a=check(label+'/target',child,target,updater), b=check(label+'/second',child,second,updater);
  save(label+'/PROMOTION.md',`# Internal decision\n\nDecision: ${a.pass&&b.pass?'retain child':'retain parent'}\nRule: both declared internal checks must pass.\nThis internal rule does not replace later external comparison.`);
  return a.pass&&b.pass;
}
if(phase==='prepare'){
  if(existsSync(out)) throw Error('Preserve existing workspace');mkdirSync(out);
  copyFileSync(script,join(out,'run-meta-skill-labs.mjs'));
  copyFileSync(join(repo,'how-did-i-generate-it/rsi/validation/META-SKILL-LABS-PROTOCOL.md'),join(out,'PROTOCOL.md'));
  save('EXECUTIONS.csv','label,task_skill,case,actual,expected,pass,decision_ms,model_fits');
  save('skills/TASK-SKILL-v0.md','# Choose an eligible ML recipe\n\nSeconds per second: 1\nUnknown units: identity\n\nChoose lower selection MAE first. Break equal-MAE ties with shorter converted duration. Convert known duration units using the factors above. Treat an absent conversion as factor one. Break remaining ties by candidate ID. Input quality scores and durations come from the same declared comparison contract. The unknown-unit fallback is intentionally faulty in this starting skill.');
  save('skills/META-SKILL-v0.md','# Fixed task-skill updater\n\nCheck policy: target-and-regression\n\nDiagnosis: read the reported failure and compare actual with expected behavior. Name the instruction that caused the error.\nProposal: make one focused revision to the target Markdown procedure that repairs the reported failure. Preserve unrelated instructions and the external evaluator. For a missing known duration unit, add its conversion.\nEvaluation: run the target case and one previously passing regression case within the declared allowance. When the target is this updater itself, defer its retention to the prespecified later matched task-skill comparison.\nRetention: retain a task child only when both internal checks pass; preserve all proposals and results.\nAllowed objects: task-skill instructions or these updater instructions. A meta revision can change proposal guidance and internal check selection; it cannot change external fixture answers or budgets.');
  save('FREEZE.md',`# Original identities\n\nUpdater SHA-256: ${identity('skills/META-SKILL-v0.md')}\nDriver SHA-256: ${sha(script)}`);
  for(const [name,fixture] of Object.entries(cases))table('fixtures/'+name+'.csv',['candidate','selection_mae','duration','unit'],fixture.rows);
  table('fixtures/EXPECTED.csv',['case','expected'],Object.entries(cases).map(([n,f])=>[n,f.expected]));
  check('prerequisites/parent-seconds','skills/TASK-SKILL-v0.md','seconds');
  check('prerequisites/parent-milliseconds','skills/TASK-SKILL-v0.md','milliseconds');
  save('PAUSE.md','# Read the two parent records\n\nUse the frozen updater to diagnose the milliseconds failure and write TASK-SKILL-v1.md plus 10-16/ACTOR-NOTE.md. Do not edit v0.');
}else if(phase==='first'){
  if(!existsSync(join(out,'10-16/ACTOR-NOTE.md')))throw Error('Actor note required');
  round('10-16','skills/TASK-SKILL-v0.md','skills/TASK-SKILL-v1.md','milliseconds','seconds','skills/META-SKILL-v0.md');
  copyFileSync(join(out,'skills/META-SKILL-v0.md'),join(out,'skills/RENAMED-UPDATER.md'));
  save('10-16/RENAME.md',`# Same bytes under another filename\n\nOriginal SHA-256: ${identity('skills/META-SKILL-v0.md')}\nRenamed SHA-256: ${identity('skills/RENAMED-UPDATER.md')}\nNo changed instruction or extra decision execution. A new name adds no mechanism.`);
}else if(phase==='second-parent'){
  check('prerequisites/second-parent-minutes','skills/TASK-SKILL-v1.md','minutes');
}else if(phase==='second'){
  if(!existsSync(join(out,'prerequisites/second-update/ACTOR-NOTE.md')))throw Error('Actor note required');
  round('prerequisites/second-update','skills/TASK-SKILL-v1.md','skills/TASK-SKILL-v2.md','minutes','milliseconds','skills/META-SKILL-v0.md');
}else if(phase==='meta-start'){
  absent('10-17/SELF-APPLICATION-BEFORE.md');frozen();
  for(const p of ['10-16/PROMOTION.md','prerequisites/second-update/PROMOTION.md']) if(!read(p).includes('retain child'))throw Error('Expected two completed child traces');
  save('10-17/SELF-APPLICATION-BEFORE.md',`# Apply the existing pipeline to itself\n\nActive updater: skills/META-SKILL-v0.md\nActive updater SHA-256: ${identity('skills/META-SKILL-v0.md')}\nObject to revise: skills/META-SKILL-v0.md\nObject SHA-256: ${identity('skills/META-SKILL-v0.md')}\nFirst trace SHA-256: ${identity('10-16/ROUND.md')}\nSecond trace SHA-256: ${identity('prerequisites/second-update/ROUND.md')}\n\nActor next reads both traces and applies diagnosis, proposal, deferred evaluation, and retention to the updater. Save one candidate v1. No automatic content generation is claimed for this fixed driver.`);
}else if(phase==='later'){
  absent('10-17/COMPARISON.csv');frozen();
  for(const p of ['10-17/META-PROPOSAL.md','10-17/v0/ACTOR-NOTE.md','10-17/v1/ACTOR-NOTE.md']) if(!existsSync(join(out,p)))throw Error('Actor note required: '+p);
  const paths=['skills/META-SKILL-v0.md','skills/META-SKILL-v1.md','skills/TASK-SKILL-v2.md','10-17/v0/TASK-PROPOSAL.md','10-17/v1/TASK-PROPOSAL.md','10-17/META-PROPOSAL.md'];
  const hashes=paths.map(p=>[p,identity(p)]);
  table('10-17/COMPARISON-FREEZE.csv',['path','sha256'],hashes);
  const summary=[];
  for(const arm of ['v0','v1']){
    const label='10-17/'+arm, child=label+'/TASK-PROPOSAL.md', updater='skills/META-SKILL-'+arm+'.md';
    copyFileSync(join(out,'skills/TASK-SKILL-v2.md'),join(out,label+'/START.md'));
    const kept=round(label,label+'/START.md',child,'microseconds','seconds',updater);
    let passed=0;
    for(const name of ['microseconds','unknown','seconds']) if(check(label+'/external-'+name,child,name,updater).pass)passed++;
    summary.push([arm,identity(updater),identity(label+'/START.md'),kept?'retain child':'retain parent',2,3,passed,0]);
  }
  for(const [p,h] of hashes)if(identity(p)!==h)throw Error('Frozen file changed: '+p);
  table('10-17/COMPARISON.csv',['updater','updater_sha256','starting_task_sha256','internal_decision','internal_checks','external_checks','external_passes','fits'],summary);
  const retain=summary[1][6]===3&&summary[1][6]>summary[0][6];
  save('10-17/META-RETENTION.md',`# External retention decision\n\nDecision: ${retain?'retain candidate v1':'retain original v0'}\nRule: candidate produces a task skill passing all three fixed external cases and exceeding v0 under equal declared check allocations.\nThe candidate updater governed its later task round before this decision. This constructed development comparison is not a statistical or protected test.`);
  const simulation=[];
  for(const horizon of [1,2,4])for(let round=1;round<=8;round++)simulation.push([horizon,round,round%horizon===0?1:0,1+(round%horizon===0?2:0)]);
  table('10-17/SCHEDULE-SIMULATION.csv',['horizon','task_round','meta_update','invented_cost_units'],simulation);
  save('10-17/SCHEDULE-SIMULATION.md','# Hypothetical schedule accounting\n\nEight task rounds. Task round cost: one invented unit. Meta update cost: two invented units.\nHorizon 1: eight updates; total 24 units.\nHorizon 2: four updates; total 16 units.\nHorizon 4: two updates; total 12 units.\n\nA longer horizon delays the next opportunity to revise the updater while spending fewer assumed update units. Responsiveness, result quality, and noise are not measured. A shorter schedule also changes the updater more often, making attribution harder unless snapshots and evaluation intervals are explicit. Zero fits or task decisions were added by this arithmetic simulation.');
}else if(phase==='seal'){
  absent('MANIFEST.csv');frozen();
  const executions=read('EXECUTIONS.csv').trim().split('\n').slice(1);
  if(executions.length!==17)throw Error('Expected seventeen decision executions');
  save('COST.md','# Counted work\n\nDecision executions: 17\nModel fits: 0\nTask-skill proposals: 4 (two prior updates and two later arms)\nMeta-skill proposals: 1\nInitial parent captures: 2\nSecond-trace preparation: 3\n10.16 child checks: 2\nLater internal checks: 4\nLater external checks: 6\n\nPer-decision runtime is recorded in EXECUTIONS.csv. This excludes agent reasoning, file preparation, and provider inference, whose costs are unknown. The separate schedule simulation uses invented units, not measured wall time. Renaming compared bytes and ran no decisions.');
  for(const lab of ['10-16','10-17'])save(lab+'/LAB-NOTE.md','# Author walkthrough\n\nLearner prediction, teach-back, and quiz: not attempted. Decisions were executed on constructed inputs. This verifies a limited local mechanism, not student learning or independent-agent performance.');
  save('PROGRESS.md','# Declared work complete\n\nSeventeen decisions executed. Zero fits. Original and proposed procedures, failures, internal and external decisions remain. No live process remains. Next: publication checks. Keep source-paper reproduction and learner/backend verification separate.');
  const collect = dir => readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?collect(join(dir,e.name)):[join(dir,e.name)]);
  table('MANIFEST.csv',['path','bytes','sha256'],collect(out).sort().map(p=>[relative(out,p).split(sep).join('/'),statSync(p).size,sha(p)]));
}else throw Error('Unknown phase');
console.log('Completed '+phase+'; originals retained at '+out);
