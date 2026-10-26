// Agent-authored bounded execution; students use the lesson's prose prompt.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {performance} from 'node:perf_hooks';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [phase,destination,...extra]=process.argv.slice(2);if(!destination)throw Error('Supply sibling workspace');
const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use sibling workspace');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>readFileSync(join(out,p),'utf8');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const absent=p=>{if(existsSync(join(out,p)))throw Error('Preserve '+p);};
const table=(p,rs)=>save(p,rs.map(r=>r.map(v=>{const s=String(v);return /[",\r\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s;}).join(',')).join('\n'));
const predictions=p=>readFileSync(p,'utf8').trim().split(/\r?\n/).slice(1).map(x=>{const r=x.split(',');return {actual:Number(r[1]),predicted:Number(r[2])};});
const score=(data,task)=>{const recalls=[0,1].map(c=>{const rs=data.filter(r=>r.actual===c);return rs.length?rs.filter(r=>r.predicted===c).length/rs.length:null;});return {score:task==='bike'?data.reduce((s,r)=>s+Math.abs(r.actual-r.predicted),0)/data.length:(recalls[0]+recalls[1])/2,recalls:task==='wine'?recalls:[]};};
const parseReport=p=>Object.fromEntries(read(p).trim().split('\n').filter(s=>s.includes(': ')).map(s=>{const i=s.indexOf(': ');return[s.slice(0,i),s.slice(i+2)];}));
const python=join(repo,'.venv/Scripts/python.exe');
if(phase==='report'){
  const [task,predictionFile,output]=extra;if(!['bike','wine'].includes(task))throw Error('Task');absent(output);
  const p=resolve(predictionFile),data=predictions(p),metrics=score(data,task);
  save(output,`# Checked prediction summary\n\nTask: ${task}\nRows: ${data.length}\nPrediction SHA-256: ${sha(p)}\nScore: ${metrics.score}\n${task==='wine'?`Recall 0: ${metrics.recalls[0]}\nRecall 1: ${metrics.recalls[1]}\n`:''}Prediction check: see the unchanged candidate CHECK.md\n`);
}else if(phase==='run'){
  absent('PROTOCOL.md');mkdirSync(out,{recursive:true});const started=performance.now();
  const sources=[['how-did-i-generate-it/rsi/validation/EFFICIENT-HARNESSES-PROTOCOL.md','PROTOCOL.md'],['how-did-i-generate-it/rsi/research/2026-09-21-EFFICIENT-HARNESSES-AUDIT.md','SOURCE-AUDIT.md'],['rsi/tools/lab.py','lab.source.py'],['rsi/tools/check_result.py','checker.source.py'],['rsi/examples/bike-demand/DATA-CARD.md','BIKE-DATA-CARD.md'],['rsi/examples/wine-quality/DATA-CARD.md','WINE-DATA-CARD.md']];
  for(const [s,d]of sources)copyFileSync(join(repo,s),join(out,d));copyFileSync(script,join(out,'run-efficient-harnesses.mjs'));
  save('QUALITY-COST.md',read('PROTOCOL.md'));
  save('H0.md','# H0\n\nRun the fixed recipe. Check predictions. Invoke the same summary tool three times, writing report-1.md, report-2.md, and report-3.md. Keep every original result and check.');
  save('H1.md','# H1\n\nRun the fixed recipe. Check predictions. Invoke the summary tool once, writing report-1.md. Keep every original result and check.');
  save('PROPOSAL.md','# Proposed report consolidation\n\nRemove two duplicate summary-tool processes per task. Keep the predictor, recipe, primary runtime report, prediction checker, summary content, and acceptance rule. Author prediction: quality stays equal, report calls and derived bytes fall, while measured runtime differences may be noisy. Inference and design cost are unknown.');
  const pinned=[...sources.map(x=>x[1]),'run-efficient-harnesses.mjs','QUALITY-COST.md','H0.md','H1.md','PROPOSAL.md'];
  table('FROZEN.csv',[['path','sha256'],...pinned.map(p=>[p,sha(join(out,p))])]);
  const calls=[];
  function call(label,exe,args){const t=performance.now(),p=spawnSync(exe,args,{cwd:repo,encoding:'utf8',timeout:60000}),elapsed=(performance.now()-t)/1000;save('commands/'+label+'.md',`# ${label}\n\nExecutable: ${exe}\nArguments:\n${args.map(a=>'- '+a).join('\n')}\n\nExit: ${p.status}\nError: ${p.error?.message||'none'}\nWall seconds: ${elapsed}\n\n\`\`\`text\n${p.stdout||''}${p.stderr||''}\n\`\`\``);calls.push([label,p.status??'interrupted',elapsed]);table('COMMANDS.csv',[['command','exit','wall_seconds'],...calls]);if(p.status!==0)throw Error('Unexpected command failure; preserve: '+label);return elapsed;}
  const outcomes=[];
  for(const [variant,task]of [['H0','bike'],['H1','bike'],['H1','wine'],['H0','wine']]){
    const base=variant+'/'+task,workspace=join(out,base,'experiment');absent(base+'/QUALITY.md');
    const begin=performance.now(),fitWall=call(variant+'-'+task+'-fit',python,[join(repo,'rsi/tools/lab.py'),'run','--task',task,'--workspace',workspace,'--model','linear','--features','all','--seed','17','--attempt-limit','1','--policy',join(out,variant+'.md'),'--hypothesis','Removing duplicate derived reports must preserve the same fixed recipe and predictions.']);
    const candidate=join(workspace,'trial-001'),checkWall=call(variant+'-'+task+'-check',python,[join(repo,'rsi/tools/check_result.py'),candidate,'--report',join(candidate,'CHECK.md')]);
    let reportWall=0,reportBytes=0;const n=variant==='H0'?3:1;
    for(let k=1;k<=n;k++){const report=base+'/report-'+k+'.md';reportWall+=call(variant+'-'+task+'-report-'+k,process.execPath,[script,'report',out,task,join(candidate,'predictions.csv'),report]);reportBytes+=statSync(join(out,report)).size;}
    const data=predictions(join(candidate,'predictions.csv')),metrics=score(data,task),report=parseReport(base+'/report-1.md');
    const validFields=report.Task===task&&Number(report.Rows)===data.length&&report['Prediction SHA-256']===sha(join(candidate,'predictions.csv'))&&Math.abs(Number(report.Score)-metrics.score)<=1e-10&&(task==='bike'||metrics.recalls.every((v,i)=>Math.abs(Number(report['Recall '+i])-v)<=1e-10));
    const evidence=existsSync(join(candidate,'CHECK.md'))&&readFileSync(join(candidate,'CHECK.md'),'utf8').includes('PASS:');
    const floor=Number.isFinite(metrics.score)&&(task==='bike'?metrics.score<=110:metrics.score>=.70&&metrics.recalls.every(v=>v>=.65));
    const pass=evidence&&validFields&&floor,elapsed=(performance.now()-begin)/1000;
    const fitSeconds=Number(readFileSync(join(workspace,'trials.csv'),'utf8').trim().split(/\r?\n/)[1].split(',')[7]);
    save(base+'/QUALITY.md',`# Fixed quality gate\n\nPass: ${pass}\nPrediction-check evidence: ${evidence}\nRequired summary fields: ${validFields}\nAbsolute quality floor: ${floor}\nScore: ${metrics.score}\nRecalls: ${metrics.recalls.join(' / ')||'not applicable'}\n`);
    outcomes.push({variant,task,pass,score:metrics.score,recalls:metrics.recalls,hash:sha(join(candidate,'predictions.csv')),reports:n,bytes:reportBytes,fitSeconds,fitWall,checkWall,reportWall,elapsed});
  }
  table('OUTCOMES.csv',[['variant','task','quality_pass','score','recall_0','recall_1','prediction_sha256','report_calls','derived_report_bytes','fit_related_seconds','fit_command_seconds','check_command_seconds','report_command_seconds','arm_wall_seconds'],...outcomes.map(r=>[r.variant,r.task,r.pass,r.score,r.recalls[0]??'not_applicable',r.recalls[1]??'not_applicable',r.hash,r.reports,r.bytes,r.fitSeconds,r.fitWall,r.checkWall,r.reportWall,r.elapsed])]);
  const comparisons=['bike','wine'].map(task=>{const a=outcomes.find(r=>r.task===task&&r.variant==='H0'),b=outcomes.find(r=>r.task===task&&r.variant==='H1');const tolerance=Math.abs(a.score-b.score)<=1e-10&&a.recalls.every((v,i)=>Math.abs(v-b.recalls[i])<=1e-10);return[task,a.pass&&b.pass&&tolerance&&b.reports<a.reports&&b.bytes<a.bytes,a.hash===b.hash,tolerance,a.reports-b.reports,a.bytes-b.bytes];});
  table('COMPARISON.csv',[['task','retain_H1','identical_predictions','paired_tolerance','report_calls_removed','derived_bytes_removed'],...comparisons]);
  save('stub/RESULT.md','# Fit stub\n\nScore: 1\nNo model was trained. This supplied number is not a measured prediction score.');
  const stubT=performance.now();save('stub/report.md',read('stub/RESULT.md'));const stubEvidence=existsSync(join(out,'stub/CHECK.md'));save('stub/QUALITY.md',`# Checker-removal counterexample\n\nRequired prediction-check evidence: ${stubEvidence}\nPass: false\nThe apparent high score cannot compensate for missing required evidence. One in-process report copy and one fit stub; no fit or valid prediction metric.\n`);
  save('COST.md',`# Cost boundaries\n\nFits: 4\nPrediction-check subprocesses: 4\nSummary-tool subprocesses: 8\nTotal successful subprocesses: ${calls.length}\nCumulative subprocess seconds: ${calls.reduce((s,r)=>s+r[2],0)}\nDriver wall seconds: ${(performance.now()-started)/1000}\nStub copy and gate seconds: ${(performance.now()-stubT)/1000}\n\nFit-related time is inside fit command time, which is inside driver wall time; do not add these nested quantities. Arm wall time includes its subprocesses. Proposal design, author inference, source reading, implementation, environment preparation, and publication costs are unknown. The failed checker-removal proposal remains in this ledger. Its cost excludes an actual fit by design.\n`);
  console.log(read('OUTCOMES.csv'));console.log(read('COMPARISON.csv'));
}else if(phase==='seal'){
  absent('MANIFEST.csv');const walk=p=>readdirSync(p).sort().flatMap(n=>{const full=join(p,n);return statSync(full).isDirectory()?walk(full):[full];});table('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
}else throw Error('Unknown phase');
