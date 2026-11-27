import sys
import sqlite3
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIR = PROJECT_ROOT / "parser"

sys.path.insert(0, str(PARSER_DIR))

from network_parser import parse_network
from database import db
from database.network_writer import store_network_connections

SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "network_sample.json"


def test_store_network_connections_in_database(tmp_path, monkeypatch):

    temporary_db = tmp_path / "test_forensics.db"

    monkeypatch.setattr(db, "DATABASE_PATH", temporary_db)

    db.initialize_database()

    parsed_data = parse_network(SAMPLE_FILE)

    result = store_network_connections(
        parsed_data,
        source_file=SAMPLE_FILE,
        case_id="NETWORK-WRITER-TEST"
    )

    connection = sqlite3.connect(temporary_db)

    try:
        network_count = connection.execute(
            'SELECT COUNT(*) FROM "Network_Connection"'
        ).fetchone()[0]

        artifact_count = connection.execute(
            'SELECT COUNT(*) FROM "Artifact"'
        ).fetchone()[0]

        evidence_count = connection.execute(
            'SELECT COUNT(*) FROM "Evidence_File"'
        ).fetchone()[0]

        case_count = connection.execute(
            'SELECT COUNT(*) FROM "Case" WHERE caseID = ?',
            ("NETWORK-WRITER-TEST",)
        ).fetchone()[0]

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    finally:
        connection.close()

    assert result["connections_stored"] == 126
    assert network_count == 126
    assert artifact_count == 126
    assert evidence_count == 1
    assert case_count == 1
    assert foreign_key_errors == []

    expected_hash = hashlib.sha256(
        SAMPLE_FILE.read_bytes()
    ).hexdigest()

    assert result["sha256"] == expected_hash