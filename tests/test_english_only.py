import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_english_only import audit


class EnglishOnlyTests(unittest.TestCase):
    def test_public_repository_has_no_cjk_source_or_paths(self):
        self.assertEqual(audit(ROOT), [])


if __name__ == "__main__":
    unittest.main()
