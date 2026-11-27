import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

from event_logs_browser.common.hashing import calculate_sha256
from event_logs_browser.common.metadata import save_metadata_json


# Chromium databases and sidecar files
SQLITE_FILES = [
    "History",
    "History-wal",
    "History-shm",
    "History-journal",
]

# Firefox database and sidecar files
FIREFOX_SQLITE_FILES = [
    "places.sqlite",
    "places.sqlite-wal",
    "places.sqlite-shm",
    "places.sqlite-journal",
]


def _collect_all_browser_profiles_from_vss(
    device_object: str,
    profile_relative_path: str,
    destination_dir: str,
    browser_name: str,
    browser_path_parts: tuple,
    database_filename: str = "History",
    sqlite_files: list = None,
    volume_root: str = None,
) -> dict:
    """
    Discover and collect browser SQLite databases from all profiles
    available inside a Windows VSS snapshot.

    Original evidence is preserved. Every copied file is verified
    using SHA-256.

    volume_root:
        Root of the volume containing the original Windows user profile,
        for example r"C:\\" or r"D:\\".

    profile_relative_path:
        User profile path relative to volume_root, for example
        r"Users\\SomeUser".
    """

    if os.name != "nt":
        raise OSError("This acquisition method requires Windows.")

    if not device_object:
        raise ValueError("VSS device object cannot be empty.")

    if not profile_relative_path:
        raise ValueError("Profile relative path cannot be empty.")

    if not database_filename:
        raise ValueError("Database filename cannot be empty.")

    if sqlite_files is None:
        sqlite_files = SQLITE_FILES

    # Determine the volume containing the user profile.
    # SystemDrive is retained as a backward-compatible default.
    if volume_root is None:
        system_drive = os.environ.get("SystemDrive")

        if not system_drive:
            raise EnvironmentError(
                "SystemDrive environment variable not found."
            )

        volume_root = system_drive + "\\"
    elif len(volume_root) == 2 and volume_root[1] == ":":
        # Normalize values such as "D:" to "D:\\"
        volume_root += "\\"

    volume_root_path = Path(volume_root).resolve()
    relative_profile_path = Path(profile_relative_path)

    if relative_profile_path.is_absolute():
        raise ValueError(
            "profile_relative_path must be relative to volume_root."
        )

    original_user_profile = (
        volume_root_path / relative_profile_path
    ).resolve()

    try:
        original_user_profile.relative_to(volume_root_path)
    except ValueError as error:
        raise ValueError(
            "User profile is not located on the specified volume."
        ) from error

    # Original browser data directory.
    original_user_data = original_user_profile.joinpath(
        *browser_path_parts
    )

    # Browser data directory inside the VSS snapshot.
    snapshot_root = device_object.rstrip("\\")
    snapshot_user_data = Path(
        os.path.join(
            snapshot_root,
            str(relative_profile_path),
            *browser_path_parts,
        )
    )

    if not snapshot_user_data.is_dir():
        raise FileNotFoundError(
            f"{browser_name} data directory not found: "
            f"{snapshot_user_data}"
        )

    output_dir = Path(destination_dir)
    metadata_path = output_dir / "browser_metadata.json"

    # Discover all browser profiles dynamically.
    discovered_profiles = []

    for profile_dir in snapshot_user_data.iterdir():
        if not profile_dir.is_dir():
            continue

        database_source = profile_dir / database_filename

        if not database_source.is_file():
            continue

        available_files = [
            profile_dir / name
            for name in sqlite_files
            if (profile_dir / name).is_file()
        ]

        if available_files:
            discovered_profiles.append({
                "name": profile_dir.name,
                "source_dir": profile_dir,
                "original_dir": original_user_data / profile_dir.name,
                "files": available_files,
            })

    if not discovered_profiles:
        raise FileNotFoundError(
            f"No {browser_name} profiles containing "
            f"{database_filename} databases were found "
            "in the VSS snapshot."
        )

    # Never overwrite existing evidence.
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Destination directory is not empty: {output_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    copied_paths = []
    created_profile_dirs = []

    try:
        collection_timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        collected_files = []
        collected_profiles = []

        for profile in discovered_profiles:
            profile_name = profile["name"]
            profile_output_dir = output_dir / profile_name

            if profile_output_dir.exists():
                raise FileExistsError(
                    f"Profile output already exists: "
                    f"{profile_output_dir}"
                )

            profile_output_dir.mkdir(parents=True)
            created_profile_dirs.append(profile_output_dir)

            profile_files = []

            for source in profile["files"]:
                destination = profile_output_dir / source.name
                original_source = (
                    profile["original_dir"] / source.name
                )

                # Track destination before copying.
                copied_paths.append(destination)

                # Always copy from the VSS snapshot.
                shutil.copy2(source, destination)

                source_hash = calculate_sha256(str(source))
                copied_hash = calculate_sha256(str(destination))

                if source_hash != copied_hash:
                    raise IOError(
                        f"SHA-256 verification failed: "
                        f"{profile_name}/{source.name}"
                    )

                artifact = {
                    "browser": browser_name,
                    "profile_name": profile_name,
                    "artifact_name": source.name,
                    "artifact_type": (
                        f"{browser_name} SQLite database"
                        if source.name == database_filename
                        else f"{browser_name} SQLite sidecar"
                    ),
                    "original_source_path": str(original_source),
                    "source_path": str(source),
                    "collected_path": str(destination.resolve()),
                    "collection_timestamp": collection_timestamp,
                    "original_file_format": (
                        "SQLite database"
                        if source.name == database_filename
                        else "SQLite sidecar file"
                    ),
                    "size_bytes": destination.stat().st_size,
                    "sha256": copied_hash,
                    "integrity_verified": True,
                }

                profile_files.append(artifact)
                collected_files.append(artifact)

            collected_profiles.append({
                "profile_name": profile_name,
                "original_profile_path": str(
                    profile["original_dir"]
                ),
                "snapshot_profile_path": str(
                    profile["source_dir"]
                ),
                "files_collected": len(profile_files),
                "integrity_verified": all(
                    item["integrity_verified"]
                    for item in profile_files
                ),
                "collected_files": profile_files,
            })

        metadata = {
            "browser": browser_name,
            "acquisition_method": "Windows Volume Shadow Copy",
            "collection_tool": (
                "Digital Forensics Investigation & Analyzer"
            ),
            "snapshot_device": device_object,
            "volume_root": str(volume_root_path),
            "original_user_data_path": str(original_user_data),
            "snapshot_user_data_path": str(snapshot_user_data),
            "collection_timestamp": collection_timestamp,
            "profiles_discovered": len(discovered_profiles),
            "profiles_collected": len(collected_profiles),
            "files_collected": len(collected_files),
            "integrity_verified": all(
                item["integrity_verified"]
                for item in collected_files
            ),
            "profiles": collected_profiles,
            "collected_files": collected_files,
        }

        saved_metadata_path = save_metadata_json(
            metadata,
            str(metadata_path),
        )

        return {
            **metadata,
            "metadata_path": saved_metadata_path,
        }

    except Exception:
        # Remove partially collected files.
        for path in copied_paths:
            if path.exists():
                path.unlink()

        for profile_dir in created_profile_dirs:
            if profile_dir.exists():
                shutil.rmtree(profile_dir)

        if metadata_path.exists():
            metadata_path.unlink()

        if output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()

        raise


def collect_all_chrome_profiles_from_vss(
    device_object: str,
    profile_relative_path: str,
    destination_dir: str,
    volume_root: str = None,
) -> dict:
    """
    Collect Chrome History databases from all profiles in a VSS snapshot.
    """

    return _collect_all_browser_profiles_from_vss(
        device_object=device_object,
        profile_relative_path=profile_relative_path,
        destination_dir=destination_dir,
        browser_name="Google Chrome",
        browser_path_parts=(
            "AppData",
            "Local",
            "Google",
            "Chrome",
            "User Data",
        ),
        database_filename="History",
        sqlite_files=SQLITE_FILES,
        volume_root=volume_root,
    )


def collect_all_edge_profiles_from_vss(
    device_object: str,
    profile_relative_path: str,
    destination_dir: str,
    volume_root: str = None,
) -> dict:
    """
    Collect Edge History databases from all profiles in a VSS snapshot.
    """

    return _collect_all_browser_profiles_from_vss(
        device_object=device_object,
        profile_relative_path=profile_relative_path,
        destination_dir=destination_dir,
        browser_name="Microsoft Edge",
        browser_path_parts=(
            "AppData",
            "Local",
            "Microsoft",
            "Edge",
            "User Data",
        ),
        database_filename="History",
        sqlite_files=SQLITE_FILES,
        volume_root=volume_root,
    )


def collect_all_firefox_profiles_from_vss(
    device_object: str,
    profile_relative_path: str,
    destination_dir: str,
    volume_root: str = None,
) -> dict:
    """
    Collect Firefox places.sqlite databases from all profiles
    in a VSS snapshot.
    """

    return _collect_all_browser_profiles_from_vss(
        device_object=device_object,
        profile_relative_path=profile_relative_path,
        destination_dir=destination_dir,
        browser_name="Mozilla Firefox",
        browser_path_parts=(
            "AppData",
            "Roaming",
            "Mozilla",
            "Firefox",
            "Profiles",
        ),
        database_filename="places.sqlite",
        sqlite_files=FIREFOX_SQLITE_FILES,
        volume_root=volume_root,
    )


def collect_chrome_database_from_vss(
    device_object: str,
    profile_relative_path: str,
    destination_dir: str,
) -> dict:
    """
    Legacy function: collect Chrome Default profile only.

    Kept for backward compatibility with existing tests or code.
    For all Chrome profiles, use collect_all_chrome_profiles_from_vss.
    """

    if os.name != "nt":
        raise OSError("This acquisition method requires Windows.")

    if not device_object:
        raise ValueError("VSS device object cannot be empty.")

    if not profile_relative_path:
        raise ValueError("Profile relative path cannot be empty.")

    system_drive = os.environ.get("SystemDrive")

    if not system_drive:
        raise EnvironmentError(
            "SystemDrive environment variable not found."
        )

    system_root = Path(system_drive + "\\").resolve()

    original_user_profile = (
        system_root / profile_relative_path
    ).resolve()

    try:
        original_user_profile.relative_to(system_root)
    except ValueError as error:
        raise ValueError(
            "User profile is not located on the snapshot volume."
        ) from error

    original_profile_dir = (
        original_user_profile
        / "AppData"
        / "Local"
        / "Google"
        / "Chrome"
        / "User Data"
        / "Default"
    )

    snapshot_root = device_object.rstrip("\\")

    source_dir = Path(
        os.path.join(
            snapshot_root,
            profile_relative_path,
            "AppData",
            "Local",
            "Google",
            "Chrome",
            "User Data",
            "Default",
        )
    )

    output_dir = Path(destination_dir)
    history_source = source_dir / "History"

    if not history_source.is_file():
        raise FileNotFoundError(
            f"Chrome History not found in snapshot: {history_source}"
        )

    available_files = [
        source_dir / name
        for name in SQLITE_FILES
        if (source_dir / name).is_file()
    ]

    if not available_files:
        raise FileNotFoundError(
            "No Chrome SQLite files were found in the snapshot."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / "browser_metadata.json"

    existing_outputs = [
        output_dir / source.name
        for source in available_files
        if (output_dir / source.name).exists()
    ]

    if existing_outputs or metadata_path.exists():
        raise FileExistsError(
            "Evidence output already exists. "
            "Choose a new destination directory."
        )

    copied_paths = []

    try:
        collection_timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        collected_files = []

        for source in available_files:
            destination = output_dir / source.name
            original_source = original_profile_dir / source.name

            copied_paths.append(destination)

            shutil.copy2(source, destination)

            source_hash = calculate_sha256(str(source))
            copied_hash = calculate_sha256(str(destination))

            if source_hash != copied_hash:
                raise IOError(
                    f"SHA-256 verification failed: {source.name}"
                )

            collected_files.append({
                "artifact_name": source.name,
                "artifact_type": (
                    "Chrome SQLite database"
                    if source.name == "History"
                    else "Chrome SQLite sidecar"
                ),
                "original_source_path": str(original_source),
                "source_path": str(source),
                "collected_path": str(destination),
                "collection_timestamp": collection_timestamp,
                "original_file_format": (
                    "SQLite database"
                    if source.name == "History"
                    else "SQLite sidecar file"
                ),
                "size_bytes": destination.stat().st_size,
                "sha256": copied_hash,
                "integrity_verified": True,
            })

        metadata = {
            "browser": "Google Chrome",
            "acquisition_method": "Windows Volume Shadow Copy",
            "collection_tool": (
                "Digital Forensics Investigation & Analyzer"
            ),
            "snapshot_device": device_object,
            "original_profile_path": str(original_profile_dir),
            "profile_source": str(source_dir),
            "collection_timestamp": collection_timestamp,
            "files_collected": len(collected_files),
            "integrity_verified": all(
                item["integrity_verified"]
                for item in collected_files
            ),
            "collected_files": collected_files,
        }

        saved_metadata_path = save_metadata_json(
            metadata,
            str(metadata_path),
        )

        return {
            **metadata,
            "metadata_path": saved_metadata_path,
        }

    except Exception:
        for path in copied_paths:
            if path.exists():
                path.unlink()

        if metadata_path.exists():
            metadata_path.unlink()

        raise
