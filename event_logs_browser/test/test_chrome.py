
import json
import sqlite3
import tempfile
from pathlib import Path

from event_logs_browser.browsers.chrome import (
    collect_chrome_artifacts,
)

from event_logs_browser.common.hashing import (
    calculate_sha256,
)


PROJECT_DIR = Path(__file__).resolve().parents[2]

SAMPLE_DB = (
    PROJECT_DIR
    / "sample_data"
    / "browser"
    / "History"
)


def test_chrome_collection():

    # Check that the sample database exists
    assert SAMPLE_DB.is_file(), (
        "Chrome sample database is missing."
    )

    # Calculate original hash before collection
    original_hash_before = calculate_sha256(
        str(SAMPLE_DB)
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        # Run Chrome Collector
        result = collect_chrome_artifacts(
            source_db=str(SAMPLE_DB),
            case_dir=temp_dir,
        )

        output_dir = (
            Path(temp_dir)
            / "historical_artifacts"
            / "browser"
            / "chrome"
        )

        # Check SQLite evidence snapshot
        evidence_copy = (
            output_dir
            / "evidence"
            / "History"
        )

        assert evidence_copy.is_file(), (
            "SQLite evidence snapshot was not created."
        )

        assert result["integrity_verified"] is True

        assert result["snapshot_sha256"] == calculate_sha256(
            str(evidence_copy)
        ), "Snapshot SHA-256 mismatch."

        # Check extracted JSON files
        history_path = output_dir / "history.json"
        downloads_path = output_dir / "downloads.json"
        metadata_path = output_dir / "collection_metadata.json"

        assert history_path.is_file()
        assert downloads_path.is_file()
        assert metadata_path.is_file()

        # Read extracted records
        history = json.loads(
            history_path.read_text(encoding="utf-8")
        )

        downloads = json.loads(
            downloads_path.read_text(encoding="utf-8")
        )

        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )

        # Verify record counts without displaying private data
        assert len(history) == result["history_records"]
        assert len(downloads) == result["download_records"]

        assert metadata["browser"] == "Google Chrome"

        # Verify snapshot SQLite integrity
        connection = sqlite3.connect(
            f"{evidence_copy.resolve().as_uri()}?mode=ro",
            uri=True,
        )

        try:
            integrity = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

        finally:
            connection.close()

        assert integrity == "ok", (
            "Evidence snapshot SQLite integrity check failed."
        )

        # Verify original database was not modified
        original_hash_after = calculate_sha256(
            str(SAMPLE_DB)
        )

        assert original_hash_before == original_hash_after, (
            "Original Chrome database was modified!"
        )

        # Display test results
        print("[PASS] SQLite evidence snapshot created")
        print("[PASS] Snapshot SHA-256 verified")
        print("[PASS] History JSON created")
        print("[PASS] Downloads JSON created")
        print("[PASS] Collection metadata created")
        print("[PASS] SQLite integrity check passed")
        print("[PASS] Original evidence remained unchanged")

        print(f"\nHistory records: {len(history)}")
        print(f"Download records: {len(downloads)}")


if __name__ == "__main__":

    test_chrome_collection()

    print("\nAll Chrome collection tests passed!")
