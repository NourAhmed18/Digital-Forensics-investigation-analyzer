
import psutil
import socket
import json
from pathlib import Path
from datetime import datetime, timezone


def get_process_name(pid):
    if pid is None:
        return None

    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return None


def collect_connections():
    connections = []
    collection_error = None

    try:
        raw_connections = psutil.net_connections(kind="inet")

    except (psutil.AccessDenied, OSError) as error:
        return connections, str(error)

    for connection in raw_connections:
        if connection.type == socket.SOCK_STREAM:
            protocol = "TCP"
        elif connection.type == socket.SOCK_DGRAM:
            protocol = "UDP"
        else:
            protocol = "Unknown"

        connections.append({
            "protocol": protocol,
            "local_addr": (
                connection.laddr.ip if connection.laddr else None
            ),
            "local_port": (
                connection.laddr.port if connection.laddr else None
            ),
            "remote_addr": (
                connection.raddr.ip if connection.raddr else None
            ),
            "remote_port": (
                connection.raddr.port if connection.raddr else None
            ),
            "status": connection.status,
            "pid": connection.pid,
            "process_name": get_process_name(connection.pid),
            "is_listening": (
                protocol == "TCP" and connection.status == "LISTEN"
            )
        })

    return connections, collection_error


def collect_interfaces():
    interfaces = {}

    for name, addresses in psutil.net_if_addrs().items():
        interfaces[name] = [
            {
                "family": str(address.family),
                "address": address.address,
                "netmask": address.netmask,
                "broadcast": address.broadcast,
                "ptp": address.ptp
            }
            for address in addresses
        ]

    return interfaces


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent.parent
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    connections, collection_error = collect_connections()

    listening = [
        connection for connection in connections
        if connection["is_listening"]
    ]

    result = {
        "artifact_type": "network_connections",
        "source_tool": f"psutil {psutil.__version__}",
        "command": "psutil.net_connections(kind='inet')",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "collection_error": collection_error,
        "limitations": [
            "Process names and PIDs may be unavailable without administrator privileges.",
            "The results represent a point-in-time snapshot.",
            "Connections may open or close during collection.",
            "UDP does not use TCP-style listening states.",
            "Some network details may be unavailable due to operating-system permissions."
        ],
        "connection_count": len(connections),
        "listening_count": len(listening),
        "connections": connections,
        "interfaces": collect_interfaces()
    }

    output_file = output_dir / "network.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, default=str)

    if collection_error:
        print("Warning: Network collection was incomplete:", collection_error)

    print(
        f"Done! Saved {len(connections)} connections "
        f"({len(listening)} listening) to {output_file}"
    )
