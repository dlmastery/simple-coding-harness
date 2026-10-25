"""Execute the declared local rubric, numerical, and paired-state teaching cases."""
import argparse
import csv
import hashlib
import importlib.util
import math
from pathlib import Path
import re
import shutil
import statistics
import sys
import time

import numpy as np
import pandas as pd


def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8',newline='\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def metrics(frame):
    recalls={label:float((frame.loc[frame.actual==label,'predicted']==label).mean()) if (frame.actual==label).any() else None for label in [0,1]}
    return dict(accuracy=float((frame.actual==frame.predicted).mean()),recall0=recalls[0],recall1=recalls[1],balanced=(recalls[0]+recalls[1])/2 if None not in recalls.values() else None)


def render_report(skill,inputs,expected_rows):
    instruction=skill.read_text(encoding='utf-8')
    child='Require both class recalls.' in instruction
    if not child and 'Report aggregate accuracy only.' not in instruction:
        raise ValueError('Unsupported reporting instruction')
    complete=all(list(frame.source_row)==expected_rows for frame in inputs.values())
    lines=['# Wine report','',f'Read skill SHA-256: {sha(skill)}.','Label: quality >= 7.','']
    if child and not complete:
        lines+=['Status: incomplete.','Limit: Supplied rows omit part of the declared selection evidence. Do not infer missing class performance.','No model comparison is completed.']
        return '\n'.join(lines)+'\n'
    lines+=['Status: complete.' if complete else 'Status: partial input.','']
    for name,frame in inputs.items():
        value=metrics(frame)
        lines+=[f'## {name}',f'Prediction evidence: inputs/{name}.csv',f'Rows: {len(frame)}.',f'Accuracy: {value["accuracy"]:.9f}.']
        if child:
            lines += [f'Class 0 recall: {value["recall0"]:.9f}.',f'Class 1 recall: {value["recall1"]:.9f}.',f'Balanced accuracy: {value["balanced"]:.9f}.']
        lines+=['']
    if child:
        lines+=['Limit: Selection results do not establish future generalization. Accuracy alone does not establish minority-class performance.']
    return '\n'.join(lines)+'\n'


def check_report(text,inputs,expected_rows,report_path):
    checks={
        'label_threshold':'Label: quality >= 7.' in text,
        'complete_input_rows':all(list(frame.source_row)==expected_rows for frame in inputs.values()),
        'limit_statement':'Limit:' in text,
        'declared_complete':'Status: complete.' in text,
    }
    for name,frame in inputs.items():
        section=text.split(f'## {name}\n',1)[1].split('\n## ',1)[0] if f'## {name}\n' in text else ''
        value=metrics(frame)
        checks[name+'_evidence_link']=f'Prediction evidence: inputs/{name}.csv' in section and (report_path.parent/'inputs'/f'{name}.csv').exists()
        for key,label in [('recall0','Class 0 recall'),('recall1','Class 1 recall'),('balanced','Balanced accuracy')]:
            matches=re.findall(re.escape(label)+r': ([0-9.]+)\.',section)
            checks[name+'_'+key]=len(matches)==1 and value[key] is not None and abs(float(matches[0])-value[key])<1e-8
    table(report_path.with_name('CHECKS.csv'),[dict(criterion=k,passed=v) for k,v in checks.items()])
    complete=all(checks.values())
    honest_missing='Status: incomplete.' in text and not checks['complete_input_rows'] and 'Do not infer missing class performance.' in text
    write(report_path.with_name('VERDICT.md'),f'# Rubric verdict\n\nTask complete: {complete}. Honest incomplete-evidence response: {honest_missing}.\n\nFailed criteria: {", ".join(k for k,v in checks.items() if not v) or "none"}.\n\nAn honest refusal can be the correct procedural response without completing the requested model comparison. This checker covers these declared fields, not general scientific validity.\n')
    return complete,honest_missing


