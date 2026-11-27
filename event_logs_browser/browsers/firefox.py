
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from event_logs_browser.common.hashing import calculate_sha256


def create_sqlite_snapshot(
    source_db: Path,
    destination_db: Path
) -> None:
    """Create a consistent SQLite snapshot using the Backup API."""

    if not source_db.is_file():
        raise FileNotFoundError(
            f"Firefox database not found: {source_db}"
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


def _safe_url(url):
    """Remove query parameters and fragments from exported URLs."""

    if not url:
        return url

    parts = urlsplit(url)

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        "",
        ""
    ))


def _firefox_time_to_utc(timestamp, divisor):
    """Convert Firefox Unix timestamps to UTC."""

    if timestamp is None:
        return None

    return datetime.fromtimestamp(
        timestamp / divisor,
        tz=timezone.utc
    ).isoformat()


def _extract_history(connection, profile_name=None):
    rows = connection.execute("""
        SELECT
            id,
            url,
            title,
            visit_count,
            last_visit_date
        FROM moz_places
        WHERE last_visit_date IS NOT NULL
        ORDER BY last_visit_date DESC
    """).fetchall()

    history = []

    for row in rows:
        history.append({
            "browser_profile": profile_name,
            "id": row["id"],
            "url": _safe_url(row["url"]),
            "title": row["title"],
            "visit_count": row["visit_count"],
            "last_visit_unix_us": row["last_visit_date"],
            "last_visit_utc": _firefox_time_to_utc(
                row["last_visit_date"],
                1_000_000
            )
        })

    return history


def _extract_downloads(connection, profile_name=None):
    rows = connection.execute("""
        SELECT
            p.id AS place_id,
            p.url,
            p.title,
            a.name AS annotation_name,
            an.content,
            an.dateAdded
        FROM moz_annos AS an
        JOIN moz_anno_attributes AS a
            ON an.anno_attribute_id = a.id
        LEFT JOIN moz_places AS p
            ON an.place_id = p.id
        WHERE a.name IN (
            'downloads/destinationFileURI',
            'downloads/metaData'
        )
        ORDER BY an.dateAdded DESC
    """).fetchall()

    downloads = {}

    for row in rows:
        place_id = row["place_id"]

        item = downloads.setdefault(place_id, {
            "browser": "Firefox",
            "browser_profile": profile_name,
            "url": _safe_url(row["url"]),
            "title": row["title"]
        })

        annotation = row["annotation_name"]
        content = row["content"]
        date_added = row["dateAdded"]

        if annotation == "downloads/destinationFileURI":
            item["destination"] = content
            item["destination_annotation_date_added_unix_us"] = (
                date_added
            )

        elif annotation == "downloads/metaData":
            try:
                metadata = json.loads(content)
            except (TypeError, json.JSONDecodeError):
                metadata = {}

            item["state"] = metadata.get("state")
            item["file_size"] = metadata.get("fileSize")
            item["deleted"] = metadata.get("deleted")
            item["end_time_unix_ms"] = metadata.get("endTime")

            item["metadata_annotation_date_added_unix_us"] = (
                date_added
            )

            item["end_time_utc"] = _firefox_time_to_utc(
                metadata.get("endTime"),
                1000
            )

    return list(downloads.values())


