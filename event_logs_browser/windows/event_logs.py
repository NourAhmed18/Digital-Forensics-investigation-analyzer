
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from event_logs_browser.common.hashing import calculate_sha256


DEFAULT_LOGS = [
    "Security",
    "System",
    "Application",
]


def collect_windows_event_logs(
    case_dir: str,
    channels: list[str] | None = None
) -> dict:
    """
    Export Windows Event Logs into the case directory.

    Original Windows Event Logs are not modified.
    Each exported EVTX file is verified using SHA-256.
    """

    if channels is None:
        channels = DEFAULT_LOGS

    if not channels:
        raise ValueError("At least one event log channel is required.")

    case_path = Path(case_dir)

    output_dir = (
        case_path
        / "historical_artifacts"
        / "event_logs"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for channel in channels:

        safe_name = channel.replace("/", "_").replace("\\", "_")
        destination = output_dir / f"{safe_name}.evtx"

        artifact_result = {
            "artifact_name": destination.name,
            "artifact_type": "Windows Event Log",
            "source_channel": channel,
            "source_path": f"Windows Event Log: {channel}",
            "collected_path": str(destination.resolve()),
            "collection_timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "original_file_format": ".evtx",
            "collection_tool": "wevtutil",
        }

        # Tracks whether this collection attempt created the file
        destination_created = False

        try:
            # Never overwrite existing evidence
            if destination.exists():
                raise FileExistsError(
                    f"Destination already exists: {destination}"
                )

            command = [
                "wevtutil",
                "epl",
                channel,
                str(destination),
                "/ow:false",
            ]

            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )

            destination_created = True

            artifact_result["size_bytes"] = destination.stat().st_size

            artifact_result["sha256"] = calculate_sha256(
                str(destination)
            )

            artifact_result["status"] = "success"

        except (subprocess.CalledProcessError, OSError) as error:

            artifact_result["status"] = "failed"
            artifact_result["error"] = str(error)

            # Remove only a partial file created by this attempt
            if destination_created and destination.exists():
                try:
                    destination.unlink()
                except OSError as cleanup_error:
                    artifact_result["cleanup_error"] = str(
                        cleanup_error
                    )

        results.append(artifact_result)

    metadata_path = output_dir / "event_logs_metadata.json"

    metadata = {
        "collection_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "collection_tool": "Windows Event Logs Collector",
        "total_channels": len(channels),
        "successful_collections": sum(
            item["status"] == "success" for item in results
        ),
        "failed_collections": sum(
            item["status"] == "failed" for item in results
        ),
        "artifacts": results,
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=4),
        encoding="utf-8",
    )

    return metadata
