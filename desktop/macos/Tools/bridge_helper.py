#!/usr/bin/env python3
"""Fixed-purpose, vendor-neutral archive reducer for the native WebView bridge."""
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


def moments_page(path: str, offset: int, limit: int) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    posts = sorted(data.get("posts", []), key=lambda p: (int(p.get("createTime") or 0), str(p.get("tid") or "")), reverse=True)
    all_media = [m for post in posts for m in (post.get("media") or [])]
    local_media = sum(1 for m in all_media if m.get("localPath"))
    missing_media = len(all_media) - local_media
    page = posts[offset:offset + limit]
    compact = [{
        "tid": p.get("tid", ""),
        "createTimeISO": p.get("createTimeISO", ""),
        "contentDesc": p.get("contentDesc", ""),
        "linkTitle": p.get("linkTitle", ""),
        "likesCount": len(p.get("likes") or []),
        "commentsCount": len(p.get("comments") or []),
        "mediaCount": len(p.get("media") or []),
        "media": [{
            "id": m.get("id", ""), "type": m.get("type", 0),
            "localPath": m.get("localPath", ""),
            "backupStatus": "available" if m.get("localPath") else m.get("backupStatus", "not-cached-locally"),
        } for m in (p.get("media") or [])],
    } for p in page]
    end = offset + len(page)
    return {
        "ok": True, "posts": compact, "total": len(posts), "nextOffset": end, "hasMore": end < len(posts),
        "mediaTotal": len(all_media), "localMediaCount": local_media,
        "missingMediaCount": missing_media,
    }


def bootstrap(chat_path: str, moments_path: str) -> dict:
    chat_file = Path(chat_path)
    moments_file = Path(moments_path)
    chat = json.loads(chat_file.read_text(encoding="utf-8")) if chat_file.is_file() else {}
    moments_count = 0
    if moments_file.is_file():
        moments_count = int(json.loads(moments_file.read_text(encoding="utf-8")).get("totalPosts", 0) or 0)
    conversations = []
    for item in chat.get("conversations", []):
        conversations.append({key: value for key, value in item.items() if key != "sha256"})
    return {
        "ok": True,
        "chat": {
            "ready": bool(chat),
            "conversationCount": chat.get("conversation_count", 0),
            "messageCount": chat.get("message_count", 0),
            "plainTextCount": chat.get("plain_text_message_count", 0),
            "path": str(chat_file.parent),
        },
        "moments": {"ready": moments_file.is_file(), "postCount": moments_count, "path": str(moments_file.parent)},
        "conversations": conversations,
    }


def archive_bootstrap(archive_path: str, moments_path: str) -> dict:
    path = Path(archive_path)
    if not path.is_file():
        return {"ok": False, "error": "archive-not-found"}
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    meta = dict(con.execute("SELECT key,value FROM metadata"))
    conversations = [{
        "session_id": row[0], "display_name": row[1], "is_group": bool(row[2]),
        "message_count": row[3], "first_timestamp": row[4], "last_timestamp": row[5],
    } for row in con.execute("SELECT session_id,display_name,is_group,message_count,first_timestamp,last_timestamp FROM conversations ORDER BY last_timestamp DESC")]
    resources = con.execute("SELECT COUNT(*),COALESCE(SUM(available),0) FROM resources").fetchone()
    con.close()
    moments_file = Path(moments_path)
    moments_count = int(json.loads(moments_file.read_text(encoding="utf-8")).get("totalPosts", 0) or 0) if moments_file.is_file() else 0
    return {
        "ok": True, "archiveMode": True,
        "chat": {"ready": True, "conversationCount": int(meta.get("conversation_count", 0)), "messageCount": int(meta.get("message_count", 0)),
                 "resourceCount": int(resources[0]), "availableResourceCount": int(resources[1]), "path": str(path.parent)},
        "moments": {"ready": moments_file.is_file(), "postCount": moments_count, "path": str(moments_file.parent)},
        "conversations": conversations,
    }


