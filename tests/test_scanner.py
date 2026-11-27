
import unittest
from pathlib import Path

from yara.scanner import YaraScanner


class TestYaraScanner(unittest.TestCase):

    def setUp(self):
        self.base_dir = Path(__file__).resolve().parents[1]
        self.rules_dir = self.base_dir / "rules"
        self.sample_file = Path(__file__).parent / "positive_sample.txt"

        self.scanner = YaraScanner(self.rules_dir)
        self.scanner.load_rules()

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
