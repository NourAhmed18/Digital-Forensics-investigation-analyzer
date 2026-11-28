
from pathlib import Path
from datetime import datetime, timezone

from .hashing import calculate_sha256


def create_artifact_metadata(
    source_path: str,
    collected_path: str,
    artifact_type: str,
    collection_tool: str
) -> dict:

    source = Path(source_path)
    collected = Path(collected_path)

    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    if not collected.is_file():
        raise FileNotFoundError(f"Collected file not found: {collected_path}")

    return {
        "artifact_name": collected.name,
        "artifact_type": artifact_type,
        "source_path": str(source.resolve()),
        "collected_path": str(collected.resolve()),
        "collection_timestamp": datetime.now(timezone.utc).isoformat(),
        "original_file_format": collected.suffix,
        "size_bytes": collected.stat().st_size,
        "sha256": calculate_sha256(str(collected)),
        "collection_tool": collection_tool,
    }



import json


def save_metadata_json(metadata: dict, output_path: str) -> str:
    """
    Save artifact metadata as a JSON file.
    Never overwrite an existing metadata file.
    """

    output = Path(output_path)

    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists():
        raise FileExistsError(
            f"Metadata file already exists: {output}"
        )

    with output.open("x", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    return str(output.resolve())