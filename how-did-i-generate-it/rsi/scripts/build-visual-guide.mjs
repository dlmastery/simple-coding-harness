// Agent-authored publisher for a visual companion, not a second lesson sequence.
import {writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {lessons,themes} from './lesson-content.mjs';
import {renderIllustration} from './lesson-illustrations.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const topics=[
  ['course-map','Your route through all twelve themes'],
  ['research-map','Inside the research studio'],
  ['capstone-map','The capstones: build, test, and explain'],
  ['09.01','From one experiment to RSI'],
  ['00.01','The answer hidden in an input'],
  ['00.02','Keep the course separate from your experiment'],
  ['00.03','Learn one number, then keep it fixed'],
  ['00.04','Check the number and the rows behind it'],
  ['01.01','Before the first improvement loop'],
  ['01.02','A plan says what should happen. A trace records what did.'],
  ['01.03','The skill guides. The agent acts. The tool runs.'],
  ['01.04','A plausible score can belong to the wrong rows'],
  ['01.05','Carry the procedure across the session boundary'],
  ['02.01','Change one factor to test your explanation'],
  ['02.02','A loop needs memory and a way out'],
  ['02.03','Feedback matters when it changes the next action'],
  ['02.04','Stop a repeated idea before it becomes another fit'],
  ['02.05','A restart does not refill the experiment budget'],
  ['02.06','Compare how two procedures spend the same attempts'],
  ['04.02','Workflow and domain meaning'],
  ['05.04','Save the state. Check the handoff.'],
  ['06.02','The builder and the system it builds'],
  ['07.08','Similar words, different changes'],
  ['09.02','Two generations can use the same improver'],
  ['09.03','Change the rule that judges skill revisions'],
  ['09.04','The next round must use the change'],
  ['09.05','Compare what each improver produces'],
  ['09.06','A proposal is not the active parent'],
  ['09.07','Three claims need different evidence'],
  ['10.01','Classify the mechanism, then test the benefit'],
  ['10.02','Follow an announcement to its evidence'],
  ['10.03','Spend the next fit on an unanswered question'],
  ['10.04','Check the result, then write the lesson'],
  ['10.05','Freeze the memory, control who can read it'],
  ['10.06','Carry the lesson, reset the run state'],
  ['10.07','A discovery tree records work that happened'],
  ['10.08','Replay stops at the edge of the record'],
  ['10.09','A replay winner still needs fresh evidence'],
  ['10.10','Repair a component. Check the system.'],
  ['10.11','Test the combination, not just its parts'],
  ['10.12','Label the procedure on every lineage edge'],
  ['10.13','The researcher decides which experiment comes next'],
  ['10.14','Improve the researcher, then test the improver'],
  ['10.15','A better researcher may not be a better improver'],
  ['10.16','Change the task skill while its updater stays fixed'],
  ['10.17','Improve the skill—and the way you revise it'],
  ['10.18','Turn a limitation into a tested claim'],
  ['10.19','Screen ideas, then test a contribution'],
  ['10.20','Answer a criticism with evidence'],
  ['10.21','Track the discovery and its researcher'],
  ['10.22','Turn a correction into something you can check'],
  ['10.23','Change the reporting skill, then test its behavior'],
  ['10.24','A reward becomes a relative learning signal'],
  ['10.25','Two ways to improve a scientific agent'],
  ['10.26','Read the metric beside the percentage'],
  ['10.27','A failed edit can still teach us'],
  ['10.28','Repair the route. Check the meaning.'],
  ['10.29','A plausible click is not a checked result'],
  ['10.30','Save work without losing the evidence'],
  ['10.31','Name the object that changes'],
  ['10.32','A shorter memory can lose the state'],
  ['10.33','Help can change behavior without changing weights'],
  ['10.34','A polished answer can break the interface'],
  ['10.35','Change the system and the rule that schedules changes'],
  ['10.36','A reference must show the work'],
  ['10.37','Compare the mechanism, then weigh the evidence'],
  ['10.38','Faster proposals do not remove a slow check'],
  ['11.01','From a new brief to a working harness'],
  ['11.02','Make a recursive experiment inspectable'],
  ['11.03','Change one dimension. Test its consequences.'],
  ['11.04','Turn a bold claim into a testable question'],
  ['11.05','Let another person follow the evidence'],
  ['compute','Move the compute, preserve the evidence']
];
const sections=topics.map(([id,title])=>{
  const l=lessons.find(x=>x.id===id);
  const guides={
    'course-map':['COURSE-MAP.md','The guided course map'],
    'research-map':['10_research_studio/README.md','The research studio and its thirteen groups'],
    'capstone-map':['11_capstones/README.md','The five capstone labs'],
    'compute':['compute/README.md','The larger-compute guide']
  };
  if(!l && !guides[id]) throw new Error('Missing illustration destination: '+id);
  const destination=l ? `${themes[l.theme].directory}/${l.group ? l.group+'/' : ''}step_${l.id.split('.')[1]}_${l.slug}/README.md` : guides[id][0];
  const label=l ? `Lab ${l.id}: ${l.title}` : guides[id][1];
  return `## ${title}\n\n${renderIllustration(id,p=>p)}\n\n[${label}](${destination}).`;
});
writeFileSync(resolve(repo,'rsi/VISUAL-GUIDE.md'),`# A visual guide to the course\n\n[Course](README.md) · [Start here](START-HERE.md)\n\nUse these illustrations to preview an idea or revisit a distinction. Follow the [learning path](LEARNING-PATH.md) for the actual lesson order; this gallery does not replace the experiments, checks, or quizzes. Each figure links to the lab that explains its mechanism. Open dense figures at full size when reading on a phone.\n\nThese are conceptual illustrations. Measured results appear as separate plots with their data and execution records.\n\n${sections.join('\n\n')}\n`);
console.log(`Published a visual companion with ${topics.length} reviewed illustrations.`);
await import('./build-visual-coverage.mjs');
