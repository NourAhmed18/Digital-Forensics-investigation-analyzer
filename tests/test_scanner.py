
import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from yara_engine.scanner import YaraScanner


class TestYaraScanner(unittest.TestCase):

    def setUp(self):
        rules_dir = BASE_DIR / "yara_engine" / "rules"
        sample_file = Path(__file__).parent / "positive_sample.txt"

        self.scanner = YaraScanner(rules_dir)
        self.scanner.load_rules()
        self.sample_file = sample_file

    def test_positive_sample_detection(self):
        result = self.scanner.scan_file(self.sample_file)

        self.assertTrue(result["is_suspicious"])
        self.assertTrue(
            any(
                match["rule"] == "Digital_Forensics_Test_Rule"
                for match in result["matches"]
            )
        )


if __name__ == "__main__":
    unittest.main()