def collect_firefox_artifacts(
    source_db: str,
    case_dir: str,
    profile_name: str | None = None,
    user_name: str | None = None,
    user_sid: str | None = None
) -> dict:
    """
    Collect Firefox browsing history and download records.

    A consistent SQLite snapshot is created before extraction.
    The original database is opened read-only.
    """

    source = Path(source_db)

    if not source.is_file():
        raise FileNotFoundError(
            f"Firefox places.sqlite not found: {source_db}"
        )


    output_dir = (
        Path(case_dir)
        / "historical_artifacts"
        / "browser"
        / "firefox"
    )

    if user_name is not None:
        if (
            not user_name
            or user_name in (".", "..")
            or Path(user_name).name != user_name
        ):
            raise ValueError("Invalid Windows username")

        user_folder = user_name

        if user_sid:
            safe_sid = user_sid.replace("\\", "_").replace("/", "_")
            user_folder = f"{user_name}_{safe_sid}"

        output_dir = output_dir / user_folder

    if profile_name is not None:
        if (
            not profile_name
            or profile_name in (".", "..")
            or Path(profile_name).name != profile_name
        ):
            raise ValueError("Invalid Firefox profile name")

        output_dir = output_dir / profile_name

    output_dir.mkdir(parents=True, exist_ok=True)

    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence_copy = evidence_dir / "places.sqlite"

    history_path = output_dir / "history.json"
    downloads_path = output_dir / "downloads.json"
    metadata_path = output_dir / "collection_metadata.json"


    output_files = [
        evidence_copy,
        history_path,
        downloads_path,
        metadata_path
    ]

    for file_path in output_files:
        if file_path.exists():
            raise FileExistsError(
                f"Output already exists: {file_path}"
            )

    create_sqlite_snapshot(
        source,
        evidence_copy
    )

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

        history = _extract_history(connection, profile_name)
        downloads = _extract_downloads(connection, profile_name)

    finally:
        connection.close()

    collection_timestamp = datetime.now(
        timezone.utc
    ).isoformat()

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
        "browser": "Mozilla Firefox",

        "user": {
            "username": user_name,
            "sid": user_sid
        },
        "profile_name": profile_name,
        "browser_profile": profile_name,
        "collection_timestamp": collection_timestamp,
        "collection_timestamp_utc": collection_timestamp,
        "source_path": str(source.resolve()),
        "evidence_copy_path": str(evidence_copy.resolve()),
        "collection_method": "SQLite Backup API",
        "timestamp_format": {
        "history": {
            "format": "Unix Timestamp",
            "unit": "microseconds",
            "epoch": "1970-01-01 00:00:00 UTC",
            "timezone": "UTC",
            "raw_field": "last_visit_unix_us",
            "converted_field": "last_visit_utc"
        },
        "downloads": {
            "end_time": {
                "format": "Unix Timestamp",
                "unit": "milliseconds",
                "epoch": "1970-01-01 00:00:00 UTC",
                "timezone": "UTC",
                "raw_field": "end_time_unix_ms",
                "converted_field": "end_time_utc"
            },
            "annotation_date_added": {
                "format": "Unix Timestamp",
                "unit": "microseconds",
                "epoch": "1970-01-01 00:00:00 UTC",
                "timezone": "UTC",
                "raw_fields": [
                    "metadata_annotation_date_added_unix_us",
                    "destination_annotation_date_added_unix_us"
                ]
            }
        }
    },
        "snapshot_sha256": snapshot_hash,
        "integrity_verified": True,
        "history_records": len(history),
        "download_records": len(downloads),
        "artifacts": [
            {
                "artifact_name": "places.sqlite",
                "artifact_type": "Firefox SQLite Snapshot",
                "source_path": str(source.resolve()),
                "collected_path": str(evidence_copy.resolve()),
                "original_file_format": ".sqlite",
                "sha256": snapshot_hash,
                "collection_tool": "Firefox Browser Collector"
            },
            {
                "artifact_name": "history.json",
                "artifact_type": "Browser History Records",
                "source_path": str(evidence_copy.resolve()),
                "collected_path": str(history_path.resolve()),
                "original_file_format": ".json",
                "sha256": calculate_sha256(str(history_path))
            },
            {
                "artifact_name": "downloads.json",
                "artifact_type": "Browser Download Records",
                "source_path": str(evidence_copy.resolve()),
                "collected_path": str(downloads_path.resolve()),
                "original_file_format": ".json",
                "sha256": calculate_sha256(str(downloads_path))
            }
        ]
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


def collect_all_firefox_profiles(
    firefox_profiles_dir: str,
    case_dir: str,
    user_name: str | None = None,
    user_sid: str | None = None
) -> dict:
    """
    Collect Firefox artifacts from all profiles in a directory.
    """

    profiles_root = Path(firefox_profiles_dir)

    if not profiles_root.is_dir():
        raise NotADirectoryError(
            f"Firefox profiles directory not found: {firefox_profiles_dir}"
        )

    profile_dirs = sorted(
        [
            profile_dir
            for profile_dir in profiles_root.iterdir()
            if profile_dir.is_dir()
            and (profile_dir / "places.sqlite").is_file()
        ],
        key=lambda path: path.name.lower()
    )

    if not profile_dirs:
        raise FileNotFoundError(
            f"No Firefox profiles containing places.sqlite found in: {profiles_root}"
        )

    output_root = (
        Path(case_dir)
        / "historical_artifacts"
        / "browser"
        / "firefox"
    )

    if user_name:
        user_folder = user_name

        if user_sid:
            safe_sid = user_sid.replace("\\", "_").replace("/", "_")
            user_folder = f"{user_name}_{safe_sid}"

        output_root = output_root / user_folder

    output_root.mkdir(parents=True, exist_ok=True)

    summary = {
        "browser": "Mozilla Firefox",
        "profiles_discovered": len(profile_dirs),
        "profiles_collected": 0,
        "total_history_records": 0,
        "total_download_records": 0,
        "integrity_verified": True,
        "profiles": []
    }

    for profile_dir in profile_dirs:

        source_db = profile_dir / "places.sqlite"

        result = collect_firefox_artifacts(
            str(source_db),
            case_dir,
            profile_name=profile_dir.name,
            user_name=user_name,
            user_sid=user_sid
        )

        profile_result = {
            "browser_profile": profile_dir.name,
            "history_records": result["history_records"],
            "download_records": result["download_records"],
            "integrity_verified": result["integrity_verified"],
            "metadata_path": str(
                output_root
                / profile_dir.name
                / "collection_metadata.json"
            )
        }

        summary["profiles"].append(profile_result)
        summary["profiles_collected"] += 1
        summary["total_history_records"] += result["history_records"]
        summary["total_download_records"] += result["download_records"]

    summary_path = output_root / "summary.json"

    if summary_path.exists():
        raise FileExistsError(
            f"Summary already exists: {summary_path}"
        )

    summary["summary_path"] = str(summary_path.resolve())

    summary_path.write_text(
        json.dumps(
            summary,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return summary