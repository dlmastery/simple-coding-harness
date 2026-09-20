"""Execute the synthetic scheduling activities in labs 07.05 and 07.06.

Author-written simulation, not a trace of independent agents or measured jobs.
Refuse to overwrite evidence. Run with --output pointing at a new directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import platform
import random
from pathlib import Path


def write(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def table(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def schedule(jobs, policy, overhead=0, setup=0, seed=17):
    pending = list(jobs)
    ready = [0, 0]
    previous = [None, None]
    history = []
    rng = random.Random(seed)
    types = sorted({job["kind"] for job in jobs})
    while pending:
        if policy == "fixed":
            job = pending.pop(0)
            worker = jobs.index(job) % 2
        else:
            worker = min(range(2), key=lambda i: (ready[i], i))
            preferred = previous[worker]
            if policy == "random_history":
                preferred = rng.choice(types)
            eligible = [job for job in pending if job["kind"] == preferred]
            if policy in {"local_history", "random_history"} and eligible:
                job = eligible[0]
            else:
                job = pending[0]
            pending.remove(job)
        setup_ticks = setup if previous[worker] != job["kind"] else 0
        assigned = ready[worker]
        start = assigned + overhead + setup_ticks
        end = start + job["duration"]
        history.append(dict(
            job=job["job"], kind=job["kind"], worker=worker,
            assigned=assigned, overhead=overhead, setup=setup_ticks,
            start=start, end=end, deadline=job["deadline"],
            lateness=max(0, end - job["deadline"]),
            result=f"checked-{job['job']}",
        ))
        ready[worker] = end
        previous[worker] = job["kind"]
    return history


def measure_and_check(jobs, events):
    # Validate identities and scheduling constraints independently of policy.
    assert sorted(row["job"] for row in events) == sorted(job["job"] for job in jobs)
    by_id = {job["job"]: job for job in jobs}
    same = pairs = 0
    for worker in range(2):
        sequence = sorted((r for r in events if r["worker"] == worker), key=lambda r: r["assigned"])
        previous_end = 0
        previous_kind = None
        for row in sequence:
            assert row["assigned"] >= previous_end
            assert row["start"] == row["assigned"] + row["overhead"] + row["setup"]
            assert row["end"] - row["start"] == by_id[row["job"]]["duration"]
            assert row["result"] == f"checked-{row['job']}"
            if previous_kind is not None:
                pairs += 1
                same += row["kind"] == previous_kind
            previous_kind, previous_end = row["kind"], row["end"]
    return dict(
        jobs=len(events), makespan_ticks=max(row["end"] for row in events),
        same_type_pairs=same, adjacent_pairs=pairs,
        clustering=same / pairs if pairs else 0,
        max_lateness_ticks=max(row["lateness"] for row in events),
        checks="pass",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(out / "PROTOCOL.md", """# Synthetic scheduling protocol

This protocol is written before execution. All jobs arrive at tick zero.
Two simulated workers have identical, fixed capabilities. Job durations,
setup costs, deadlines, and coordination overhead are invented inputs.
A tick is a simulation unit, not a measured second. No ML fit is run.

Lab 07.05 uses six jobs with durations 8, 1, 7, 1, 6, 1. Compare fixed
round-robin assignment with an idle worker taking the next queued job.
The optional counterexample adds three ticks of extra coordination per
dynamic assignment; fixed assignment has no extra overhead. This assumption
tests sensitivity and is not an estimate of a real scheduler's cost.

Lab 07.06 uses twelve one-tick jobs, with types A,A,B,B repeated three times.
A worker pays one setup tick initially and whenever its job type changes.
Compare FIFO, preference for the worker's previous type, and preference
for a randomly assigned history type with seed 17. There is no central
batch plan. Ties select the lower worker ID and then the earlier queued job.

Clustering is the fraction of consecutive jobs on the same worker with
equal types, pooled across workers. It is defined before examining traces.
Report makespan and maximum lateness separately. The optional paired
counterexample gives only the first two B jobs a deadline of tick 3.
All other deadlines are tick 100. There is no claim of optimal scheduling.

Every result must retain each job exactly once, preserve its duration and
constructed result, and avoid overlapping work on a worker. Learner
predictions and teach-back are untested because this is an author walkthrough.
""")
    organization = [dict(job=f"J{i+1:02}", kind="check", duration=d, deadline=100)
                    for i, d in enumerate([8, 1, 7, 1, 6, 1])]
    emergence = [dict(job=f"J{i+1:02}", kind=k, duration=1, deadline=100)
                 for i, k in enumerate("AABBAABBAABB")]
    urgent = [dict(job, deadline=3 if job["job"] in {"J03", "J04"} else 100)
              for job in emergence]
    for name, jobs in [("organization", organization), ("emergence", emergence), ("urgent", urgent)]:
        table(out / f"{name}-jobs.csv", jobs)
    cases = [
        ("organization-fixed", organization, "fixed", 0, 0),
        ("organization-dynamic", organization, "fifo", 0, 0),
        ("organization-overhead", organization, "fifo", 3, 0),
        ("emergence-fifo", emergence, "fifo", 0, 1),
        ("emergence-local", emergence, "local_history", 0, 1),
        ("emergence-random", emergence, "random_history", 0, 1),
        ("urgent-fifo", urgent, "fifo", 0, 1),
        ("urgent-local", urgent, "local_history", 0, 1),
    ]
    rows = []
    for name, jobs, policy, overhead, setup in cases:
        events = schedule(jobs, policy, overhead, setup)
        table(out / f"{name}-events.csv", events)
        rows.append(dict(case=name, policy=policy, **measure_and_check(jobs, events)))
    table(out / "RESULTS.csv", rows)
    rendered = "\n".join(f"| {r['case']} | {r['makespan_ticks']} | {r['clustering']:.2f} | {r['max_lateness_ticks']} |" for r in rows)
    write(out / "README.md", f"""# Organization and emergence walkthrough

Actual execution of an explicitly synthetic simulation. No student participated,
no worker is a coding-agent process, and no model or improvement rule learns.
The agent wrote and ran the implementation for the course activities.

Read [the prespecified protocol](PROTOCOL.md), [results](RESULTS.csv), and
the per-case event CSVs in this directory. The input CSVs retain every job.

| Case | Completion tick | Same-type fraction | Maximum lateness |
|---|---:|---:|---:|
{rendered}

All eight cases passed identity, duration, result, and non-overlap checks.
Clustering is useful only for the typed-job cases. With one type in the first
three cases it is trivially 1.00 and says nothing about specialization.

The fixed assignment has loads 21 and 3. Dynamic assignment reaches tick 14;
adding the declared coordination cost moves it to tick 23. The workers did
not get better at their jobs. Only the dispatch arrangement changed.

Preference for recent job type produces longer runs of similar work. The
random-history and FIFO controls change that pattern. The urgent-job pair
shows why less total completion time does not guarantee less lateness.
These are consequences of the constructed inputs and local rules, not
measurements of a production scheduler or evidence of general intelligence.

Source: `how-did-i-generate-it/rsi/scripts/run-organization-walkthrough.py`

Source SHA-256: `{source_hash}`

Python: {platform.python_version()}; platform: {platform.system()} {platform.machine()}.

To repeat, ask the coding agent to run the saved driver with a new output
folder. The driver refuses to overwrite an existing evidence directory.
""")
    print(f"Executed {len(rows)} synthetic cases; all scheduling checks passed.")
    for row in rows:
        print(f"{row['case']}: completion={row['makespan_ticks']}, clustering={row['clustering']:.2f}, lateness={row['max_lateness_ticks']}")


if __name__ == "__main__":
    main()
