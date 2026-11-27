
import os
import subprocess
from pathlib import Path

from event_logs_browser.browsers.vss_acquisition import (
    collect_all_edge_profiles_from_vss,
)


def get_existing_snapshot_device(shadow_id: str) -> str:
    """
    Get the device path of an existing VSS snapshot.
    Does not create or delete snapshots.
    """

    script = f"""
    $shadow = Get-CimInstance Win32_ShadowCopy |
        Where-Object {{ $_.ID -eq '{shadow_id}' }}

    if (-not $shadow) {{
        throw "Requested VSS snapshot was not found."
    }}

    $shadow.DeviceObject
    """

    process = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"Could not locate VSS snapshot: {process.stderr}"
        )

    device_object = process.stdout.strip()

    if not device_object:
        raise RuntimeError("VSS device path is empty.")

    return device_object


def main():

    # Use the existing retained snapshot.
    snapshot_id = "{261228FE-DF76-4523-8EB0-FFC18014363C}"

    snapshot_device = get_existing_snapshot_device(snapshot_id)

    system_drive = os.environ["SystemDrive"] + "\\"
    user_profile = os.environ["USERPROFILE"]

    profile_relative = os.path.relpath(
        user_profile,
        system_drive,
    )

    project_root = Path(__file__).resolve().parents[2]

    destination = (
        project_root
        / "test_output"
        / "Edge-VSS-Acquisition-Test-3"
    )

    print("Using existing snapshot:", snapshot_device)
    print("\nCollecting all Edge profiles...")

    result = collect_all_edge_profiles_from_vss(
        device_object=snapshot_device,
        profile_relative_path=profile_relative,
        destination_dir=str(destination),
    )

    print("\nEdge acquisition completed!")
    print("Profiles discovered:", result["profiles_discovered"])
    print("Profiles collected:", result["profiles_collected"])
    print("Files collected:", result["files_collected"])
    print("Integrity verified:", result["integrity_verified"])
    print("Metadata:", result["metadata_path"])

    for profile in result["profiles"]:

        print("\nProfile:", profile["profile_name"])
        print("Files:", profile["files_collected"])
        print("Integrity:", profile["integrity_verified"])

        for artifact in profile["collected_files"]:
            print("  File:", artifact["artifact_name"])
            print("  SHA256:", artifact["sha256"])
            print("  Verified:", artifact["integrity_verified"])


if __name__ == "__main__":
    main()
