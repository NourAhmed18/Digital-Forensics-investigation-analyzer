import sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIR = PROJECT_ROOT / "parser"

sys.path.insert(0, str(PARSER_DIR))

from process_parser import parse_processes


SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "processes_sample.json"


def test_parse_real_sample():
    result = parse_processes(SAMPLE_FILE)

    assert result["metadata"]["artifact_type"] == "processes"
    assert len(result["processes"]) == 288


def test_cmdline_list_is_converted_to_string(tmp_path):
    sample = {
        "artifact_type": "processes",
        "processes": [
            {
                "pid": 10,
                "cmdline": ["python", "app.py"],
            }
        ],
    }

    file_path = tmp_path / "processes.json"
    file_path.write_text(json.dumps(sample), encoding="utf-8")

    result = parse_processes(file_path)

    assert result["processes"][0]["command_line"] == "python app.py"


def test_missing_values_are_handled(tmp_path):
    sample = {
        "artifact_type": "processes",
        "processes": [
            {
                "pid": 20,
                "name": "test.exe",
            }
        ],
    }

    file_path = tmp_path / "processes.json"
    file_path.write_text(json.dumps(sample), encoding="utf-8")

    result = parse_processes(file_path)

    process = result["processes"][0]

    assert process["pid"] == 20
    assert process["process_name"] == "test.exe"
    assert process["username"] is None
    assert process["command_line"] is None


def test_invalid_artifact_type_is_rejected(tmp_path):
    sample = {
        "artifact_type": "network",
        "processes": [],
    }

    file_path = tmp_path / "invalid.json"
    file_path.write_text(json.dumps(sample), encoding="utf-8")

    try:
        parse_processes(file_path)
    except ValueError:
        pass
    else:
        assert False, "Parser should reject invalid artifact type"