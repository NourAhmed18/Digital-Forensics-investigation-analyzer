import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from event_logs_browser.common.hashing import calculate_sha256


def create_sqlite_snapshot(source_db: Path, destination_db: Path):
    """
    Create a consistent SQLite snapshot without modifying the original database.
    """
    source_db = Path(source_db)
    destination_db = Path(destination_db)

    if not source_db.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")

    if destination_db.exists():
        raise FileExistsError(
            f"Snapshot already exists: {destination_db}"
        )

    destination_db.parent.mkdir(parents=True, exist_ok=True)

    source_connection = None
    destination_connection = None

    try:
        source_uri = source_db.resolve().as_uri() + "?mode=ro"
        source_connection = sqlite3.connect(source_uri, uri=True)

        destination_connection = sqlite3.connect(destination_db)

        source_connection.backup(destination_connection)

    except Exception:
        if destination_connection:
            destination_connection.close()

        if destination_connection:
            destination_connection = None

        if destination_db.exists():
            destination_db.unlink()

        raise

    finally:
        if source_connection:
            source_connection.close()

        if destination_connection:
            destination_connection.close()

    return destination_db


def collect_edge_artifacts(
    source_db: str,
    case_dir: str,
    browser_profile: str | None = None
):
    """
    Collect Microsoft Edge browsing history and download records.
    The original database is never modified.
    """

    source_db = Path(source_db)
    case_dir = Path(case_dir)

    output_dir = (
        case_dir
        / "historical_artifacts"
        / "browser"
        / "edge"
    )

    evidence_dir = output_dir / "evidence"

    snapshot_db = evidence_dir / "History"
    history_json = output_dir / "history.json"
    downloads_json = output_dir / "downloads.json"
    metadata_json = output_dir / "collection_metadata.json"

    if not source_db.exists():
        raise FileNotFoundError(
            f"Edge History database not found: {source_db}"
        )

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Output directory already contains files: {output_dir}"
        )

    evidence_dir.mkdir(parents=True, exist_ok=True)

    create_sqlite_snapshot(source_db, snapshot_db)

    snapshot_hash = calculate_sha256(str(snapshot_db))

    connection = sqlite3.connect(
        snapshot_db.resolve().as_uri() + "?mode=ro",
        uri=True
    )

    try:
        integrity_result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity_result != "ok":
            raise sqlite3.DatabaseError(
                f"SQLite integrity check failed: {integrity_result}"
            )

        history_query = """
            SELECT
                id,
                url,
                title,
                visit_count,
                typed_count,
                last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
        """

        history_rows = connection.execute(
            history_query
        ).fetchall()

        history_records = [
            {
                "id": row[0],
                "browser_profile": browser_profile,
                "url": row[1],
                "title": row[2],
                "visit_count": row[3],
                "typed_count": row[4],
                "last_visit_time": row[5]
            }
            for row in history_rows
        ]

        downloads_query = """
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
        """

        download_rows = connection.execute(
            downloads_query
        ).fetchall()

        download_records = [
            {
                "id": row[0],
                "browser_profile": browser_profile,
                "guid": row[1],
                "current_path": row[2],
                "target_path": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "received_bytes": row[6],
                "total_bytes": row[7],
                "state": row[8],
                "danger_type": row[9],
                "interrupt_reason": row[10],
                "mime_type": row[11],
                "original_mime_type": row[12]
            }
            for row in download_rows
        ]

    finally:
        connection.close()

    with open(history_json, "w", encoding="utf-8") as file:
        json.dump(
            history_records,
            file,
            indent=4,
            ensure_ascii=False
        )

    with open(downloads_json, "w", encoding="utf-8") as file:
        json.dump(
            download_records,
            file,
            indent=4,
            ensure_ascii=False
        )

    artifacts = {}

    for artifact_path in [
        snapshot_db,
        history_json,
        downloads_json
    ]:
        artifacts[artifact_path.name] = {
            "path": str(artifact_path),
            "sha256": calculate_sha256(str(artifact_path)),
            "size_bytes": artifact_path.stat().st_size
        }

    collection_timestamp = datetime.now(timezone.utc).isoformat()

    metadata = {
        "browser": "Microsoft Edge",
        "browser_profile": browser_profile,
        "collection_tool": "Edge Browser Collector",
        "source_database": str(source_db.resolve()),
        "collection_time_utc": collection_timestamp,
        "collection_timestamp_utc": collection_timestamp,
        "collection_method": "SQLite Backup API",
        "timestamp_format": {
            "format": "WebKit Timestamp",
            "unit": "microseconds",
            "epoch": "1601-01-01 00:00:00 UTC",
            "timezone": "UTC",
            "normalization": "Raw timestamps are preserved. UTC datetime conversion is handled by the Parser module."
        },
        "snapshot_database": str(snapshot_db),
        "snapshot_sha256": snapshot_hash,
        "integrity_verified": integrity_result == "ok",
        "history_records": len(history_records),
        "download_records": len(download_records),
        "artifacts": artifacts
    }

    with open(metadata_json, "w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    return {
        "browser": "Microsoft Edge",
        "browser_profile": browser_profile,
        "history_records": len(history_records),
        "download_records": len(download_records),
        "integrity_verified": integrity_result == "ok",
        "artifacts": artifacts,
        "metadata": str(metadata_json)
    }


def collect_all_edge_profiles(vss_user_data_dir: str, case_dir: str):
    """
    Collect Edge History databases from all browser profiles
    available in a VSS-acquired User Data directory.
    Each profile is collected separately.
    """

    vss_user_data_dir = Path(vss_user_data_dir)
    case_dir = Path(case_dir)

    if not vss_user_data_dir.exists() or not vss_user_data_dir.is_dir():
        raise FileNotFoundError(
            f"Edge User Data directory not found: {vss_user_data_dir}"
        )

    # Find browser profiles containing a History database.
    profiles = sorted(
        [
            profile_dir
            for profile_dir in vss_user_data_dir.iterdir()
            if profile_dir.is_dir()
            and (profile_dir / "History").is_file()
        ],
        key=lambda path: path.name.lower()
    )

    if not profiles:
        raise FileNotFoundError(
            f"No Edge profiles with History databases found in: "
            f"{vss_user_data_dir}"
        )

    output_root = case_dir / "All_Profiles"

    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(
            f"Output directory already contains files: {output_root}"
        )

    output_root.mkdir(parents=True, exist_ok=True)

    results = []

    for profile_dir in profiles:
        profile_name = profile_dir.name
        source_db = profile_dir / "History"

        profile_case_dir = output_root / profile_name

        print(f"Collecting Edge profile: {profile_name}")

        result = collect_edge_artifacts(
            str(source_db),
            str(profile_case_dir),
            browser_profile=profile_name
        )

        results.append({
            "browser_profile": profile_name,
            "history_records": result["history_records"],
            "download_records": result["download_records"],
            "integrity_verified": result["integrity_verified"],
            "metadata": result["metadata"]
        })

    summary = {
        "browser": "Microsoft Edge",
        "collection_method": "Windows Volume Shadow Copy",
        "source_user_data_directory": str(vss_user_data_dir.resolve()),
        "profiles_discovered": len(profiles),
        "profiles_collected": len(results),
        "total_history_records": sum(
            item["history_records"] for item in results
        ),
        "total_download_records": sum(
            item["download_records"] for item in results
        ),
        "all_profiles_integrity_verified": all(
            item["integrity_verified"] for item in results
        ),
        "profiles": results
    }

    summary_path = output_root / "summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            indent=4,
            ensure_ascii=False
        )

    return summary
