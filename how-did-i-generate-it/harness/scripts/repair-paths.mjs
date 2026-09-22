import fs from 'node:fs';
import path from 'node:path';
import {readmes} from './pre-move-files.mjs';
const posix=path.posix;
const pairs=fs.readFileSync('how-did-i-generate-it/harness/MIGRATION.tsv','utf8').trim().split('\n').slice(1).map(l=>l.split('\t'));
const migrated=p=>{const row=pairs.find(([old])=>p===old||p.startsWith(old+'/'));return row?row[1]+p.slice(row[0].length):p;};
let changed=0;
for(const oldFile of readmes){
 if(oldFile==='README.md')continue;
 const newFile=migrated(oldFile);
 if(!fs.existsSync(newFile))continue;
 const original=fs.readFileSync(newFile,'utf8');
 let text=original.replace(/\]\(([^)\n]+)\)/g,(all,target)=>{
  if(/^(?:[a-z]+:|#)/i.test(target)||target.includes(' '))return all;
  const [file,hash]=target.split('#');
  const oldTarget=posix.normalize(posix.join(posix.dirname(oldFile),file));
  const newTarget=migrated(oldTarget);
  if(newFile===oldFile&&newTarget===oldTarget)return all;
  return ']('+posix.relative(posix.dirname(newFile),newTarget)+(hash?'#'+hash:'')+')';
 });
 // Commands and inline paths referring to a different snapshot or root file.
 text=text.replace(/(?:\.\.\/)+[\w./-]+/g,token=>{
  // Link targets were already fixed; only translate paths that resolve in the old tree.
  const oldTarget=posix.normalize(posix.join(posix.dirname(oldFile),token));
  const newTarget=migrated(oldTarget);
  if(!fs.existsSync(newTarget)||newTarget===oldTarget&&newFile===oldFile)return token;
  return posix.relative(posix.dirname(newFile),newTarget)||'.';
 });
 for(const [old,target] of pairs){
  text=text.replaceAll('cd '+old,'cd '+target);
  text=text.replaceAll('simple-coding-harness/'+old,'simple-coding-harness/'+target);
 }
 if(text!==original){fs.writeFileSync(newFile,text);changed++;}
}
console.log(`Repaired paths in ${changed} Markdown files.`);
