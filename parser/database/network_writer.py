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


def store_network_connections(
    parsed_data,
    source_file,
    case_id="NETWORK-PARSER-TEST"
):
    """Store parsed network connections in SQLite."""

    source_file = Path(source_file)
    metadata = parsed_data["metadata"]
    connections = parsed_data["connections"]

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
                        'DELETE FROM "Network_Connection" WHERE artifactID = ?',
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
            "Network Parser Test",
            "Test case for Network Parser database integration",
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
            "network_parser",
            metadata.get("source_tool"),
            metadata.get("collected_at_utc"),
            "UTC",
            "hash_calculated"
        ))

        evidence_id = cursor.lastrowid

        # Store each connection as an Artifact + Network_Connection
        for network in connections:

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
                "network_connection",
                metadata.get("collected_at_utc"),
                "UTC",
                metadata.get("collected_at_utc"),
                (
                    f"{network.get('protocol')} connection "
                    f"{network.get('local_ip')}:{network.get('local_port')} "
                    f"-> {network.get('remote_ip')}:{network.get('remote_port')}"
                ),
                json.dumps(network, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat()
            ))

            artifact_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO "Network_Connection" (
                    artifactID, protocol,
                    local_ip, local_port,
                    remote_ip, remote_port,
                    connection_state, process_pid,
                    process_name, is_listening
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id,
                network.get("protocol"),
                network.get("local_ip"),
                network.get("local_port"),
                network.get("remote_ip"),
                network.get("remote_port"),
                network.get("connection_state"),
                network.get("process_pid"),
                network.get("process_name"),
                network.get("is_listening")
            ))

        connection.commit()

        return {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "connections_stored": len(connections),
            "sha256": file_hash
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()