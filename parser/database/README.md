# Database Schema

## Overview
This directory contains the SQLite database schema for the Digital Forensics Investigation & Analyzer project.

## Database Tables

The database consists of nine tables:

1. **Case** – Stores investigation case information.
2. **Evidence_File** – Stores evidence file metadata and integrity information.
3. **Artifact** – Stores normalized forensic artifacts and timestamp information.
4. **Process** – Stores process-related forensic records.
5. **Network_Connection** – Stores network connection records.
6. **File_Event** – Stores file-related events.
7. **System_Event** – Stores operating system events.
8. **Browser_History** – Stores browser history and download records.
9. **Collector_Metadata** – Stores collector and host metadata.

## Relationships
- Evidence_File references Case.
- Artifact references Evidence_File.
- Process references Artifact.
- Network_Connection references Artifact.
- File_Event references Artifact.
- System_Event references Artifact.
- Browser_History references Artifact.
- Collector_Metadata references Artifact.

## Schema File

`schema.sql` contains the SQL statements required to create the database tables, primary keys, and foreign key relationships.

## Notes
- Timestamps are stored as TEXT to support ISO 8601 date-time formats.
- Foreign key enforcement should be enabled when opening a SQLite connection using `PRAGMA foreign_keys = ON;`.
- This schema is designed to support forensic artifact parsing, evidence traceability, and timeline generation.