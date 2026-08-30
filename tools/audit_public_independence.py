#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SOURCE_SUFFIXES = {".py", ".swift", ".js", ".mjs", ".sh", ".toml", ".json"}
FORBIDDEN_DATA_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".key", ".pem", ".p12"}


def audit(root: Path) -> dict:
    root = root.resolve()
    errors: list[str] = []
    files = 0
    ignored_parts = {".git", ".git.nosync", ".build", "dist", "__pycache__", ".venv"}
    for path in root.rglob("*"):
        if any(part in ignored_parts for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            try:
                path.resolve().relative_to(root)
            except ValueError:
                errors.append(f"external symlink: {path.relative_to(root)}")
            continue
        if not path.is_file():
            continue
        files += 1
        relative = str(path.relative_to(root))
        if path.suffix.lower() in FORBIDDEN_DATA_SUFFIXES:
            errors.append(f"runtime data/credential-like file: {relative}")
        if path.stat().st_size > 2 * 1024 * 1024:
            errors.append(f"unexpected large tracked source candidate: {relative}")
        prefix = path.read_bytes()[:16]
        if prefix.startswith(b"SQLite format 3") or prefix[:4] in {b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe"}:
            errors.append(f"database or executable binary: {relative}")
        if path.suffix.lower() in SOURCE_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            absolute_user_pattern = "/" + "Users/" + r"[^/\s]+"
            if re.search(absolute_user_pattern, text):
                errors.append(f"absolute user path: {relative}")
    return {"ok": not errors, "files": files, "errors": sorted(errors)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prove the public tree has no private/runtime dependency")
    parser.add_argument("root", type=Path, nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 2)


if __name__ == "__main__":
    main()
