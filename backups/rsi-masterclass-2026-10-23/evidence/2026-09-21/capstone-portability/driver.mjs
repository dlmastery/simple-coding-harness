// Two author smoke runs through a fixed shared tool and canonical skill.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const root=resolve(repo,'../rsi-work-2026-09-21-capstone-portability');
const python=resolve(repo,'.venv/Scripts/python.exe'),lab=resolve(repo,'rsi/tools/lab.py'),checker=resolve(repo,'rsi/tools/check_result.py');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const csv=(fields,rows)=>fields.join(',')+'\n'+rows.map(r=>fields.map(k=>'"'+String(r[k]).replaceAll('"','""')+'"').join(',')).join('\n')+'\n';
const put=(p,s)=>{if(existsSync(p))throw Error('Refuse overwrite '+p);writeFileSync(p,s);};
const paths=base=>readdirSync(base,{withFileTypes:true}).flatMap(e=>e.name==='__pycache__'?[]:e.isDirectory()?paths(resolve(base,e.name)):[resolve(base,e.name)]);
function run(label,args,expected=0){
  const path=resolve(root,'commands',label+'.md');if(existsSync(path))throw Error('Command already recorded');
  const started=new Date().toISOString(),t=performance.now();
  const r=spawnSync(python,args,{cwd:repo,encoding:'utf8',timeout:60000,windowsHide:true});
  put(path,`# ${label}\n\nStarted: ${started}\n\nExecutable: ${python}\n\nArguments: ${args.map(x=>'`'+x+'`').join(' ')}\n\nExit: ${r.status}; signal: ${r.signal}; seconds: ${(performance.now()-t)/1000}\n\n\`\`\`text\n${r.stdout||''}${r.stderr||''}${r.error?String(r.error):''}\n\`\`\`\n`);
  console.log(label+': '+r.status+' '+(r.stdout||r.stderr||'').trim());
  if(r.status!==expected)throw Error('Unexpected status '+label);
}
switch(process.argv[2]){
  case 'prepare':{
    if(existsSync(root))throw Error('Workspace exists');mkdirSync(resolve(root,'commands'),{recursive:true});mkdirSync(resolve(root,'sources'));
    copyFileSync(fileURLToPath(import.meta.url),resolve(root,'driver.mjs'));
    const inputs=[['PROTOCOL.md','how-did-i-generate-it/rsi/validation/CAPSTONE-PORTABILITY-PROTOCOL.md'],
      ['RUN-SKILL.md','rsi/skills/run-ml-experiment/SKILL.md'],['TUTOR-SKILL.md','rsi/skills/rsi-tutor/SKILL.md'],
      ['BIKE-DATA-CARD.md','rsi/examples/bike-demand/DATA-CARD.md'],['WINE-DATA-CARD.md','rsi/examples/wine-quality/DATA-CARD.md'],
      ['sources/lab.py','rsi/tools/lab.py'],['sources/check_result.py','rsi/tools/check_result.py'],['sources/requirements.txt','rsi/tools/requirements.txt'],
      ['sources/hour.csv','rsi/examples/bike-demand/source/hour.csv'],['sources/winequality-red.csv','rsi/examples/wine-quality/source/winequality-red.csv']];
    const records=[];
    for(const [destination,source] of inputs){copyFileSync(resolve(repo,source),resolve(root,destination));records.push({source,destination,sha256:hash(resolve(repo,source))});}
    put(resolve(root,'SOURCES.csv'),csv(['source','destination','sha256'],records));
    put(resolve(root,'DECISION.md'),'# Before the two fits\n\nThe author read the canonical skill and both data cards. Use explicit task, all permitted features, linear model, seed 17 and one attempt per task. The same Markdown procedure governs data inspection, bounded execution and checking; source snapshots alone do not prove compliance.\n\nBike hypothesis: calendar and observed weather can support a simple retrospective rental-count estimate. This is not tomorrow\'s forecast. Metric: MAE, smaller is better; chronological split.\n\nWine hypothesis: a balanced logistic classifier on permitted chemistry inputs provides an executable baseline for the quality-at-least-seven label. Metric: balanced accuracy, larger is better; feature-group split; inspect both recalls.\n\nThese are smoke hypotheses, not comparative gain claims. Model families differ because targets differ. No I1 transfer or new autonomous research is tested. Learner predictions and quiz responses are unattempted.\n');
    run('00-environment',['-c',"import sys,platform,importlib.metadata as m; print(sys.version); print(platform.platform()); print(*[k+'='+m.version(k) for k in ['numpy','pandas','scikit-learn','scipy','matplotlib']],sep=chr(10))"]);
    break;
  }
  case 'execute':{
    const invalid=resolve(root,'unsupported-task');
    run('01-invalid-task',[lab,'run','--task','unsupported','--workspace',invalid,'--hypothesis','Refusal before allocation'],2);
    if(existsSync(invalid))throw Error('Invalid task created a workspace');
    put(resolve(root,'RECOVERY.md'),'# Invalid request recovered\n\nThe unsupported task name was refused by argparse before any workspace or attempt was created. Correcting the name selects the declared bike task. It does not refund a charged failure; none was admitted. Continue the original one-fit-per-task allocation.\n');
    for(const task of ['bike','wine']){
      const work=resolve(root,task),policy=resolve(root,'RUN-SKILL.md');
      run(task+'-inspect',[lab,'inspect','--task',task,'--workspace',work]);
      const args=[lab,'run','--task',task,'--workspace',work,'--model','linear','--features','all','--seed','17','--attempt-limit','1','--policy',policy,'--hypothesis',task==='bike'?'Calendar and observed weather support a simple retrospective demand estimate':'Balanced logistic classification supplies a chemistry-based quality-threshold smoke baseline'];
      run(task+'-fit',args);
      run(task+'-check',[checker,resolve(work,'trial-001'),'--report',resolve(work,'trial-001/CHECK.md')]);
      run(task+'-resume-compare',[lab,'compare','--workspace',work]);
      run(task+'-extra-fit-refused',args,2);
      if(task==='wine'){
        const changed=[...args];changed[changed.indexOf('--attempt-limit')+1]='2';run('wine-budget-change-refused',changed,2);
      }
    }
    break;
  }
  case 'seal':{
    const files=paths(root);put(resolve(root,'MANIFEST.csv'),csv(['path','sha256'],files.map(p=>({path:relative(root,p).replaceAll('\\','/'),sha256:hash(p)}))));console.log('Sealed '+files.length+' files.');break;
  }
  default:throw Error('Expected prepare, execute or seal');
}