def report_case(folder,skill,inputs,expected_rows,omit_minority=False):
    folder.mkdir(parents=True,exist_ok=False)
    for name,frame in inputs.items():
        (folder/'inputs').mkdir(exist_ok=True)
        frame.to_csv(folder/'inputs'/f'{name}.csv',index=False)
    text=render_report(skill,inputs,expected_rows)
    if omit_minority:
        text=re.sub(r'^Class 1 recall: .+\n','',text,flags=re.M)
    report=folder/'REPORT.md'
    write(report,text)
    passed,honest=check_report(text,inputs,expected_rows,report)
    return dict(case=folder.name,skill_sha256=sha(skill),task_complete=passed,honest_incomplete=honest)


def softmax(logits):
    maximum=max(logits)
    weights=[math.exp(x-maximum) for x in logits]
    return [x/sum(weights) for x in weights]


def numerical(root):
    true=[0.,0.,1.,1.]
    cases={'correct_rewards':[0.,0.,1.,1.],'equal_rewards':[1.,1.,1.,1.],'one_wrong_reward':[1.,0.,1.,1.]}
    summaries=[]
    for name,rewards in cases.items():
        mean=statistics.mean(rewards)
        spread=statistics.pstdev(rewards)
        advantage=[(r-mean)/(spread+1e-8) for r in rewards]
        before=[0.]*4
        probability=softmax(before)
        gradient=[(a-p*sum(advantage))/4 for a,p in zip(advantage,probability)]
        def objective(theta):
            return sum(a*math.log(p) for a,p in zip(advantage,softmax(theta)))/4
        numeric=[]
        for index in range(4):
            plus=before.copy();minus=before.copy()
            plus[index]+=1e-6;minus[index]-=1e-6
            numeric.append((objective(plus)-objective(minus))/2e-6)
        error=max(abs(a-b) for a,b in zip(gradient,numeric))
        if error>1e-7:
            raise ValueError('Gradient failed finite-difference check')
        after=[value+0.4*g for value,g in zip(before,gradient)]
        updated=softmax(after)
        if not all(math.isfinite(x) and x>=0 for x in updated) or abs(sum(updated)-1)>1e-12:
            raise ValueError('Invalid toy policy')
        table(root/'10-24'/f'{name}.csv',[dict(action=i,true_reward=true[i],observed_reward=rewards[i],advantage=advantage[i],gradient=gradient[i],finite_difference=numeric[i],old_logit=before[i],new_logit=after[i],old_probability=probability[i],new_probability=updated[i]) for i in range(4)])
        summaries.append(dict(case=name,mean=mean,population_std=spread,objective_before=objective(before),objective_after=objective(after),expected_true_reward_before=sum(p*r for p,r in zip(probability,true)),expected_true_reward_after=sum(p*r for p,r in zip(updated,true)),action0_probability_after=updated[0],gradient_max_error=error))
        if name=='equal_rewards' and (any(advantage) or updated!=probability):
            raise ValueError('Equal rewards must have no preference update')
        if name=='one_wrong_reward' and not updated[0]>probability[0]:
            raise ValueError('Expected the falsely rewarded action to gain probability')
    table(root/'10-24/SUMMARY.csv',summaries)
    write(root/'10-24/OBJECTIVE.md','# Numerical illustration\n\nFour enumerated actions; initial logits zero. The policy is softmax. With fixed advantages A, maximize J(theta) = mean_i A_i log p_i(theta) by one gradient-ascent step of size 0.4. Advantages use population spread plus 1e-8. The analytic gradient is (A_i - p_i sum_j A_j)/4. Each case includes a central finite-difference check with step 1e-6.\n\nThese are hand-specified rewards and an actual small numerical calculation. No text trajectories, pretrained model, token objective, ratio clipping, reference policy, sampled KL term, or optimizer loop are implemented. No LLM weights or checkpoint exist.\n')
    print('Three numerical cases completed; gradients checked.')


