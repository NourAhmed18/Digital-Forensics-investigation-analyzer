# Evidence Package Specification

## 1. Purpose

This document defines the standard structure of evidence packages used by the Digital Forensics Investigation & Analyzer project.

All collection modules must follow this structure to ensure consistency and simplify system integration.

## 2. Case Directory Structure

Each investigation must have its own case directory.

```text
case_<case_id>/
│
├── case_metadata.json
│
├── host_info/
│
├── volatile_artifacts/
│   ├── processes/
│   ├── network/
│   ├── persistence/
│   └── memory/
│
├── historical_artifacts/
│   ├── event_logs/
│   └── browser/
│
├── collected_files/
│
├── hashes/
│
├── logs/
│
└── reports/
```

## 3. Case Metadata

Each case must include a `case_metadata.json` file containing basic investigation information.

Example:

```json
{
  "case_id": "CASE001",
  "hostname": "WORKSTATION01",
  "username": "analyst",
  "operating_system": "Windows",
  "collection_timestamp": "2026-11-20T10:00:00Z",
  "collector_version": "1.0"
}
```

## 4. Artifact Requirements

Every collected artifact should include:

- Artifact name.
- Artifact type.
- Source path.
- Collection timestamp.
- Original file format.
- Collection tool.
- SHA-256 hash where applicable.

## 5. File Naming Convention

Files should use clear and descriptive names.

Examples:

- `processes.json`
- `network_connections.json`
- `event_logs.evtx`
- `browser_history.json`
- `collection.log`

## 6. Evidence Integrity

All modules must follow these rules:

- Preserve original evidence files.
- Do not modify original source files.
- Calculate SHA-256 hashes where applicable.
- Record collection errors and limitations.
- Keep source paths for traceability.

## 7. Integration Requirements

All modules must save their output inside the assigned case directory.

The Parser & Timeline Engine will use this package structure to locate and process collected evidence.

The YARA Detection Engine will use supported evidence files for scanning.

The Dashboard & Reporting module will use the normalized results and case metadata.

## 8. Standardization

Any changes to the evidence package structure must be reviewed by the Project Lead before implementation.

All team members must follow the agreed structure to maintain compatibility between project components.
