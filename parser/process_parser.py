import json
from pathlib import Path


def parse_processes(file_path):
    """
    Parse process data from the Collector JSON output
    and return normalized process records.
    """

    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if data.get("artifact_type") != "processes":
        raise ValueError("Invalid artifact type: expected 'processes'")

    processes = data.get("processes", [])

    if not isinstance(processes, list):
        raise ValueError("'processes' must be a list")

    parsed_processes = []

    for process in processes:

        cmdline = process.get("cmdline")

        # Normalize command line from list to string
        if isinstance(cmdline, list):
            cmdline = " ".join(cmdline)
        elif cmdline is not None and not isinstance(cmdline, str):
            cmdline = str(cmdline)

        parsed_process = {
            "pid": process.get("pid"),
            "parent_pid": process.get("ppid"),
            "process_name": process.get("name"),
            "executable_path": process.get("exe"),
            "command_line": cmdline,
            "username": process.get("username"),
            "status": process.get("status"),
            "start_time": process.get("create_time_utc"),
            "end_time": None,
            "executable_sha256": process.get("sha256"),
        }

        parsed_processes.append(parsed_process)

    return {
        "metadata": {
            "artifact_type": data.get("artifact_type"),
            "source_tool": data.get("source_tool"),
            "command": data.get("command"),
            "collected_at_utc": data.get("collected_at_utc"),
            "limitations": data.get("limitations"),
            "process_count": data.get("process_count"),
        },
        "processes": parsed_processes,
    }


if __name__ == "__main__":

    sample_file = (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "processes_sample.json"
    )

    result = parse_processes(sample_file)

    print("Parser executed successfully!")
    print("Processes parsed:", len(result["processes"]))
    print("\nFirst parsed process:")
    print(json.dumps(result["processes"][0], indent=2, ensure_ascii=False))