import importlib.util
import tempfile
import unittest
from pathlib import Path


class IndependenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("audit_public_independence", repo / "tools/audit_public_independence.py")
        cls.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.module)
        cls.repo = repo

    def test_public_tree_has_no_private_dependency(self):
        result = self.module.audit(self.repo)
        self.assertEqual(result["errors"], [])

    def test_audit_detects_runtime_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "runtime.sqlite").write_bytes(b"SQLite format 3\x00")
            result = self.module.audit(root)
            self.assertFalse(result["ok"])

    def test_credential_reset_invalidates_stale_task_notifications(self):
        source = (self.repo / "desktop/macos/Web/app.js").read_text(encoding="utf-8")
        self.assertIn("state.taskEpoch += 1", source)
        self.assertIn("epoch !== state.taskEpoch", source)
        self.assertIn("status.state === 'cancelled'", source)
