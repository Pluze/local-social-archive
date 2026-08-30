#!/usr/bin/env python3
"""Fail when repository paths or UTF-8 source text contain CJK characters."""
from __future__ import annotations

import argparse
from pathlib import Path


BLOCKED_RANGES = (
    (0x2E80, 0x2FFF),
    (0x3000, 0x303F),
    (0x31C0, 0x31EF),
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
    (0x20000, 0x323AF),
)
SKIP_DIRECTORIES = {".git", ".git.nosync", ".build", "__pycache__"}


def blocked_character(value: str) -> str | None:
    return next((character for character in value if any(start <= ord(character) <= end for start, end in BLOCKED_RANGES)), None)


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRECTORIES for part in relative.parts):
            continue
        if character := blocked_character(str(relative)):
            errors.append(f"path contains blocked character {character!r}: {relative}")
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if character := blocked_character(line):
                errors.append(f"text contains blocked character {character!r}: {relative}:{number}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()
    errors = [error for root in args.roots for error in audit(root.resolve())]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"English-only audit passed for {len(args.roots)} repository root(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
