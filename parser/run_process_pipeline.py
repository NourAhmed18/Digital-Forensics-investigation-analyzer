import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from process_parser import parse_processes
from database.process_writer import store_processes

SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "processes_sample.json"


def main():
    print("Starting Process Pipeline...")

    parsed_data = parse_processes(SAMPLE_FILE)
    print(f"Parsed {len(parsed_data['processes'])} processes.")

    result = store_processes(parsed_data, source_file=SAMPLE_FILE)

    print("\nDatabase insertion successful!")
    print(f"Case ID: {result['case_id']}")
    print(f"Evidence ID: {result['evidence_id']}")
    print(f"Processes stored: {result['processes_stored']}")
    print(f"SHA256: {result['sha256']}")


if __name__ == "__main__":
    main()