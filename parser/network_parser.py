import json
from pathlib import Path


def parse_network(file_path):
    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if data.get("artifact_type") != "network_connections":
        raise ValueError(
            "Invalid artifact type: expected 'network_connections'"
        )

    connections = data.get("connections", [])

    if not isinstance(connections, list):
        raise ValueError("'connections' must be a list")

    parsed_connections = []

    for connection in connections:
        parsed_connection = {
            "protocol": connection.get("protocol"),
            "local_ip": connection.get("local_addr"),
            "local_port": connection.get("local_port"),
            "remote_ip": connection.get("remote_addr"),
            "remote_port": connection.get("remote_port"),
            "connection_state": connection.get("status"),
            "process_pid": connection.get("pid"),
            "process_name": connection.get("process_name"),
            "is_listening": connection.get("is_listening"),
        }

        parsed_connections.append(parsed_connection)

    return {
        "metadata": {
            "artifact_type": data.get("artifact_type"),
            "source_tool": data.get("source_tool"),
            "command": data.get("command"),
            "collected_at_utc": data.get("collected_at_utc"),
            "collection_error": data.get("collection_error"),
            "limitations": data.get("limitations"),
            "connection_count": data.get("connection_count"),
            "listening_count": data.get("listening_count"),
            "interfaces": data.get("interfaces"),
        },
        "connections": parsed_connections,
    }


if __name__ == "__main__":
    sample_file = (
        Path(__file__).resolve().parents[1]
        / "sample_data"
        / "network_sample.json"
    )

    result = parse_network(sample_file)

    print("Network Parser executed successfully!")
    print("Connections parsed:", len(result["connections"]))

    print("\nMetadata:")
    print(json.dumps(result["metadata"], indent=2, ensure_ascii=False))

    print("\nFirst parsed connection:")
    print(json.dumps(result["connections"][0], indent=2, ensure_ascii=False))