
import json
import tempfile
import unittest
from pathlib import Path

from event_logs_browser.browsers.firefox import (
    collect_firefox_artifacts,
)
from event_logs_browser.common.hashing import calculate_sha256


class FirefoxSuiteTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source_dir = Path(
            "test_output/Firefox-Download-Inspection"
        )
        cls.source_db = cls.source_dir / "places.sqlite"

        if not cls.source_db.is_file():
            raise FileNotFoundError(
                f"Firefox test database not found: {cls.source_db}"
            )

    def test_collection_and_profile_separation(self):
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp) / "case"
            profile_name = "test-profile"

            result = collect_firefox_artifacts(
                source_db=str(self.source_db),
                case_dir=str(case_dir),
                profile_name=profile_name
            )

            output_dir = (
                case_dir
                / "historical_artifacts"
                / "browser"
                / "firefox"
                / profile_name
            )

            self.assertTrue(result["integrity_verified"])
            self.assertEqual(result["browser"], "Mozilla Firefox")

            self.assertTrue(
                (output_dir / "evidence" / "places.sqlite").is_file()
            )
            self.assertTrue((output_dir / "history.json").is_file())
            self.assertTrue((output_dir / "downloads.json").is_file())
            self.assertTrue(
                (output_dir / "collection_metadata.json").is_file()
            )

            history = json.loads(
                (output_dir / "history.json").read_text(
                    encoding="utf-8"
                )
            )

            downloads = json.loads(
                (output_dir / "downloads.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                len(history), result["history_records"]
            )
            self.assertEqual(
                len(downloads), result["download_records"]
            )

            print(
                f"History: {len(history)}, "
                f"Downloads: {len(downloads)}"
            )

    def test_original_evidence_unchanged(self):
        source_files = [
            self.source_db,
            self.source_dir / "places.sqlite-wal",
            self.source_dir / "places.sqlite-shm",
        ]

        source_files = [
            file for file in source_files if file.is_file()
        ]

        before = {
            file.name: calculate_sha256(str(file))
            for file in source_files
        }

        with tempfile.TemporaryDirectory() as temp:
            collect_firefox_artifacts(
                source_db=str(self.source_db),
                case_dir=str(Path(temp) / "case")
            )

        after = {
            file.name: calculate_sha256(str(file))
            for file in source_files
        }

        self.assertEqual(before, after)

    def test_legacy_output_without_profile_name(self):
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp) / "case"

            collect_firefox_artifacts(
                source_db=str(self.source_db),
                case_dir=str(case_dir)
            )

            old_output_dir = (
                case_dir
                / "historical_artifacts"
                / "browser"
                / "firefox"
            )

            self.assertTrue(
                (old_output_dir / "history.json").is_file()
            )

    def test_invalid_profile_names(self):
        invalid_names = [
            "",
            ".",
            "..",
            "../escape",
            r"..\escape",
        ]

        for name in invalid_names:
            with self.subTest(profile_name=name):
                with tempfile.TemporaryDirectory() as temp:
                    with self.assertRaises(ValueError):
                        collect_firefox_artifacts(
                            source_db=str(self.source_db),
                            case_dir=str(Path(temp) / "case"),
                            profile_name=name
                        )

    def test_missing_database(self):
        with tempfile.TemporaryDirectory() as temp:
            missing_db = Path(temp) / "missing.sqlite"

            with self.assertRaises(FileNotFoundError):
                collect_firefox_artifacts(
                    source_db=str(missing_db),
                    case_dir=str(Path(temp) / "case")
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
