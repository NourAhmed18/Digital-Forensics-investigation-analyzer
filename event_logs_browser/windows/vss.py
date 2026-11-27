
import json
import subprocess
import base64
import sys
from pathlib import Path
import configparser


def create_shadow_copy(volume: str = "C:\\") -> dict:
    """
    Create a Windows Volume Shadow Copy.

    Returns the shadow ID and device path.
    Requires administrator privileges.
    """

    if sys.platform != "win32":
        raise OSError("VSS is only supported on Windows.")

    if not volume.endswith("\\"):
        volume += "\\"

    powershell_script = f"""
    $ErrorActionPreference = 'Stop'

    $result = Invoke-CimMethod `
        -ClassName Win32_ShadowCopy `
        -MethodName Create `
        -Arguments @{{
            Volume = '{volume}'
            Context = 'ClientAccessible'
        }}

    if ($result.ReturnValue -ne 0) {{
        throw "VSS creation failed. ReturnValue: $($result.ReturnValue)"
    }}

    $shadow = Get-CimInstance Win32_ShadowCopy |
        Where-Object {{ $_.ID -eq $result.ShadowID }}

    if (-not $shadow) {{
        throw "Shadow Copy was created but could not be located."
    }}

    [PSCustomObject]@{{
        return_value = [int]$result.ReturnValue
        shadow_id = [string]$shadow.ID
        device_object = [string]$shadow.DeviceObject
        volume_name = [string]$shadow.VolumeName
        install_date = [string]$shadow.InstallDate
    }} | ConvertTo-Json -Compress
    """

    encoded_script = base64.b64encode(
        powershell_script.encode("utf-16le")
    ).decode("ascii")

    process = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded_script,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"VSS creation failed:\n{process.stderr}"
        )

    try:
        result = json.loads(process.stdout.strip())
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Could not read VSS response: {process.stdout}"
        ) from error

    if result["return_value"] != 0:
        raise RuntimeError("VSS returned an unsuccessful status.")

    return result


#---
"""
Discover Windows profiles automatically
Record the SID, username, local path, volume, and profile type.
Does not collect or modify any evidence.
"""

import os




def discover_windows_user_profiles() -> list[dict]:
    """
    Discover Windows user and service profiles using Win32_UserProfile.

    Records profiles even when their directories are missing or inaccessible.
    Does not collect or modify any evidence.
    """

    if sys.platform != "win32":
        raise OSError("Windows profile discovery requires Windows.")

    powershell_script = r"""
    $ErrorActionPreference = 'Stop'

    $profiles = Get-CimInstance Win32_UserProfile |
        Where-Object { $_.LocalPath } |
        Select-Object SID, LocalPath, Special, Loaded, Status, LastUseTime

    ConvertTo-Json -InputObject @($profiles) -Depth 3 -Compress
    """

    encoded_script = base64.b64encode(
        powershell_script.encode("utf-16le")
    ).decode("ascii")

    process = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded_script,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"Windows profile discovery failed:\n{process.stderr}"
        )

    try:
        raw_profiles = json.loads(process.stdout.strip())
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Could not parse Windows profiles: {process.stdout}"
        ) from error

    if isinstance(raw_profiles, dict):
        raw_profiles = [raw_profiles]

    discovered = []

    for profile in raw_profiles:
        local_path = profile.get("LocalPath")

        if not local_path:
            continue

        local_path = os.path.normpath(local_path)
        normalized_path = local_path.lower()

        special = bool(profile.get("Special"))
        loaded = bool(profile.get("Loaded"))

        if "\\windows\\serviceprofiles\\" in normalized_path:
            profile_type = "service"
        elif (
            "\\windows\\system32\\config\\" in normalized_path
            or special
        ):
            profile_type = "system"
        else:
            profile_type = "user"

        path_exists = os.path.exists(local_path)
        path_accessible = False
        discovery_status = "path_not_found"

        if path_exists:
            try:
                if not os.path.isdir(local_path):
                    discovery_status = "not_a_directory"
                else:
                    # Actually attempt to list the directory.
                    with os.scandir(local_path) as entries:
                        next(entries, None)

                    path_accessible = True
                    discovery_status = "accessible"

            except PermissionError:
                discovery_status = "permission_denied"

            except OSError as error:
                discovery_status = f"access_error: {error}"

        discovered.append({
            "sid": profile.get("SID"),
            "username": os.path.basename(local_path),
            "local_path": local_path,
            "volume": os.path.splitdrive(local_path)[0],
            "special": special,
            "loaded": loaded,
            "profile_type": profile_type,
            "path_exists": path_exists,
            "path_accessible": path_accessible,
            "discovery_status": discovery_status,
            "status": profile.get("Status"),
            "last_use_time": profile.get("LastUseTime"),
        })
        sid_counts = {}

    for item in discovered:
        sid = item.get("sid")
        if sid:
            sid_counts[sid] = sid_counts.get(sid, 0) + 1

    for item in discovered:
        sid = item.get("sid")
        item["duplicate_sid"] = (
            bool(sid) and sid_counts.get(sid, 0) > 1
        )

    return discovered


