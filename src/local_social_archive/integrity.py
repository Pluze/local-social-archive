from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_integrity_manifest(root: Path) -> dict:
    files = {
        str(path.relative_to(root)): {"sha256": sha256_file(path), "size": path.stat().st_size}
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "integrity.json"
    }
    value = {"algorithm": "sha256", "files": files}
    (root / "integrity.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def verify_integrity(root: Path) -> dict:
    manifest_path = root / "integrity.json"
    if not manifest_path.is_file():
        return {"ok": False, "missingManifest": True, "missing": [], "changed": [], "unexpected": []}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("files", {})
    actual_paths = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != "integrity.json"}
    missing = sorted(set(expected) - actual_paths)
    unexpected = sorted(actual_paths - set(expected))
    changed = sorted(
        relative for relative in set(expected) & actual_paths
        if sha256_file(root / relative) != expected[relative].get("sha256")
        or (root / relative).stat().st_size != expected[relative].get("size")
    )
    return {"ok": not missing and not unexpected and not changed, "missing": missing, "changed": changed, "unexpected": unexpected}
