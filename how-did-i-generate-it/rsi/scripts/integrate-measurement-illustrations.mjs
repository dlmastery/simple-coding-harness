// Integrate reviewed measurement figures; retained authoring step.
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const items=[
  [
    "08.01",
    "paired-seeds-comparison-v1",
    "Keep every planned pair, not just the best run",
    "Three paired seeds compare frozen tree and forest recipes on one task and split. Six result slots lead to paired differences, while a separate crossed-out example rejects reporting only a favorable seed.",
    "The difference is forest MAE minus tree MAE, so a negative value favors the forest. Recipe families and complexity differ; seeds are paired within that comparison. The star on seed 29 is an arbitrary example of selective reporting, not the best seed in the archived run. Blank cells and checklist marks specify planned work, not new measurements. The measured plot below uses the actual recorded results. Three seeds do not establish transfer to other tasks or data splits."
  ],
  [
    "08.02",
    "freeze-before-final-v2",
    "Freeze the choice before you reveal the final score",
    "A recorded candidate choice is locked before its frozen recipe is refitted on original training rows and scored on final rows. Another selection fit is refused. A separate panel distinguishes the local workflow lock from access isolation.",
    "Use the original experiment workspace, not a new experiment with a reset selection history. The final operation permits a refit of the frozen recipe on original training rows only; it does not permit another selection fit or adding selection rows to training. Preserve the lock even if final scoring fails. The pictured lock is a cooperative local control over public data. Actual access isolation requires separate permissions and an evaluator; this course does not claim those controls exist. The recipe, reason, and contract belong in the decision record, not extra fields invented for FINAL-LOCK.md."
  ],
  [
    "08.03",
    "research-cost-ledger-v1",
    "Count the work that produced the retained result",
    "Proposal, data, fit, checking, review, retry, and failure records feed a complete cost ledger. The retained candidate is only a subset. A separate invented example shows how proposal overhead can erase a fit-time advantage.",
    "Account for the full search effort, including work that failed or did not help. Wall time, tokens, fit time, and GPU-hours measure different resources; do not add overlapping durations or unlike units. The token counter is an instrument icon, not a zero-usage observation. Leave unavailable usage unknown. The 20+p versus 30+10 comparison is invented arithmetic with sequential stages and equal other costs. It is not a measured result from this course, and equal fit counts do not establish equal total cost."
  ],
  [
    "08.04",
    "memory-skill-factorial-v1",
    "Test the combination, not only its parts",
    "Four fixed parent/child and memory-absent/present combinations form a factorial comparison. Memory effects are compared within each skill. A detached fifth condition removes one conflicting memory rule and keeps a separate record.",
    "Keep the same memory version in both memory-present arms and the same parent or child instructions across its row. The blank records do not assume the child wins or memory helps. Differences between the two memory effects describe an interaction in these observations; noisy results need uncertainty analysis before a broader claim. The four main checks or fits and the separate follow-up have distinct budgets. Fresh folders do not isolate agent knowledge. The archived worked example below replays deterministic decisions over cached predictions; it is not an LLM training experiment."
  ],
  [
    "08.05",
    "frozen-skill-transfer-v1",
    "Freeze the procedure before testing a new task",
    "Two bike-developed task skills are frozen before wine feedback. A predeclared adapter maps the target, metric, and interfaces. Each skill gets two wine fits; result-informed edits require a new development version and fresh transfer cases.",
    "The frozen objects are the research instructions and their declared interfaces. The left-hand cards list task-specific material those instructions operate on; do not reuse a fitted bike model as a wine classifier or treat model code as the skill itself. Declare target, inputs, split, model interface, and maximizing balanced accuracy before wine outcomes. Keep both class recalls and all four attempts. The author already knew the public wine task, so the archived exercise is a transfer replay, not a fresh unseen-task test. No result is filled in here."
  ],
  [
    "08.06",
    "metric-switch-and-rollback-v1",
    "Reject a win created by changing the metric",
    "An apparent majority-class win based on ordinary accuracy is checked against the declared balanced-accuracy objective using existing predictions. A changed active version is restored; otherwise rejection alone is recorded, with failed evidence preserved.",
    "The constant predictor has recalls one and zero when both classes occur, giving balanced accuracy 0.5. The failure concerns this fixture's unsupported promotion and omitted evidence; a majority baseline is not invalid for every task and is not automatically worse than every candidate. Checklist marks describe required checks, not a new execution. Restore the prior valid version only if the fixture replaced it. A new accuracy objective requires an explicit new task and tradeoff; it cannot relabel the earlier comparison."
  ]
];
const outputs=[
  [
    "paired-seeds-comparison-v1",
    "exec-6e4a52f3-24d4-481f-a2f9-1b7af5f16a7e.png",
    true
  ],
  [
    "freeze-before-final-v1",
    "exec-65bc2319-b7db-4d21-995b-21099efd1814.png",
    false
  ],
  [
    "freeze-before-final-v2",
    "exec-33768c35-a07b-43c9-9cb2-7805c24aa4a1.png",
    true
  ],
  [
    "research-cost-ledger-v1",
    "exec-f058164e-65b6-4fe1-9ac8-3d8d8c27ff74.png",
    true
  ],
  [
    "memory-skill-factorial-v1",
    "exec-bc1f58b5-89d5-4830-9e4a-f8a4508513db.png",
    true
  ],
  [
    "frozen-skill-transfer-v1",
    "exec-5598ea3b-8dbb-4910-b498-a87ff72cd348.png",
    true
  ],
  [
    "metric-switch-and-rollback-v1",
    "exec-5a172dc3-b984-462a-aa59-c0dd8c575a7c.png",
    true
  ]
];
function edit(path,fn){const p=resolve(root,path); const old=readFileSync(p,'utf8'); const next=fn(old); if(next===old)throw Error('No change: '+path);writeFileSync(p,next);}
edit('how-did-i-generate-it/rsi/scripts/lesson-illustrations.mjs',s=>s.replace("  'compute': {",items.map(([id,stem,title,alt,caption])=>"  '"+id+"': "+JSON.stringify({file:stem+'.png',alt,caption},null,4)+",").join('\n')+"\n  'compute': {"));
edit('how-did-i-generate-it/rsi/scripts/build-illustration-manifest.mjs',s=>s.replace('const outputs=[','const outputs=[\n'+outputs.map(x=>'  '+JSON.stringify(x)+',').join('\n')));
edit('how-did-i-generate-it/rsi/scripts/build-visual-guide.mjs',s=>s.replace("  ['09.02'",items.map(([id,stem,title])=>'  '+JSON.stringify([id,title])+',').join('\n')+"\n  ['09.02'"));
edit('how-did-i-generate-it/rsi/visuals/generated/README.md',s=>s.replace('Ninety-nine selected','One hundred five selected').replace('All 147 generated','All 154 generated').replace('the remaining focused lesson illustrations are still in progress','all 101 labs now have individual illustrations').replace('## Lab 07.01',items.map(([id,stem,title,alt,caption])=>'## Lab '+id+'\n\n!['+alt+']('+stem+'.png)\n\nSelected: ['+stem+'.png]('+stem+'.png). Exact [prompt]('+stem+'.prompt.md). '+caption).join('\n\n')+'\n\nThe [first final-boundary draft](freeze-before-final-v1.png) and its [prompt](freeze-before-final-v1.prompt.md) are preserved. The selected revision corrects selection-fit versus final-refit language, lock fields, and access controls. See the [measurement review](../../validation/MEASUREMENT-ILLUSTRATIONS.md).\n\n## Lab 07.01'));
edit('how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs',s=>s.replace('Four arms with one fit each, or four executable fixture checks if fitting is unnecessary.','Four main arms, each with one fit or one executable check. The separately declared follow-up adds one check, or one fit if needed.').replace('Remove a conflicting memory rule in a separately declared follow-up. Do not merge that new result into the original experiment.','Remove one conflicting memory rule and check one affected arm in a separately declared follow-up. Keep all other conditions fixed. Preserve both memory versions and the extra check or fit cost. Do not merge this fifth result into the original four-arm experiment.'));
edit('how-did-i-generate-it/rsi/scripts/guidance-improvement.mjs',s=>s.replace("['Effect comparison','Compares memory within each skill version and skill change within each memory condition.']","['Effect comparison','Compares memory within each skill version and skill change within each memory condition.'],['Separate follow-up record','Preserves the removed rule, both memory versions, affected arm, outcome, and additional check or fit cost.']"));
