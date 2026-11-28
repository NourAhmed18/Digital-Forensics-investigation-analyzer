import sys
import sqlite3
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIR = PROJECT_ROOT / "parser"

sys.path.insert(0, str(PARSER_DIR))

from process_parser import parse_processes
from database import db
from database.process_writer import store_processes


SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "processes_sample.json"


def test_store_processes_in_database(tmp_path, monkeypatch):
    # Use a temporary database instead of the project's real database
    temporary_db = tmp_path / "test_forensics.db"
    monkeypatch.setattr(db, "DATABASE_PATH", temporary_db)

    # Initialize the temporary database
    db.initialize_database()

    # Parse sample data
    parsed_data = parse_processes(SAMPLE_FILE)

    # Store parsed processes
    result = store_processes(
        parsed_data,
        source_file=SAMPLE_FILE,
        case_id="WRITER-TEST"
    )

    # Verify database contents
    connection = sqlite3.connect(temporary_db)

    try:
        process_count = connection.execute(
            'SELECT COUNT(*) FROM "Process"'
        ).fetchone()[0]

        artifact_count = connection.execute(
            'SELECT COUNT(*) FROM "Artifact"'
        ).fetchone()[0]

        evidence_count = connection.execute(
            'SELECT COUNT(*) FROM "Evidence_File"'
        ).fetchone()[0]

        case_count = connection.execute(
            'SELECT COUNT(*) FROM "Case" WHERE caseID = ?',
            ("WRITER-TEST",)
        ).fetchone()[0]

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    finally:
        connection.close()

    # Assertions
    assert result["processes_stored"] == 288
    assert process_count == 288
    assert artifact_count == 288
    assert evidence_count == 1
    assert case_count == 1
    assert foreign_key_errors == []

    # Verify source file hash
    expected_hash = hashlib.sha256(
        SAMPLE_FILE.read_bytes()
    ).hexdigest()

    assert result["sha256"] == expected_hash