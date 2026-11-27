
import json
from pathlib import Path

from event_logs_browser.common.metadata import create_artifact_metadata

# Create sample evidence files for testing
source_file = Path("test_source.txt")
collected_file = Path("test_collected.txt")

source_file.write_text(
    "Digital Forensics Test Evidence",
    encoding="utf-8"
)

collected_file.write_text(
    "Digital Forensics Test Evidence",
    encoding="utf-8"
)

# Generate metadata
metadata = create_artifact_metadata(
    source_path=str(source_file),
    collected_path=str(collected_file),
    artifact_type="Test File",
    collection_tool="Manual Test"
)

# Display metadata
print(json.dumps(metadata, indent=4))
