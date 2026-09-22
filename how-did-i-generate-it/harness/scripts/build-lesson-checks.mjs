import fs from 'node:fs';
import {checks} from './lesson-checks.mjs';
const rows=fs.readFileSync('how-did-i-generate-it/harness/MIGRATION.tsv','utf8').trim().split('\n').slice(1).map(l=>l.split('\t'));
for(const [old,dir] of rows){
 const id=old.match(/^step_(\d+(?:_\d+)?)/)[1];
 const [question,answer]=checks[id]||[];
 if(!question)throw Error('Missing checkpoint '+id);
 const file=dir+'/README.md';
 const original=fs.readFileSync(file,'utf8');
 const body=original.replace(/\n<!-- harness-learning-check -->[\s\S]*?<!-- \/harness-learning-check -->\n?/,'');
 fs.writeFileSync(file,body.trimEnd()+`\n\n<!-- harness-learning-check -->
## Check your understanding

${question}

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

${answer}

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
`);
}
console.log(`Added ${rows.length} lesson-specific questions with explained answers and controlled-change prompts.`);
