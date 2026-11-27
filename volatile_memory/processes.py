
import psutil
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


def calculate_sha256(file_path, cache=None):
    if cache is None:
        cache = {}

    if not file_path:
        return None

    if file_path in cache:
        return cache[file_path]

    try:
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        cache[file_path] = sha256.hexdigest()

    except (PermissionError, FileNotFoundError, OSError):
        cache[file_path] = None

    return cache[file_path]


def collect_processes():
    processes = {}
    hash_cache = {}

    attributes = [
        "pid", "ppid", "name", "cmdline",
        "exe", "username", "create_time", "status"
    ]

    for process in psutil.process_iter(attributes):
        try:
            info = process.info

            pid = info["pid"]
            ppid = info["ppid"]

            if not info["name"]:
                continue

            if pid == ppid:
                continue

            creation_time = info["create_time"]

            processes[pid] = {
                "pid": pid,
                "ppid": ppid,
                "name": info["name"],
                "cmdline": info["cmdline"],
                "exe": info["exe"],
                "username": info["username"],
                "status": info["status"],
                "create_time_utc": (
                    datetime.fromtimestamp(
                        creation_time, timezone.utc
                    ).isoformat()
                    if creation_time else None
                ),
                "sha256": calculate_sha256(
                    info["exe"], hash_cache
                )
            }

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes


def build_tree(processes):
    children = {}

    for pid, info in processes.items():
        parent_pid = info["ppid"]

        if parent_pid in processes:
            children.setdefault(parent_pid, []).append(pid)

    visited = set()

    def build_node(pid):
        visited.add(pid)

        node = dict(processes[pid])
        node["children"] = []

        for child_pid in sorted(children.get(pid, [])):
            if child_pid not in visited:
                node["children"].append(build_node(child_pid))

        return node

    # Start with processes whose parents were not collected.
    roots = [
        pid for pid, info in processes.items()
        if info["ppid"] not in processes
    ]

    tree = []

    for pid in sorted(roots):
        if pid not in visited:
            tree.append(build_node(pid))

    # Include any remaining processes, such as unusual
    # orphaned or cyclic relationships.
    for pid in sorted(processes):
        if pid not in visited:
            tree.append(build_node(pid))

    return tree


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent.parent
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    processes = collect_processes()
    tree = build_tree(processes)

    result = {
        "artifact_type": "processes",
        "source_tool": f"psutil {psutil.__version__}",
        "command": "psutil.process_iter()",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Some processes may be inaccessible without administrator privileges.",
            "Processes can start or stop during collection.",
            "Executable hashing may fail if the file is inaccessible.",
            "The process tree represents a point-in-time snapshot."
        ],
        "process_count": len(processes),
        "processes": list(processes.values()),
        "process_tree": tree
    }

    output_file = output_dir / "processes.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, default=str)

    print(
        f"Done! Saved {len(processes)} processes "
        f"to {output_file}"
    )
