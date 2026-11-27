"""Safe, non-invasive host metadata collection."""

from __future__ import annotations

import ctypes
import getpass
import json
import os
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _is_privileged() -> tuple[bool, str]:
    """Return privilege state without executing shell commands."""
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin()), "windows IsUserAnAdmin"
        except (AttributeError, OSError):
            return False, "windows privilege check unavailable"
    geteuid = getattr(os, "geteuid", None)
    if geteuid is not None:
        uid = geteuid()
        return uid == 0, f"POSIX geteuid={uid}"
    return False, "privilege check unavailable"


def collect_host_info() -> dict[str, Any]:
    """Collect identifying host metadata suitable for a case package."""
    privileged, privilege_method = _is_privileged()
    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = "unknown"
    try:
        username = getpass.getuser()
    except (KeyError, OSError):
        username = "unknown"

    return {
        "schema_version": "1.0",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "operating_system": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "distribution": platform.platform(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
        },
        "hostname": hostname,
        "username": username,
        "privilege": {
            "is_privileged": privileged,
            "check_method": privilege_method,
        },
        "environment": {
            "process_id": os.getpid(),
            "working_directory": str(Path.cwd()),
        },
    }


def write_host_info(path: Path) -> dict[str, Any]:
    data = collect_host_info()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data
