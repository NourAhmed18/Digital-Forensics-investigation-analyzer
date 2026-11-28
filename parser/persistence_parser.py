import json
from pathlib import Path


def parse_persistence_file(file_path):
    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if data.get("artifact_type") != "persistence_artifacts":
        raise ValueError("Invalid persistence artifact file")

    parsed_artifacts = []

    # Parse Registry Entries
    for entry in data.get("registry_entries", []):
        parsed_artifacts.append({
            "artifact_type": "persistence",
            "persistence_type": "registry",

            "hive": entry.get("hive"),
            "registry_path": entry.get("registry_path"),
            "registry_view": entry.get("registry_view"),
            "entry_name": entry.get("entry_name"),
            "entry_value": entry.get("entry_value"),
            "value_type": entry.get("value_type"),

            "scope": None,
            "startup_folder": None,
            "startup_path": None,
            "startup_name": None,
            "is_directory": None,
            "classification": None,
            "size_bytes": None,
            "modified_at_utc": None,

            "timestamp": entry.get("collected_at_utc"),
            "raw_record": entry,
        })

    # Parse Startup Items
    for item in data.get("startup_items", []):
        parsed_artifacts.append({
            "artifact_type": "persistence",
            "persistence_type": "startup",

            "hive": None,
            "registry_path": None,
            "registry_view": None,
            "entry_name": None,
            "entry_value": None,
            "value_type": None,

            "scope": item.get("scope"),
            "startup_folder": item.get("startup_folder"),
            "startup_path": item.get("path"),
            "startup_name": item.get("name"),
            "is_directory": item.get("is_directory"),
            "classification": item.get("classification"),
            "size_bytes": item.get("size_bytes"),
            "modified_at_utc": item.get("modified_at_utc"),

            "timestamp": item.get("collected_at_utc"),
            "raw_record": item,
        })

    metadata = {
        "source_tool": data.get("source_tool"),
        "command": data.get("command"),
        "collected_at_utc": data.get("collected_at_utc"),
        "completed_at_utc": data.get("completed_at_utc"),
        "registry_entry_count": data.get("registry_entry_count"),
        "startup_item_count": data.get("startup_item_count"),
    }

    return {
        "metadata": metadata,
        "artifacts": parsed_artifacts,
    }