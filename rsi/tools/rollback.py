"""rollback - restore a pack from one of its versions (the snapshots patch_pack / apply took before landing).

    python ../tools/rollback.py --pack .claude/skills/adult-income --version gen_001
    python ../tools/rollback.py --pack .claude/skills/adult-income --list

Every file of the snapshot lands, extras of the live pack go; the checksums
afterwards are in the result and in the trace. Safe inheritance made concrete.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs  # noqa: E402
from _lib.state import pack_name, runs_root  # noqa: E402
from _lib.trace import TraceLog  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, version="the version label, e.g. gen_001", list={"action": "store_true", "help": "list the versions"}), task=False, arm=False)


def main(argv=None):
    a = PARSER.parse_args(argv)
    pack = Path(a.pack)
    if not (pack / "SKILL.md").exists():
        raise ValueError(f"no SKILL.md under {pack}")
    versions = runs_root(pack, a.run) / pack_name(pack) / "versions"
    names = sorted(p.name for p in versions.glob("gen_*")) if versions.exists() else []
    if a.list or not a.version:
        return {"pack": pack_name(pack), "versions": names, "dir": str(versions)}
    packs.rollback(pack, versions, a.version)
    checksums = packs.checksums(pack)
    TraceLog(versions.parent / "rollbacks.jsonl").append(event="rollback", problem=None, arm="human", seed=None,
                                                         info={"version": a.version, "checksums": checksums})
    return {"rolled_back_to": a.version, "pack": pack_name(pack), "checksums": checksums}


if __name__ == "__main__":
    cli.main(main)
