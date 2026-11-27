import tempfile
from pathlib import Path

from event_logs_browser.common.evidence_copy import copy_evidence


with tempfile.TemporaryDirectory() as temp_dir:

    temp = Path(temp_dir)

    source = temp / "source_evidence.txt"

    destination = (
        temp
        / "case_001"
        / "historical_artifacts"
        / "source_evidence.txt"
    )

    # Create a sample evidence file
    source.write_text(
        "Digital Forensics Test Evidence",
        encoding="utf-8"
    )

    # Copy and verify the evidence
    result = copy_evidence(
        str(source),
        str(destination)
    )

    print(result)

    print("Original still exists:", source.is_file())
    print("Copied file exists:", destination.is_file())

    print(
        "Same content:",
        source.read_bytes() == destination.read_bytes()
    )