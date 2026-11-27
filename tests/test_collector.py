from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from collector.core import collect_case, sha256_file
from collector.host_info import collect_host_info


class CollectorTests(unittest.TestCase):
    def test_host_info_has_required_fields(self) -> None:
        info = collect_host_info()
        self.assertIn("operating_system", info)
        self.assertTrue(info["hostname"])
        self.assertTrue(info["username"])
        self.assertIn("is_privileged", info["privilege"])

    def test_case_contains_hashed_evidence_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = collect_case(root, case_id="unit-test", config={"schema_version": "1.0", "enabled_modules": ["host_info", "future_module"]})
            self.assertTrue(result.host_info_path.is_file())
            self.assertTrue((result.case_dir / "logs" / "collector.log").is_file())
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["hash_algorithm"], "SHA-256")
            host_record = next(item for item in manifest["records"] if item["relative_path"].endswith("host_info.json"))
            self.assertEqual(host_record["sha256"], sha256_file(result.host_info_path))
            self.assertEqual(result.skipped_modules, ("future_module",))

    def test_each_run_creates_a_new_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = collect_case(root, case_id="same-id")
            second = collect_case(root, case_id="same-id")
            self.assertNotEqual(first.case_dir, second.case_dir)
            self.assertEqual(len(list(root.iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
