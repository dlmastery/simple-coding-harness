import fs from 'node:fs';
import path from 'node:path';
import cp from 'node:child_process';
const pairs=fs.readFileSync('how-did-i-generate-it/harness/MIGRATION.tsv','utf8').trim().split('\n').slice(1).map(l=>l.split('\t'));
const files=['README.md',...fs.readdirSync('harness').filter(n=>n.endsWith('.md')).map(n=>'harness/'+n),'harness/skills/harness-tutor/SKILL.md',...pairs.map(([,p])=>p+'/README.md'),...new Set(pairs.map(([,p])=>path.posix.dirname(p)+'/README.md'))];
let links=0,unchanged=0;const problems=[];
for(const file of files){
 const prose=fs.readFileSync(file,'utf8').replace(/```[\s\S]*?```/g,'').replace(/`[^`\n]*`/g,'');
 for(const m of prose.matchAll(/\[[^\]]*\]\(([^)\n]+)\)/g)){
  const target=m[1].split('#')[0];
  if(!target||/^[a-z]+:/i.test(target))continue;
  links++;
  if(!fs.existsSync(path.resolve(path.dirname(file),target)))problems.push(`${file}: missing ${target}`);
 }
}
const tree=cp.execFileSync('git',['ls-tree','-r','fc018b0'],{encoding:'utf8'}).trim().split('\n');
const identities=[];
for(const line of tree){
 const [info,old]=line.split('\t');const pair=pairs.find(([p])=>old.startsWith(p+'/'));
 if(!pair||old.endsWith('.md'))continue;
 const current=pair[1]+old.slice(pair[0].length);
 identities.push([current,info.split(' ')[2]]);
}
// Batch hashing retains Git's clean-filter handling without starting one process per file.
const hashes=cp.execFileSync('git',['hash-object','--stdin-paths'],{input:identities.map(x=>x[0]).join('\n')+'\n',encoding:'utf8',maxBuffer:8*1024*1024}).trim().split('\n');
for(const [i,[file,expected]] of identities.entries()){
 if(hashes[i]!==expected){
  if(file==='harness/07_server/step_51_trueforge_comparison/test_step.py')console.log('Expected migration change: comparison test discovers themed paths.');
  else problems.push(`Implementation changed: ${file}`);
 }else unchanged++;
}
if(pairs.length!==54||new Set(pairs.map(p=>p[1])).size!==54)problems.push('Lesson inventory mismatch');
const backup=fs.readFileSync('how-did-i-generate-it/harness/backups/README-before-reorganization.md');
const old=cp.execFileSync('git',['show','fc018b0:README.md']);
// Compare normalized repository bytes because checkout uses the repository's line-ending policy.
if(backup.toString().replace(/\r\n/g,'\n')!==old.toString().replace(/\r\n/g,'\n'))problems.push('README backup mismatch');
console.log(`54 unique lessons; ${files.length} published pages; ${links} local file links; ${unchanged} unchanged implementation/configuration files.`);
for(const p of problems)console.log(p);
console.log(`${problems.length} publication problems.`);
process.exitCode=problems.length?1:0;
