import importlib.util
import unittest
from pathlib import Path


class ComponentContractTests(unittest.TestCase):
    def test_public_placeholder_is_explicitly_unimplemented(self):
        repo = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("check_component", repo / "tools/check_component.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        value = module.check_component(repo / "components/provider")
        self.assertFalse(value["implementationIncluded"])
        self.assertTrue(all(status == "unavailable" for status in value["capabilities"].values()))
        self.assertFalse(any(path.suffix in {".db", ".sqlite"} for path in (repo / "components").rglob("*")))
