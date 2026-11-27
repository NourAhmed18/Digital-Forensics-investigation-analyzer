# Collector Agent integration contract

## Case package

Each execution creates a new directory under the selected output directory. The directory name contains the requested case ID and a UTC timestamp. The collector does not overwrite an existing case.

The stable paths are:

- `config/collector_config.json`: configuration copied into the case.
- `evidence/host/host_info.json`: endpoint metadata collected by this module.
- `evidence/modules/`: reserved for integrated collection modules.
- `logs/collector.log`: execution log.
- `metadata/manifest.json`: SHA-256 records for every file under `evidence/`.
- `metadata/collection_summary.json`: completion status and skipped modules.

## Module contract

An integrated module should be enabled by name in `collector/collector_config.json`, write only inside `evidence/modules/<module-name>/`, and produce JSON or CSV with a `schema_version`, `collected_at_utc`, `source_tool`, and `limitations` field. It must preserve the original source path where applicable and must not modify source evidence.

Modules that are not installed are recorded as skipped. This lets the collector run on a minimal endpoint while the volatile-artifacts and historical-artifacts modules are integrated incrementally.

## Integrity and limitations

The manifest uses SHA-256 and records relative paths, sizes, timestamps, and source. It is generated after collection. The collector is a metadata agent; it does not acquire RAM, export event logs, read browser databases, or collect file contents yet. Those capabilities belong to the other project areas and should be added as explicit, documented modules.
