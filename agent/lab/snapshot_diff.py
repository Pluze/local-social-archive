#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def inventory(root: Path) -> dict[str, dict]:
    root = root.resolve()
    result: dict[str, dict] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        stat = path.stat()
        result[str(path.relative_to(root))] = {
            "size": stat.st_size,
            "mtimeNs": stat.st_mtime_ns,
            "sha256": digest.hexdigest(),
        }
    return result


def compare(before: dict, after: dict) -> dict:
    old, new = set(before), set(after)
    return {
        "added": sorted(new - old),
        "removed": sorted(old - new),
        "changed": sorted(path for path in old & new if before[path] != after[path]),
        "unchanged": len([path for path in old & new if before[path] == after[path]]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Content-free file inventory and before/after comparison")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture"); capture.add_argument("root", type=Path); capture.add_argument("output", type=Path)
    diff = commands.add_parser("compare"); diff.add_argument("before", type=Path); diff.add_argument("after", type=Path)
    args = parser.parse_args()
    if args.command == "capture":
        value = {"format": 1, "rootLabel": args.root.name, "files": inventory(args.root)}
        args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "files": len(value["files"]), "output": str(args.output)}))
    else:
        before = json.loads(args.before.read_text(encoding="utf-8"))["files"]
        after = json.loads(args.after.read_text(encoding="utf-8"))["files"]
        print(json.dumps({"ok": True, **compare(before, after)}, indent=2))


if __name__ == "__main__":
    main()
