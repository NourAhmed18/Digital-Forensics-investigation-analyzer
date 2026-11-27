
from event_logs_browser.windows.vss import create_shadow_copy


def main():
    print("Starting VSS test...")

    result = create_shadow_copy("C:\\")

    print("\nVSS created successfully!")
    print("Return Value:", result["return_value"])
    print("Shadow ID:", result["shadow_id"])
    print("Device Object:", result["device_object"])
    print("Volume:", result["volume_name"])
    print("Install Date:", result["install_date"])


if __name__ == "__main__":
    main()
