import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "parser"))

from network_parser import parse_network
from database.network_writer import store_network_connections


SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "network_sample.json"


def main():
    print("Starting Network Pipeline...")

    parsed_data = parse_network(SAMPLE_FILE)

    print(f"Parsed {len(parsed_data['connections'])} network connections.")

    result = store_network_connections(
        parsed_data,
        source_file=SAMPLE_FILE
    )

    print("\nDatabase insertion successful!")
    print(f"Case ID: {result['case_id']}")
    print(f"Evidence ID: {result['evidence_id']}")
    print(f"Connections stored: {result['connections_stored']}")
    print(f"SHA256: {result['sha256']}")


if __name__ == "__main__":
    main()