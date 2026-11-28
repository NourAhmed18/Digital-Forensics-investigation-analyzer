from parser.persistence_parser import parse_persistence_file
from parser.database.persistence_writer import store_persistence_artifacts
def run_pipeline():
    source_file = "sample_data/persistence_sample.json"

    parsed_data = parse_persistence_file(source_file)

    result = store_persistence_artifacts(
        parsed_data,
        source_file
    )

    print("Persistence Pipeline completed successfully!")
    print(f"Case ID: {result['case_id']}")
    print(f"Evidence ID: {result['evidence_id']}")
    print(f"Artifacts stored: {result['artifacts_stored']}")
    print(f"Registry stored: {result['registry_stored']}")
    print(f"Startup stored: {result['startup_stored']}")
    print(f"SHA256: {result['sha256']}")


if __name__ == "__main__":
    run_pipeline()