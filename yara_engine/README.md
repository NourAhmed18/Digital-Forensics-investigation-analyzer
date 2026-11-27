# YARA Engine

## Overview
The YARA Engine is a component of the Digital Forensics Investigation Analyzer project. It scans files for suspicious patterns using YARA rules.

## Features
- Loads YARA rules from the rules directory.
- Scans files for suspicious patterns.
- Reports matched rule names.
- Returns whether a file is suspicious.

## Project Structure
```text
yara_engine/
├── scanner.py
├── output.py
├── __init__.py
└── rules/
    └── test_rule.yar

Install the required dependencies:
pip install -r requirements.txt


From the project root directory, run:
python tests/test_scanner.py


- positive_sample.txt: Contains a test marker expected to trigger the YARA rule.
- negative_sample.txt: Contains harmless text and should produce no matches.
Output
The scanner reports matching YARA rules and indicates whether the scanned file is suspicious.
