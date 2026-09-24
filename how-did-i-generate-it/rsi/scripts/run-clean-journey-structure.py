"""Execute graph and domain activities against the clean journey's artifacts."""
import argparse
import csv
from datetime import datetime
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.workspace.resolve()
    assert (out / "FOUNDATION-RESULT.md").exists(), "Complete the foundation stage first."
    for name in ["03-01", "03-02", "03-03", "03-04", "03-05", "03-06", "04-01", "04-02", "04-03", "04-04", "04-05", "05-01"]:
        if (out / name).exists():
            raise RuntimeError(f"Preserve previous evidence: {name}")
    sys.path.insert(0, str(repo / "rsi/tools"))
    import lab
    import mechanisms

    checks = []
    def record(name, observed, expected):
        checks.append((name, str(observed), str(expected), observed == expected))
        save(out / "STRUCTURE-CHECKS.md", "# Executed graph and domain checks\n\n| Check | Observed | Expected | Pass |\n|---|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} | {d} |" for a,b,c,d in checks) + "\n")
        if observed != expected:
            raise AssertionError(name)

    dependencies = {"frame": [], "inspect": ["frame"], "split": ["inspect"], "fit": ["split"], "check": ["fit"], "report": ["check"]}
    graph = 'flowchart TD\n  frame["Frame task"] -->|TASK.md| inspect["Inspect data"]\n  inspect -->|DATA-REPORT.md| split["Check partitions"]\n  split -->|row identities| fit["Fit recipe"]\n  fit -->|predictions.csv| check["Recompute MAE"]\n  check -->|CHECK.md| report["Write report"]\n'
    save(out / "03-01/workflow.mmd", graph)
    save(out / "03-01/WORKFLOW.md", "# Action dependencies\n\nEach edge names the result required by its destination. The diagram source is workflow.mmd. This sequence has no cycle; the later bounded repair graph does.\n\n" + "\n".join(f"- {node}: needs {', '.join(needs) or 'task request'}." for node,needs in dependencies.items()) + "\n")
    record("03.01 valid order", mechanisms.order_is_valid(list(dependencies), dependencies), True)
    record("03.01 check before fit", mechanisms.order_is_valid(["frame","inspect","split","check","fit","report"], dependencies), False)

    sample = lab.read_data("bike").head(3)
    sample_path = out / "03-02/valid.csv"
    sample_path.parent.mkdir(parents=True)
    sample.to_csv(sample_path, index=False)
    sample.drop(columns="cnt").to_csv(out / "03-02/missing-target.csv", index=False)
    def route(path):
        if not path.exists():
            return "unknown: stop and obtain evidence"
        with path.open(encoding="utf-8") as stream:
            fields = next(csv.reader(stream))
        return "valid: may proceed" if "cnt" in fields else "invalid: repair before fitting"
    for filename, expected in [("valid.csv","valid: may proceed"), ("missing-target.csv","invalid: repair before fitting"), ("absent.csv","unknown: stop and obtain evidence")]:
        record(f"03.02 {filename}", route(out / "03-02" / filename), expected)
    save(out / "03-02/ROUTES.md", "# Observed routes\n\n" + "\n".join(f"- {name}: {route(out / '03-02' / name)}" for name in ["valid.csv","missing-target.csv","absent.csv"]) + "\n\nThis fixture checks target presence only. No fit runs on any fixture in this activity. Missing evidence does not default to success.\n")

    candidate = "00-03/trial-001"
    contract = digest(out / "00-03/CONTRACT.md")
    data = dict(check="data", candidate=candidate, contract=contract, status="pass")
    resource = dict(check="resources", candidate=candidate, contract=contract, status="pass")
    record("03.03 complete join", mechanisms.join_checks(candidate, contract, [data, resource]), "pass")
    record("03.03 missing result", mechanisms.join_checks(candidate, contract, [data]), "incomplete")
    record("03.03 wrong candidate", mechanisms.join_checks(candidate, contract, [data, dict(resource,candidate="other")]), "mismatch")
    save(out / "03-03/JOIN-REPORT.md", f"# Join evidence\n\nCandidate: {candidate}. Contract SHA-256: {contract}.\n\nData result: {data!r}\n\nResource result: {resource!r}\n\nMatching results pass; a missing resource result is incomplete; another candidate's result is rejected. These are sequential control fixtures tied to an actual candidate, not concurrent agent checks or a resource measurement.\n")

    repair_traces = []
    for name, effective in [("effective",True),("ineffective",False)]:
        fixture = out / "03-04" / name / "data.csv"
        fixture.parent.mkdir(parents=True)
        sample.drop(columns="cnt").to_csv(fixture,index=False)
        trace = []
        for attempt in range(3):
            state = route(fixture)
            trace.append((attempt,state,digest(fixture)))
            if state.startswith("valid") or attempt == 2:
                break
            if effective:
                sample.to_csv(fixture,index=False)
        repair_traces.append((name,trace))
        record(f"03.04 {name} exit", trace[-1][1].startswith("valid"), effective)
        record(f"03.04 {name} checks", len(trace), 2 if effective else 3)
        save(fixture.parent / "TRACE.md", f"# {name} repair\n\nAt most two repairs; the target-presence rule stays fixed.\n\n" + "\n".join(f"- Repairs used {n}: {state}; file SHA-256 {h}." for n,state,h in trace) + "\n")
    save(out / "03-04/WORKFLOW.md", "# Repair cycle\n\nCheck → valid: stop. Check → invalid: repair if fewer than two repairs have been used, then check again. After two ineffective repairs, stop with failure. The return edge carries attempts and the last missing-field result.\n")

    recovery = out / "03-05/diagnostic"
    shutil.copytree(out / "00-03", recovery)
    prediction = recovery / "trial-001/predictions.csv"
    before = digest(prediction)
    ledger_before = digest(recovery / "trials.csv")
    try:
        raise OSError("Teaching failure: report renderer unavailable")
    except OSError as error:
        save(recovery / "REPORT-FAILURE.md", f"# Actual injected exception\n\n{error}\n")
    import check_result
    score = check_result.check(recovery / "trial-001")
    save(recovery / "RECOVERED-REPORT.md", f"# Recovered report\n\nRecomputed selection MAE: {score:.6f}. Source predictions SHA-256: {before}. No new fit was requested.\n")
    record("03.05 prediction reuse", digest(prediction), before)
    record("03.05 unchanged fit ledger", digest(recovery / "trials.csv"), ledger_before)
    record("03.05 split descendants", sorted(mechanisms.affected_nodes({"split"},dependencies)), ["check","fit","report","split"])
    # Stale dependency check without changing the original evidence.
    stale = recovery / "altered-predictions.csv"
    shutil.copyfile(prediction,stale)
    with stale.open("a",encoding="utf-8") as stream:
        stream.write("\n")
    record("03.05 changed bytes invalidate report", digest(stale) != before, True)
    save(out / "03-05/RECOVERY.md", "# Selective recovery\n\nThe report operation raised the labelled error. The prediction file and fit ledger stayed unchanged while a checked report was rebuilt. A changed split invalidates split, fit, check, and report. A separate altered prediction file fails the stored dependency hash. This does not claim all semantically equivalent CSV encodings need a new model fit.\n")
    save(out / "03-06/VIEWS.md", "# Three views\n\nThe control plan permits inspect → split → fit → check → report. Its arrows are requirements. Data flow carries the reports and prediction rows named in 03-01/workflow.mmd. Actual command events are in COMMANDS.md. The injected report failure and successful repair are in 03-05/diagnostic. The failed render exists in the trace; drawing a verifier node alone would not supply an executed check.\n")

    save(out / "04-01/ENTITIES.md", "# Domain objects\n\nDataset: pinned hourly observations. Column: hr. Target: cnt. Partition: selection rows in 2012-H1. Recipe: constant/calendar/seed17. Candidate: that recipe under the frozen contract. Run: trial-001, one execution. Metric: MAE. Evidence: source-row predictions and a recomputed result. Two executions of one recipe are separate runs.\n")
    good = "| Subject | Relation | Object |\n|---|---|---|\n| model | uses feature | hr |\n| scaler | fit on | train |\n| search | selects on | selection |\n| model | measured by | MAE |\n"
    bad = "| Subject | Relation | Object |\n|---|---|---|\n| model | uses feature | total_users |\n| total_users | derived from | target |\n| scaler | fit on | final |\n| search | selects on | final |\n"
    save(out / "04-02/RELATIONS.md", good + "\nThe model uses the hour column. This is a relation between domain objects, not an instruction to execute one node after another.\n")
    save(out / "04-03/INVARIANTS.md", "# Fixed rules\n\nA prediction recipe cannot use a feature derived from the target. Fitted transforms use training rows only. Search selects on selection data, never final data. Valid example: model uses hr. Invalid example: model uses a renamed total_users field that is declared target-derived. The alias does not change its meaning.\n")
    save(out / "04-04/ORIGINAL.md", bad)
    save(out / "04-04/CORRECTED.md", good)
    for name, expected in [("ORIGINAL",3),("CORRECTED",0)]:
        violations = lab.audit_domain(out / f"04-04/{name}.md",out / f"04-04/{name}-CHECK.md")
        record(f"04.04 {name} violations",len(violations),expected)
    save(out / "04-05/VOCABULARY-v1.md", "# Retrospective task\n\nObserved calendar and weather describe an hour already recorded. The target remains hidden from the recipe, but this does not establish forecast-time availability.\n")
    save(out / "04-05/VOCABULARY-v2.md", "# Day-ahead task\n\nForecast origin: the previous day at noon. Every feature must have a release timestamp at or before that origin. The target hour is tomorrow at noon. Preserve v1 as a different task.\n")
    origin = datetime.fromisoformat("2012-01-01T12:00:00")
    available = lambda release: datetime.fromisoformat(release) <= origin
    record("04.05 observed future weather",available("2012-01-02T12:00:00"),False)
    record("04.05 earlier forecast release",available("2012-01-01T09:00:00"),True)
    save(out / "04-05/IMPACT.md", "# Meaning change and impact\n\nThe synthetic release-time fixtures reject tomorrow's observed weather and admit a forecast released before the origin. The supplied bike table has no archived forecast issue times. A new data source, feature availability rules, rolling-origin split design, recipes, and evaluation are needed. No old retrospective score establishes day-ahead performance. No forecast model was fitted. The two fixture timestamps are constructed examples, not verified dataset fields.\n")

    save(out / "05-01/SYSTEM.md", "# Coordinated fixed components\n\nThe baseline skill selects the declared recipe. Domain rules check feature meaning before execution. The generated controller limits attempts. The shared tool trains and saves predictions. A separate calculation verifies rows and metric. Reporting links these results. Components remain fixed during this demonstration.\n")
    before_system = len(lab.records(out / "05-01"))
    record("05.01 leaked fixture stops before fit",bool(lab.audit_domain(out / "04-04/ORIGINAL.md",out / "05-01/LEAKAGE-REFUSAL.md")),True)
    record("05.01 no leaked fit recorded",len(lab.records(out / "05-01")),before_system)
    command = [sys.executable,str(out / "02-04/controller.py"),"run","--repo",str(repo),"--workspace",str(out / "05-01"),"--limit","1","--model","constant","--features","calendar","--hypothesis","Run the fixed components after the valid domain check."]
    record("05.01 valid domain check",len(lab.audit_domain(out / "04-04/CORRECTED.md",out / "05-01/DOMAIN-CHECK.md")),0)
    started = time.perf_counter()
    result = subprocess.run(command,cwd=repo,capture_output=True,text=True,encoding="utf-8",timeout=60)
    save(out / "05-01/EXECUTION.md",f"# Actual invocation\n\n{command!r}\n\nExit: {result.returncode}; wall seconds: {time.perf_counter()-started:.6f}.\n\n```text\n{result.stdout}\n{result.stderr}\n```\n")
    record("05.01 baseline exit",result.returncode,0)
    record("05.01 exactly one fit",len(lab.records(out / "05-01")),1)
    for lab_id in ["03-01","03-02","03-03","03-04","03-05","03-06","04-01","04-02","04-03","04-04","04-05","05-01"]:
        save(out / lab_id / "PROGRESS.md", "# Author execution\n\nMain mechanism exercised; see STRUCTURE-CHECKS.md and this folder's actual artifacts. Learner predictions and quiz: unattempted. Same author context. See the route coverage record for omissions.\n")
    save(out / "STRUCTURE-SOURCE.md",f"# Implementation identity\n\nDriver SHA-256: {digest(Path(__file__))}. Shared mechanisms SHA-256: {digest(repo / 'rsi/tools/mechanisms.py')}. Domain tool SHA-256: {digest(repo / 'rsi/tools/lab.py')}.\n\nThe driver uses the supplied graph primitives and adds concrete file, route, recovery, and availability checks. It does not claim independently generated graph primitives or separate evaluator authority.\n")
    save(out / "PROGRESS.md", "# Clean journey progress\n\nFoundation and graph/domain stages complete. One fixed system baseline also executed. Next: generated harness packages, then the improver comparison. Learner assessments remain unattempted.\n")
    print(f"Structure stage complete: {len(checks)} checks and one new baseline fit.")


if __name__ == "__main__":
    main()
