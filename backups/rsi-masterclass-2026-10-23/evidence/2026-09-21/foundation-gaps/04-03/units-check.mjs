import {readFileSync} from 'node:fs';
const text=readFileSync(process.argv[2],'utf8');
const metric=/^Metric: (.*)$/m.exec(text)?.[1]?.trim();
const units=/^Units: (.*)$/m.exec(text)?.[1]?.trim();
const ok=metric==='MAE'&&Boolean(units);
console.log(ok?'PASS: MAE has a nonempty unit label':'FAIL: this MAE fixture needs a nonempty unit label');
process.exitCode=ok?0:1;
