import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIR = PROJECT_ROOT / "parser"

sys.path.insert(0, str(PARSER_DIR))

from network_parser import parse_network

SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "network_sample.json"


def test_parse_real_network_sample():
    result = parse_network(SAMPLE_FILE)

    assert result["metadata"]["artifact_type"] == "network_connections"
    assert len(result["connections"]) == 126
    assert result["metadata"]["listening_count"] == 40


def test_connection_fields_are_normalized():
    result = parse_network(SAMPLE_FILE)

    connection = result["connections"][0]

    expected_fields = {
        "protocol",
        "local_ip",
        "local_port",
        "remote_ip",
        "remote_port",
        "connection_state",
        "process_pid",
        "process_name",
        "is_listening",
    }

    assert set(connection.keys()) == expected_fields


def test_null_remote_values_are_handled():
    result = parse_network(SAMPLE_FILE)

    connections_with_null_remote = [
        connection
        for connection in result["connections"]
        if connection["remote_ip"] is None
        or connection["remote_port"] is None
    ]

    assert len(connections_with_null_remote) > 0


def test_metadata_is_preserved():
    result = parse_network(SAMPLE_FILE)

    metadata = result["metadata"]

    assert metadata["source_tool"] is not None
    assert metadata["collected_at_utc"] is not None
    assert metadata["limitations"] is not None
    assert isinstance(metadata["interfaces"], dict)


def test_invalid_artifact_type_is_rejected(tmp_path):
    invalid_file = tmp_path / "invalid_network.json"

    invalid_file.write_text(
        '{"artifact_type": "wrong_type", "connections": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        parse_network(invalid_file)