def archive_page(archive_path: str, session_id: str, offset: int, limit: int) -> dict:
    con = sqlite3.connect(f"file:{Path(archive_path)}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute("""SELECT id,local_id,server_id,base_type,subtype,timestamp,sender_name,is_self,label,content FROM (
                          SELECT id,local_id,server_id,base_type,subtype,timestamp,sender_name,is_self,label,content,sort_seq
                          FROM messages WHERE session_id=? ORDER BY timestamp DESC,sort_seq DESC,local_id DESC,id DESC LIMIT ? OFFSET ?)
                          ORDER BY timestamp,sort_seq,local_id,id""",
                       (session_id, limit, offset)).fetchall()
    ids = [int(row["id"]) for row in rows]
    grouped = {message_id: [] for message_id in ids}
    if ids:
        marks = ",".join("?" for _ in ids)
        for resource in con.execute(f"""SELECT id,message_id,kind,variant,size,status,original_name,mime,available
                                        FROM resources WHERE message_id IN ({marks}) ORDER BY message_id,
                                        CASE variant WHEN 'high' THEN 0 WHEN 'normal' THEN 1 WHEN 'thumbnail' THEN 2 ELSE 3 END""", ids):
            grouped[int(resource["message_id"])].append({key: resource[key] for key in resource.keys() if key != "message_id"})
    total = int(con.execute("SELECT message_count FROM conversations WHERE session_id=?", (session_id,)).fetchone()[0])
    con.close()
    messages = []
    for row in rows:
        item = {key: row[key] for key in row.keys()}
        item["is_self"] = bool(item["is_self"])
        item["resources"] = grouped.get(int(row["id"]), [])
        item["formatted_time"] = __import__("datetime").datetime.fromtimestamp(int(row["timestamp"])).astimezone().strftime("%Y-%m-%d %H:%M:%S") if row["timestamp"] else "Unknown time"
        messages.append(item)
    end = offset + len(messages)
    return {"ok": True, "messages": messages, "offset": offset, "nextOffset": end, "hasMore": end < total, "total": total}


def archive_location(archive_path: str, session_id: str, mode: str, value: int, limit: int = 100) -> dict:
    con = sqlite3.connect(f"file:{Path(archive_path)}?mode=ro", uri=True)
    if mode == "date":
        newer = int(con.execute("SELECT COUNT(*) FROM messages WHERE session_id=? AND timestamp>=?", (session_id, value)).fetchone()[0])
        con.close()
        return {"ok": True, "offset": newer, "anchorId": 0}
    row = con.execute("SELECT id,timestamp,sort_seq,local_id FROM messages WHERE session_id=? AND id=?", (session_id, value)).fetchone()
    if not row:
        con.close(); return {"ok": False, "error": "message-not-found"}
    newer = int(con.execute("""SELECT COUNT(*) FROM messages WHERE session_id=? AND
        (timestamp>? OR (timestamp=? AND sort_seq>?) OR (timestamp=? AND sort_seq=? AND local_id>?) OR
         (timestamp=? AND sort_seq=? AND local_id=? AND id>?))""",
        (session_id,row[1],row[1],row[2],row[1],row[2],row[3],row[1],row[2],row[3],row[0])).fetchone()[0])
    con.close()
    return {"ok": True, "offset": max(0, newer - limit // 2), "anchorId": int(row[0])}


def archive_search(archive_path: str, query: str, session_id: str = "", limit: int = 120) -> dict:
    con = sqlite3.connect(f"file:{Path(archive_path)}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    # FTS query terms are quoted so punctuation in a user search is literal.
    terms = [part.replace('"', '""') for part in query.split() if part]
    fts = " AND ".join(f'"{part}"' for part in terms)
    if not fts:
        return {"ok": True, "results": []}
    session_clause = " AND m.session_id=?" if session_id else ""
    parameters = (fts, session_id, limit) if session_id else (fts, limit)
    rows = con.execute(f"""SELECT m.id AS message_id,m.session_id,c.display_name,m.timestamp,m.sender_name,
                                 snippet(message_fts,0,'[',']',' ... ',24) AS snippet
                          FROM message_fts JOIN messages m ON m.id=message_fts.rowid
                          JOIN conversations c USING(session_id) WHERE message_fts MATCH ?{session_clause}
                          ORDER BY rank LIMIT ?""", parameters).fetchall()
    con.close()
    return {"ok": True, "results": [{key: row[key] for key in row.keys()} for row in rows]}


def archive_resource(archive_path: str, resource_id: int) -> dict:
    con = sqlite3.connect(f"file:{Path(archive_path)}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT id,kind,variant,size,original_name,mime,source_path,archive_path,available FROM resources WHERE id=?", (resource_id,)).fetchone()
    con.close()
    if not row:
        return {"ok": False, "error": "resource-not-found"}
    return {"ok": True, **{key: row[key] for key in row.keys()}}


def install_export_viewer(root: Path, manifest: dict) -> None:
    template = Path(__file__).with_name("export_viewer.html")
    if not template.is_file():
        raise FileNotFoundError("export viewer template is missing")
    shutil.copy2(template, root / "index.html")
    data_dir = root / "data"; data_dir.mkdir(exist_ok=True)
    payload = json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/")
    (data_dir / "manifest.js").write_text(f"window.__WX_MANIFEST__={payload};\n", encoding="utf-8")


def write_viewer_chunk(data_dir: Path, name: str, rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    filename = f"{name}.js"
    (data_dir / filename).write_text(f"window.__WX_CHUNK__={payload};\n", encoding="utf-8")
    return f"data/{filename}"


def archive_export(archive_path: str, destination: str, session_ids: list[str], options: dict) -> dict:
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    con = sqlite3.connect(f"file:{Path(archive_path)}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    kinds = set(options.get("mediaKinds") or [])
    include_text = bool(options.get("includeText", True))
    include_json = bool(options.get("includeJSON", True))
    include_sqlite = bool(options.get("includeSQLite", True))
    portable = sqlite3.connect(root / "chat-archive.sqlite") if include_sqlite else None
    if portable:
        portable.executescript("""
        CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE conversations(session_id TEXT PRIMARY KEY,display_name TEXT,is_group INTEGER,message_count INTEGER,first_timestamp INTEGER,last_timestamp INTEGER);
        CREATE TABLE messages(id INTEGER PRIMARY KEY,session_id TEXT,local_id INTEGER,server_id INTEGER,local_type INTEGER,base_type INTEGER,subtype INTEGER,sort_seq INTEGER,timestamp INTEGER,sender_id TEXT,sender_name TEXT,is_self INTEGER,label TEXT,content TEXT,raw_content TEXT,source_shard TEXT);
        CREATE INDEX messages_session_time ON messages(session_id,timestamp,sort_seq,local_id);
        CREATE TABLE resources(id INTEGER PRIMARY KEY,message_id INTEGER,kind TEXT,variant TEXT,size INTEGER,status INTEGER,file_hash TEXT,original_name TEXT,mime TEXT,available INTEGER,included INTEGER,exported_path TEXT);
        CREATE INDEX resources_message ON resources(message_id);
        """)
    data_dir = root / "data"; data_dir.mkdir(exist_ok=True)
    decoded_images = {}
    image_cache = root / ".image-cache"
    if "image" in kinds and session_ids:
        marks = ",".join("?" for _ in session_ids)
        image_paths = [str(row[0]) for row in con.execute(f"""SELECT DISTINCT COALESCE(NULLIF(r.archive_path,''),r.source_path)
            FROM resources r JOIN messages m ON m.id=r.message_id WHERE r.kind='image' AND r.available=1
            AND m.session_id IN ({marks})""", session_ids) if row[0] and Path(row[0]).is_file()]
        if image_paths:
            list_file = data_dir / ".image-paths.json"
            list_file.write_text(json.dumps(image_paths), encoding="utf-8")
            try:
                raw = subprocess.check_output(["/opt/homebrew/bin/node", str(Path(__file__).with_name("media_decoder.mjs")), "--batch", str(list_file), str(image_cache)], text=True, stderr=subprocess.STDOUT)
                decoded_images = {item["source"]: item for item in json.loads(raw).get("items", []) if item.get("ok")}
            except Exception:
                decoded_images = {}
            list_file.unlink(missing_ok=True)
    viewer_items = []
    exported_messages = exported_resources = 0
    manifest = {"schemaVersion": 2, "type": "local-chat-portable-archive", "options": options, "conversations": []}
    for conversation_index, session_id in enumerate(session_ids):
        convo = con.execute("SELECT * FROM conversations WHERE session_id=?", (session_id,)).fetchone()
        if not convo:
            continue
        if portable:
            portable.execute("INSERT INTO conversations VALUES(?,?,?,?,?,?)", tuple(convo))
        safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in str(convo["display_name"]))[:80].strip() or "Conversation"
        folder = root / f"{safe}-{session_id[:12]}"
        folder.mkdir(parents=True, exist_ok=True)
        media_dir = folder / "Media"
        text_file = (folder / "messages.txt").open("w", encoding="utf-8") if include_text else None
        json_file = (folder / "messages.jsonl").open("w", encoding="utf-8") if include_json else None
        resource_manifest = []
        viewer_chunks, viewer_buffer = [], []
        rows = con.execute("SELECT * FROM messages WHERE session_id=? ORDER BY timestamp,sort_seq,local_id,id", (session_id,))
        for row in rows:
            item = dict(row)
            stamp = __import__("datetime").datetime.fromtimestamp(int(row["timestamp"])).astimezone().strftime("%Y-%m-%d %H:%M:%S") if row["timestamp"] else "Unknown time"
            item["formatted_time"] = stamp
            if text_file: text_file.write(f"[{stamp}] {row['sender_name']}（{row['label']}）\n{row['content']}\n\n")
            if portable: portable.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(row))
            resources = []
            for resource in con.execute("SELECT * FROM resources WHERE message_id=?", (row["id"],)):
                r = dict(resource)
                source = r.get("archive_path") or r.get("source_path") or ""
                included = r.get("kind") in kinds and source and Path(source).is_file()
                exported_path = ""
                if included:
                    decoded = decoded_images.get(source) if r.get("kind") == "image" else None
                    copy_source = str(decoded.get("output")) if decoded else source
                    if decoded: r["mime"] = decoded.get("mime") or r.get("mime")
                    media_dir.mkdir(exist_ok=True)
                    suffix = Path(copy_source).suffix
                    name = f"{resource['id']}-{resource['kind']}-{resource['variant']}{suffix}"
                    target = media_dir / name
                    if not target.exists(): shutil.copy2(copy_source, target)
                    exported_path = str(target.relative_to(root))
                    r["exportedPath"] = exported_path
                    exported_resources += 1
                if portable:
                    portable.execute("INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                                     (r["id"], r["message_id"], r["kind"], r["variant"], r["size"], r["status"], r["file_hash"], r["original_name"], r["mime"], r["available"], int(bool(included)), exported_path))
                r.pop("source_path", None); r.pop("archive_path", None)
                resources.append(r); resource_manifest.append(r)
            item["resources"] = resources
            if json_file: json_file.write(json.dumps(item, ensure_ascii=False) + "\n")
            viewer_buffer.append(item)
            if len(viewer_buffer) >= 500:
                viewer_chunks.append(write_viewer_chunk(data_dir, f"chat-{conversation_index}-{len(viewer_chunks)}", viewer_buffer))
                viewer_buffer = []
            exported_messages += 1
        if viewer_buffer:
            viewer_chunks.append(write_viewer_chunk(data_dir, f"chat-{conversation_index}-{len(viewer_chunks)}", viewer_buffer))
        if text_file: text_file.close()
        if json_file: json_file.close()
        if include_json: (folder / "media-manifest.json").write_text(json.dumps(resource_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["conversations"].append({"sessionId": session_id, "displayName": convo["display_name"], "messageCount": convo["message_count"], "folder": folder.name})
        viewer_items.append({"id": session_id, "displayName": convo["display_name"], "count": convo["message_count"], "chunks": viewer_chunks})
    con.close()
    if image_cache.exists(): shutil.rmtree(image_cache)
    if portable:
        portable.executemany("INSERT INTO metadata VALUES(?,?)", [("schema_version", "1"), ("type", "local-chat-portable-archive"), ("exported_at", __import__("datetime").datetime.now().astimezone().isoformat()), ("options", json.dumps(options, ensure_ascii=False))])
        portable.commit(); portable.close()
    manifest.update({"messageCount": exported_messages, "resourceCount": exported_resources,
                     "note": "Image .dat files are preserved source resources and can be decoded by Local Social Archive. Voice .silk files are preserved source audio."})
    (root / "export-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    install_export_viewer(root, {"type": "chats", "kindLabel": "Chat archive", "total": exported_messages, "items": viewer_items})
    return {"ok": True, "count": len(manifest["conversations"]), "messageCount": exported_messages, "resourceCount": exported_resources, "path": str(root)}


def moments_export(source_path: str, destination: str, options: dict) -> dict:
    source = Path(source_path)
    root = Path(destination); root.mkdir(parents=True, exist_ok=False)
    data = json.loads(source.read_text(encoding="utf-8"))
    kinds = set(options.get("mediaKinds") or [])
    include_json = bool(options.get("includeJSON", True))
    include_sqlite = bool(options.get("includeSQLite", True))
    output = {key: value for key, value in data.items() if key != "posts"}; output["posts"] = []
    media_count = 0
    posts = sorted(data.get("posts", []), key=lambda p: (int(p.get("createTime") or 0), str(p.get("tid") or "")), reverse=True)
    for post in posts:
        clone = {key: value for key, value in post.items() if key not in {"rawXml", "interactionXml", "linkUrl"}}
        clone["media"] = []
        for index, media in enumerate(post.get("media") or []):
            item = dict(media)
            url = str(item.get("url") or item.get("thumb") or "")
            kind = "video" if int(item.get("type") or 0) == 6 or int(post.get("type") or 0) == 15 or "video" in url.lower() or ".mp4" in url.lower() else "image"
            local = str(item.get("localPath") or "")
            if kind in kinds and local:
                candidate = (source.parent / local).resolve()
                if candidate.is_file() and candidate.is_relative_to(source.parent.resolve()):
                    target = root / "Media" / candidate.name; target.parent.mkdir(exist_ok=True)
                    if not target.exists(): shutil.copy2(candidate, target)
                    item["localPath"] = str(target.relative_to(root)); media_count += 1
            elif local:
                item["localPath"] = ""
            for key in ("url", "thumb", "remoteUrl", "token", "key", "videoKey", "encIdx"):
                item.pop(key, None)
            item["kind"] = kind; item["included"] = bool(item.get("localPath"))
            item["exportedPath"] = item.get("localPath") or ""
            clone["media"].append(item)
        output["posts"].append(clone)
    portable_options = {key: value for key, value in options.items() if key != "includeRemoteRefs"}
    output["portableExport"] = {"schemaVersion": 1, "type": "local-timeline-portable-archive", "options": portable_options}
    if include_json: (root / "moments-archive.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if include_sqlite:
        db = sqlite3.connect(root / "moments-archive.sqlite")
        db.executescript("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE posts(id TEXT PRIMARY KEY,tid TEXT,create_time INTEGER,create_time_iso TEXT,content TEXT,link_title TEXT,raw_json TEXT); CREATE TABLE media(id INTEGER PRIMARY KEY,post_id TEXT,kind TEXT,local_path TEXT,status TEXT,included INTEGER,raw_json TEXT);")
        db.executemany("INSERT INTO metadata VALUES(?,?)", [("schema_version", "1"), ("type", "local-timeline-portable-archive"), ("options", json.dumps(portable_options, ensure_ascii=False))])
        for post in output["posts"]:
            db.execute("INSERT INTO posts VALUES(?,?,?,?,?,?,?)", (str(post.get("id") or post.get("tid")), str(post.get("tid") or ""), int(post.get("createTime") or 0), post.get("createTimeISO"), post.get("contentDesc"), post.get("linkTitle"), json.dumps(post, ensure_ascii=False)))
            for media in post.get("media") or []:
                db.execute("INSERT INTO media(post_id,kind,local_path,status,included,raw_json) VALUES(?,?,?,?,?,?)", (str(post.get("id") or post.get("tid")), media.get("kind"), media.get("localPath"), media.get("backupStatus"), int(bool(media.get("included"))), json.dumps(media, ensure_ascii=False)))
        db.commit(); db.close()
    (root / "export-manifest.json").write_text(json.dumps({"schemaVersion": 1, "type": "local-timeline-portable-archive", "postCount": len(output["posts"]), "mediaCount": media_count, "options": portable_options}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data_dir = root / "data"; data_dir.mkdir(exist_ok=True)
    chunks = []
    for index in range(0, len(output["posts"]), 100):
        chunks.append(write_viewer_chunk(data_dir, f"moments-{index // 100}", output["posts"][index:index + 100]))
    install_export_viewer(root, {"type": "moments", "kindLabel": "Moments archive", "total": len(output["posts"]), "items": [{"id": "moments", "displayName": "My Moments", "count": len(output["posts"]), "chunks": chunks}]})
    return {"ok": True, "count": len(output["posts"]), "resourceCount": media_count, "path": str(root)}


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "bootstrap":
        print(json.dumps(bootstrap(sys.argv[2], sys.argv[3]), ensure_ascii=False))
        return
    if len(sys.argv) == 5 and sys.argv[1] == "moments-page":
        print(json.dumps(moments_page(sys.argv[2], max(0, int(sys.argv[3])), min(100, max(10, int(sys.argv[4])))), ensure_ascii=False))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "archive-bootstrap":
        print(json.dumps(archive_bootstrap(sys.argv[2], sys.argv[3]), ensure_ascii=False))
        return
    if len(sys.argv) == 6 and sys.argv[1] == "archive-page":
        print(json.dumps(archive_page(sys.argv[2], sys.argv[3], max(0, int(sys.argv[4])), min(500, max(20, int(sys.argv[5])))), ensure_ascii=False))
        return
    if len(sys.argv) == 7 and sys.argv[1] == "archive-locate":
        print(json.dumps(archive_location(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), min(500, max(20, int(sys.argv[6])))), ensure_ascii=False))
        return
    if len(sys.argv) in (4, 5) and sys.argv[1] == "archive-search":
        print(json.dumps(archive_search(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) == 5 else ""), ensure_ascii=False))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "archive-resource":
        print(json.dumps(archive_resource(sys.argv[2], int(sys.argv[3])), ensure_ascii=False))
        return
    if len(sys.argv) == 6 and sys.argv[1] == "archive-export":
        print(json.dumps(archive_export(sys.argv[2], sys.argv[3], json.loads(sys.argv[4]), json.loads(sys.argv[5])), ensure_ascii=False))
        return
    if len(sys.argv) == 5 and sys.argv[1] == "moments-export":
        print(json.dumps(moments_export(sys.argv[2], sys.argv[3], json.loads(sys.argv[4])), ensure_ascii=False))
        return
    raise SystemExit("unsupported bridge helper command")


if __name__ == "__main__":
    main()
