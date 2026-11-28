
# YARA Engine

## Overview
The YARA Engine is a component of the Digital Forensics Investigation Analyzer project. It scans files for suspicious patterns using YARA rules.

## Features
- Loads YARA rules from the rules directory.
- Scans files for suspicious patterns.
- Reports matched rule names, tags, and metadata.
- Indicates whether a file is suspicious.
- Saves scan results as JSON.

## Project Structure
```text
yara_engine/
├── scanner.py
├── output.py
├── __init__.py
└── rules/
    └── test_rule.yar
```

## Requirements
From the repository root, install dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests
Run the following command from the repository root:

```bash
python tests/test_scanner.py
```

The tests verify:
- Positive sample detection.
- Negative sample produces no matches.

## Output
The scanner returns the file path, matched rules, tags, metadata, and an is_suspicious boolean.

The output helper saves scan results in JSON format.
