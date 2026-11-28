import sqlite3
import json
import hashlib
from pathlib import Path

from parser.persistence_parser import parse_persistence_file
from parser.database.persistence_writer import store_persistence_artifacts


def test_persistence_writer(tmp_path, monkeypatch):

    db_path = tmp_path / "test_forensics.db"

    def fake_get_connection():
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    monkeypatch.setattr(
        "parser.database.persistence_writer.get_connection",
        fake_get_connection
    )

    schema_path = Path("parser/database/schema.sql")

    with sqlite3.connect(db_path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))

    source_file = Path("sample_data/persistence_sample.json")

    parsed_data = parse_persistence_file(source_file)

    result = store_persistence_artifacts(
        parsed_data,
        source_file
    )

    assert result["artifacts_stored"] == 30
    assert result["registry_stored"] == 27
    assert result["startup_stored"] == 3

    with sqlite3.connect(db_path) as connection:

        artifact_count = connection.execute(
            'SELECT COUNT(*) FROM "Artifact"'
        ).fetchone()[0]

        persistence_count = connection.execute(
            'SELECT COUNT(*) FROM "Persistence_Artifact"'
        ).fetchone()[0]

        registry_count = connection.execute("""
            SELECT COUNT(*)
            FROM "Persistence_Artifact"
            WHERE persistence_type = 'registry'
        """).fetchone()[0]

        startup_count = connection.execute("""
            SELECT COUNT(*)
            FROM "Persistence_Artifact"
            WHERE persistence_type = 'startup'
        """).fetchone()[0]

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    assert artifact_count == 30
    assert persistence_count == 30
    assert registry_count == 27
    assert startup_count == 3
    assert foreign_key_errors == []