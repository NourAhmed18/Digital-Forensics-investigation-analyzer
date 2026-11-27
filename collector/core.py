"""Case package creation and evidence-integrity helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .host_info import write_host_info

LOGGER = logging.getLogger("forensics.collector")


@dataclass(frozen=True)
class CollectionResult:
    case_dir: Path
    manifest_path: Path
    host_info_path: Path
    skipped_modules: tuple[str, ...]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def configure_logging(log_path: Path, verbose: bool = False) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    for handler in LOGGER.handlers[:]:
        handler.close()
        LOGGER.removeHandler(handler)
    LOGGER.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    LOGGER.addHandler(file_handler)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    LOGGER.addHandler(console)


def create_case_layout(output_dir: Path, case_id: str | None = None) -> Path:
    timestamp = utc_now().strftime("%Y%m%dT%H%M%S%fZ")
    safe_id = (case_id or f"case-{timestamp}").replace("/", "_").replace("\\", "_")
    case_dir = output_dir.expanduser().resolve() / f"{safe_id}_{timestamp}"
    for directory in ("config", "evidence/host", "evidence/modules", "metadata", "logs"):
        (case_dir / directory).mkdir(parents=True, exist_ok=False)
    return case_dir


def _copy_config(case_dir: Path, config_path: Path | None, config: dict[str, Any]) -> Path:
    destination = case_dir / "config" / "collector_config.json"
    if config_path and config_path.is_file():
        shutil.copy2(config_path, destination)
    else:
        _json_dump(destination, config)
    return destination


def build_manifest(case_dir: Path, source: str = "collector-agent") -> Path:
    records: list[dict[str, Any]] = []
    evidence_root = case_dir / "evidence"
    for path in sorted(evidence_root.rglob("*")):
        if not path.is_file():
            continue
        records.append({
            "relative_path": path.relative_to(case_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "collected_at_utc": utc_now().isoformat(),
            "source": source,
        })
    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": utc_now().isoformat(),
        "hash_algorithm": "SHA-256",
        "records": records,
    }
    path = case_dir / "metadata" / "manifest.json"
    _json_dump(path, manifest)
    return path


def collect_case(
    output_dir: Path,
    case_id: str | None = None,
    config: dict[str, Any] | None = None,
    config_path: Path | None = None,
    verbose: bool = False,
) -> CollectionResult:
    """Create a new case and run enabled, available collection modules."""
    config = config or {"schema_version": "1.0", "enabled_modules": ["host_info"]}
    case_dir = create_case_layout(output_dir, case_id)
    configure_logging(case_dir / "logs" / "collector.log", verbose=verbose)
    LOGGER.info("Starting collection case=%s", case_dir.name)

    copied_config = _copy_config(case_dir, config_path, config)
    LOGGER.info("Configuration saved to %s", copied_config.relative_to(case_dir))
    host_info_path = case_dir / "evidence" / "host" / "host_info.json"
    write_host_info(host_info_path)
    LOGGER.info("Collected host information")

    skipped: list[str] = []
    for module_name in config.get("enabled_modules", []):
        if module_name == "host_info":
            continue
        # Future modules are deliberately isolated. They can write only below evidence/modules.
        LOGGER.warning("Module '%s' is not installed; skipped", module_name)
        skipped.append(str(module_name))

    manifest_path = build_manifest(case_dir)
    LOGGER.info("Manifest created with SHA-256 hashes: %s", manifest_path.relative_to(case_dir))
    summary = {
        "schema_version": "1.0",
        "case_id": case_dir.name,
        "completed_at_utc": utc_now().isoformat(),
        "status": "completed",
        "skipped_modules": skipped,
        "manifest": manifest_path.relative_to(case_dir).as_posix(),
    }
    _json_dump(case_dir / "metadata" / "collection_summary.json", summary)
    LOGGER.info("Collection completed successfully")
    return CollectionResult(case_dir, manifest_path, host_info_path, tuple(skipped))
