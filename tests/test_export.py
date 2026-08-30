import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from local_social_archive.cli import contained_file, export_archive
from local_social_archive.integrity import verify_integrity
from local_social_archive.model import archive_stats, load_archive, validate_archive
from local_social_archive.redact import redact_archive


class ExportTests(unittest.TestCase):
    def test_synthetic_export_and_path_containment(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.json"
            source.write_text((repo / "examples/demo.json").read_text(encoding="utf-8"), encoding="utf-8")
            output = root / "result"
            result = export_archive(source, output, root, repo / "viewer/index.html", set(), True, True)
            self.assertEqual(result["entries"], 2)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "archive.json").is_file())
            self.assertTrue((output / "integrity.json").is_file())
            self.assertTrue(verify_integrity(output)["ok"])
            with sqlite3.connect(output / "archive.sqlite") as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM entries").fetchone()[0], 2)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertIsNone(contained_file(root, "../outside.txt"))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["total"], 2)

    def test_validation_stats_and_redaction(self):
        repo = Path(__file__).resolve().parents[1]
        data = load_archive(repo / "examples/demo.json")
        self.assertEqual(validate_archive(data), [])
        self.assertEqual(archive_stats(data), {"collections": 1, "entries": 2, "media": 0})
        redacted = redact_archive(data, "test-salt", drop_text=True)
        self.assertEqual(validate_archive(redacted), [])
        self.assertEqual(redacted["collections"][0]["entries"][0]["text"], "[redacted]")
        self.assertTrue(str(redacted["collections"][0]["entries"][0]["author"]).startswith("person-"))

    def test_integrity_detects_change(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / "result"
            export_archive(repo / "examples/demo.json", output, root, repo / "viewer/index.html", set(), True, False)
            (output / "manifest.json").write_text("changed", encoding="utf-8")
            result = verify_integrity(output)
            self.assertFalse(result["ok"])
            self.assertEqual(result["changed"], ["manifest.json"])


if __name__ == "__main__":
    unittest.main()
