import {readFileSync} from 'node:fs';
const lines=readFileSync(process.argv[2],'utf8').trim().split(/\r?\n/);
const fields=new Map(),errors=[];
for(const line of lines){
 const match=/^([A-Za-z]+): (.+)$/.exec(line);
 if(!match){errors.push('Malformed line');continue;}
 const [,key,value]=match;
 if(!['Candidate','Status'].includes(key))errors.push('Unexpected field: '+key);
 if(fields.has(key))errors.push('Repeated field: '+key);
 fields.set(key,value);
}
if(lines.length!==2)errors.push('Expected exactly two lines');
if(!/^[A-Z]$/.test(fields.get('Candidate')||''))errors.push('Candidate must be one uppercase letter');
if(!['checked','unchecked'].includes(fields.get('Status')))errors.push('Status must be checked or unchecked');
console.log(errors.length?'REJECT\n'+errors.join('\n'):'ACCEPT: structural contract only');
process.exitCode=errors.length?1:0;
