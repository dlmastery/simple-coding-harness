// Original technical schematics. These are not generated raster illustrations.
// Arrows describe the relation stated in each caption, not measured causal effects.
const D=(caption,body)=>({caption,body});
export const diagrams={
'00.01':D('Predict the hourly total from allowed inputs. The two component counts already contain the answer.',`A["Calendar and observed weather"] --> B["Predict hourly rentals"]
C["casual + registered"] --> D["Actual cnt: outcome"]
B --> E["Compare with outcome"]
D --> E`),
'00.02':D('Keep course sources separate from your own work. A command must produce an inspectable artifact.',`A["Read course files"] --> B["Create learner workspace"]
B --> C["Run one command"]
C --> D["Open its actual output"]`),
'00.03':D('Learn the median from training rows once. Use it to predict every selection row.',`A["Training targets"] --> B["Training median"]
B --> C["Constant predictions"]
D["Selection targets"] --> E["MAE"]
C --> E`),
'00.04':D('A report is a claim. Prediction rows and a separate calculation let you check that claim.',`A["Saved predictions and targets"] --> B["Recompute error"]
B --> C["Compare values"]
D["Reported error"] --> C
C --> E["Agreement or mismatch"]`),
'01.01':D('Follow one fixed process. No outer search chooses a new recipe after the result.',`A["Frame task"] --> B["Inspect data"] --> C["Validate split"] --> D["Fit baseline"] --> E["Check report"]`),
'01.02':D('The process becomes evidence only when its actions run and their outputs are retained.',`A["Fixed process"] --> B["Execute actions"] --> C["Save outputs"] --> D["Check trace against process"]`),
'01.03':D('The skill tells the agent how to carry out the process. Tools perform the concrete operations.',`A["Readable skill"] --> B["Agent chooses next action"] --> C["Tool executes"] --> D["Observed result"]`),
'01.04':D('The checker starts from prediction rows. It does not accept the solver’s reported score as its input truth.',`A["Prediction rows"] --> B["Separate metric calculation"] --> C["Agreement check"]
D["Solver report"] --> C
C --> E["Accept evidence or flag mismatch"]`),
'01.05':D('A new session receives saved files. It should not need an unrecorded explanation from the previous chat.',`A["Skill, task, versions, setup"] --> B["New session"] --> C["Fresh baseline run"] --> D["Compare evidence"]`),
'02.01':D('The weak result motivates a specific new candidate. The evaluator stays fixed.',`A["Baseline result"] --> B["State a hypothesis"] --> C["Change model only"] --> D["Same evaluator"] --> E["Compare with baseline"]`),
'02.02':D('Each admitted attempt spends budget, even when it fails. State determines whether another attempt may start.',`A["State and remaining budget"] --> B{"Attempt allowed?"}
B -->|yes| C["Run and record attempt"]
C --> D["Update incumbent and budget"] --> A
B -->|no| E["Stop and report"]`),
'02.03':D('Use an observed error to choose one intervention. Keep other factors fixed to make the comparison interpretable.',`A["Error pattern"] --> B["Hypothesis"] --> C["One feature change"] --> D["Same model and evaluator"] --> E["Compare error patterns"]`),
'02.04':D('A loop needs a path out. Repeated failure, oscillation, or exhausted budget can trigger the declared stop rule.',`A["Attempt"] --> B["Check outcome and history"]
B -->|useful next action| A
B -->|stop rule reached| C["Retain evidence and stop"]`),
'02.05':D('Resume from recorded state only after reconciling unfinished work. Starting again must not erase spent attempts.',`A["Progress and ledger"] --> B["Inspect active process"] --> C{"State consistent?"}
C -->|yes| D["Resume remaining work"]
C -->|no| E["Record interruption and diagnose"]`),
'02.06':D('Both search rules start from the same conditions and receive the same total attempt allowance.',`A["Same task and starting state"] --> B["Search rule A"]
A --> C["Search rule B"]
B --> D["Outcomes and total cost"]
C --> D`),
'03.01':D('An arrow is a prerequisite: the destination needs the source to finish first.',`A["Inspect data"] --> B["Validate split"] --> C["Fit model"] --> D["Check predictions"]`),
'03.02':D('Different failures require different routes. A data problem should not trigger an expensive model search.',`A["Check failure type"] --> B{"Data or model?"}
B -->|data| C["Repair data contract"]
B -->|model| D["Propose model change"]
C --> E["Recheck"]
D --> E`),
'03.03':D('A join waits for all required checks on the same candidate. An old pass for another candidate cannot fill the gap.',`A["Candidate identity"] --> B["Data check"]
A --> C["Result check"]
B --> D["Join matching verdicts"]
C --> D
D --> E["Proceed only if all pass"]`),
'03.04':D('The retry cycle has a limit. Its failure path is part of the graph.',`A["Run operation"] --> B{"Valid result?"}
B -->|yes| C["Continue"]
B -->|no| D{"Repair budget left?"}
D -->|yes| A
D -->|no| E["Stop with failure record"]`),
'03.05':D('Changing an upstream artifact invalidates its descendants. Unaffected independent work can remain valid.',`A["Changed data transform"] --> B["Invalidate fitted model"] --> C["Invalidate predictions and score"]
D["Unchanged source license"] --> E["Keep valid provenance check"]`),
'03.06':D('Three views answer different questions. A drawn branch does not prove that branch ran.',`A["One workflow"] --> B["Plan: what may run"]
A --> C["Data flow: what each action needs"]
A --> D["Trace: what actually ran"]`),
'04.01':D('Name distinct objects before relating them. A dataset, a candidate, and a run are not interchangeable.',`A["Dataset version"] -->|input to| B["Candidate recipe"]
B -->|executed in| C["Run"]
C -->|produces| D["Predictions and metric"]`),
'04.02':D('These arrows describe meaning and provenance. They are not a schedule of commands.',`A["Candidate"] -->|trained on| B["Training partition"]
A -->|evaluated on| C["Selection partition"]
D["Score"] -->|measures| A
D -->|uses metric| E["MAE"]`),
'04.03':D('A rule constrains a relation. Training a transform on final data violates the declared experiment meaning.',`A["Transform"] -->|must fit on| B["Training rows"]
C["Proposed fit on final rows"] --> D["Rule check"] --> E["Reject contradiction"]`),
'04.04':D('A syntactically valid table can describe an invalid experiment. Meaning rules expose the contradiction.',`A["Readable facts"] --> B["Check relations against rules"]
B --> C["Target-derived input"]
B --> D["Final data used for training or selection"]
C --> E["Explain and reject"]
D --> E`),
'04.05':D('A changed definition propagates to the checks and reports that depend on it. Keep the earlier version interpretable.',`A["Definition v1"] --> B["Recorded experiment v1"]
A -->|explicit revision| C["Definition v2"] --> D["Update dependent checks"] --> E["New experiment v2"]`),
'05.01':D('Fixed components coordinate one valid experiment. A domain check can stop an invalid request before fitting.',`A["Task skill"] --> B["Domain check"] --> C["ML tool"] --> D["Result checker"] --> E["Report"]`),
'05.02':D('Routing selects an existing procedure appropriate to the task. It does not learn a new procedure.',`A["Task brief"] --> B{"Target type"}
B -->|count| C["Regression with MAE"]
B -->|binary label| D["Classification with balanced accuracy"]
B -->|unknown| E["Ask for a valid contract"]`),
'05.03':D('Retrieve relevant reusable knowledge, but initialize current state from the active task.',`A["Scoped experience"] --> B["Retrieve for current task"] --> C["Current decision"]
D["Current ledger and budget"] --> C`),
'05.04':D('Planning, execution, and checking have different responsibilities. Separate boxes alone do not enforce separate access.',`A["Planner: propose action"] --> B["Executor: perform action"] --> C["Checker: inspect evidence"] --> D["Record decision"]`),
'05.05':D('An ablation removes one component under matched conditions. Its effect may depend on the other components.',`A["Same cases and budget"] --> B["Full system"]
A --> C["System minus one component"]
B --> D["Compare outcomes and costs"]
C --> D`),
'06.01':D('The brief fixes scientific choices and required behavior. The builder supplies implementation details.',`A["Task, data, metric, split"] --> C["Readable harness brief"]
B["Budget, outputs, refusals"] --> C
C --> D["Resolve scientific ambiguity"]`),
'06.02':D('The builder produces the harness. The harness then runs the task. These are different objects.',`A["Brief"] --> B["Builder skill: meta-harness"] --> C["Generated harness"] --> D["Actual baseline run"] --> E["Checked evidence"]`),
'06.03':D('Trace each important requirement to implementation and then to observed behavior.',`A["Brief requirement"] --> B["Generated implementation"] --> C["Executed check"]
C --> D["Satisfied or unresolved"]`),
'06.04':D('A boundary is demonstrated by a meaningful refusal tied to the current request.',`A["Current request and identity"] --> B["Check contract and budget"]
B -->|valid| C["Fit and verify"]
B -->|invalid| D["Refuse before extra fit"]`),
'06.05':D('A fixed builder can generate different task-specific systems. Different output does not mean the builder learned.',`A["Unchanged builder"] --> B["Bike harness: MAE"]
A --> C["Wine harness: balanced accuracy"]
D["Different task briefs"] --> A`),
'06.06':D('Recreate behavior from saved inputs and dependencies. Generated source need not be byte-identical to satisfy the same contract.',`A["Brief, builder, code, data, versions"] --> B["Clean output folder"] --> C["Execute baseline and refusal"] --> D["Compare behavior"]`),
'07.01':D('Correction repairs the current output. It need not create a lasting instruction for future tasks.',`A["Current wrong result"] --> B["Check and correct"] --> C["Corrected current result"]`),
'07.02':D('A reflection is a hypothesis about the failure. Test it before treating it as a reliable lesson.',`A["Failure trace"] --> B["Proposed explanation"] --> C["Counterexample test"] --> D["Scoped lesson or rejection"]`),
'07.03':D('Persistent learning requires a retained change that is used later. Use and benefit are separate checks.',`A["Prior experience"] --> B["Retained lesson"] --> C["Later decision uses lesson"] --> D["Evaluate later outcome"]`),
'07.04':D('The task skill changes while its updater stays fixed. This is not yet an inherited change to the updater.',`A["Fixed improvement procedure"] --> B["Task skill v1"]
A --> C["Task skill v2"]
B --> D["Matched task comparison"]
C --> D`),
'07.05':D('Local assignment rules can change who does which work. Reorganization alone does not establish a performance gain.',`A["Work and local routing rules"] --> B["Initial assignments"] --> C["Changed assignments"] --> D["Measure resulting behavior"]`),
'07.06':D('A collective pattern can arise from local interactions. Observing the pattern is different from measuring useful improvement.',`A["Local rules"] --> B["Repeated interactions"] --> C["Collective pattern"] --> D["Separate usefulness check"]`),
'07.07':D('Self-play supplies interactions or challenges. Transfer still needs an evaluation outside those interactions.',`A["Role A"] -->|challenge| B["Role B"]
B -->|response| A
A --> C["Retained experience"] --> D["Fresh external task check"]`),
'07.08':D('Self-modification changes a component. Keep its parent and evaluate the change before retaining it.',`A["Parent component"] --> B["Proposed modification"] --> C["Execute and check"]
C -->|passes rule| D["Retain child"]
C -->|fails rule| E["Keep parent and failure"]`),
'08.01':D('A repeated comparison reveals variation. One favorable run cannot establish a reliable advantage.',`A["Prespecified comparison"] --> B["Repeated matched runs"] --> C["All outcomes"] --> D["Difference and uncertainty"]`),
'08.02':D('Freeze selection before final evaluation. Final feedback does not flow back into ordinary selection.',`A["Training"] --> B["Selection search"] --> C["Freeze chosen recipe"] --> D["Final evaluation"] --> E["Report once"]`),
'08.03':D('Research cost includes proposing, running, checking, and failed work. Fit time is only one component.',`A["Proposal cost"] --> E["Total research cost"]
B["Execution cost"] --> E
C["Evaluation cost"] --> E
D["Retries and failures"] --> E`),
'08.04':D('The four conditions separate memory and procedure changes. They also reveal whether the changes interact.',`A["Same task and resources"] --> B["Original procedure, no memory"]
A --> C["Original procedure, memory"]
A --> D["New procedure, no memory"]
A --> E["New procedure, memory"]`),
'08.05':D('Freeze the learned change before testing a new task. New-task feedback must not silently tune the candidate being evaluated.',`A["Development experience"] --> B["Freeze retained change"] --> C["Prespecified transfer task"] --> D["Scoped transfer claim"]`),
'08.06':D('A lower reported error does not override invalid evidence. Rollback preserves both the parent and the rejected record.',`A["Apparent winning candidate"] --> B["Check validity and retention rule"]
B -->|valid improvement| C["Promote"]
B -->|invalid or worse| D["Retain parent and rejection"]`),
'09.01':D('The solver proposes task experiments. The improver changes that solver procedure. The evaluator measures outcomes.',`A["Improver"] -->|revises| B["Solver skill"]
B -->|proposes| C["ML candidate"]
C --> D["Fixed evaluator"]
D -->|development evidence| A`),
'09.02':D('Many solver revisions can come from one unchanged improver. Iteration count does not establish recursion in the improver.',`A["Fixed improver v0"] --> B["Solver v1"]
A --> C["Solver v2"]
A --> D["Solver v3"]`),
'09.03':D('An improver revision is a proposal about how to improve later work. It still needs inheritance and evaluation.',`A["Observed improver failure"] --> B["Revision hypothesis"] --> C["Improver v1"]
D["Improver v0 preserved"] --> C`),
'09.04':D('A later round must read the revised improver and execute an action it requires. A saved file alone is insufficient.',`A["Improver v1 and hash"] --> B["Later round loads v1"] --> C["Changed instruction executes"] --> D["Trace and decision"]`),
'09.05':D('Compare the improvements produced by the two improvers from matched starts. Do not compare only their instruction text.',`A["Matched starting solver and tasks"] --> B["Old improver"]
A --> C["Revised improver"]
B --> D["Resulting solver improvement and total cost"]
C --> D`),
'09.06':D('Each generation retains lineage and passes the declared checks. A failed revision can end the chain or keep the parent.',`A["Generation 0"] --> B["Propose revised improver"] --> C["Check and compare"]
C -->|retain| D["Generation 1 inherits revision"]
C -->|reject or budget spent| E["Keep parent and stop"]`),
'09.07':D('Each claim needs its own evidence. Structural inheritance does not by itself establish benefit or acceleration.',`A["Version and execution trace"] --> B["Structural inheritance claim"]
C["Matched improver comparison"] --> D["Effectiveness claim"]
E["Comparable rates across generations"] --> F["Acceleration claim"]`),
'10.01':D('Apply each source’s definitions to actual artifacts. Equal level numbers from different frameworks need not mean the same thing.',`A["Observed artifacts"] --> C["Classify with stated criteria"]
B["Source definitions"] --> C
C --> D["Supported label and missing evidence"]`),
'10.02':D('Follow a claim back to its original evidence. A social announcement and a reproduced experiment are different endpoints.',`A["Announcement"] --> B["Primary source and date"] --> C["Method and artifacts"] --> D["Verified claim or explicit gap"]`),
'10.03':D('Choose an experiment for the uncertainty it can resolve. A likely high score is not always the most informative next observation.',`A["Unknown behavior"] --> B["Discriminating experiment"] --> C["Observed outcome"] --> D["Narrower uncertainty"]`),
'10.04':D('The verifier checks the outcome. The actor writes memory; the verdict does not approve the wording of that memory.',`A["Task outcome"] --> B["Verifier verdict"] --> C["Actor writes scoped memory"] --> D["Test memory interpretation"]`),
'10.05':D('Freeze memory before comparing access conditions. Evaluation does not update that memory.',`A["Frozen memory version"] --> B["Memory condition"]
C["Matched evaluation tasks"] --> B
C --> D["No-memory condition"]
B --> E["Compare outcomes and context limits"]
D --> E`),
'10.06':D('Working state belongs to this run. Scoped experience can inform another run without carrying over stale candidate IDs or budgets.',`A["Reusable experience"] --> C["Current decision"]
B["New run state"] --> C
D["Old run state"] --> E["Archive with old run"]`),
'10.07':D('The tree stores attempted descendants and actual outcomes. An unexecuted branch remains unknown.',`A["Measured baseline"] --> B["Measured child 1"]
A --> C["Measured child 2"]
A -.-> D["Unexecuted branch: unknown"]`),
'10.08':D('Replay can answer only questions covered by recorded work. It does not create new environment outcomes.',`A["Frozen discovery tree"] --> C["Replay under budget"]
B["Node-order policy"] --> C
C --> D["Known recorded outcome"]
C --> E["Uncovered query: unknown"]`),
'10.09':D('A policy selected by replay still needs a fresh online check. Discovery and fresh evaluation answer different questions.',`A["Replay comparison"] --> B["Freeze policy"] --> C["New environment execution"] --> D["Check transfer and total cost"]`),
'10.10':D('Use repeated contrasting traces to localize a failure, then restrict the proposed edit to a declared module.',`A["Success and failure traces"] --> B["Recurring failure pattern"] --> C["Responsible module"] --> D["Bounded module edit"]`),
'10.11':D('Two useful edits can conflict when combined. Test the integrated system and its transfer separately.',`A["Module edit A"] --> C["Integrated harness"]
B["Module edit B"] --> C
C --> D["Interaction checks"] --> E["Frozen transfer check"]`),
'10.12':D('A lineage must identify what each child changes. Agent changes and changes to the agent’s updater support different claims.',`A["Parent system"] --> B["Child agent artifact"]
A --> C["Child improvement procedure"]
B --> D["Audit changed object and later use"]
C --> D`),
'10.13':D('The inner researcher uses a fixed procedure to search ML candidates. Keep its search record and budget visible.',`A["Fixed researcher skill"] --> B["Propose ML candidate"] --> C["Run and evaluate"] --> D["Update search state"]
D -->|budget remains| B`),
'10.14':D('The outer experiment changes the inner researcher. Count the cost of discovering that change as well as its later use.',`A["Outer research procedure"] --> B["Revised inner researcher"] --> C["Fresh matched ML tasks"] --> D["Gain and full research cost"]`),
'10.15':D('An ignition claim concerns whether improvement can sustain further improvement. It needs a different comparison from one useful outer edit.',`A["Initial outer change"] --> B["Later improvement work"] --> C["Comparable generations"] --> D["Evidence for or against sustained benefit"]`),
'10.16':D('The fixed pipeline changes a task skill, tests it, and retains only an eligible revision.',`A["Fixed skill updater"] --> B["Candidate task skill"] --> C["Execute fresh task checks"]
C -->|retain rule passes| D["Active task skill"]
C -->|fails| E["Keep parent"]`),
'10.17':D('Task skills can change frequently while the updater changes less often. The new updater must govern a later skill revision.',`A["Task-skill update history"] --> B["Revise updater at checkpoint"] --> C["Later updater version"] --> D["New task-skill update uses it"]`),
'10.18':D('Turn an observed limitation into a falsifiable hypothesis before changing the experiment.',`A["Observed limitation"] --> B["Hypothesis"] --> C["Predicted difference"] --> D["Prespecified experiment"]`),
'10.19':D('Screening selects promising ideas. Ablation then asks which part contributes under a controlled comparison.',`A["Several hypotheses"] --> B["Bounded screening"] --> C["Selected candidate"] --> D["Remove one contribution"] --> E["Compare under same checks"]`),
'10.20':D('A criticism leads to a targeted check. The response should cite its result, including a result that weakens the claim.',`A["Research claim"] --> B["Specific criticism"] --> C["Targeted check"] --> D["Evidence-based response"]`),
'10.21':D('Better research outputs and a better research procedure are distinct objects of evaluation.',`A["Successive research artifacts"] --> B["Artifact-quality comparison"]
C["Old and revised scientist procedures"] --> D["Matched fresh-task comparison"]`),
'10.22':D('A human correction becomes a learning opportunity only after its task, evidence, and acceptance rubric are explicit.',`A["Researcher request and correction"] --> B["Executable task"] --> C["Observable rubric"] --> D["Checked discovery example"]`),
'10.23':D('Hold the model fixed while testing a harness edit. Keep the rubric fixed during this comparison.',`A["Fixed model and rubric"] --> B["Parent harness"]
A --> C["Edited harness"]
B --> D["Matched task outcomes"]
C --> D`),
'10.24':D('The numerical exercise turns a group of rewards into relative advantages. This is not an LLM training run or full GRPO.',`A["Labelled reward group"] --> B["Group mean and spread"] --> C["Relative advantages"] --> D["Toy update or zero-variance handling"]`),
'10.25':D('Track model and harness versions as a pair. Changing either can alter compatibility with the other.',`A["Model 0, harness 0"] -->|harness change| B["Model 0, harness 1"]
B -->|model update| C["Model 1, harness 1"]
C --> D["Check pair before next cycle"]`),
'10.26':D('Read each result with its protocol. Single-attempt accuracy and multi-attempt coverage cannot be exchanged.',`A["Paper table or figure"] --> B["Task, split, attempt count, metric"] --> C["Correct scoped comparison"] --> D["Claim and limits"]`),
'10.27':D('Raw traces, a knowledge store, and active instructions have different roles. Rejected instruction edits need not erase the trace.',`A["Raw execution traces"] --> B["Scoped knowledge store"] --> C["Candidate skill edit"] --> D["Promotion check"]
D -->|accepted| E["Active skill"]`),
'10.28':D('A procedure graph specifies actions and transitions. Freeze the selected graph before testing it on fresh cases.',`A["Failure trace"] --> B["Bounded graph edit"] --> C["Development checks"] --> D["Freeze selected graph"] --> E["Fresh evaluation"]`),
'10.29':D('Observe an actual page action and its result. A revised GUI skill needs another execution to establish that the repair works.',`A["Browser action"] --> B["Observed UI outcome"] --> C["Scoped skill repair"] --> D["New execution and check"]`),
'10.30':D('A cheaper harness is eligible only if it still meets the declared quality requirement.',`A["Candidate harness"] --> B["Measure full cost and quality"] --> C{"Quality floor met?"}
C -->|yes| D["Compare efficiency"]
C -->|no| E["Reject apparent saving"]`),
'10.31':D('Name the object that changes. In Harness-of-Harness, the developed software changes while the agent configuration remains fixed.',`A["HarnessDev"] --> B["Created or revised agent harness"]
C["Harness-of-Harness"] --> D["Evolving software and evidence"]
E["Fixed agent configuration"] --> D`),
'10.32':D('Both memory representations refer to the same event history. The checker computes truth from the original events.',`A["Original events"] --> B["Raw-history input"]
A --> C["Summary plus later events"]
A --> D["Exact state checker"]
B --> E["Compare answers"]
C --> E
D --> E`),
'10.33':D('Action hints and richer observations supply different assistance. Remove help in a separate fresh check.',`A["Same task"] --> B["Hint about next action"]
A --> C["More state information"]
B --> D["Assisted outcomes"]
C --> D
D --> E["Fresh unassisted check"]`),
'10.34':D('An otherwise sensible answer can violate a harness interface. The local correction restores compatibility without training model weights.',`A["Response fixture"] --> B["Fixed parser"] --> C["Mismatch"] --> D["Local correction"] --> E["Rerun parser check"]`),
'10.35':D('The simulation composes typed changes and can revise their schedule. Its synthetic values are not model-training results.',`A["Versioned evidence"] --> B["Scheduler policy"]
B --> C["Data operator"]
B --> D["Harness operator"]
B --> E["Model-state operator"]
C --> F["Fixed external checks"]
D --> F
E --> F`),
'10.36':D('Check a reference before using it to diagnose failure. A proposed edit must also pass leakage and regression checks.',`A["Reference trajectory"] --> B["Verify genuine execution"] --> C["Diagnose failed trace"] --> D["Propose skill edit"] --> E["Quality and performance gates"]`),
'10.37':D('Compare systems on common questions before comparing scores. Missing evidence stays visible.',`A["Different systems"] --> B["Changed object, feedback, inheritance"] --> C["Evaluation and resources"] --> D["Source-linked comparison"]`),
'10.38':D('The slow stage limits total speedup. The calculator uses declared synthetic costs, not a forecast.',`A["Proposal time"] --> B["Execution time"] --> C["Evaluation time"] --> D["Total time per checked result"]`),
'11.01':D('A new scientific brief should produce a runnable system and a meaningful refusal. Files alone are insufficient.',`A["New task brief"] --> B["Generated harness"] --> C["Baseline and invalid request"] --> D["Evidence and peer handoff"]`),
'11.02':D('The capstone joins revision, inheritance, and matched evaluation in a bounded experiment.',`A["Prespecified protocol"] --> B["Improver revision"] --> C["Later round uses revision"] --> D["Matched comparison"] --> E["Scoped final claim"]`),
'11.03':D('Task transfer, agent portability, and compute portability require different checks. One passing check does not certify the others.',`A["Saved system"] --> B["New task check"]
A --> C["New coding-agent check"]
A --> D["New compute-backend check"]`),
'11.04':D('Audit an unfamiliar claim through its source, artifacts, and strongest alternative explanation.',`A["Unfamiliar RSI claim"] --> B["Primary source and artifacts"] --> C["Alternative explanation"] --> D["Discriminating evidence or unresolved gap"]`),
'11.05':D('Teach-back connects the mechanism to an observation and then to a new case. Repeating vocabulary is not enough.',`A["Explain the mechanism"] --> B["Show actual evidence"] --> C["Predict a changed case"] --> D["Defend the claim and its limit"]`),
};

export function renderDiagram(id) {
  const d=diagrams[id];
  if (!d) throw new Error(`Missing technical schematic for lab ${id}`);
  const horizontal=new Set(['00.01','00.03','00.04','01.04','03.03','03.05','03.06','04.01','04.02','05.02','05.03','05.05','06.05','07.04','07.05','07.06','07.07','08.03','08.04','09.02','09.05','09.07','10.05','10.06','10.07','10.08','10.11','10.12','10.21','10.23','10.25','10.31','10.32','10.33','10.35','11.03']);
  const direction=horizontal.has(id)?'LR':'TD';
  return `\`\`\`mermaid\n%%{init: {"theme":"base","themeVariables":{"background":"#ffffff","primaryColor":"#eef5fb","primaryTextColor":"#172b3a","primaryBorderColor":"#45667d","lineColor":"#45667d","secondaryColor":"#fff3d9","tertiaryColor":"#e9f6f0","fontFamily":"Arial"}}}%%\nflowchart ${direction}\n${d.body}\n\`\`\`\n\n*Read the diagram:* ${d.caption}`;
}
