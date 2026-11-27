
from pathlib import Path

from event_logs_browser.common.hashing import calculate_sha256


SAMPLE_DIR = (
    Path(__file__).resolve().parents[2]
    / "sample_data"
    / "event_logs"
)


EXPECTED_HASHES = {
    "Application.evtx": (
        "65b2fc189868e481dce29b6ee6ec48c256ef3085d2641598055695ed7e539e84"
    ),
    "Security.evtx": (
        "4342d2a435e6057c0a759c97d9e4bc5deb641e92f853c7a3833e7c1c94bf909f"
    ),
    "System.evtx": (
        "d14fde99a242bd6e097c55344f5ce395fe536b901480995f36585b9c96835462"
    ),
}


def test_evtx_samples_integrity():

    for filename, expected_hash in EXPECTED_HASHES.items():

        file_path = SAMPLE_DIR / filename

        # Check that the file exists
        assert file_path.is_file(), (
            f"Missing evidence file: {filename}"
        )

        # Check that the file is not empty
        assert file_path.stat().st_size > 0, (
            f"Evidence file is empty: {filename}"
        )

        # Calculate SHA-256
        actual_hash = calculate_sha256(str(file_path))

        # Compare with the reference hash
        assert actual_hash == expected_hash, (
            f"SHA-256 mismatch for {filename}"
        )

        print(f"[PASS] {filename}")
        print(f"       SHA-256: {actual_hash}")


if __name__ == "__main__":
    test_evtx_samples_integrity()
    print("\nAll EVTX sample integrity tests passed!")
