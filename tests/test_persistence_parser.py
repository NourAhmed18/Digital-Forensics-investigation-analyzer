from parser.persistence_parser import parse_persistence_file


SAMPLE_FILE = "sample_data/persistence_sample.json"


def test_persistence_total_count():
    result = parse_persistence_file(SAMPLE_FILE)
    assert len(result["artifacts"]) == 30


def test_registry_count():
    result = parse_persistence_file(SAMPLE_FILE)
    registry = [
        item for item in result["artifacts"]
        if item["persistence_type"] == "registry"
    ]
    assert len(registry) == 27


def test_startup_count():
    result = parse_persistence_file(SAMPLE_FILE)
    startup = [
        item for item in result["artifacts"]
        if item["persistence_type"] == "startup"
    ]
    assert len(startup) == 3


def test_metadata():
    result = parse_persistence_file(SAMPLE_FILE)

    assert result["metadata"]["registry_entry_count"] == 27
    assert result["metadata"]["startup_item_count"] == 3


def test_raw_record_preserved():
    result = parse_persistence_file(SAMPLE_FILE)

    assert all(
        item["raw_record"] is not None
        for item in result["artifacts"]
    )