# Digital Forensics Investigation & Analyzer

## About the Project

A Python-based Digital Forensics Investigation and Analyzer designed to collect, preserve, analyze, and report digital evidence from authorized Windows and Linux endpoints.

The project aims to identify suspicious activities, analyze digital artifacts, and generate structured forensic reports.

## Project Objectives

- Collect digital evidence from authorized endpoints.
- Preserve evidence integrity using SHA-256 hashing.
- Analyze collected artifacts.
- Detect suspicious patterns using YARA.
- Generate a unified forensic timeline.
- Visualize investigation results through a dashboard.
- Export forensic reports in PDF and HTML formats.

## Project Modules

| Module | Responsibility |
|---|---|
| Collector Agent | Endpoint information and evidence collection |
| Volatile & Memory | Processes, network connections, and persistence |
| Logs & Browser | Event logs and browser artifacts |
| Parser & SQLite | Evidence parsing and timeline generation |
| YARA Engine | Threat detection and anomaly analysis |
| Dashboard & Reporting | Visualization and forensic reports |
| Integration | System architecture and module integration |

## Technology Stack

- Python
- Git & GitHub
- SQLite
- JSON / CSV
- YARA
- Flask or Streamlit (to be finalized)
- Pytest

## Repository Structure

```text
collector/
volatile_memory/
logs_browser/
parser/
yara_engine/
dashboard/
integration/
tests/
sample_data/
docs/
```

## Team Collaboration

The project uses GitHub branches and Pull Requests to support independent development, code reviews, and system integration.

The `main` branch contains the stable version, while `integration` is used to combine and test team contributions.

## Evidence Integrity

All evidence must be collected from authorized sources, preserved without modification, and verified using SHA-256 hashes.

Synthetic evidence and controlled laboratory data will be used for testing and demonstrations.

## Ethical Use

This tool is intended strictly for authorized digital forensic investigations and educational laboratory environments.
