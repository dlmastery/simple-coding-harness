import fs from 'node:fs';
import path from 'node:path';
import {themes} from './themes.mjs';
const root='harness';
const pairs=fs.readFileSync('how-did-i-generate-it/harness/MIGRATION.tsv','utf8').trim().split('\n').slice(1).map(l=>l.split('\t'));
const rows=pairs.map(([old,dir])=>({old,dir,title:fs.readFileSync(dir+'/README.md','utf8').split(/\r?\n/)[0].replace(/^# /,''),theme:themes.find(t=>dir.startsWith(root+'/'+t.dir+'/'))}));
const write=(file,body)=>fs.writeFileSync(file,body.trim()+'\n');
for(const [index,t] of themes.entries()){
 const labs=rows.filter(l=>l.theme===t);
 const table=labs.map(l=>`| [${l.title}](${path.posix.basename(l.dir)}/README.md) | [Code and offline test](${path.posix.basename(l.dir)}/) |`).join('\n');
 write(`${root}/${t.dir}/README.md`, `# ${t.title}

[Course](../../README.md) · [All lessons](../COURSE-MAP.md) · [Start here](../START-HERE.md) · [Glossary](../GLOSSARY.md)

Theme ${index+1} of 7 · ${labs.length} lessons · Original stages ${t.range}

${t.intro}

![${t.title}: a conceptual mechanism illustrated with actions and evidence.](../assets/${t.image}-v${t.image==="production"?2:t.image==="server"?3:1}.png)

*${t.limit} This figure explains the theme; individual lessons introduce its components gradually.* [Open the full-size figure](../assets/${t.image}-v${t.image==="production"?2:t.image==="server"?3:1}.png).

## Before you start

${t.before} Use [setup](../START-HERE.md) and a disposable learner workspace. Let the coding agent write commands and implementation changes. You predict behavior, inspect results and explain what happened.

## Work through the theme

${t.example}

| Lesson | Runnable snapshot |
|---|---|
${table}

Read the lessons in this order. Each snapshot has its own files; the agent should run its test from that snapshot's directory. Do not install several versions of the same harness command into one environment at once.

## Run, inspect and explain

Ask the tutor to open the first unfinished lesson, explain its new mechanism and run its offline test. Keep live provider calls separate: confirm the available endpoint, credentials and resource limit before using it. Save a prediction and the actual observation in your learner notes.

Try one controlled change in a copy. Predict its effect before the agent edits it. Re-run the relevant check and compare both outcomes. If a dependency or platform capability is missing, keep the error and use the source explanation until setup is repaired; do not describe that as a successful live run.

## Key takeaways

- ${t.after}
- ${t.limit}
- Keep an actual trace or test result beside each claim about behavior.

## Check your understanding

${t.question}

<details>
<summary>Hint and explanation</summary>

First name the object whose behavior you are claiming to know. Then identify the observation that supports that claim.

${t.answer}

</details>

## What's next

${index<themes.length-1?`The next theme asks you to ${themes[index+1].title.toLowerCase()}. Continue to [${themes[index+1].title}](../${themes[index+1].dir}/README.md).`:'Use the [teaching roadmap](../TEACHING-ROADMAP.md) to prepare a small evidence-linked portfolio. Then choose [generative UI](../../genui/README.md) or [RSI](../../rsi/README.md) according to the problem you want to study.'}
`);
}
for(const [i,l] of rows.entries()){
 const file=l.dir+'/README.md';
 let text=fs.readFileSync(file,'utf8');
 const nav=`[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)`;
 if(!text.includes('<!-- harness-navigation -->')){
  const split=text.indexOf('\n');
  text=text.slice(0,split+1)+`\n<!-- harness-navigation -->\n${nav}\n\nYou are in **${l.theme.title}**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. ${i?`Previous: [${rows[i-1].title}](${path.posix.relative(l.dir,rows[i-1].dir)}/README.md).`:'This is the first lesson.'} ${i+1<rows.length?`Next: [${rows[i+1].title}](${path.posix.relative(l.dir,rows[i+1].dir)}/README.md).`:'This is the final comparison lesson.'}\n\n[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.\n<!-- /harness-navigation -->\n`+text.slice(split+1);
 }
 write(file,text);
}
write(`${root}/COURSE-MAP.md`, `# Follow the harness from request to reliable execution

[Course](../README.md) · [Start here](START-HERE.md) · [Teaching roadmap](TEACHING-ROADMAP.md) · [Glossary](GLOSSARY.md)

The parent course contains **54 runnable lessons in seven themes**. Original lesson IDs are preserved: stage 2 has four lessons, so the last ID is 51. Each lesson is a code snapshot, not a claim that the entire system has reached production readiness.

![One model call develops into a controlled loop and an inspectable harness.](assets/overview-v1.png)

First understand a request and observation. Then add controls. Compare adapters only after you can say what they own. Add tools, recovery and inspectability before moving the loop behind a service. See the [migration map](MIGRATION.md) if you have an old path.

${themes.map((t,i)=>`## ${i+1}. ${t.title}\n\n${t.intro}\n\n**Readiness check:** ${t.after}\n\n[Theme guide and infographic](${t.dir}/README.md)\n\n| Lesson | Source and test |\n|---|---|\n${rows.filter(l=>l.theme===t).map(l=>`| [${l.title}](${path.posix.relative(root,l.dir)}/README.md) | [Files](${path.posix.relative(root,l.dir)}/) |`).join('\n')}`).join('\n\n')}
`);
write(`${root}/MIGRATION.md`, `# Find a lesson after the move

[Course](../README.md) · [Every lesson](COURSE-MAP.md)

The lesson IDs and implementations are preserved. The folders now live inside themes. Numeric commands such as \`python run_tests.py 14 15\` still run from the repository root. The full harness selector is \`python run_tests.py harness\`. An old bookmark to a root-level lesson may need the new path below; GitHub does not redirect file moves automatically.

The original long README is [backed up](../how-did-i-generate-it/harness/backups/README-before-reorganization.md) exactly as it was. Its old paths describe the historical layout. Use this map for current locations. The executable code remains beside each current lesson.

| Original root directory | Current lesson |
|---|---|
${rows.map(l=>`| \`${l.old}/\` | [${l.title}](${path.posix.relative(root,l.dir)}/README.md) |`).join('\n')}
`);
write('README.md', `# Build a coding agent, one mechanism at a time

Ask a model to explain a file and it can produce a plausible answer. Give it a file-reading tool and it can inspect the actual contents. Feed that observation into its next request and you have the beginning of an agent loop.

This course builds the machinery around that loop: tools, skills, state, permissions, context, recovery and evaluation. Each lesson keeps a runnable implementation beside its explanation. You can ask your coding agent to execute and modify the examples while you predict, inspect and explain the behavior.

![A model call becomes a controlled tool loop, then a harness with state, context, tests and human decisions.](harness/assets/overview-v1.png)

*A conceptual map of the course. Later lessons add the controls around the early loop. An illustration is not evidence that a particular sandbox, provider or deployment has passed a check.* [View full size](harness/assets/overview-v1.png).

**Begin with [Start here](harness/START-HERE.md).** Browse [all 54 lessons](harness/COURSE-MAP.md), use the [glossary](harness/GLOSSARY.md), or plan a class with the [teaching roadmap](harness/TEACHING-ROADMAP.md).

## What you will learn

- Trace a model request through a tool action and returned observation.
- Distinguish reusable skills, tool implementations, context, state and the harness that coordinates them.
- Test permission decisions, execution boundaries, stopping rules and recovery behavior.
- Compare local, SDK and hosted implementations by who owns each responsibility.
- Read tests and traces critically, then demonstrate a small working change with its limits.

**Prerequisites:** basic familiarity with files, functions and command output. No harness background is required. A coding agent can write the implementation and commands for you; reading small code examples helps you inspect its work.

**Equipment:** a CPU laptop, Python 3.10 or later for the Python lessons, and a coding agent with file and command access for guided study. Some extensions need Node, a browser, provider credentials or a running service. Offline tests use fakes; hosted runs have separate requirements and costs.

**Time:** begin with one 60–90 minute guided session. For the complete course, provisionally allow 30–50 hours of reading, discussion and small exercises, plus setup, live integrations and capstone work. This is an author planning estimate, not measured learner duration. The roadmap explains shorter routes and readiness checks.

## Seven themes, one clear path

| Theme | Original stages | What becomes possible |
|---|---|---|
${themes.map((t,i)=>`| [${i+1}. ${t.title}](harness/${t.dir}/README.md) | ${t.range} | ${t.after} |`).join('\n')}

The first two themes form the core. SDKs and the service are comparative routes; their live integrations are optional for understanding the local loop. Follow the listed prerequisites before entering the later recovery and production themes.

## Your first instruction to the agent

Open the repository root and paste:

\`\`\`text
Read harness/skills/harness-tutor/SKILL.md
and harness/START-HERE.md.
Begin the first lesson with me.
Explain one model request before adding tools.
You write commands and implementation changes.
I will predict, inspect and explain.
Run the offline check first and pause for my answer.
Keep my experiments in a separate learner copy.
\`\`\`

The tutor skill is a readable procedure. An agent without native skill discovery can open the file directly. Its actual tools and execution boundaries still determine what it can do.

## Find the material

\`\`\`text
README.md                         course entrance
harness/
  START-HERE.md                   setup and first session
  COURSE-MAP.md                   every lesson in learning order
  TEACHING-ROADMAP.md              routes, sessions and readiness checks
  GLOSSARY.md                     definitions and examples
  01_foundations/ ... 07_server/  themed guides and runnable lessons
  assets/                        overview and seven theme infographics
  skills/harness-tutor/           agent-guided learning procedure
genui/                           generative UI course
rsi/                             ML experiments to recursive self-improvement
how-did-i-generate-it/harness/    backup, plan, prompts and validation
run_tests.py                     offline test discovery across courses
check_snippets.py                quoted-code consistency checks
\`\`\`

The [migration map](harness/MIGRATION.md) connects every old lesson path to its new home. The [original walkthrough](how-did-i-generate-it/harness/backups/README-before-reorganization.md) is retained as a historical backup. Use the current lesson READMEs for runnable paths and detailed explanations.

## Continue into another course

| Course | Question it explores | Start |
|---|---|---|
| Generative UI | How does an agent produce an interface people can use? | [GenUI](genui/README.md); its guide names the harness prerequisites |
| Recursive self-improvement | How can we test changes to an ML research process and its improver? | [RSI](rsi/README.md); 101 labs, an expanded glossary and a teaching roadmap |

RSI starts with basic ML knowledge and introduces its own harness concepts. You do not need to finish every provider example here before beginning it.

## What has been checked

The reorganization preserves the lesson snapshots and updates their discovery and navigation. Consult the [validation record](how-did-i-generate-it/harness/VALIDATION.md) for actual checks and remaining failures. Passing fake-model tests does not establish live-provider compatibility, production safety or student learning outcomes.
`);
console.log(`Wrote 7 theme guides, 54 navigation blocks, course map, migration map and root README.`);
