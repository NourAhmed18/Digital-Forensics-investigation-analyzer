import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from event_logs_browser.common.hashing import calculate_sha256


def create_sqlite_snapshot(
    source_db: Path,
    destination_db: Path
) -> None:
    """
    Create a consistent SQLite snapshot using SQLite's backup API.

    The source database is opened in read-only mode.
    The original database and its WAL/SHM files are not modified.
    """

    if not source_db.is_file():
        raise FileNotFoundError(
            f"SQLite source database not found: {source_db}"
        )

    if destination_db.exists():
        raise FileExistsError(
            f"Snapshot already exists: {destination_db}"
        )

    source_connection = None
    destination_connection = None

    try:
        source_uri = f"{source_db.resolve().as_uri()}?mode=ro"

        source_connection = sqlite3.connect(
            source_uri,
            uri=True
        )

        destination_connection = sqlite3.connect(
            str(destination_db)
        )

        # Create a consistent snapshot, including committed WAL data
        source_connection.backup(destination_connection)

    except Exception:
        if destination_connection is not None:
            destination_connection.close()
            destination_connection = None

        if destination_db.exists():
            destination_db.unlink()

        raise

    finally:
        if destination_connection is not None:
            destination_connection.close()

        if source_connection is not None:
            source_connection.close()


