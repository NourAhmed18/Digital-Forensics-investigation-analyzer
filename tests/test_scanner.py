
import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from yara_engine.scanner import YaraScanner


class TestYaraScanner(unittest.TestCase):

    def setUp(self):
        rules_dir = BASE_DIR / "yara_engine" / "rules"
        self.positive_sample = Path(__file__).parent / "positive_sample.txt"
        self.negative_sample = Path(__file__).parent / "negative_sample.txt"

        self.scanner = YaraScanner(rules_dir)
        self.scanner.load_rules()

    def test_positive_sample_detection(self):
        result = self.scanner.scan_file(self.positive_sample)

        self.assertTrue(result["is_suspicious"])
        self.assertTrue(
            any(
                match["rule"] == "Digital_Forensics_Test_Rule"
                for match in result["matches"]
            )
        )

    def test_negative_sample_no_detection(self):
        result = self.scanner.scan_file(self.negative_sample)

        self.assertFalse(result["is_suspicious"])
        self.assertEqual(len(result["matches"]), 0)


if __name__ == "__main__":
    unittest.main()
