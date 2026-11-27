import json
import hashlib
import sqlite3
from pathlib import Path


def calculate_sha256(file_path):
    """Calculate SHA-256 hash without loading the whole file into memory."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def check_sqlite_integrity(db_path):
    """Independently check the integrity of a SQLite evidence copy."""
    try:
        connection = sqlite3.connect(
            Path(db_path).resolve().as_uri() + "?mode=ro",
            uri=True
        )
        try:
            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            return result is not None and result[0] == "ok"
        finally:
            connection.close()

    except (sqlite3.Error, OSError):
        return False


def get_artifact_entries(metadata):
    artifacts = metadata.get("artifacts", [])

    if isinstance(artifacts, dict):
        entries = []
        for name, details in artifacts.items():
            if isinstance(details, dict):
                entry = details.copy()
                entry.setdefault("artifact_name", name)
                entries.append(entry)
        return entries

    if isinstance(artifacts, list):
        return artifacts

    return []


def resolve_artifact_path(file_path, metadata_path):
    path = Path(file_path)

    if path.is_absolute():
        return path

    # First, check relative to the project working directory
    project_path = Path.cwd() / path

    if project_path.is_file():
        return project_path

    # Otherwise, check relative to the metadata directory
    metadata_path = Path(metadata_path)
    metadata_relative_path = metadata_path.parent / path

    return metadata_relative_path

def verify_artifacts(metadata, metadata_path):
    """Verify artifact existence and SHA-256 values."""
    results = []

    for artifact in get_artifact_entries(metadata):
        artifact_name = artifact.get("artifact_name", "Unknown")
        artifact_path = artifact.get("collected_path") or artifact.get("path")
        expected_hash = artifact.get("sha256")

        if not artifact_path:
            results.append({
                "name": artifact_name,
                "status": "missing_path"
            })
            continue

        path = resolve_artifact_path(artifact_path, metadata_path)

        if not path.is_file():
            results.append({
                "name": artifact_name,
                "status": "missing_file",
                "path": str(path)
            })
            continue

        actual_hash = calculate_sha256(path)

        if not expected_hash:
            status = "hash_not_recorded"
        elif actual_hash.lower() == expected_hash.lower():
            status = "verified"
        else:
            status = "hash_mismatch"

        results.append({
            "name": artifact_name,
            "status": status,
            "path": str(path),
            "sha256": actual_hash
        })

    return results



def analyze_browser_profile(metadata_path):
    metadata_path = Path(metadata_path)
    metadata = load_json(metadata_path)

    browser = metadata.get("browser", "Unknown")
    profile = metadata.get("profile_name", "Default / Not specified")

    if isinstance(metadata.get("user"), dict):
        username = metadata["user"].get("username")
    else:
        username = None

    history_path = metadata_path.parent / "history.json"
    downloads_path = metadata_path.parent / "downloads.json"

    history_count = None
    downloads_count = None
    errors = []

    if history_path.is_file():
        try:
            history_count = len(load_json(history_path))
        except (json.JSONDecodeError, OSError) as error:
            errors.append(f"History JSON error: {error}")
    else:
        errors.append("history.json missing")

    if downloads_path.is_file():
        try:
            downloads_count = len(load_json(downloads_path))
        except (json.JSONDecodeError, OSError) as error:
            errors.append(f"Downloads JSON error: {error}")
    else:
        errors.append("downloads.json missing")

    artifact_results = verify_artifacts(metadata, metadata_path)

    integrity_recorded = metadata.get("integrity_verified")

    sqlite_entry = next(
        (
            item for item in get_artifact_entries(metadata)
            if item.get("artifact_name") in ("History", "places.sqlite")
        ),
        None
    )

    sqlite_verified = None

    if sqlite_entry:
        sqlite_path = (
            sqlite_entry.get("collected_path")
            or sqlite_entry.get("path")
        )

        if sqlite_path:
            sqlite_path = resolve_artifact_path(
                sqlite_path,
                metadata_path
            )

            if sqlite_path.is_file():
                sqlite_verified = check_sqlite_integrity(sqlite_path)
            else:
                errors.append(
                    f"SQLite evidence file missing: {sqlite_path}"
                )
        else:
            errors.append("SQLite artifact path not recorded")
    else:
        errors.append("SQLite artifact not found in metadata")

    return {
        "browser": browser,
        "username": username or "Not specified",
        "profile": profile,
        "history_records": history_count,
        "download_records": downloads_count,
        "integrity_recorded": integrity_recorded,
        "sqlite_integrity_check": sqlite_verified,
        "artifact_verification": artifact_results,
        "errors": errors
    }


def generate_browser_report(metadata_paths):
    report = []

    for metadata_path in metadata_paths:
        try:
            report.append(
                analyze_browser_profile(metadata_path)
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            report.append({
                "metadata_path": str(metadata_path),
                "errors": [str(error)]
            })

    return report


def print_browser_report(report):
    print("\n========== BROWSER FORENSICS REPORT ==========\n")

    total_history = 0
    total_downloads = 0

    for item in report:
        print("-" * 55)
        print("Browser:", item.get("browser", "Unknown"))
        print("User:", item.get("username", "Unknown"))
        print("Profile:", item.get("profile", "Unknown"))
        print("History:", item.get("history_records"))
        print("Downloads:", item.get("download_records"))

        print(
            "Recorded integrity:",
            item.get("integrity_recorded")
        )
        print(
            "Independent SQLite check:",
            item.get("sqlite_integrity_check")
        )

        if isinstance(item.get("history_records"), int):
            total_history += item["history_records"]

        if isinstance(item.get("download_records"), int):
            total_downloads += item["download_records"]

        print("\nArtifact verification:")

        for artifact in item.get("artifact_verification", []):
            print(
                "  ",
                artifact["name"],
                "->",
                artifact["status"]
            )

        for error in item.get("errors", []):
            print("ERROR:", error)

    print("\n" + "=" * 55)
    print("TOTAL HISTORY RECORDS:", total_history)
    print("TOTAL DOWNLOAD RECORDS:", total_downloads)
    print("PROFILES IN REPORT:", len(report))
    print("=" * 55)


if __name__ == "__main__":
    metadata_files = [
        Path(
            "test_output/Browser-Parsing-Test/"
            "historical_artifacts/browser/chrome/"
            "collection_metadata.json"
        ),
        Path(
            "test_output/Browser-Parsing-Edge-Test/"
            "historical_artifacts/browser/edge/"
            "collection_metadata.json"
        ),
        Path(
            "test_output/Browser-Parsing-Firefox-Final-Test/"
            "historical_artifacts/browser/firefox/DELL/"
            "axmdn7r2.default-release/collection_metadata.json"
        )
    ]

    report = generate_browser_report(metadata_files)
    print_browser_report(report)