def collect_chrome_artifacts(
    source_db: str,
    case_dir: str,
    browser_profile: str | None = None
) -> dict:
    """
    Collect Chrome browsing history and download records.

    A consistent SQLite snapshot is created before extraction.
    The original Chrome database is never intentionally modified.
    """

    source = Path(source_db)

    if not source.is_file():
        raise FileNotFoundError(
            f"Chrome History database not found: {source_db}"
        )

    output_dir = (
        Path(case_dir)
        / "historical_artifacts"
        / "browser"
        / "chrome"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence_copy = evidence_dir / "History"

    history_path = output_dir / "history.json"
    downloads_path = output_dir / "downloads.json"
    metadata_path = output_dir / "collection_metadata.json"

    # Do not overwrite previously collected evidence
    output_files = [
        evidence_copy,
        history_path,
        downloads_path,
        metadata_path,
    ]

    for file_path in output_files:
        if file_path.exists():
            raise FileExistsError(
                f"Output already exists: {file_path}"
            )


    # Calculate source hash before collection
    source_hash_before = calculate_sha256(
        str(source)
    )
    # Create a consistent SQLite snapshot
    create_sqlite_snapshot(
        source,
        evidence_copy
    )
    # Calculate source hash after collection
    source_hash_after = calculate_sha256(
        str(source)
    )
    # Verify that the original database was not modified
    source_unchanged = (
        source_hash_before == source_hash_after
    )

    # Calculate the hash of the collected snapshot
    snapshot_hash = calculate_sha256(
        str(evidence_copy)
    )

    connection = sqlite3.connect(
        f"{evidence_copy.resolve().as_uri()}?mode=ro",
        uri=True
    )

    connection.row_factory = sqlite3.Row

    try:
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise ValueError(
                f"SQLite integrity check failed: {integrity}"
            )

        # Extract browsing history
        history_rows = connection.execute("""
            SELECT
                id,
                url,
                title,
                visit_count,
                typed_count,
                last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
        """).fetchall()

        history = [
            {
                **dict(row),
                "browser_profile": browser_profile
            }
    for row in history_rows
        ]

        # Extract download records
        download_rows = connection.execute("""
            SELECT
                id,
                guid,
                current_path,
                target_path,
                start_time,
                end_time,
                received_bytes,
                total_bytes,
                state,
                danger_type,
                interrupt_reason,
                mime_type,
                original_mime_type
            FROM downloads
            ORDER BY start_time DESC
        """).fetchall()

        downloads = [
            {
                **dict(row),
                "browser_profile": browser_profile
            }
            for row in download_rows
        ]

    finally:
        connection.close()

    collection_timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    # Save structured records
    history_path.write_text(
        json.dumps(
            history,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    downloads_path.write_text(
        json.dumps(
            downloads,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    result = {
        "browser": "Google Chrome",
        "browser_profile": browser_profile,
        "collection_timestamp": collection_timestamp,
        "collection_timestamp_utc": collection_timestamp,
        "source_path": str(source.resolve()),
        "evidence_copy_path": str(evidence_copy.resolve()),
        "collection_method": "SQLite Backup API",
        "timestamp_format": {
            "format": "WebKit Timestamp",
            "unit": "microseconds",
            "epoch": "1601-01-01 00:00:00 UTC",
            "timezone": "UTC",
            "normalization": "Raw timestamps are preserved. UTC datetime conversion is handled by the Parser module."
        },
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "source_unchanged": source_unchanged,
        "snapshot_sha256": snapshot_hash,
        "integrity_verified": True,
        "history_records": len(history),
        "download_records": len(downloads),
        "artifacts": [
            {
                "artifact_name": "History",
                "artifact_type": "Chrome SQLite Snapshot",
                "source_path": str(source.resolve()),
                "collected_path": str(evidence_copy.resolve()),
                "original_file_format": ".sqlite",
                "sha256": snapshot_hash,
                "collection_tool": "Chrome Browser Collector",
            },
            {
                "artifact_name": "history.json",
                "artifact_type": "Browser History Records",
                "source_path": str(evidence_copy.resolve()),
                "collected_path": str(history_path.resolve()),
                "original_file_format": ".json",
                "sha256": calculate_sha256(str(history_path)),
            },
            {
                "artifact_name": "downloads.json",
                "artifact_type": "Browser Download Records",
                "source_path": str(evidence_copy.resolve()),
                "collected_path": str(downloads_path.resolve()),
                "original_file_format": ".json",
                "sha256": calculate_sha256(str(downloads_path)),
            },
        ],
    }

    metadata_path.write_text(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return result

def collect_all_chrome_profiles(
    vss_user_data_dir: str,
    case_dir: str
) -> dict:
    """
    Collect Chrome history and download records
    from all profiles acquired through VSS.
    """

    source_root = Path(vss_user_data_dir)

    if not source_root.is_dir():
        raise FileNotFoundError(
            f"Chrome VSS profiles directory not found: {source_root}"
        )

    # Discover all profiles containing a History database.
    profiles = sorted(
        [
            profile
            for profile in source_root.iterdir()
            if profile.is_dir()
            and (profile / "History").is_file()
        ],
        key=lambda profile: profile.name.lower()
    )

    if not profiles:
        raise FileNotFoundError(
            "No Chrome profiles containing History databases were found."
        )

    output_root = Path(case_dir) / "All_Profiles"

    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty: {output_root}"
        )

    output_root.mkdir(parents=True, exist_ok=True)

    results = []

    for profile in profiles:
        profile_name = profile.name
        source_db = profile / "History"

        profile_case_dir = output_root / profile_name

        result = collect_chrome_artifacts(
            str(source_db),
            str(profile_case_dir),
            browser_profile=profile_name
        )

        results.append({
            "browser_profile": profile_name,
            "history_records": result["history_records"],
            "download_records": result["download_records"],
            "integrity_verified": result["integrity_verified"],
            "metadata_path": str(
                profile_case_dir
                / "historical_artifacts"
                / "browser"
                / "chrome"
                / "collection_metadata.json"
            )
        })

    summary = {
        "browser": "Google Chrome",
        "profiles_discovered": len(profiles),
        "profiles_collected": len(results),
        "total_history_records": sum(
            item["history_records"] for item in results
        ),
        "total_download_records": sum(
            item["download_records"] for item in results
        ),
        "integrity_verified": all(
            item["integrity_verified"] for item in results
        ),
        "profiles": results
    }

    summary_path = output_root / "summary.json"

    summary_path.write_text(
        json.dumps(
            summary,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return {
        **summary,
        "summary_path": str(summary_path.resolve())
    }