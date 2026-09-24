// Make every required comparison and counterexample fit its declared allowance.
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=dirname(fileURLToPath(import.meta.url));
const changes={
  'lessons-science.mjs':[
    ['One skill edit and two checker runs; no model-weight training.','One skill edit and four checker runs: parent and child on complete and incomplete evidence fixtures. No model-weight training.'],
    ['Use parent and child on matched report fixtures. Run the executable rubric checks and retain both outputs.','Use parent and child on the same complete and incomplete evidence fixtures, making four report/check pairs. Retain every output and verdict. Do not invent missing class evidence to satisfy the rubric.'],
    ['Plan two small development-only screening experiments. State subset selection, metric, cost limit, and the rule for advancing one idea. Keep final data untouched.','Plan two small development-only screening experiments. State subset selection, metric, cost limit, and the rule for advancing one idea. Have the agent generate a separate screening runner; the supplied general tool keeps its training partition fixed. Preserve the original data and contracts, fit preprocessing only on the declared training subset, and keep final data untouched.']
  ],
  'lessons-frontier.mjs':[
    ['One graph edit and two checks; at most two fits.','One graph edit and four executable fixture checks: two selection cases, one fresh case, and one semantic-error case. Use a fit stub; no training.'],
    ['Run selection checks, preserve rejected edits, freeze the chosen graph, and test a fresh fixture.','Run the target and regression selection fixtures, preserve rejected edits, freeze the chosen graph, and test a fresh fixture. Use a fit stub throughout. Reserve the fourth check for the semantic-error fixture below.'],
    ['Introduce a validly typed but semantically wrong feature. Explain why the procedure graph still needs domain checks.','For the fourth check, introduce a validly typed but semantically wrong feature and execute the domain check. Explain why a procedure graph still needs meaning rules.'],
    ['Add a filter and candidate detail view. Ask the browser-capable agent','Add a filter and candidate detail view, with an invalid candidate’s warning visible only in its detail view from the first attempt onward. Ask the browser-capable agent'],
    ['Hide an invalid candidate’s warning behind a detail view. Test whether the revised skill inspects it before selecting.','Inspect the two saved UI attempts. Determine whether each inspected the warning hidden in the detail view before selecting. Do not add a third UI attempt to improve the presentation.'],
    ['Two variants, at most two fits each. Include proposal and checking overhead.','Two variants, at most two fits each, plus one checker-removal fixture with a fit stub. Include proposal and checking overhead.'],
    ['Run the same comparison after removing a necessary checker in a labelled fixture. Explain why the apparent saving is not a valid win.','Run one labelled fixture with a necessary checker removed and a fit stub in place of training. Compare its missing evidence with the declared quality floor. Explain why the apparent saving is not a valid win.'],
    ['Two short task attempts and one counterexample; no model-weight training.','Five short attempts: raw history, summary plus tail, faulty summary, and two expanded-description conditions. No model-weight training.'],
    ['Three short attempts, no required model fit.','Four short attempts: action hint, richer observation, unassisted fresh fixture, and stale-hint counterexample. No model fits.'],
    ['Three interface checks, no LLM training.','Four interface checks: valid, mismatched, locally repaired, and incompatible-template counterexample. No LLM training.'],
    ['Three trace checks and one candidate-skill evaluation on two fixtures.','Four trace checks, including the alternative-path counterexample, and one candidate-skill evaluation on two fixtures. No model fits.'],
    ['One numerical simulation with three scenarios; no paid compute.','Five numerical scenarios: baseline, faster proposals, faster evaluation, checking overhead, and one saturation or verifier-cost extension. No paid compute.']
  ],
  'lessons-capstone.mjs':[
    ['Keep evaluation and promotion rules outside the ordinary candidate’s writable surface, or state the weaker local boundary.','Keep the external comparison and final acceptance criteria outside the ordinary candidate’s writable surface, or state the weaker local boundary. An improver’s internal proposal-selection rule may be revised as a candidate change; the unchanged external protocol judges its consequences.']
  ]
};
for(const [file,pairs] of Object.entries(changes)){
  const path=resolve(dir,file); let body=readFileSync(path,'utf8');
  for(const [old,next] of pairs){
    if(body.includes(next)) continue;
    if(!body.includes(old)) throw new Error(`Missing source in ${file}: ${old}`);
    body=body.replace(old,next);
  }
  writeFileSync(path,body);
}
console.log('Reconciled studio budgets and external acceptance boundary.');
