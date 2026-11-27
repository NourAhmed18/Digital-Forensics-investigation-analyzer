import sqlite3
from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Database file location
DATABASE_PATH = PROJECT_ROOT / "output" / "forensics.db"

# Schema file location
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection():
    """Create and return a SQLite database connection."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """Initialize the database using the project's schema."""

    with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
        schema = schema_file.read()

    connection = get_connection()

    try:
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized successfully: {DATABASE_PATH}")