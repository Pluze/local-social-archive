from __future__ import annotations

import csv
from pathlib import Path


def from_csv(path: Path, title: str = "Imported local archive") -> dict:
    collections: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row_number, row in enumerate(csv.DictReader(stream), 2):
            collection_id = row.get("collection_id") or "default"
            collection = collections.setdefault(collection_id, {
                "id": collection_id,
                "title": row.get("collection_title") or collection_id,
                "entries": [],
            })
            entry = {
                "id": row.get("id") or f"row-{row_number}",
                "timestamp": row.get("timestamp") or None,
                "author": row.get("author") or None,
                "isSelf": str(row.get("is_self", "")).lower() in {"1", "true", "yes"},
                "category": row.get("category") or None,
                "text": row.get("text") or "",
                "media": [],
            }
            if row.get("media_path"):
                entry["media"].append({"kind": row.get("media_kind") or "file", "path": row["media_path"], "name": row.get("media_name") or ""})
            collection["entries"].append(entry)
    return {"schemaVersion": 1, "title": title, "collections": list(collections.values())}
