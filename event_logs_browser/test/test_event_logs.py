
import json
import tempfile
from pathlib import Path

from event_logs_browser.windows.event_logs import (
    collect_windows_event_logs,
)


def verify_artifact_metadata(artifact):
    """
    Verify metadata fields for a successfully collected artifact.
    """

    assert artifact["status"] == "success"
    assert artifact["source_channel"]
    assert artifact["collection_timestamp"]
    assert artifact["sha256"]
    assert artifact["size_bytes"] > 0

    print(f"[PASS] Metadata: {artifact['artifact_name']}")


def test_windows_event_logs_collection():
    """
    Test Windows Event Logs collection and metadata generation.
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        # Run the collector
        result = collect_windows_event_logs(temp_dir)

        # Check collection summary
        assert result["total_channels"] == 3
        assert result["successful_collections"] == 3
        assert result["failed_collections"] == 0

        # Check metadata JSON file
        metadata_path = (
            Path(temp_dir)
            / "historical_artifacts"
            / "event_logs"
            / "event_logs_metadata.json"
        )

        assert metadata_path.is_file()

        saved_metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )

        assert saved_metadata == result

        # Verify metadata for every artifact
        for artifact in result["artifacts"]:
            verify_artifact_metadata(artifact)

        print("\nAll event log metadata tests passed!")


if __name__ == "__main__":
    test_windows_event_logs_collection()
