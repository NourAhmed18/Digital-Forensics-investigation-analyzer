import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from .db import get_connection


def calculate_sha256(file_path):
    """Calculate SHA256 hash of the source evidence file."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def store_persistence_artifacts(
    parsed_data,
    source_file,
    case_id="PERSISTENCE-PARSER-TEST"
):
    """Store parsed persistence artifacts in SQLite."""

    source_file = Path(source_file)
    metadata = parsed_data["metadata"]
    artifacts = parsed_data["artifacts"]

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Clean up previous test case if it exists
        existing_case = cursor.execute(
            'SELECT caseID FROM "Case" WHERE caseID = ?',
            (case_id,)
        ).fetchone()

        if existing_case:
            evidence_ids = cursor.execute(
                'SELECT evidenceID FROM "Evidence_File" WHERE caseID = ?',
                (case_id,)
            ).fetchall()

            for (evidence_id,) in evidence_ids:
                artifact_ids = cursor.execute(
                    'SELECT artifactID FROM "Artifact" WHERE evidenceID = ?',
                    (evidence_id,)
                ).fetchall()

                for (artifact_id,) in artifact_ids:
                    cursor.execute(
                        'DELETE FROM "Persistence_Artifact" '
                        'WHERE artifactID = ?',
                        (artifact_id,)
                    )

                    cursor.execute(
                        'DELETE FROM "Artifact" WHERE artifactID = ?',
                        (artifact_id,)
                    )

                cursor.execute(
                    'DELETE FROM "Evidence_File" WHERE evidenceID = ?',
                    (evidence_id,)
                )

            cursor.execute(
                'DELETE FROM "Case" WHERE caseID = ?',
                (case_id,)
            )

        # Create Case
        cursor.execute("""
            INSERT INTO "Case" (
                caseID, case_name, description, hostname,
                os_name, os_version, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            "Persistence Parser Test",
            "Test case for Persistence Parser database integration",
            None,
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
            "testing"
        ))

        # Calculate evidence integrity hash
        file_hash = calculate_sha256(source_file)
        file_size = source_file.stat().st_size

        # Create Evidence File
        cursor.execute("""
            INSERT INTO "Evidence_File" (
                caseID, file_name, original_path, stored_path,
                file_type, file_size, sha256_hash,
                source_module, acquisition_tool,
                acquired_at, timezone, integrity_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            source_file.name,
            str(source_file),
            str(source_file),
            "JSON",
            file_size,
            file_hash,
            "persistence_parser",
            metadata.get("source_tool"),
            metadata.get("collected_at_utc"),
            "UTC",
            "hash_calculated"
        ))

        evidence_id = cursor.lastrowid

        # Store each persistence record
        for item in artifacts:

            timestamp = item.get("timestamp")

            if item["persistence_type"] == "registry":
                description = (
                    f"Registry persistence: "
                    f"{item.get('hive')}\\"
                    f"{item.get('registry_path')} - "
                    f"{item.get('entry_name')}"
                )

            else:
                description = (
                    f"Startup item: "
                    f"{item.get('startup_name')} - "
                    f"{item.get('classification')}"
                )

            # Create Artifact
            cursor.execute("""
                INSERT INTO "Artifact" (
                    evidenceID, artifact_type,
                    original_timestamp, original_timezone,
                    timestamp_utc, event_description,
                    raw_record, parsed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id,
                "persistence",
                timestamp,
                "UTC",
                timestamp,
                description,
                json.dumps(item.get("raw_record"), ensure_ascii=False),
                datetime.now(timezone.utc).isoformat()
            ))

            artifact_id = cursor.lastrowid

            # Create Persistence_Artifact record
            cursor.execute("""
                INSERT INTO "Persistence_Artifact" (
                    artifactID, persistence_type,
                    hive, registry_path, registry_view,
                    entry_name, entry_value, value_type,
                    scope, startup_folder, startup_path,
                    startup_name, is_directory,
                    classification, size_bytes,
                    modified_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id,
                item.get("persistence_type"),

                item.get("hive"),
                item.get("registry_path"),
                item.get("registry_view"),
                item.get("entry_name"),
                item.get("entry_value"),
                item.get("value_type"),

                item.get("scope"),
                item.get("startup_folder"),
                item.get("startup_path"),
                item.get("startup_name"),
                item.get("is_directory"),
                item.get("classification"),
                item.get("size_bytes"),
                item.get("modified_at_utc")
            ))

        connection.commit()

        return {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "artifacts_stored": len(artifacts),
            "registry_stored": sum(
                1 for item in artifacts
                if item["persistence_type"] == "registry"
            ),
            "startup_stored": sum(
                1 for item in artifacts
                if item["persistence_type"] == "startup"
            ),
            "sha256": file_hash
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()