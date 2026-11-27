
# Windows Event Log Sample Evidence

## Description
Sample Windows Event Log files collected from a Windows 10 virtual machine for testing the Digital Forensics Investigation & Analyzer project.

## Evidence Files

| File | Original Source Channel | Format |
|---|---|---|
| Security.evtx | Security | EVTX |
| System.evtx | System | EVTX |
| Application.evtx | Application | EVTX |

## Collection Method
The files were exported using the Windows Event Utility (wevtutil).

## Integrity
The following SHA-256 hashes were calculated after transferring the sample files to the project.

| File | SHA-256 |
|---|---|
| Application.evtx | `65B2FC1898684E81DCE29B6EE6EC48C256EF3085D2641598055695ED7E539E84` |
| Security.evtx    | `4342D2A435E6057C0A759C97D9E4BC5DEB641E92F853C7A3833E7C1C94BF909F` |
| System.evtx      | `D14FDE99A242BD6E097C55344F5CE395FE536B901480995F36585B9C96835462` |


## Usage
These files are provided as test evidence for:
- Windows Event Log collection tests.
- EVTX file handling and validation.
- SHA-256 integrity verification.
- Parser and timeline integration tests.

## Important
These are sample evidence files. Original Windows Event Logs were not modified during export.
