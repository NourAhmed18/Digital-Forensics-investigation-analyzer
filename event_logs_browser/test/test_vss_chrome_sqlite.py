
import shutil
import sqlite3
from pathlib import Path

from event_logs_browser.common.hashing import calculate_sha256


def main():
    project_root = Path(__file__).resolve().parents[2]

    evidence_dir = (
        project_root
        / "test_output"
        / "VSS-Chrome-Acquisition-Metadata-Test-5"
    )

    working_dir = (
        project_root
        / "test_output"
        / "VSS-Chrome-Working-Test-7"
    )

    evidence_db = evidence_dir / "History"
    working_db = working_dir / "History"

    if not evidence_db.is_file():
        raise FileNotFoundError(
            "Evidence History database not found."
        )

    if working_dir.exists():
        raise FileExistsError(
            f"Working directory already exists: {working_dir}"
        )

    # Record hashes before analysis.
    evidence_hashes_before = {
        file.name: calculate_sha256(str(file))
        for file in evidence_dir.iterdir()
        if file.is_file()
    }

    # Copy the complete acquired package.
    shutil.copytree(evidence_dir, working_dir)

    print("Evidence copied to working directory.")

    journal = working_dir / "History-journal"
    print("Journal available:", journal.is_file())

    # Open the working copy normally.
    # SQLite may perform journal recovery on this copy.
    connection = sqlite3.connect(str(working_db))

    try:
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        history_count = connection.execute(
            "SELECT COUNT(*) FROM urls"
        ).fetchone()[0]

        downloads_count = connection.execute(
            "SELECT COUNT(*) FROM downloads"
        ).fetchone()[0]

        print("\nSQLite Integrity:", integrity)
        print("History Records:", history_count)
        print("Download Records:", downloads_count)

    finally:
        connection.close()

    # Verify that the acquired evidence was not modified.
    evidence_hashes_after = {
        file.name: calculate_sha256(str(file))
        for file in evidence_dir.iterdir()
        if file.is_file()
    }

    unchanged = evidence_hashes_before == evidence_hashes_after

    print("\nOriginal evidence unchanged:", unchanged)

    if integrity != "ok":
        raise RuntimeError("SQLite integrity check failed.")

    if not unchanged:
        raise RuntimeError("Acquired evidence was modified.")

    print("\nPASS: SQLite analysis completed on working copy.")


if __name__ == "__main__":
    main()
