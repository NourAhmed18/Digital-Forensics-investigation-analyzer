
import yara
from pathlib import Path


class YaraScanner:
    def __init__(self, rules_path=None):
        if rules_path is None:
            rules_path = Path(__file__).parent / "rules"

        self.rules_path = Path(rules_path)
        self.rules = None

    def load_rules(self):
        """Load YARA rules from the rules directory."""

        if not self.rules_path.is_dir():
            raise FileNotFoundError(
                f"Rules directory not found: {self.rules_path}"
            )

        rule_files = sorted(
            list(self.rules_path.glob("*.yar")) +
            list(self.rules_path.glob("*.yara"))
        )

        if not rule_files:
            raise FileNotFoundError("No YARA rule files found.")

        self.rules = yara.compile(
            filepaths={
                f"rule_{index}": str(path)
                for index, path in enumerate(rule_files)
            }
        )

        return True

    def scan_file(self, file_path):
        """Scan a file and return matched YARA rules."""

        if self.rules is None:
            raise RuntimeError("Load YARA rules before scanning.")

        file_path = Path(file_path)

        if not file_path.is_file():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        matches = self.rules.match(str(file_path))

        return {
            "file": str(file_path),
            "matches": [
                {
                    "rule": match.rule,
                    "tags": list(match.tags),
                    "meta": dict(match.meta)
                }
                for match in matches
            ],
            "is_suspicious": bool(matches)
        }

