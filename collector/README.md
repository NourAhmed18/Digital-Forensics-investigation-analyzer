# Cross-Platform Collector Agent

The Collector Agent creates a self-contained case package for an authorized Windows or Linux endpoint. The current implementation is intentionally dependency-free and non-invasive: it collects host metadata, records provenance, preserves the configuration used, writes an execution log, and creates a SHA-256 manifest.

## Usage

From the repository root:

```bash
python -m collector.cli --output cases --case-id lab-host-01 --verbose
```

The command creates a folder similar to:

```text
cases/lab-host-01_20261120T133512Z/
├── config/collector_config.json
├── evidence/host/host_info.json
├── evidence/modules/
├── logs/collector.log
└── metadata/
    ├── collection_summary.json
    └── manifest.json
```

Use `--config path/to/config.json` to record a different configuration. A case directory is never reused, which prevents accidental overwriting of collected evidence. File paths supplied as case IDs are sanitized.

## Evidence and integrity

`host_info.json` contains the collection timestamp in UTC, operating-system details, hostname, username, process ID, working directory, and a privilege-status result. The collector does not execute shell commands and does not collect passwords, environment variables, file contents, or network payloads.

`metadata/manifest.json` contains one record per file under `evidence/`, including relative path, size, collection timestamp, source, and SHA-256. Future modules must write their outputs below `evidence/modules/` and add source-tool, command, timestamp, and limitation fields to their own artifact metadata.

## Configuration and modules

`enabled_modules` currently supports `host_info`. Other names are logged as skipped instead of failing the case, allowing the collector to integrate safely with the volatile-artifacts and historical-artifacts teams later. A skipped module is listed in `metadata/collection_summary.json`.

## Installation and testing

Python 3.10 or newer is recommended. There are no runtime dependencies:

```bash
python -m unittest discover -s tests -v
```

Only run the tool on systems and evidence for which the investigator has explicit authorization. The package is designed for controlled forensic and educational environments.
