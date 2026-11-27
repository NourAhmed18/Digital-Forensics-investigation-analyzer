import json
from pathlib import Path


def save_scan_results(results, output_path):
    """Save YARA scan results as JSON."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    return str(output_path)