#---



def discover_browser_locations(
    include_service_profiles=False
) -> list[dict]:
    """
    Discover standard browser data directories for Windows profiles.

    User profiles are included by default.
    Service profiles can optionally be included.
    System profiles are excluded.

    Missing and inaccessible browser paths are recorded.
    """

    profiles = discover_windows_user_profiles()

    browser_locations = {
        "Google Chrome": (
            "AppData", "Local", "Google", "Chrome", "User Data"
        ),
        "Microsoft Edge": (
            "AppData", "Local", "Microsoft", "Edge", "User Data"
        ),
        "Mozilla Firefox": (
            "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"
        ),
    }

    discovered = []

    for profile in profiles:
        profile_type = profile.get("profile_type")

        if profile_type == "system":
            continue

        if profile_type == "service" and not include_service_profiles:
            continue

        user_path = Path(profile["local_path"])

        for browser_name, relative_parts in browser_locations.items():
            browser_path = user_path.joinpath(*relative_parts)

            record = {
                "username": profile["username"],
                "sid": profile["sid"],
                "profile_type": profile_type,
                "user_profile_path": str(user_path),
                "browser": browser_name,
                "browser_root": str(browser_path),
                "volume": profile["volume"],
                "discovery_status": None,
                "error": None,
            }

            try:
                if not profile.get("path_accessible", False):
                    record["discovery_status"] = (
                        "user_profile_not_accessible"
                    )

                elif not browser_path.exists():
                    record["discovery_status"] = "browser_not_found"

                elif not browser_path.is_dir():
                    record["discovery_status"] = "not_a_directory"

                else:
                    record["discovery_status"] = "found"

            except PermissionError as error:
                record["discovery_status"] = "permission_denied"
                record["error"] = str(error)

            except OSError as error:
                record["discovery_status"] = "discovery_error"
                record["error"] = str(error)

            discovered.append(record)

    return discovered



#---



def discover_firefox_profiles(browser_root: Path) -> list[dict]:
    """
    Discover Firefox profiles using profiles.ini.

    Supports relative and absolute profile paths.
    Keeps missing profiles in the discovery results.
    Does not modify Firefox files.
    """

    profiles_ini = browser_root / "profiles.ini"

    if not profiles_ini.is_file():
        return [{
            "profile_name": None,
            "profile_path": None,
            "discovery_status": "profiles_ini_not_found",
            "error": None,
        }]

    config = configparser.ConfigParser()

    try:
        config.read(profiles_ini, encoding="utf-8")

    except (OSError, configparser.Error) as error:
        return [{
            "profile_name": None,
            "profile_path": None,
            "discovery_status": "profiles_ini_read_error",
            "error": str(error),
        }]

    discovered = []

    for section in config.sections():
        if not section.lower().startswith("profile"):
            continue

        profile_name = config.get(
            section, "Name", fallback=section
        )

        profile_path_value = config.get(
            section, "Path", fallback=None
        )

        if not profile_path_value:
            discovered.append({
                "profile_name": profile_name,
                "profile_path": None,
                "discovery_status": "profile_path_missing",
                "error": None,
            })
            continue

        is_relative = config.getboolean(
            section, "IsRelative", fallback=True
        )

        profile_path = Path(profile_path_value)

        if is_relative:
            profile_path = browser_root / profile_path

        profile_path = Path(os.path.normpath(str(profile_path)))

        record = {
            "profile_name": profile_name,
            "profile_path": str(profile_path),
            "discovery_status": None,
            "error": None,
        }

        try:
            if not profile_path.exists():
                record["discovery_status"] = "profile_not_found"

            elif not profile_path.is_dir():
                record["discovery_status"] = "not_a_directory"

            else:
                record["discovery_status"] = "found"

        except PermissionError as error:
            record["discovery_status"] = "permission_denied"
            record["error"] = str(error)

        except OSError as error:
            record["discovery_status"] = "discovery_error"
            record["error"] = str(error)

        discovered.append(record)

    if not discovered:
        discovered.append({
            "profile_name": None,
            "profile_path": None,
            "discovery_status": "no_profiles_listed",
            "error": None,
        })

    return discovered



