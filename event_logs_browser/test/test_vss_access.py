
import os
from pathlib import Path


def main():
    # Snapshot created in the previous test
    device_object = (
        r"\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy6"
    )

    # Get the current Windows user profile relative to C:\
    system_drive = os.environ["SystemDrive"] + "\\"
    user_profile = os.environ["USERPROFILE"]

    profile_relative = os.path.relpath(
        user_profile,
        system_drive
    )

    # Build the Chrome History path inside the snapshot
    history_path = (
        device_object.rstrip("\\")
        + "\\"
        + profile_relative
        + r"\AppData\Local\Google\Chrome\User Data\Default\History"
    )

    print("Checking Chrome History inside VSS...")
    print("Snapshot path:", history_path)

    if not os.path.isfile(history_path):
        raise FileNotFoundError(
            "Chrome History was not found inside the snapshot."
        )

    file_size = os.path.getsize(history_path)

    # Read only the SQLite file signature
    with open(history_path, "rb") as file:
        header = file.read(16)

    print("\nFile found successfully!")
    print("File size:", file_size)
    print("SQLite header:", header)

    if header != b"SQLite format 3\x00":
        raise ValueError("The file does not have a valid SQLite header.")

    print("\nPASS: Python can access Chrome History from VSS.")


if __name__ == "__main__":
    main()
