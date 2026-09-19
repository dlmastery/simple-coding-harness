"""read_pack - every file of a pack as {path: text}, with checksums and the versions on disk.

    python ../tools/read_pack.py --pack .claude/skills/adult-income
    python ../tools/read_pack.py --pack .claude/skills/adult-income --checksums     # checksums only
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs  # noqa: E402
from _lib.state import lesson_dir, pack_name, runs_root  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, checksums={"action": "store_true", "help": "only the checksums"}), task=False, arm=False)


def main(argv=None):
    a = PARSER.parse_args(argv)
    pack = Path(a.pack)
    if not (pack / "SKILL.md").exists():
        raise ValueError(f"no SKILL.md under {pack}")
    versions = runs_root(pack, a.run) / pack_name(pack) / "versions"
    out = {"pack": pack_name(pack), "dir": str(pack), "lesson": str(lesson_dir(pack)), "checksums": packs.checksums(pack),
           "versions": sorted(p.name for p in versions.glob("gen_*")) if versions.exists() else []}
    if not a.checksums:
        out["files"] = packs.read_pack(pack)
    return out


if __name__ == "__main__":
    cli.main(main)