def discover_browser_databases() -> list[dict]:
    """
    Discover actual Chrome, Edge, and Firefox browser profiles.

    Chromium profiles are identified using Local State.
    Firefox profiles are discovered from the Profiles directory.

    Missing databases and access errors are recorded.
    Original evidence is never modified.
    """

    browser_locations = discover_browser_locations()

    database_names = {
        "Google Chrome": "History",
        "Microsoft Edge": "History",
        "Mozilla Firefox": "places.sqlite",
    }

    discovered = []

    for browser in browser_locations:
        browser_name = browser["browser"]
        browser_root = Path(browser["browser_root"])
        database_name = database_names[browser_name]

        base_record = {
            "username": browser["username"],
            "sid": browser["sid"],
            "profile_type": browser["profile_type"],
            "browser": browser_name,
            "browser_profile": None,
            "database_name": database_name,
            "database_path": None,
            "file_size": None,
            "volume": browser["volume"],
            "discovery_status": None,
            "error": None,
        }

        # Check the browser root before accessing its contents.
        try:
            if not browser_root.exists():
                record = base_record.copy()
                record["discovery_status"] = "browser_not_found"
                discovered.append(record)
                continue

            if not browser_root.is_dir():
                record = base_record.copy()
                record["discovery_status"] = "not_a_directory"
                discovered.append(record)
                continue

            if browser_name in ("Google Chrome", "Microsoft Edge"):
                local_state = browser_root / "Local State"

                if not local_state.is_file():
                    record = base_record.copy()
                    record["discovery_status"] = "local_state_not_found"
                    discovered.append(record)
                    continue

                with local_state.open("r", encoding="utf-8") as file:
                    state_data = json.load(file)

                profile_info = (
                    state_data.get("profile", {}).get("info_cache", {})
                )

                profile_entries = [
                    {
                        "profile_name": name,
                        "profile_path": browser_root / name,
                        "profile_status": "found",
                        "profile_error": None,
                    }
                    for name in profile_info.keys()
                ]

                if not profile_entries:
                    record = base_record.copy()
                    record["discovery_status"] = "no_profiles_listed"
                    discovered.append(record)
                    continue

            else:
                firefox_profiles = discover_firefox_profiles(browser_root.parent)

                profile_entries = [
                    {
                        "profile_name": item["profile_name"],
                        "profile_path": (
                            Path(item["profile_path"])
                            if item["profile_path"]
                            else None
                        ),
                        "profile_status": item["discovery_status"],
                        "profile_error": item["error"],
                    }
                    for item in firefox_profiles
                ]

        except PermissionError as error:
            record = base_record.copy()
            record["discovery_status"] = "permission_denied"
            record["error"] = str(error)
            discovered.append(record)
            continue

        except json.JSONDecodeError as error:
            record = base_record.copy()
            record["discovery_status"] = "invalid_local_state"
            record["error"] = str(error)
            discovered.append(record)
            continue

        except OSError as error:
            record = base_record.copy()
            record["discovery_status"] = "discovery_error"
            record["error"] = str(error)
            discovered.append(record)
            continue
        for entry in profile_entries:
            profile_name = entry["profile_name"]
            profile_dir = entry["profile_path"]

            record = {
                **base_record,
                "browser_profile": profile_name,
                "profile_status": entry["profile_status"],
                "database_path": None,
            }

            try:
                if profile_dir is None:
                    record["discovery_status"] = entry["profile_status"]
                    record["error"] = entry["profile_error"]

                elif not profile_dir.is_dir():
                    record["discovery_status"] = "profile_not_found"

                else:
                    database_path = profile_dir / database_name
                    record["database_path"] = str(database_path)

                    if database_path.is_file():
                        record["file_size"] = database_path.stat().st_size
                        record["discovery_status"] = "found"
                    else:
                        record["discovery_status"] = "database_not_found"

            except PermissionError as error:
                record["discovery_status"] = "permission_denied"
                record["error"] = str(error)

            except OSError as error:
                record["discovery_status"] = "discovery_error"
                record["error"] = str(error)

            discovered.append(record)

    return discovered





#---

def discover_sqlite_sidecars() -> list[dict]:
    """
    Discover browser SQLite databases and their sidecar files.

    Keeps profiles even when the main database is missing
    or inaccessible.
    Does not open, copy, or modify evidence.
    """

    databases = discover_browser_databases()

    sidecar_suffixes = [
        "-wal",
        "-shm",
        "-journal",
    ]

    discovered = []

    for database in databases:
        existing_files = []

        database_path_value = database.get("database_path")

        if database_path_value:
            database_path = Path(database_path_value)

            if database.get("discovery_status") == "found":
                try:
                    if database_path.is_file():
                        existing_files.append({
                            "file_type": "database",
                            "file_path": str(database_path),
                            "file_size": database_path.stat().st_size,
                        })

                    for suffix in sidecar_suffixes:
                        sidecar_path = Path(str(database_path) + suffix)

                        try:
                            if sidecar_path.is_file():
                                existing_files.append({
                                    "file_type": suffix.lstrip("-"),
                                    "file_path": str(sidecar_path),
                                    "file_size": sidecar_path.stat().st_size,
                                })

                        except OSError:
                            continue

                except OSError:
                    pass

        discovered.append({
            "username": database["username"],
            "sid": database.get("sid"),
            "profile_type": database["profile_type"],
            "browser": database["browser"],
            "browser_profile": database["browser_profile"],
            "database_name": database["database_name"],
            "database_path": database["database_path"],
            "volume": database["volume"],
            "discovery_status": database["discovery_status"],
            "error": database["error"],
            "files": existing_files,
        })

    return discovered
