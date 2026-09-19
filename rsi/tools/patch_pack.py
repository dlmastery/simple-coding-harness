"""patch_pack - the meta harness's one move: propose one patch to the target pack, and put it through the gate.

    # stage 1 - the proposal (one per visit; snapshots the target under versions/ before anything lands)
    python ../tools/patch_pack.py --pack .claude/skills/adult-income-meta --task ../tasks/02_breast_cancer.json \\
        --target .claude/skills/adult-income --files @files.json --recipe @evidence.json --summary "policy line -> obey-memory"
    # stage 2 - under `approval: human` (the meta pack's front matter), after the user answered
    python ../tools/patch_pack.py --pack ... --task ... --target ... --proposal g1 --approved "<the user's exact words>"

`--files` is {path: {"after": text | null}}. The script refuses a second
proposal in the same visit, a patch outside the meta pack's `patches:` globs,
one that changes more than 20 % of the pack's text, or one that removes the
test rule from SKILL.md. Under `approval: gate` the private split decides at
stage 1 - the evidence recipe is scored against the incumbent on a split the
target never sees; a loss rolls the target back to the snapshot. Under
`approval: human` stage 1 returns the diff and waits; stage 2 lands or
rejects with the user's words. `approval: both` is the gate first, then the
human. `config.json` `{"meta": "off"}` in the meta pack is META_OFF: nothing
is proposed.
"""
import json
import sys
from difflib import SequenceMatcher
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, proposals, recipe, tasks  # noqa: E402
from _lib.state import Run, config, require_tool  # noqa: E402

SIZE_CAP = 0.20   # a patch may change at most this share of the pack's text

PARSER = cli.common(cli.parser(__doc__, target={"required": True, "help": "the pack to patch"},
                               files="stage 1: {path: {after: text | null}} (JSON or @file)",
                               recipe="stage 1: the evidence recipe (the best val recipe of the last problem)",
                               summary={"default": "", "help": "stage 1: one line"},
                               visit={"type": "int", "default": 1, "help": "stage 1: the visit number (one proposal per visit)"},
                               proposal="stage 2: the proposal id", approved="stage 2: the user's exact words",
                               edited="stage 2: the user's version of --files, with --approved edit"))


def incumbent_recipe(target_run):
    """The recipe the target pack stands on: the best val fit of the newest problem in its log, else the baseline."""
    scored = [r for r in target_run.all_traces() if r["val_score"] is not None]
    if not scored:
        return recipe.BASELINE
    last = scored[-1]["problem"]
    return max((r for r in scored if r["problem"] == last), key=lambda r: r["val_score"])["recipe"]


def private_gate(run, target_run, candidate):
    """Keep-or-rollback on the private split: the candidate must not score below the incumbent."""
    before = tasks.score_on(run.task, run.seed, incumbent_recipe(target_run), "private")
    after = tasks.score_on(run.task, run.seed, candidate, "private")
    keep = after is not None and (before is None or after >= before)
    run.log("gate", before=before, after=after, keep=keep)
    return {"before": before, "after": after, "keep": keep}