def paired_simulation(root):
    invented={('M0','H0'):.4,('M0','H1'):.7,('M1','H0'):.8,('M1','H1'):.6}
    cached={pair:score for pair,score in invented.items()}
    table(root/'10-25/PAIR-VALUES.csv',[dict(model=m,harness=h,invented_score=s,kind='synthetic table evaluation') for (m,h),s in cached.items()])
    active=('M0','H0')
    transitions=[dict(step=0,operation='initial pair',model=active[0],harness=active[1],invented_score=cached[active])]
    chosen=max(['H0','H1'],key=lambda h:cached[('M0',h)])
    active=('M0',chosen)
    transitions.append(dict(step=1,operation='harness selection',model=active[0],harness=active[1],invented_score=cached[active]))
    active=('M1',chosen)
    transitions.append(dict(step=2,operation='model-update placeholder; no training',model=active[0],harness=active[1],invented_score=cached[active]))
    active=('M1',max(['H0','H1'],key=lambda h:cached[('M1',h)]))
    transitions.append(dict(step=3,operation='harness re-selection',model=active[0],harness=active[1],invented_score=cached[active]))
    table(root/'10-25/TRANSITIONS.csv',transitions)
    if [r['harness'] for r in transitions]!=['H0','H1','H1','H0']:
        raise ValueError('Unexpected pair lineage')
    write(root/'10-25/PAIRS.md','# Synthetic paired state\n\nFour table values were read once and cached. The sequence M0/H0 → M0/H1 → M1/H1 → M1/H0 has invented scores 0.40 → 0.70 → 0.60 → 0.80. The best harness changes when the model label changes.\n\nThe model transition is a placeholder, not trained weights. The four evaluations are table lookups, not model executions. The re-selection step reuses the cached values rather than adding hidden evaluations. The table is fixed throughout.\n')


