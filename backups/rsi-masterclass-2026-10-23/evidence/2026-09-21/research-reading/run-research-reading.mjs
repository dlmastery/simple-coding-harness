// Preserve two author source audits and inspect existing evidence. Zero fits.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [phase,destination]=process.argv.slice(2);if(!destination)throw Error('Supply sibling workspace');const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use sibling workspace');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const csv=(p,rs)=>save(p,rs.map(r=>r.join(',')).join('\n'));
const read=p=>readFileSync(join(out,p),'utf8');
const walk=p=>readdirSync(p).sort().flatMap(n=>{const f=join(p,n);return statSync(f).isDirectory()?walk(f):[f];});
if(phase==='run'){
  if(existsSync(out))throw Error('Preserve existing workspace');mkdirSync(out,{recursive:true});
  const prefix='rsi/evidence/2026-09-20/';
  const raw=[['clean-journey/02-04/CONTROLLER-CONTRACT.md','fixed-contract.md'],['clean-journey/02-04/controller.py','fixed-controller.py'],['clean-journey/02-04/requests.csv','fixed-requests.csv'],...['MEMORY-v1.md','DECISION.csv','OUTCOMES.csv','SCOPE-CHECK.csv','USE-AND-BENEFIT.md'].map(n=>['self-star-and-measurement/07-03/'+n,'memory-'+n]),...['IMPROVER-v0.md','IMPROVER-v1.md','EXECUTION-TRACE.md'].map(n=>['inherited-improver/'+n,n]),['two-generations/LINEAGE.md','negative-lineage.md']];
  const sources=[['how-did-i-generate-it/rsi/validation/RESEARCH-READING-PROTOCOL.md','PROTOCOL.md'],...['FRAMEWORK.md','THREE-CASES.md','CLAIM-CARD.md','SEARCH-RECORD.md'].map(n=>['how-did-i-generate-it/rsi/research/research-reading/'+n,n]),...raw.map(([s,d])=>[prefix+s,'local/'+d])];
  for(const [s,d]of sources){mkdirSync(dirname(join(out,d)),{recursive:true});if(s.includes('/research/research-reading/'))save(d,readFileSync(join(repo,s),'utf8').replaceAll('../../../../rsi/evidence/2026-09-20/','../../2026-09-20/'));else copyFileSync(join(repo,s),join(out,d));}
  copyFileSync(script,join(out,'run-research-reading.mjs'));
  csv('SOURCES.csv',[['repository_path','copy','source_sha256','copy_sha256'],...sources.map(([s,d])=>[s,d,sha(join(repo,s)),sha(join(out,d))])]);
  const checks=[['fixed controller hash',read('local/fixed-contract.md').includes(sha(join(out,'local/fixed-controller.py')))],['saved memory hash',read('local/memory-DECISION.csv').includes(sha(join(out,'local/memory-MEMORY-v1.md')))],['later improver hash',read('local/EXECUTION-TRACE.md').includes(sha(join(out,'local/IMPROVER-v1.md')))]];
  csv('IDENTITY-CHECKS.csv',[['check','passed'],...checks]);
  save('LOCAL-CHECK.md',`# Check the referenced identities\n\n${checks.map(([n,v])=>'- '+n+': '+(v?'PASS':'FAIL')).join('\n')}\n\nThese comparisons connect recorded hashes to the copied controller, memory, and later improver. They do not rerun those experiments or prove a scientific classification. Read the original decisions with their reported limits.`);
  save('LAB-NOTE.md','# Author reading record\n\nLab 10.01 distinguishes saved files from later use and a constructed inheritance demonstration from a measured improver advantage. Lab 10.02 traces one current primary announcement, retaining unknown website date and artifact access.\n\nLearner predictions, explanation, quiz, and transfer response: unattempted. Zero new fits. Author/inference cost unknown. No independent paper reproduction. All original course illustrations retained without generation.');
  console.log(checks.map(([n,v])=>`${n}: ${v?'PASS':'FAIL'}`).join('\n'));
  if(checks.some(([,v])=>!v))process.exitCode=1;
}else if(phase==='seal'){
  if(existsSync(join(out,'MANIFEST.csv')))throw Error('Already sealed');csv('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
}else throw Error('Use run or seal');