def checked_patch(run, target, files, rec):
    """The patch as {path: {before, after}} after every rule; raises on the first broken one."""
    current = packs.read_pack(target)
    allowed = (run.meta.get("metadata") or {}).get("patches")
    changes, changed = {}, 0
    for name, change in files.items():
        if not isinstance(change, dict) or "after" not in change:
            raise ValueError("each file change is {after: text | null}")
        if allowed and not any(fnmatch(name, pat) for pat in allowed):
            raise ValueError(f"this meta pack may patch {allowed} only, not {name}")
        before, after = current.get(name) or "", change["after"] or ""
        changes[name] = {"before": current.get(name), "after": change["after"]}
        changed += round((1 - SequenceMatcher(None, before, after).ratio()) * max(len(before), len(after)))
    total = sum(len(t) for t in current.values()) or 1
    if changed > SIZE_CAP * total:
        raise ValueError(f"the patch changes {changed} of {total} characters, more than {int(SIZE_CAP * 100)} % of the pack; one small change per generation")
    if "SKILL.md" in changes and changes["SKILL.md"]["after"] and "after FREEZE" not in changes["SKILL.md"]["after"]:
        raise ValueError("a patch may not remove the test rule from SKILL.md")
    return {"files": changes, "recipe": rec}


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "patch_pack")
    target = Path(a.target)
    target_run = Run(target, a.task, "memory", a.seed, a.run)
    versions = target_run.versions_dir
    mode = (run.meta.get("metadata") or {}).get("approval", "human")
    if config(run.pack_dir).get("meta") == "off":
        return {"meta_off": True, "landed": False, "note": "META_OFF: this meta pack proposes nothing; the target stays byte-identical"}

    if a.proposal:                                            # ---------------- stage 2: the human answered
        if not a.approved or not a.approved.strip():
            raise ValueError('stage 2 needs --approved "<the user\'s exact words>"; nothing lands without an answer')
        path, record = proposals.load(run.root, a.proposal)
        if record["applied"] or record["decision"] in ("n",):
            raise ValueError(f"proposal {a.proposal} is already decided ({record['decision']})")
        decision = proposals.classify(a.approved)
        record.update(decision=decision, words=a.approved, approved_by="human")
        label = record.get("version")
        if decision == "n":
            if label:                                         # `both`: the gate landed it; the human's no rolls it back
                packs.rollback(target, versions, label)
                run.log("rollback", proposal=a.proposal, version=label, by="human", checksums=packs.checksums(target))
            proposals.save(path, record)
            run.log("reject", proposal=a.proposal, words=a.approved, by="human")
            return {"id": a.proposal, "decision": "n", "landed": False, "rolled_back_to": label, "words": a.approved}
        payload = record["payload"]
        if decision == "edit":
            if a.edited is None:
                raise ValueError("--approved edit needs --edited <the user's version of the files>; nothing lands")
            if label:
                packs.rollback(target, versions, label)
            payload = checked_patch(run, target, cli.value(a.edited), payload["recipe"])
            record["payload"] = payload
            label = proposals.land_patch(target, versions, payload)
        elif not label:
            label = proposals.land_patch(target, versions, payload)
        record.update(applied=True, version=label)
        proposals.save(path, record)
        run.log("apply", proposal=a.proposal, decision=decision, words=a.approved, by="human", version=label,
                files=sorted(payload["files"]), checksums=packs.checksums(target))
        return {"id": a.proposal, "decision": decision, "landed": True, "version": label, "files": sorted(payload["files"]),
                "approved_by": "human", "words": a.approved}

    # -------------------------------------------------------------- stage 1: the proposal
    if a.files is None or a.recipe is None:
        raise ValueError("stage 1 needs --files and --recipe (and --summary)")
    for p in (run.root / "proposals").glob("g*.json"):
        if json.loads(p.read_text(encoding="utf-8")).get("visit") == a.visit:
            raise ValueError(f"one proposal per visit; visit {a.visit} already made {p.stem} (pass --visit {a.visit + 1} for a new visit)")
    rec = recipe.validate(cli.value(a.recipe))
    payload = checked_patch(run, target, cli.value(a.files), rec)
    record, diff = proposals.write(run.root, "patch", payload, a.summary, target, prefix="g", extra={"visit": a.visit, "mode": mode})
    path = run.root / "proposals" / f"{record['id']}.json"
    if mode in ("gate", "both"):
        label = proposals.land_patch(target, versions, payload)
        verdict = private_gate(run, target_run, rec)
        record["gate"] = verdict
        if not verdict["keep"]:
            packs.rollback(target, versions, label)
            record.update(decision="n", approved_by="gate", applied=False)
            proposals.save(path, record)
            run.log("rollback", proposal=record["id"], version=label, gate=verdict, by="gate", checksums=packs.checksums(target))
            return {"id": record["id"], "decision": "n", "approved_by": "gate", "gate": verdict, "landed": False, "rolled_back_to": label, "diff": diff}
        record["version"] = label
        if mode == "both":
            proposals.save(path, record)
            run.log("gate_kept", proposal=record["id"], version=label, gate=verdict)
            return {"id": record["id"], "decision": None, "gate": verdict, "landed": "pending", "version": label, "diff": diff,
                    "next": f"The gate kept it. Show the diff to the user, ask approve / edit / reject, then: python ../tools/patch_pack.py "
                            f"--pack {a.pack} --task {a.task} --target {a.target} --proposal {record['id']} --approved \"<their words>\""}
        record.update(decision="y", approved_by="gate", applied=True)
        proposals.save(path, record)
        run.log("apply", proposal=record["id"], decision="y", by="gate", version=label, gate=verdict, files=sorted(payload["files"]),
                checksums=packs.checksums(target))
        return {"id": record["id"], "decision": "y", "approved_by": "gate", "gate": verdict, "landed": True, "version": label,
                "files": sorted(payload["files"]), "diff": diff}
    proposals.save(path, record)
    run.log("propose", proposal=record["id"], kind="patch", summary=a.summary, files=sorted(payload["files"]))
    return {"id": record["id"], "decision": None, "landed": False, "diff": diff, "summary": a.summary,
            "next": f"Show the diff to the user. Ask: approve / edit / reject. Then: python ../tools/patch_pack.py --pack {a.pack} "
                    f"--task {a.task} --target {a.target} --proposal {record['id']} --approved \"<the user's exact words>\""}


if __name__ == "__main__":
    cli.main(main)
