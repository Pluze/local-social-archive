import importlib.util
import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


class MomentsExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[1]
        helper = cls.repo / "desktop/macos/Tools/bridge_helper.py"
        spec = importlib.util.spec_from_file_location("bridge_helper", helper)
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def fixture(self, root: Path) -> Path:
        media = root / "source-media.jpg"
        media.write_bytes(b"\xff\xd8\xfffixture")
        source = root / "my-moments.json"
        source.write_text(json.dumps({
            "totalPosts": 2,
            "posts": [
                {
                    "id": "old", "tid": "100", "createTime": 100,
                    "createTimeISO": "1970-01-01T00:01:40Z", "contentDesc": "Old",
                    "linkTitle": "Title", "linkUrl": "https://invalid.example/post",
                    "rawXml": "<url>https://invalid.example/raw</url>",
                    "interactionXml": "<token>private</token>",
                    "media": [{
                        "id": "m1", "type": 2, "localPath": media.name,
                        "url": "https://invalid.example/media", "thumb": "https://invalid.example/thumb",
                        "token": "private-token", "key": "private-key", "videoKey": "private-video-key",
                        "encIdx": "private-index", "backupStatus": "available"
                    }]
                },
                {"id": "new", "tid": "200", "createTime": 200, "createTimeISO": "1970-01-01T00:03:20Z", "contentDesc": "New", "media": []}
            ]
        }), encoding="utf-8")
        return source

    def test_portable_export_is_newest_first_and_contains_no_remote_access_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.fixture(root)
            destination = root / "export"
            result = self.bridge.moments_export(str(source), str(destination), {
                "includeJSON": True, "includeSQLite": True,
                "includeRemoteRefs": True, "mediaKinds": ["image"]
            })
            self.assertTrue(result["ok"])
            archive = json.loads((destination / "moments-archive.json").read_text(encoding="utf-8"))
            self.assertEqual([post["id"] for post in archive["posts"]], ["new", "old"])
            serialized = json.dumps(archive)
            for forbidden in ("https://invalid.example", "rawXml", "interactionXml", "linkUrl", "token", "videoKey", "encIdx", "includeRemoteRefs"):
                self.assertNotIn(forbidden, serialized)
            all_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in destination.rglob("*") if path.is_file() and path.suffix != ".sqlite")
            self.assertNotIn("https://invalid.example", all_text)
            with sqlite3.connect(destination / "moments-archive.sqlite") as database:
                self.assertNotIn("link_url", [row[1] for row in database.execute("PRAGMA table_info(posts)")])
                self.assertNotIn("remote_url", [row[1] for row in database.execute("PRAGMA table_info(media)")])

    def test_standalone_html_is_newest_first_and_does_not_link_remote_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.fixture(root)
            renderer = self.repo / "desktop/macos/Tools/render_moments_html.mjs"
            subprocess.run(["node", str(renderer), str(source)], check=True, capture_output=True, text=True)
            html = (root / "my-moments.html").read_text(encoding="utf-8")
            self.assertLess(html.index("New"), html.index("Old"))
            self.assertNotIn("https://invalid.example", html)
            self.assertNotIn("open original URL", html)


if __name__ == "__main__":
    unittest.main()
