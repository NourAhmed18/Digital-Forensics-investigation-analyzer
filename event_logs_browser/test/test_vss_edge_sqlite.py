
import shutil
import sqlite3
from pathlib import Path

from event_logs_browser.common.hashing import calculate_sha256


def get_file_hashes(directory: Path) -> dict:
    """Calculate hashes for every file in a directory."""

    return {
        file.relative_to(directory).as_posix():
            calculate_sha256(str(file))
        for file in directory.rglob("*")
        if file.is_file()
    }


def main():

    project_root = Path(__file__).resolve().parents[2]

    # Original acquired Edge evidence.
    evidence_dir = (
        project_root
        / "test_output"
        / "Edge-VSS-Acquisition-Test"
    )

    # Separate directory for SQLite analysis.
    working_dir = (
        project_root
        / "test_output"
        / "Edge-VSS-Working-Test-5"
    )

    if not evidence_dir.is_dir():
        raise FileNotFoundError(
            f"Edge evidence directory not found: {evidence_dir}"
        )

    if not (evidence_dir / "browser_metadata.json").is_file():
        raise FileNotFoundError(
            "Edge browser metadata file not found."
        )

    if working_dir.exists():
        raise FileExistsError(
            f"Working directory already exists: {working_dir}\n"
            "Choose a new working directory name."
        )

    # Record original evidence hashes before analysis.
    evidence_hashes_before = get_file_hashes(evidence_dir)

    # Copy the complete evidence package.
    shutil.copytree(evidence_dir, working_dir)

    print("Evidence copied to working directory.")

    results = []
    failed_profiles = []

    # Find all profile directories containing History.
    profile_dirs = sorted(
        [
            directory
            for directory in working_dir.iterdir()
            if directory.is_dir()
            and (directory / "History").is_file()
        ],
        key=lambda path: path.name
    )

    if not profile_dirs:
        raise RuntimeError(
            "No Edge profiles found in the working directory."
        )

    print("Profiles found:", len(profile_dirs))

    # Analyze each profile's working copy.
    for profile_dir in profile_dirs:

        profile_name = profile_dir.name
        history_db = profile_dir / "History"

        print("\n" + "=" * 45)
        print("Profile:", profile_name)

        connection = sqlite3.connect(
            f"file:{history_db.as_posix()}?mode=rw",
            uri=True
        )

        try:
            integrity = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table'"
                )
            }

            history_count = None
            downloads_count = None

            if "urls" in tables:
                history_count = connection.execute(
                    "SELECT COUNT(*) FROM urls"
                ).fetchone()[0]

            if "downloads" in tables:
                downloads_count = connection.execute(
                    "SELECT COUNT(*) FROM downloads"
                ).fetchone()[0]

            print("SQLite Integrity:", integrity)
            print("History Records:", history_count)
            print("Download Records:", downloads_count)

            result = {
                "profile": profile_name,
                "integrity": integrity,
                "history_records": history_count,
                "download_records": downloads_count,
            }

            results.append(result)

            if integrity != "ok":
                failed_profiles.append(profile_name)

        except sqlite3.Error as error:

            print("SQLite Error:", error)
            failed_profiles.append(profile_name)

            results.append({
                "profile": profile_name,
                "error": str(error),
            })

        finally:
            connection.close()

    # Verify original evidence remains unchanged.
    evidence_hashes_after = get_file_hashes(evidence_dir)

    unchanged = (
        evidence_hashes_before == evidence_hashes_after
    )

    print("\n" + "=" * 45)
    print("FINAL RESULTS")
    print("=" * 45)

    print("Profiles tested:", len(results))
    print("Profiles failed:", len(failed_profiles))
    print("Original evidence unchanged:", unchanged)

    if failed_profiles:
        print("Failed profiles:", failed_profiles)

    if not unchanged:
        raise RuntimeError(
            "Original Edge evidence was modified."
        )

    if failed_profiles:
        raise RuntimeError(
            "SQLite integrity failed for one or more profiles."
        )

    print("\nPASS: All Edge profiles passed SQLite testing.")
    print("Analysis was performed on working copies only.")


if __name__ == "__main__":
    main()
