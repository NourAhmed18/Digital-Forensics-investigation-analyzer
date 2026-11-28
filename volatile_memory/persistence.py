
"""
Windows persistence-artifact collector for the DEPI Digital Forensics project.

Read-only collection of common persistence locations:
- HKCU/HKLM Run and RunOnce registry keys (32-bit and 64-bit views)
- Current-user and all-users Startup folders

Startup-folder items receive a basic file classification.
Classification is an investigative hint, not a malware verdict.

Run from the project root:
    py -m volatile_memory.persistence
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def classify_startup_item(path):
    """Classify a Startup-folder item without executing or modifying it."""

    if path.is_dir():
        return "directory"

    suffix = path.suffix.lower()

    if path.name.lower() == "desktop.ini":
        return "metadata_file"

    if suffix in {".lnk", ".url"}:
        return "shortcut_or_link"

    executable_or_script_extensions = {
        ".exe", ".com", ".bat", ".cmd", ".ps1", ".psm1",
        ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
        ".hta", ".scr",
    }

    if suffix in executable_or_script_extensions:
        return "executable_or_script"

    return "other_file"


def collect_registry_entries():
    """Collect values from common Windows Run and RunOnce registry keys."""

    if os.name != "nt":
        return [], [
            "Registry collection is available only on Windows."
        ]

    import winreg

    entries = []
    errors = []

    locations = [
        ("HKCU", winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Run"),

        ("HKCU", winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),

        ("HKLM", winreg.HKEY_LOCAL_MACHINE,
         r"Software\Microsoft\Windows\CurrentVersion\Run"),

        ("HKLM", winreg.HKEY_LOCAL_MACHINE,
         r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]

    views = [
        ("64-bit", getattr(winreg, "KEY_WOW64_64KEY", 0)),
        ("32-bit", getattr(winreg, "KEY_WOW64_32KEY", 0)),
    ]

    for hive_name, hive, subkey in locations:
        for view_name, view_flag in views:

            try:
                with winreg.OpenKey(
                    hive,
                    subkey,
                    0,
                    winreg.KEY_READ | view_flag
                ) as key:

                    _, value_count, _ = winreg.QueryInfoKey(key)

                    for index in range(value_count):
                        try:
                            name, value, value_type = winreg.EnumValue(
                                key, index
                            )

                            entries.append({
                                "hive": hive_name,
                                "registry_path": subkey,
                                "registry_view": view_name,
                                "entry_name": name,
                                "entry_value": str(value),
                                "value_type": value_type,
                                "collected_at_utc": utc_now(),
                            })

                        except OSError as exc:
                            errors.append(
                                f"Could not read value {index} from "
                                f"{hive_name}\\{subkey} "
                                f"({view_name}): {exc}"
                            )

            except FileNotFoundError:
                continue

            except PermissionError as exc:
                errors.append(
                    f"Permission denied: {hive_name}\\{subkey} "
                    f"({view_name}): {exc}"
                )

            except OSError as exc:
                errors.append(
                    f"Could not read {hive_name}\\{subkey} "
                    f"({view_name}): {exc}"
                )

    return entries, errors


def collect_startup_items():
    """Collect metadata about files in common Windows Startup folders."""

    appdata = os.environ.get("APPDATA")
    programdata = os.environ.get("PROGRAMDATA")

    candidates = []

    if appdata:
        candidates.append((
            "current_user",
            Path(appdata) /
            "Microsoft/Windows/Start Menu/Programs/Startup",
        ))

    if programdata:
        candidates.append((
            "all_users",
            Path(programdata) /
            "Microsoft/Windows/Start Menu/Programs/Startup",
        ))

    items = []
    errors = []

    for scope, folder in candidates:

        if not folder.exists():
            continue

        try:
            for path in folder.iterdir():

                try:
                    stat = path.stat()
                    is_directory = path.is_dir()

                    items.append({
                        "scope": scope,
                        "startup_folder": str(folder),
                        "path": str(path),
                        "name": path.name,
                        "is_directory": is_directory,
                        "classification": classify_startup_item(path),
                        "size_bytes": stat.st_size,
                        "modified_at_utc": datetime.fromtimestamp(
                            stat.st_mtime,
                            timezone.utc
                        ).isoformat(),
                        "collected_at_utc": utc_now(),
                    })

                except OSError as exc:
                    errors.append(
                        f"Could not inspect {path}: {exc}"
                    )

        except PermissionError as exc:
            errors.append(
                f"Permission denied reading {folder}: {exc}"
            )

        except OSError as exc:
            errors.append(
                f"Could not read {folder}: {exc}"
            )

    return items, errors


def collect_persistence():
    """Return persistence artifacts and collection provenance."""

    started_at = utc_now()

    registry_entries, registry_errors = collect_registry_entries()
    startup_items, startup_errors = collect_startup_items()

    limitations = [
        "Only the listed common Windows persistence locations are collected.",
        "Collected entries are indicators, not proof of malicious activity.",
        "Startup file classifications are based on file type and are not malware verdicts.",
        "Some locations may require elevated permissions to read completely.",
        "This is a point-in-time snapshot; system state may change after collection.",
        "The 32-bit and 64-bit registry views may contain identical entries.",
    ]

    if os.name != "nt":
        limitations.append(
            "Registry collection was skipped because this host is not Windows."
        )

    return {
        "artifact_type": "persistence_artifacts",
        "source_tool": (
            f"Python {sys.version.split()[0]} standard library"
        ),
        "command": "py -m volatile_memory.persistence",
        "collected_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "registry_entry_count": len(registry_entries),
        "startup_item_count": len(startup_items),
        "registry_entries": registry_entries,
        "startup_items": startup_items,
        "errors": registry_errors + startup_errors,
        "limitations": limitations,
    }


def main():
    result = collect_persistence()

    # Save output relative to the project folder,
    # not the terminal's current working directory.
    project_dir = Path(__file__).resolve().parent.parent
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "persistence.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {result['registry_entry_count']} registry entries "
        f"and {result['startup_item_count']} Startup items "
        f"to {output_file}"
    )

    if result["errors"]:
        print(
            f"Completed with {len(result['errors'])} warning(s). "
            "See persistence.json."
        )


if __name__ == "__main__":
    main()
