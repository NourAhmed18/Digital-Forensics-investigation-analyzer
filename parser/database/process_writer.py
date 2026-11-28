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


def store_processes(parsed_data, source_file, case_id="PROCESS-PARSER-TEST"):
    """Store parsed processes in SQLite."""

    source_file = Path(source_file)
    metadata = parsed_data["metadata"]
    processes = parsed_data["processes"]

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Clean up previous test run, if any
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
                        'DELETE FROM "Process" WHERE artifactID = ?',
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

        # Create test case
        cursor.execute("""
            INSERT INTO "Case" (
                caseID, case_name, description, hostname,
                os_name, os_version, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            "Process Parser Test",
            "Test case for Process Parser database integration",
            None,
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
            "testing"
        ))

        # Register source evidence file
        file_hash = calculate_sha256(source_file)
        file_size = source_file.stat().st_size

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
            "process_parser",
            metadata.get("source_tool"),
            metadata.get("collected_at_utc"),
            "UTC",
            "hash_calculated"
        ))

        evidence_id = cursor.lastrowid

        # Store each process as an Artifact + Process record
        for process in processes:

            original_timestamp = process.get("start_time")

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
                "process",
                original_timestamp,
                "UTC" if original_timestamp else None,
                original_timestamp,
                f"Process {process.get('process_name')} (PID {process.get('pid')})",
                json.dumps(process, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat()
            ))

            artifact_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO "Process" (
                    artifactID, pid, parent_pid,
                    process_name, executable_path,
                    command_line, username, status,
                    start_time, end_time, executable_sha256
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id,
                process.get("pid"),
                process.get("parent_pid"),
                process.get("process_name"),
                process.get("executable_path"),
                process.get("command_line"),
                process.get("username"),
                process.get("status"),
                process.get("start_time"),
                process.get("end_time"),
                process.get("executable_sha256")
            ))

        connection.commit()

        return {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "processes_stored": len(processes),
            "sha256": file_hash
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()