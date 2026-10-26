// Author-maintenance driver. Students invoke the tutor, not this implementation.
import {readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync, cpSync, readdirSync} from 'node:fs';
import {resolve, dirname, relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const root=resolve(repo,'../rsi-work-2026-09-21-capstone-recursion');
const pkg=resolve(root,'package');
const python=resolve(repo,'.venv/Scripts/python.exe');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const put=(p,s)=>{if(existsSync(p))throw Error('Refuse overwrite: '+p);writeFileSync(p,s);};
const csv=(fields,rows)=>fields.join(',')+'\n'+rows.map(r=>fields.map(k=>'"'+String(r[k]).replaceAll('"','""')+'"').join(',')).join('\n')+'\n';
const paths=base=>readdirSync(base,{withFileTypes:true}).flatMap(e=>e.name==='__pycache__'?[]:e.isDirectory()?paths(resolve(base,e.name)):[resolve(base,e.name)]);
function run(label,args,expected=0){
  const log=resolve(root,'commands',label+'.md');if(existsSync(log))throw Error('Command already recorded '+label);
  const started=new Date().toISOString(),t=performance.now();
  const r=spawnSync(python,args,{cwd:pkg,encoding:'utf8',timeout:60000,windowsHide:true});
  put(log,`# ${label}\n\nStarted: ${started}\n\nExecutable: ${python}\n\nArguments: ${args.map(x=>'`'+x+'`').join(' ')}\n\nExit: ${r.status}; signal: ${r.signal}; seconds: ${(performance.now()-t)/1000}\n\n\`\`\`text\n${r.stdout||''}${r.stderr||''}${r.error?String(r.error):''}\n\`\`\`\n`);
  console.log(label+': '+r.status+' '+(r.stdout||'').trim());
  if(r.status!==expected)throw Error('Unexpected status '+label);
}
const work=resolve(root,'experiment');
const fit=(name,model)=>run(name,[resolve(pkg,'run.py'),'run','--workspace',work,'--candidate',name,'--model',model]);
const control=(label,action,extra=[],expected=0)=>run(label,[resolve(pkg,'recursive_control.py'),action,'--root',root,...extra],expected);
switch(process.argv[2]){
  case 'prepare':{
    if(existsSync(root))throw Error('Workspace exists; inspect it');
    mkdirSync(resolve(root,'commands'),{recursive:true});
    cpSync(resolve(repo,'how-did-i-generate-it/rsi/capstone-package'),pkg,{recursive:true});
    mkdirSync(resolve(pkg,'data'));
    copyFileSync(resolve(repo,'rsi/evidence/2026-09-21/capstone-harness/package/data/winequality-white.csv'),resolve(pkg,'data/winequality-white.csv'));
    copyFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/CAPSTONE-RECURSION-PROTOCOL.md'),resolve(root,'PROTOCOL.md'));
    copyFileSync(fileURLToPath(import.meta.url),resolve(root,'driver.mjs'));
    const runner=resolve(pkg,'run.py');let s=readFileSync(runner,'utf8');
    s=s.replace('import argparse','import joblib\nimport argparse');
    const anchor="            table.to_csv(destination / 'predictions.csv', index=False)";
    if(!s.includes(anchor))throw Error('Extension anchor missing');
    s=s.replace(anchor,anchor+"\n            joblib.dump(model, destination / 'model.joblib', compress=3)\n            pd.DataFrame({'row_id': train, 'actual': data.loc[train, 'quality'].to_numpy(), 'prediction': train_pred}).to_csv(destination / 'training-predictions.csv', index=False)");
    s=s.replace("'predictions_sha256': sha(destination / 'predictions.csv')}","'predictions_sha256': sha(destination / 'predictions.csv'),\n                       'model_sha256': sha(destination / 'model.joblib'),\n                       'training_predictions_sha256': sha(destination / 'training-predictions.csv')}");
    writeFileSync(runner,s);
    const task=resolve(pkg,'task.py');s=readFileSync(task,'utf8').replace("'requirements.txt']","'requirements.txt', 'recursive_control.py']");writeFileSync(task,s);
    put(resolve(root,'EXTENSION.md'),'# Versioned capstone extension\n\nThe original 11.01 package remains sealed. This copy saves fitted models and training predictions, adds their hashes to each report, and includes recursive_control.py in package identity. Its fixed controller reads versioned Markdown instructions. It does not generate its own changes. Only locally generated model files are loaded. All inherited baseline documentation refers to 11.01; PROTOCOL.md controls this separate experiment.\n');
    put(resolve(root,'I0.md'),'# I0: select a prediction recipe\n\nCompare the incumbent and permitted proposals in declared order. Retain only a strict improvement. Ties keep the earlier candidate.\n\nRank candidates by: training_MAE\n\nSave the complete decision trace and retained task recipe. External acceptance and terminal evaluation are governed by the frozen protocol.\n');
    const frozen=['PROTOCOL.md','I0.md','driver.mjs',...paths(pkg).map(p=>relative(root,p).replaceAll('\\','/'))];
    put(resolve(root,'FROZEN.csv'),csv(['path','sha256'],frozen.map(p=>({path:p,sha256:hash(resolve(root,p))}))));
    run('00-environment',['-c',"import sys, platform, importlib.metadata as m; print(sys.version); print(platform.platform()); print(*[k+'='+m.version(k) for k in ['numpy','pandas','scikit-learn','scipy','joblib']], sep=chr(10))"]);
    run('01-prepare',[resolve(pkg,'run.py'),'prepare','--workspace',work,'--budget','8']);
    break;
  }
  case 'generation-one':{
    fit('g1-ridge','ridge');fit('g1-tree','tree');
    control('04-g1-select','select',['--phase','g1','--skill','I0.md','--candidates','g1-ridge','g1-tree']);
    break;
  }
  case 'comparison':{
    if(!existsSync(resolve(root,'CHANGE-PROPOSAL.md'))||!existsSync(resolve(root,'I1.md')))throw Error('Read generation one and save the actual proposal first');
    put(resolve(root,'CHILD-FROZEN.csv'),csv(['path','sha256'],[{path:'I1.md',sha256:hash(resolve(root,'I1.md'))}]));
    const skill=readFileSync(resolve(root,'g1-TASK-SKILL.md'),'utf8');
    const incumbent=skill.match(/^Model: (.+)$/m)[1];
    const menu=[incumbent,...['ridge','tree','forest'].filter(m=>m!==incumbent)];
    for(const arm of ['i0','i1']){
      copyFileSync(resolve(root,'g1-TASK-SKILL.md'),resolve(root,'g2-'+arm+'-START.md'));
      for(const model of menu)fit('g2-'+arm+'-'+model,model);
      control('g2-'+arm+'-select','select',['--phase','g2-'+arm,'--skill',arm==='i0'?'I0.md':'I1.md','--candidates',...menu.map(m=>'g2-'+arm+'-'+m)]);
    }
    control('20-freeze','freeze');
    run('21-extra-fit-refused',[resolve(pkg,'run.py'),'run','--workspace',work,'--candidate','g3-extra','--model','ridge'],2);
    break;
  }
  case 'final':{
    control('22-terminal-evaluation','final');control('23-repeat-final-refused','final',[],2);
    run('24-post-final-fit-refused',[resolve(pkg,'run.py'),'run','--workspace',work,'--candidate','g3-post-final','--model','ridge'],2);
    break;
  }
  case 'seal':{
    const files=paths(root).filter(p=>!p.endsWith('/MANIFEST.csv')&&!p.endsWith('\\MANIFEST.csv'));
    put(resolve(root,'MANIFEST.csv'),csv(['path','sha256'],files.map(p=>({path:relative(root,p).replaceAll('\\','/'),sha256:hash(p)}))));
    console.log('Sealed '+files.length+' files; environment cache excluded.');break;
  }
  default:throw Error('Expected prepare, generation-one, comparison, final, or seal');
}
