
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = PROJECT_ROOT / "evidence" / "memory" / "memdump.mem"
OUTPUT_FILE = PROJECT_ROOT / "output" / "memory_acquisition.json"


def calculate_sha256(file_path):
    """Calculate SHA-256 without loading the whole dump into memory."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def collect_memory_metadata():
    """Verify and document an existing memory acquisition."""

    if not MEMORY_FILE.exists():
        raise FileNotFoundError(
            f"Memory dump not found: {MEMORY_FILE}"
        )

    file_info = MEMORY_FILE.stat()
    file_hash = calculate_sha256(MEMORY_FILE)

    metadata = {
        "artifact_type": "Physical Memory Dump",
        "evidence_file": str(MEMORY_FILE),
        "file_name": MEMORY_FILE.name,
        "file_size_bytes": file_info.st_size,
        "sha256": file_hash,
        "operating_system": platform.platform(),
        "acquisition_tool": "Exterro FTK Imager 8.3.0.27",
        "acquisition_method": "FTK Imager - Capture Memory",
        "source_tool": "Exterro FTK Imager",
        "collection_tool": "Python hashlib",
        "verification_timestamp_utc": datetime.now(
    timezone.utc
).isoformat(),
"acquisition_timestamp_utc": None,
        "file_last_modified": datetime.fromtimestamp(
            file_info.st_mtime,
            timezone.utc
        ).isoformat(),
        "limitations": [
            "The memory dump was acquired separately using FTK Imager.",
            "This module verifies and documents the existing dump.",
            "The dump may contain sensitive information.",
            "A hash verifies file integrity after acquisition, "
            "but does not independently prove acquisition authenticity."
        ]
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    return metadata


if __name__ == "__main__":
    try:
        result = collect_memory_metadata()

        print("Memory evidence verified successfully!")
        print(f"File: {result['file_name']}")
        print(f"Size: {result['file_size_bytes']:,} bytes")
        print(f"SHA-256: {result['sha256']}")
        print(f"Saved metadata to: {OUTPUT_FILE}")

    except (OSError, ValueError) as error:
        print(f"Memory verification failed: {error}")
