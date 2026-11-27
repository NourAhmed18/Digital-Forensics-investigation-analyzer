
from event_logs_browser.common.hashing import calculate_sha256

test_file = "test_evidence.txt"

with open(test_file, "w", encoding="utf-8") as file:
    file.write("Digital Forensics Test Evidence")

result = calculate_sha256(test_file)

print("SHA-256:", result)
