
import shutil
from pathlib import Path

from .hashing import calculate_sha256


def copy_evidence(source_path: str, destination_path: str) -> dict:
    """
    Copy an evidence file without modifying the original.
    Verify the copied file using SHA-256.
    """

    source = Path(source_path)
    destination = Path(destination_path)

    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different.")

    if destination.exists():
        raise FileExistsError(
            f"Destination already exists: {destination}"
        )

    source_hash = calculate_sha256(str(source))

    shutil.copy2(source, destination)

    copied_hash = calculate_sha256(str(destination))

    if source_hash != copied_hash:
        destination.unlink()
        raise IOError("Evidence copy integrity verification failed.")

    return {
        "source_path": str(source.resolve()),
        "destination_path": str(destination.resolve()),
        "source_sha256": source_hash,
        "copied_sha256": copied_hash,
        "integrity_verified": True
    }
