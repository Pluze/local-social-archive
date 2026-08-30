from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from .csv_adapter import from_csv
from .integrity import verify_integrity, write_integrity_manifest
from .model import archive_stats, load_archive, validate_archive
from .redact import redact_archive


ALLOWED_MEDIA = {"image", "video", "audio", "file"}


def safe_component(value: object, fallback: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in str(value or ""))
    return cleaned[:80].strip() or fallback


def contained_file(root: Path, relative: object) -> Path | None:
    if not relative:
        return None
    candidate = (root / str(relative)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def write_chunk(folder: Path, name: str, entries: list[dict]) -> str:
    payload = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    filename = f"{name}.js"
    (folder / filename).write_text(f"window.__ARCHIVE_CHUNK__={payload};\n", encoding="utf-8")
    return f"data/{filename}"


def create_database(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript("""
    PRAGMA journal_mode=DELETE;
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE collections(id TEXT PRIMARY KEY,title TEXT NOT NULL,entry_count INTEGER NOT NULL);
    CREATE TABLE entries(id TEXT PRIMARY KEY,collection_id TEXT NOT NULL,timestamp INTEGER,author TEXT,is_self INTEGER,category TEXT,text TEXT,raw_json TEXT);
    CREATE INDEX entries_collection_time ON entries(collection_id,timestamp,id);
    CREATE TABLE media(id INTEGER PRIMARY KEY,entry_id TEXT NOT NULL,kind TEXT,name TEXT,mime TEXT,included INTEGER,exported_path TEXT,raw_json TEXT);
    CREATE INDEX media_entry ON media(entry_id);
    """)
    return db


def export_archive(source: Path, destination: Path, media_root: Path, viewer: Path,
                   media_kinds: set[str], include_json: bool, include_text: bool) -> dict:
    data = load_archive(source)
    errors = validate_archive(data)
    if errors:
        raise ValueError("invalid interchange archive:\n- " + "\n- ".join(errors))
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    data_dir = destination / "data"; data_dir.mkdir()
    assets_dir = destination / "media"
    db = create_database(destination / "archive.sqlite")
    manifest_items, json_collections = [], []
    total_entries = copied_media = 0
    text_handle = (destination / "archive.txt").open("w", encoding="utf-8") if include_text else None
    for collection_index, collection in enumerate(data["collections"]):
        collection_id = str(collection.get("id") or f"collection-{collection_index}")
        title = str(collection.get("title") or collection_id)
        entries = collection.get("entries") if isinstance(collection.get("entries"), list) else []
        db.execute("INSERT INTO collections VALUES(?,?,?)", (collection_id, title, len(entries)))
        chunks, buffer, exported_entries = [], [], []
        for entry_index, entry in enumerate(entries):
            item = dict(entry)
            entry_id = str(item.get("id") or f"{collection_id}-{entry_index}")
            item.update({"id": entry_id, "collectionId": collection_id})
            media_out = []
            for media_index, media in enumerate(item.get("media") or []):
                record = dict(media); kind = str(record.get("kind") or "file")
                source_file = contained_file(media_root, record.get("path"))
                exported_path = ""
                included = kind in media_kinds and kind in ALLOWED_MEDIA and source_file is not None
                if included:
                    folder = assets_dir / safe_component(collection_id, "collection")
                    folder.mkdir(parents=True, exist_ok=True)
                    name = f"{safe_component(entry_id, 'entry')}-{media_index}{source_file.suffix}"
                    target = folder / name; shutil.copy2(source_file, target)
                    exported_path = str(target.relative_to(destination)); copied_media += 1
                record["included"] = bool(included); record["exportedPath"] = exported_path
                record.pop("path", None); media_out.append(record)
                db.execute("INSERT INTO media(entry_id,kind,name,mime,included,exported_path,raw_json) VALUES(?,?,?,?,?,?,?)",
                           (entry_id, kind, record.get("name"), record.get("mime"), int(bool(included)), exported_path, json.dumps(record, ensure_ascii=False)))
            item["media"] = media_out
            db.execute("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?)", (entry_id, collection_id, item.get("timestamp"), item.get("author"), int(bool(item.get("isSelf"))), item.get("category"), item.get("text"), json.dumps(item, ensure_ascii=False)))
            if text_handle:
                text_handle.write(f"[{item.get('timestamp', '')}] {item.get('author', '')} ({item.get('category', '')})\n{item.get('text', '')}\n\n")
            buffer.append(item); exported_entries.append(item); total_entries += 1
            if len(buffer) == 500:
                chunks.append(write_chunk(data_dir, f"collection-{collection_index}-{len(chunks)}", buffer)); buffer = []
        if buffer: chunks.append(write_chunk(data_dir, f"collection-{collection_index}-{len(chunks)}", buffer))
        manifest_items.append({"id": collection_id, "title": title, "count": len(entries), "chunks": chunks})
        if include_json: json_collections.append({"id": collection_id, "title": title, "entries": exported_entries})
    if text_handle: text_handle.close()
    metadata = {"schema_version": "1", "title": str(data.get("title") or "Local archive"), "entry_count": str(total_entries), "media_count": str(copied_media)}
    db.executemany("INSERT INTO metadata VALUES(?,?)", metadata.items()); db.commit(); db.close()
    if include_json:
        (destination / "archive.json").write_text(json.dumps({"schemaVersion": 1, "title": data.get("title"), "collections": json_collections}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    viewer_manifest = {"title": data.get("title") or "Local archive", "total": total_entries, "items": manifest_items}
    (data_dir / "manifest.js").write_text("window.__ARCHIVE_MANIFEST__=" + json.dumps(viewer_manifest, ensure_ascii=False).replace("</", "<\\/") + ";\n", encoding="utf-8")
    shutil.copy2(viewer, destination / "index.html")
    (destination / "manifest.json").write_text(json.dumps({**viewer_manifest, "includedMediaKinds": sorted(media_kinds), "copiedMedia": copied_media}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_integrity_manifest(destination)
    return {"entries": total_entries, "media": copied_media, "output": str(destination)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build, inspect and verify portable local social archives")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build an offline archive from normalized JSON")
    build.add_argument("source", type=Path); build.add_argument("destination", type=Path)
    build.add_argument("--media-root", type=Path, default=Path(".")); build.add_argument("--media", default="image,video,audio,file")
    build.add_argument("--no-json", action="store_true"); build.add_argument("--text", action="store_true")
    validate = commands.add_parser("validate", help="validate normalized input JSON"); validate.add_argument("source", type=Path)
    inspect = commands.add_parser("inspect", help="summarize normalized input JSON"); inspect.add_argument("source", type=Path)
    verify = commands.add_parser("verify", help="verify an exported archive's SHA-256 manifest"); verify.add_argument("archive", type=Path)
    redact = commands.add_parser("redact", help="create a review-safe normalized JSON copy")
    redact.add_argument("source", type=Path); redact.add_argument("destination", type=Path); redact.add_argument("--salt", required=True)
    redact.add_argument("--drop-text", action="store_true"); redact.add_argument("--keep-media-metadata", action="store_true")
    csv_command = commands.add_parser("from-csv", help="convert a simple CSV file to normalized JSON")
    csv_command.add_argument("source", type=Path); csv_command.add_argument("destination", type=Path); csv_command.add_argument("--title", default="Imported local archive")
    argv = sys.argv[1:]
    if argv and argv[0] not in {"build", "validate", "inspect", "verify", "redact", "from-csv", "-h", "--help"}:
        argv.insert(0, "build")
    args = parser.parse_args(argv)
    if args.command in {"validate", "inspect"}:
        data = load_archive(args.source.resolve()); errors = validate_archive(data)
        result = {"ok": not errors, **archive_stats(data), "errors": errors}
        print(json.dumps(result, ensure_ascii=False)); raise SystemExit(0 if not errors else 2)
    if args.command == "verify":
        result = verify_integrity(args.archive.resolve()); print(json.dumps(result, ensure_ascii=False)); raise SystemExit(0 if result["ok"] else 2)
    if args.command == "redact":
        data = load_archive(args.source.resolve()); errors = validate_archive(data)
        if errors: parser.error("invalid source: " + "; ".join(errors))
        output = redact_archive(data, args.salt, args.drop_text, not args.keep_media_metadata)
        args.destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(args.destination)}, ensure_ascii=False)); return
    if args.command == "from-csv":
        output = from_csv(args.source.resolve(), args.title)
        args.destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, **archive_stats(output), "output": str(args.destination)}, ensure_ascii=False)); return
    kinds = {value.strip() for value in args.media.split(",") if value.strip()}; unknown = kinds - ALLOWED_MEDIA
    if unknown: parser.error("unknown media kinds: " + ", ".join(sorted(unknown)))
    viewer = Path(__file__).with_name("viewer.html")
    result = export_archive(args.source.resolve(), args.destination.resolve(), args.media_root.resolve(), viewer, kinds, not args.no_json, args.text)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
