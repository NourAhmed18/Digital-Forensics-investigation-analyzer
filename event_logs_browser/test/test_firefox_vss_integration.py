from pathlib import Path

from event_logs_browser.browsers.vss_acquisition import (
    collect_all_firefox_profiles_from_vss
)

from event_logs_browser.browsers.firefox import (
    collect_firefox_artifacts
)


SHADOW_DEVICE = (
    r"\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy7"
)

PROFILE_PATH = r"Users\DELL"

root = Path("test_output/Firefox-VSS-Integration-5")

acquisition_dir = root / "collected_profiles"
case_dir = root / "case"

# Step 1: Acquire Firefox profiles from VSS
acquisition = collect_all_firefox_profiles_from_vss(
    device_object=SHADOW_DEVICE,
    profile_relative_path=PROFILE_PATH,
    destination_dir=str(acquisition_dir)
)

print("VSS Acquisition:")
print("Profiles:", acquisition["profiles_collected"])
print("Files:", acquisition["files_collected"])
print("Integrity:", acquisition["integrity_verified"])

# Step 2: Analyze every acquired Firefox profile
for profile_dir in acquisition_dir.iterdir():

    if not profile_dir.is_dir():
        continue

    source_db = profile_dir / "places.sqlite"

    if not source_db.is_file():
        continue

    print("\nProcessing profile:", profile_dir.name)

    result = collect_firefox_artifacts(
        source_db=str(source_db),
        case_dir=str(case_dir),
        profile_name=profile_dir.name
    )

    print("History:", result["history_records"])
    print("Downloads:", result["download_records"])
    print("SQLite Integrity:", result["integrity_verified"])

print("\nPASS: Firefox VSS integration completed.")