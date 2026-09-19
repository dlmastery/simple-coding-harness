"""The human approval cycle: propose -> show -> y / n / edit -> apply.

Every "generate" and every "improve" in the series goes through this file.
A meta pack calls the `propose` tool with a whole pack or a patch; the tool
shows it and asks the human; only a `y` or an `edit` lets `apply` land it on
disk, and an `edit` lands the human's version, not the model's. The human is
the acceptance rule (the framework paper's L1-L4 boundary); in step 09 the
same cycle can be answered by the private gate instead, and the README says
which decision moved.

Tests script the human: `Human(["y", "n", ("edit", {...})])`, or the
environment variable `HUMAN=script:y,n,y` for a run without a terminal.
"""

import json
import os
import sys
from difflib import unified_diff


class Human:
    """Answers `y`, `n` or `edit` at each approval. Scripted answers run out -> `n`: nothing lands by default."""

    def __init__(self, answers=None):
        self.answers = list(answers) if answers is not None else None
        self.asked = []

    @classmethod
    def from_env(cls):
        spec = os.environ.get("HUMAN", "")
        if spec.startswith("script:"):
            return cls([a.strip() for a in spec[len("script:"):].split(",") if a.strip()])
        return cls(None)

    def decide(self, proposal):
        self.asked.append(proposal["id"])
        if self.answers is not None:
            if not self.answers:
                return "n", None
            answer = self.answers.pop(0)
            if isinstance(answer, tuple):        # ("edit", payload): the human's version
                return "edit", answer[1]
            return answer, None
        return self.ask_terminal(proposal)

    @staticmethod
    def ask_terminal(proposal):
        while True:
            try:
                answer = input(f"  approve {proposal['id']} ({proposal['kind']})? [y/n/edit] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return "n", None
            if answer in ("y", "n"):
                return answer, None
            if answer == "edit":
                print("  paste the edited payload as JSON on one line:")
                try:
                    return "edit", json.loads(input("  edit> "))
                except (EOFError, KeyboardInterrupt, ValueError):
                    return "n", None


def show(proposal, out=sys.stdout):
    """What the human sees before answering: the kind, the summary, and every file or the diff."""
    print(f"--- proposal {proposal['id']}: {proposal['kind']} - {proposal.get('summary', '')}", file=out)
    payload = proposal["payload"]
    if proposal["kind"] == "pack":
        for name, text in payload.items():
            print(f"### {name}\n{text.rstrip()}", file=out)
    elif proposal["kind"] == "patch":
        for name, change in payload["files"].items():
            before = (change.get("before") or "").splitlines()
            after = (change.get("after") or "").splitlines()
            print("\n".join(unified_diff(before, after, f"a/{name}", f"b/{name}", lineterm="", n=1)), file=out)
        if "recipe" in payload:
            print(f"(evidence recipe: {json.dumps(payload['recipe'])})", file=out)
    else:
        print(json.dumps(payload, indent=1), file=out)
    print("--- end of proposal", file=out)


class Proposals:
    """The proposals of one run, decided the moment they are made, applied only on request."""

    def __init__(self, human, quiet=False):
        self.human = human
        self.items = {}
        self.quiet = quiet

    def propose(self, kind, payload, summary=""):
        pid = f"p{len(self.items) + 1}"
        proposal = {"id": pid, "kind": kind, "payload": payload, "summary": summary, "decision": None, "applied": False}
        self.items[pid] = proposal
        if not self.quiet:
            show(proposal)
        decision, edited = self.human.decide(proposal)
        proposal["decision"] = decision
        if decision == "edit":
            proposal["payload"] = edited     # the human's version is what may land
        return proposal

    def approved(self, pid):
        p = self.items.get(pid)
        return p is not None and p["decision"] in ("y", "edit")
