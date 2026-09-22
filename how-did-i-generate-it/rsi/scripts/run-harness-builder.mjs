// Bounded parent/child executions of an existing generated classification harness.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync,cpSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {performance} from 'node:perf_hooks';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [phase,destination]=process.argv.slice(2);if(!destination)throw Error('Supply sibling workspace');const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use sibling workspace');
const shaBytes=b=>createHash('sha256').update(b).digest('hex'),sha=p=>shaBytes(readFileSync(p));
const read=p=>readFileSync(join(out,p),'utf8');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const absent=p=>{if(existsSync(join(out,p)))throw Error('Preserve '+p);};
const table=(p,rs)=>save(p,rs.map(r=>r.map(v=>{const s=String(v);return /[",\r\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s;}).join(',')).join('\n'));
const walk=p=>readdirSync(p).sort().flatMap(n=>{const f=join(p,n);return statSync(f).isDirectory()?walk(f):[f];});
const verify=()=>{for(const row of read('FROZEN.csv').trim().split('\n').slice(1)){const [p,h]=row.split(',');if(sha(join(out,p))!==h)throw Error('Frozen input changed: '+p);}};
if(phase==='prepare'){
  absent('PROTOCOL.md');mkdirSync(out,{recursive:true});
  const historical='rsi/evidence/2026-09-20/clean-journey/06-05/';cpSync(join(repo,historical,'package'),join(out,'parent/package'),{recursive:true});
  const sources=[['how-did-i-generate-it/rsi/validation/HARNESS-BUILDER-PROTOCOL.md','PROTOCOL.md'],['how-did-i-generate-it/rsi/research/2026-09-21-HARNESS-BUILDER-AUDIT.md','SOURCE-MAP.md'],[historical+'HARNESS-BRIEF.md','HARNESS-BRIEF.md'],[historical+'run/trial-002/RESULT.md','HISTORICAL-RESULT.md'],['rsi/tools/lab.py','lab.source.py'],['rsi/tools/check_result.py','checker.source.py'],['rsi/skills/build-ml-harness/SKILL.md','CURRENT-BUILDER-REFERENCE.md']];
  for(const [s,d]of sources)copyFileSync(join(repo,s),join(out,d));copyFileSync(script,join(out,'run-harness-builder.mjs'));
  const builderPath='rsi/skills/build-ml-harness/SKILL.md',expected=read('parent/package/PROVENANCE.md').match(/Builder SHA-256: ([a-f0-9]{64})/)[1];
  const commits=spawnSync('git',['log','--format=%H','--',builderPath],{cwd:repo,encoding:'utf8',timeout:60000});if(commits.status!==0)throw Error('Cannot inspect builder history');let found;
  for(const commit of commits.stdout.trim().split('\n')){const p=spawnSync('git',['show',commit+':'+builderPath],{cwd:repo,timeout:60000});if(p.status===0&&shaBytes(p.stdout)===expected){writeFileSync(join(out,'BUILDER.md'),p.stdout);found=commit;break;}}
  if(!found)throw Error('Exact historical builder not recovered; no fit allowed');
  save('BUILDER-IDENTITY.md',`# Historical builder identity\n\nRecovered Git commit: ${found}\nHistorical builder SHA-256: ${expected}\nCurrent reference SHA-256: ${sha(join(out,'CURRENT-BUILDER-REFERENCE.md'))}\n\nThe generation provenance names the historical bytes. The current skill is a later version, retained only for comparison. No builder is executed or edited in this study.`);
  table('SOURCES.csv',[['repository_path','copy','sha256'],...sources.map(([s,d])=>[s,d,sha(join(out,d))])]);
  const files=walk(out).map(p=>relative(out,p).split(sep).join('/'));table('FROZEN.csv',[['path','sha256'],...files.map(p=>[p,sha(join(out,p))])]);console.log(read('BUILDER-IDENTITY.md'));
}else if(['parent','child'].includes(phase)){
  verify();const arm=phase;absent(arm+'/STARTED.md');
  if(arm==='child'){
    if(!read('parent/REPORT-CHECK.md').includes('Pass: false'))throw Error('Observe parent failure before repair');
    cpSync(join(out,'parent/package'),join(out,'child/package'),{recursive:true});
    const source=read('child/package/run.py');
    const helper=`def complete_class_recall_report(candidate):\n    """Add explicit per-class recalls without changing predictions or score."""\n    with (candidate / "predictions.csv").open(encoding="utf-8", newline="") as stream:\n        rows = list(csv.DictReader(stream))\n    lines = []\n    for label in (0, 1):\n        selected = [row for row in rows if float(row["actual"]) == label]\n        if not selected:\n            raise ValueError("Cannot report recall for an absent class.")\n        recall = sum(float(row["predicted"]) == label for row in selected) / len(selected)\n        lines.append(f"Class {label} recall: {recall:.12f}")\n    with (candidate / "RESULT.md").open("a", encoding="utf-8", newline="\\n") as stream:\n        stream.write("\\n" + "\\n".join(lines) + "\\n")\n\n\n`;
    const anchor='            check_result.check(workspace / row["candidate"])';if(!source.includes(anchor)||!source.includes('def main():'))throw Error('Unexpected parent shape');
    save('child/package/run.py',source.replace('def main():',helper+'def main():').replace(anchor,anchor+'\n            complete_class_recall_report(workspace / row["candidate"])'));
    save('child/CHANGE.md','# Report component repair\n\nAdd explicit class recalls from the saved prediction rows after the existing prediction check. Keep the generated task wrapper, two-attempt internal ceiling, shared runtime, estimator, features, seed, and checker unchanged. This run allocates only one fit per arm. No builder ran.');
    table('CHILD-FREEZE.csv',[['path','sha256'],...walk(join(out,'child/package')).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
  }
  save(arm+'/STARTED.md',`# Charged arm\n\nArm: ${arm}\nAllocated fits: 1\nRecipe: wine / linear / all / seed 17\nStarted UTC: ${new Date().toISOString()}\nBuilder SHA-256: ${sha(join(out,'BUILDER.md'))}\n`);
  const calls=[];function call(label,exe,args){const t=performance.now(),p=spawnSync(exe,args,{cwd:repo,encoding:'utf8',timeout:60000}),seconds=(performance.now()-t)/1000;save(arm+'/commands/'+label+'.md',`# ${label}\n\nExecutable: ${exe}\nArguments:\n${args.map(a=>'- '+a).join('\n')}\n\nExit: ${p.status}\nError: ${p.error?.message||'none'}\nWall seconds: ${seconds}\n\n\`\`\`text\n${p.stdout||''}${p.stderr||''}\n\`\`\``);calls.push([label,p.status??'interrupted',seconds]);table(arm+'/COMMANDS.csv',[['command','exit','wall_seconds'],...calls]);if(p.status!==0)throw Error('Unexpected command failure; preserve arm');}
  const python=join(repo,'.venv/Scripts/python.exe'),experiment=join(out,arm,'experiment');
  call('fit',python,[join(out,arm,'package/run.py'),'run','--repo',repo,'--workspace',experiment,'--model','linear','--features','all','--seed','17','--hypothesis','Explicit class recalls should improve report completeness without changing predictions.']);
  const candidate=join(experiment,'trial-001');call('check-predictions',python,[join(repo,'rsi/tools/check_result.py'),candidate,'--report',join(candidate,'CHECK.md')]);
  const values=readFileSync(join(candidate,'predictions.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(s=>s.split(',').slice(1).map(Number));
  const recalls=[0,1].map(label=>{const rs=values.filter(r=>r[0]===label);return rs.filter(r=>r[1]===label).length/rs.length;});
  const report=readFileSync(join(candidate,'RESULT.md'),'utf8');const matches=[0,1].map(label=>report.match(new RegExp('Class '+label+' recall: ([0-9.]+)')));
  const match=matches.every((m,i)=>m&&Number.isFinite(Number(m[1]))&&Math.abs(Number(m[1])-recalls[i])<=1e-10);
  save(arm+'/REPORT-CHECK.md',`# Explicit recall requirement\n\nPass: ${match}\nClass 0 expected recall: ${recalls[0]}\nClass 1 expected recall: ${recalls[1]}\nClass 0 field present: ${Boolean(matches[0])}\nClass 1 field present: ${Boolean(matches[1])}\nPrediction check: passed in separate calculation\nBuilder SHA-256: ${sha(join(out,'BUILDER.md'))}\nMissing fields are not zero recall. The confusion matrix already encodes enough information to derive them; this gate requires explicit readable values.`);
  if(arm==='child')save('COMPARISON.md',`# Parent and child\n\nParent explicit-recall gate: failed\nChild explicit-recall gate: ${match?'passed':'failed'}\nIdentical prediction bytes: ${sha(join(out,'parent/experiment/trial-001/predictions.csv'))===sha(join(candidate,'predictions.csv'))}\nBuilder SHA-256: ${sha(join(out,'BUILDER.md'))}\n\nThe reporting component changed; the builder did not. Both arms ran the same recipe once. No new builder generation or held-out generalization was tested.`);
  console.log(read(arm+'/REPORT-CHECK.md'));
}else if(phase==='seal'){
  absent('MANIFEST.csv');verify();table('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
}else throw Error('Unknown phase');
