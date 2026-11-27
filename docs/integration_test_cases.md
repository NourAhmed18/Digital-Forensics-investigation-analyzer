# Integration Test Cases

## 1. Purpose

This document defines the test cases used to verify that all project components work correctly together.

The tests focus on module compatibility, evidence handling, data processing, detection, and reporting.

## 2. Test Environment

- Operating System: Windows / Linux (where supported).
- Programming Language: Python.
- Database: SQLite.
- Evidence Format: JSON, CSV, EVTX, and supported log files.
- Detection Engine: YARA.

## 3. Integration Test Cases

### INT-01: Case Directory Creation

**Objective:** Verify that the Collector Agent creates the required case directory.

**Steps:**
1. Execute the Collector Agent.
2. Start a new collection operation.
3. Check the generated directory.

**Expected Result:** A case directory is created using the agreed structure.

### INT-02: Host Information Collection

**Objective:** Verify host information collection.

**Steps:**
1. Run the Collector Agent.
2. Allow the host information module to execute.
3. Inspect the generated output.

**Expected Result:** Hostname, username, operating system, and privilege information are collected where supported.

### INT-03: Volatile Artifacts Collection

**Objective:** Verify collection of volatile system artifacts.

**Steps:**
1. Execute the volatile collection module.
2. Inspect process and network outputs.
3. Check persistence artifacts where supported.

**Expected Result:** Collected artifacts are saved in the correct case directory.

### INT-04: Historical Artifacts Collection

**Objective:** Verify event-log and browser-artifact collection.

**Steps:**
1. Execute the historical collection module.
2. Inspect exported event logs.
3. Check browser history and download records where supported.

**Expected Result:** Supported historical artifacts are collected while preserving original evidence.

### INT-05: Evidence Hash Verification

**Objective:** Verify evidence integrity using SHA-256.

**Steps:**
1. Select a collected evidence file.
2. Calculate its SHA-256 hash.
3. Compare it with the recorded hash.

**Expected Result:** The calculated hash matches the recorded hash when the evidence file remains unchanged.

### INT-06: Artifact Parsing

**Objective:** Verify that the Parser Engine processes supported evidence formats.

**Steps:**
1. Provide sample JSON, CSV, and supported log files.
2. Execute the Parser Engine.
3. Inspect parsing results.

**Expected Result:** Supported records are parsed into the expected structured format.

### INT-07: SQLite Database Storage

**Objective:** Verify database integration.

**Steps:**
1. Execute the Parser Engine.
2. Import normalized records into SQLite.
3. Query the database.

**Expected Result:** Parsed records are stored and can be retrieved successfully.

### INT-08: Timeline Generation

**Objective:** Verify unified timeline generation.

**Steps:**
1. Provide parsed records containing timestamps.
2. Execute the timeline module.
3. Inspect the generated timeline.

**Expected Result:** Records are arranged chronologically using normalized UTC timestamps while preserving original timestamp information.

### INT-09: YARA Detection

**Objective:** Verify YARA scanning and alert generation.

**Steps:**
1. Prepare authorized positive and negative test files.
2. Execute the YARA scanning module.
3. Inspect generated alerts.

**Expected Result:** Matching test files generate alerts containing rule names and relevant evidence references. Negative test files do not trigger the tested rules.

### INT-10: Dashboard Integration

**Objective:** Verify dashboard communication with analysis outputs.

**Steps:**
1. Import a test case.
2. Open the dashboard.
3. Inspect evidence, alerts, and timeline views.

**Expected Result:** Available case information is displayed correctly.

### INT-11: Forensic Report Generation

**Objective:** Verify report export functionality.

**Steps:**
1. Open an analyzed case.
2. Request a PDF or HTML report.
3. Inspect the generated report.

**Expected Result:** The report contains available case information, evidence references, hashes, and chain-of-custody information where recorded.

### INT-12: Error Handling

**Objective:** Verify that modules handle invalid or missing inputs.

**Steps:**
1. Provide an invalid or unsupported input file.
2. Execute the relevant module.
3. Inspect its logs.

**Expected Result:** The module handles the error without crashing unexpectedly and records the issue.

## 4. Test Results

Test results must be recorded after actual execution.

## 5. Acceptance Criteria

The integration testing phase will be considered successful when:

- All required test cases have been executed.
- Critical integration issues have been resolved.
- Evidence integrity checks produce the expected results.
- Data flows correctly between supported modules.
- Dashboard and reporting functions work with the integrated outputs.

## 6. Test Documentation

For each executed test, the team must record:

- Test ID.
- Execution date.
- Tested module.
- Actual result.
- Pass or Fail status.
- Screenshots or logs where applicable.
- Issues identified during testing.