def paper_arithmetic(root):
    # Manually transcribed rounded inputs checked against the primary source.
    inputs=[('coupled','single-attempt test accuracy','4.2',42.2,73.3),('harness','first-response validation accuracy','4.3',31.1,51.1),('model','pass-at-four problem coverage','4.4 and 7.3',48.3,67.8)]
    table(root/'10-26/PAPER-ARITHMETIC.csv',[dict(case=name,metric=metric,section=section,before_percent=before,after_percent=after,percentage_points=round(after-before,10),relative_percent_change=100*(after-before)/before,origin='paper-reported rounded inputs; arithmetic only') for name,metric,section,before,after in inputs])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True)
    args=parser.parse_args()
    repo,root=args.repo.resolve(),args.output.resolve()
    root.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    shutil.copyfile(args.protocol,root/'PROTOCOL.md')
    shutil.copyfile(__file__,root/'driver.source.py')
    spec=importlib.util.spec_from_file_location('studio_lab',repo/'rsi/tools/lab.py')
    lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
    data=lab.read_data('wine');mask=lab.partitions(data,'wine')['selection']
    expected_rows=list(np.flatnonzero(mask))
    expected_targets=lab.target(data,'wine').loc[mask].to_numpy()
    inputs={};identities=[]
    for name,trial in [('majority','trial-001'),('logistic','trial-002')]:
        source=repo/f'rsi/evidence/2026-09-20/author-wine/{trial}/predictions.csv'
        frame=pd.read_csv(source)
        if list(frame.source_row)!=expected_rows or not np.array_equal(frame.actual,expected_targets) or not frame.predicted.isin([0,1]).all():
            raise ValueError('Reused predictions fail source identity check')
        inputs[name]=frame
        (root/'source-inputs').mkdir(exist_ok=True)
        shutil.copyfile(source,root/'source-inputs'/f'{name}.csv')
        identities.append(dict(model=name,source=str(source.relative_to(repo)).replace('\\','/'),sha256=sha(source),rows=len(frame)))
    table(root/'INPUTS.csv',identities)
    write(root/'SOURCE.md',f'# Source identity\n\nDriver SHA-256: {sha(Path(__file__))}. Protocol SHA-256: {sha(root/"PROTOCOL.md")}. Shared runtime SHA-256: {sha(repo/"rsi/tools/lab.py")}. Wine data SHA-256: {lab.DATA["wine"][1]}. Python: {sys.version}.\n\nNo fits. Same author context. Input selection predictions are from the earlier retained author run; this execution validates their source rows and target values before reuse.\n')
    write(root/'10-22/REQUEST.md','# Synthetic classroom request\n\n“Compare these wine models; do not hide failure on rare high-quality wines.”\n\nThis is the course author’s fixture, not an interview, expert correction, or actual researcher message.\n')
    write(root/'10-22/TASK.md','# Report the wine comparison\n\nUse the preserved majority and logistic selection predictions. Label positive as quality >= 7. Report both class recalls, balanced accuracy, linked row-level evidence, and the limits of this single selection comparison. An incomplete input must remain incomplete.\n')
    write(root/'10-22/RUBRIC.md','# Fixed reporting rubric\n\nCheck the declared label threshold, full expected selection rows, existing evidence links, both class recalls for each model, balanced accuracy, and an explicit limit. Recompute reported numbers from the supplied predictions. Task completion requires all criteria. Record honest abstention separately; it does not complete a missing-data comparison.\n\nThis rubric checks a narrow reporting task, not expert scientific validity.\n')
    parent=root/'10-23/REPORT-SKILL-parent.md';child=root/'10-23/REPORT-SKILL-child.md'
    write(parent,'# Parent reporting skill\n\nRead the supplied predictions and declared label. Report aggregate accuracy only. Link the supplied evidence.\n')
    write(child,'# Child reporting skill\n\nRead the supplied predictions and declared label. Require both class recalls. Include balanced accuracy, row-level evidence links, and an explicit limit. Refuse incomplete evidence. Do not invent missing class performance.\n')
    verdicts=[]
    for name,omit in [('complete-report',False),('minority-recall-omitted',True)]:
        verdicts.append(dict(lab='10.22',**report_case(root/'10-22'/name,child,inputs,expected_rows,omit)))
    incomplete={name:frame[frame.actual==0].copy() for name,frame in inputs.items()}
    write(root/'10-23/INCOMPLETE-FIXTURE.md','# Altered evidence fixture\n\nRemoved every true-positive-class row from each prediction file. This is a deliberate missing-evidence case, not a new data partition or model run. The original full input remains in source-inputs.\n')
    for name,fixture in [('complete',inputs),('incomplete',incomplete)]:
        for version,skill in [('parent',parent),('child',child)]:
            verdicts.append(dict(lab='10.23',**report_case(root/'10-23'/f'{version}-{name}',skill,fixture,expected_rows)))
    table(root/'REPORT-VERDICTS.csv',verdicts)
    if [r['task_complete'] for r in verdicts]!=[True,False,False,True,False,False] or not verdicts[-1]['honest_incomplete']:
        raise ValueError('Unexpected rubric outcomes')
    numerical(root);paired_simulation(root);paper_arithmetic(root)
    write(root/'PROGRESS.md','# Author execution complete\n\nExecuted six report checks, three numerical cases with finite-difference validation, and four synthetic pair evaluations. Recomputed three paper-result differences from rounded inputs. No new model fits or LLM training.\n\nLearner prediction, quiz, and teach-back are unattempted. Reporter behavior uses an explicit constrained interpreter, not an independent language-model comparison. Source audit and larger-compute planning notes must be read alongside these outputs.\n')
    table(root/'COST.csv',[dict(fits=0,llm_training_runs=0,report_checks=6,numerical_cases=3,synthetic_pair_evaluations=4,driver_seconds=time.perf_counter()-start,authoring_and_inference_cost='unknown')])
    print('Completed six report checks, three numerical cases, four paired table evaluations, and source-result arithmetic.')


if __name__=='__main__':
    main()
