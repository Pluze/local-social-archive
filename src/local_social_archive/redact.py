from __future__ import annotations

import copy
import hashlib


def pseudonym(value: object, salt: str) -> str:
    digest = hashlib.sha256((salt + "\0" + str(value or "")).encode()).hexdigest()[:12]
    return f"person-{digest}"


def redact_archive(data: dict, salt: str, drop_text: bool = False, drop_media: bool = True) -> dict:
    output = copy.deepcopy(data)
    output["title"] = "Redacted local archive"
    for collection in output.get("collections", []):
        collection["title"] = f"Collection {pseudonym(collection.get('id'), salt)[7:]}"
        for entry in collection.get("entries", []):
            if entry.get("author"):
                entry["author"] = pseudonym(entry["author"], salt)
            if drop_text:
                entry["text"] = "[redacted]"
            if drop_media:
                entry["media"] = []
            else:
                for media in entry.get("media", []):
                    media["path"] = "redacted"
                    media["unavailable"] = True
    return output
