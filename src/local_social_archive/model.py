from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def load_archive(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("archive root must be an object")
    return value


def iter_entries(data: dict) -> Iterator[tuple[dict, dict]]:
    for collection in data.get("collections", []):
        for entry in collection.get("entries", []):
            yield collection, entry


def validate_archive(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    collections = data.get("collections")
    if not isinstance(collections, list):
        return errors + ["collections must be an array"]
    collection_ids: set[str] = set()
    entry_ids: set[str] = set()
    allowed_media = {"image", "video", "audio", "file"}
    for ci, collection in enumerate(collections):
        where = f"collections[{ci}]"
        if not isinstance(collection, dict):
            errors.append(f"{where} must be an object"); continue
        cid = collection.get("id")
        if not isinstance(cid, str) or not cid:
            errors.append(f"{where}.id must be a non-empty string")
        elif cid in collection_ids:
            errors.append(f"duplicate collection id: {cid}")
        else:
            collection_ids.add(cid)
        if not isinstance(collection.get("title"), str):
            errors.append(f"{where}.title must be a string")
        entries = collection.get("entries")
        if not isinstance(entries, list):
            errors.append(f"{where}.entries must be an array"); continue
        for ei, entry in enumerate(entries):
            ewhere = f"{where}.entries[{ei}]"
            if not isinstance(entry, dict):
                errors.append(f"{ewhere} must be an object"); continue
            eid = entry.get("id")
            if not isinstance(eid, str) or not eid:
                errors.append(f"{ewhere}.id must be a non-empty string")
            elif eid in entry_ids:
                errors.append(f"duplicate entry id: {eid}")
            else:
                entry_ids.add(eid)
            if not isinstance(entry.get("text"), str):
                errors.append(f"{ewhere}.text must be a string")
            for mi, media in enumerate(entry.get("media", [])):
                mwhere = f"{ewhere}.media[{mi}]"
                if not isinstance(media, dict):
                    errors.append(f"{mwhere} must be an object"); continue
                if media.get("kind") not in allowed_media:
                    errors.append(f"{mwhere}.kind is unsupported")
                if not isinstance(media.get("path"), str) or not media.get("path"):
                    errors.append(f"{mwhere}.path must be a non-empty string")
    return errors


def archive_stats(data: dict) -> dict[str, int]:
    entries = media = 0
    for _, entry in iter_entries(data):
        entries += 1
        media += len(entry.get("media") or [])
    return {"collections": len(data.get("collections", [])), "entries": entries, "media": media}
