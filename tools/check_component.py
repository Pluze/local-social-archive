#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def check_component(root: Path) -> dict:
    errors: list[str] = []
    adapter = root / "Adapter.swift"
    contract = root / "component-contract.json"
    if not adapter.is_file():
        errors.append("missing Adapter.swift")
    else:
        source = adapter.read_text(encoding="utf-8")
        if "ArchiveBridge" not in source:
            errors.append("Adapter.swift does not implement ArchiveBridge")
        if not re.search(r"func\s+makeArchiveBridge\s*\(\s*\)\s*->\s*ArchiveBridge", source):
            errors.append("Adapter.swift does not expose makeArchiveBridge()")
    value: dict = {}
    if not contract.is_file():
        errors.append("missing component-contract.json")
    else:
        try:
            value = json.loads(contract.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid component contract: {error}")
        if value.get("contractVersion") != 1:
            errors.append("unsupported component contractVersion")
        if not isinstance(value.get("capabilities"), dict):
            errors.append("capabilities must be an object")
    forbidden = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(root))
        lowered = relative.lower()
        if lowered.endswith((".db", ".sqlite", ".sqlite3", ".key", ".pem", ".p12")):
            forbidden.append(relative)
    if forbidden:
        errors.append("runtime data or credential-like files present: " + ", ".join(sorted(forbidden)))
    return {
        "ok": not errors,
        "component": value.get("component"),
        "implementationIncluded": value.get("implementationIncluded"),
        "capabilities": value.get("capabilities", {}),
        "files": sum(1 for path in root.rglob("*") if path.is_file()),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Local Social Archive acquisition component")
    parser.add_argument("component", type=Path)
    args = parser.parse_args()
    result = check_component(args.component.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 2)


if __name__ == "__main__":
    main()
