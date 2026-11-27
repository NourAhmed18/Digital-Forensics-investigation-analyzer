# Module Interfaces

## 1. Purpose

This document defines the communication interfaces between the six main project components.

The goal is to ensure that all modules use consistent input and output formats and can be integrated into one working system.

## 2. General Integration Rules

- Each module must have a clearly defined responsibility.
- All modules must use the shared case directory structure.
- JSON should be used for structured metadata and artifact records where applicable.
- Original evidence files must remain unchanged.
- Each module must document its inputs, outputs, errors, and dependencies.
- All timestamps must preserve their original values and timezone information.

## 3. Module Interfaces

### 3.1 Cross-Platform Collector Agent

**Input:**
- Collection configuration.
- Target system information.

**Responsibilities:**
- Detect operating system, hostname, and username.
- Create the case directory.
- Launch supported collection modules.

**Output:**
- Case metadata.
- Host information.
- Collection logs.
- Structured evidence package.

**Output Location:**
`case_<case_id>/`

### 3.2 Volatile Artifacts & Memory Acquisition

**Input:**
- Case directory.
- Collection permissions and configuration.

**Responsibilities:**
- Collect running processes.
- Collect active network connections and listening ports.
- Collect persistence indicators.
- Acquire memory where supported.

**Output:**
- Process information.
- Network connection records.
- Persistence artifacts.
- Memory acquisition files and metadata.

**Output Location:**
`volatile_artifacts/`

### 3.3 Event Logs, Browser & Historical Artifacts

**Input:**
- Case directory.
- Supported operating-system and browser sources.

**Responsibilities:**
- Export relevant event and system logs.
- Collect browser history and download records.
- Extract artifact metadata.
- Preserve original evidence copies.

**Output:**
- Event log files.
- Browser history records.
- Download records.
- Source paths and collection metadata.

**Output Location:**
`historical_artifacts/`

### 3.4 Parser, SQLite & Timeline Engine

**Input:**
- Structured evidence package.
- JSON, CSV, EVTX, log files, browser databases, and collector metadata.

**Responsibilities:**
- Parse supported evidence formats.
- Normalize timestamps into UTC while preserving original timestamps and timezone information.
- Store normalized records in SQLite.
- Generate a unified timeline.
- Link records to their original evidence sources.

**Output:**
- SQLite database.
- Normalized artifact records.
- Unified timeline.
- Parsing logs and errors.

**Output Location:**
`case_<case_id>/analysis/`

### 3.5 YARA Detection Engine

**Input:**
- Collected evidence files.
- Supported memory inputs.
- YARA rules.

**Responsibilities:**
- Scan supported files and memory inputs.
- Identify suspicious indicators.
- Assign severity and confidence.
- Record the matching rule and source evidence.

**Output:**
- Structured detection alerts.
- Rule names.
- Severity and confidence values.
- Evidence references.

**Output Location:**
`case_<case_id>/alerts/`

### 3.6 Dashboard & Reporting

**Input:**
- Case metadata.
- SQLite database.
- Unified timeline.
- YARA detection alerts.
- Evidence references.

**Responsibilities:**
- Import and browse investigation cases.
- Display evidence and processes.
- Display network connections and alerts.
- Provide timeline visualization.
- Support searching and filtering.
- Export PDF and HTML forensic reports.

**Output:**
- Dashboard views.
- Search and filtering results.
- PDF/HTML forensic reports.
- Report metadata and hash information.

**Output Location:**
`case_<case_id>/reports/`

## 4. Shared Data Requirements

All modules should follow these common requirements:

- Every investigation must have a unique case ID.
- Every artifact must have a clear source reference.
- Timestamps should use ISO 8601 format.
- UTC timestamps must be used for normalized timeline records.
- SHA-256 hashes should be calculated where applicable.
- Collection errors must be documented.
- Original evidence must be preserved.

## 5. Integration Workflow

The expected communication flow is:

1. The Collector Agent creates the case directory.
2. Volatile and historical collection modules produce evidence.
3. The Parser Engine reads supported artifacts.
4. Parsed records are stored in the SQLite database.
5. The YARA Engine scans supported evidence and generates alerts.
6. The Dashboard reads the database, timeline, and alerts.
7. The Reporting component exports forensic reports.

## 6. Interface Compatibility

Each team member must provide:

- Module source code.
- Input and output documentation.
- Required dependencies.
- Sample output files.
- Basic test cases.
- Known limitations and error-handling information.

The Project Lead is responsible for reviewing interface compatibility and resolving integration issues.

## 7. Change Management

Any changes to module inputs, outputs, file formats, or directory structures must be documented and reviewed before integration.

This specification may be updated as the project implementation evolves.
