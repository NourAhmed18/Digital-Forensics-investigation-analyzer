# Digital Forensics Investigation & Analyzer
## Role 3: Volatile Artifacts & Memory Acquisition

### Project Overview
This module collects and documents volatile system information and selected persistence artifacts from a Windows system as part of a Digital Forensics Investigation & Analyzer project.

### Technologies Used
- Python 3.14
- psutil 7.2.2
- Windows Registry
- FTK Imager 8.3.0.27
- SHA-256 hashing

### Project Structure
```text
DEPI PROJECT/
├── evidence/
│   └── memory/
│       └── memdump.mem
├── output/
│   ├── processes.json
│   ├── network.json
│   ├── persistence.json
│   └── memory_acquisition.json
├── volatile_memory/
│   ├── __init__.py
│   ├── processes.py
│   ├── network.py
│   ├── persistence.py
│   └── memory.py
└── requirements.txt
```

### Installation
Install the required Python dependency:

```bash
py -m pip install -r requirements.txt
```

### Running the Collectors

Run these commands from the main project directory:

**1. Process Collection**
```bash
py -m volatile_memory.processes
```
Collects running processes, process information, executable hashes where accessible, and a process tree.

**2. Network Collection**
```bash
py -m volatile_memory.network
```
Collects active TCP/UDP connections, listening TCP ports, and network interface information.

**3. Persistence Collection**
```bash
py -m volatile_memory.persistence
```
Collects selected Windows Registry Run/RunOnce entries and Startup-folder items.

**4. Memory Evidence Verification**
```bash
py -m volatile_memory.memory
```
Verifies the previously acquired memory image and calculates its SHA-256 hash. It does not acquire RAM itself.

### Memory Acquisition
Physical memory was acquired manually using FTK Imager 8.3.0.27.

The resulting memory image is stored in:
`evidence/memory/memdump.mem`

The Python memory module verifies the image's existence, size, and SHA-256 hash and records metadata in the output directory.

### Evidence Integrity
- SHA-256 hashing is used to verify collected memory evidence and hash accessible process executables.
- Collection timestamps and tool information are recorded in the JSON outputs.
- Access restrictions and collection limitations are documented where applicable.
- Collection results represent a snapshot of the system at the time of execution.

### Limitations
- Some processes and network details may be inaccessible without administrator privileges.
- Process and network information can change while collection is running.
- Registry and Startup-folder collection covers selected persistence locations, not every possible persistence mechanism.
- Memory acquisition is performed separately using FTK Imager.
- A matching SHA-256 hash verifies file consistency, but does not independently establish the authenticity of the original acquisition.

### Role 3 Deliverables
- Process collector and process tree.
- Network connections collector.
- Persistence artifacts collector.
- Memory acquisition documentation and verification wrapper.
- JSON evidence outputs.