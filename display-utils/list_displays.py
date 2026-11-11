#!/usr/bin/env python3
"""List all connected displays with their serial numbers and Quartz IDs."""

import json
import subprocess
import Quartz
from Cocoa import NSNumber


def get_display_serial_number(display_id):
    """Get serial number directly from Quartz display ID using IOKit."""
    try:
        info_dict = Quartz.CoreGraphics.CGDisplayCreateInfoDictionary(display_id)
        if not info_dict:
            return None

        # Try to extract serial number
        serial_num = info_dict.get('DisplaySerialNumber')
        if serial_num and isinstance(serial_num, NSNumber):
            return f"{serial_num.intValue():08x}"

        serial_num = info_dict.get('kDisplaySerialNumber')
        if serial_num and isinstance(serial_num, NSNumber):
            return f"{serial_num.intValue():08x}"

        return None
    except Exception:
        return None


def list_displays():
    """List all connected displays."""
    # Get displays from Quartz
    (err, displays, _) = Quartz.CGGetActiveDisplayList(10, None, None)

    print("Connected Displays:")
    print("=" * 70)

    for display_id in displays:
        current_mode = Quartz.CGDisplayCopyDisplayMode(display_id)
        if not current_mode:
            continue

        width = Quartz.CGDisplayModeGetWidth(current_mode)
        height = Quartz.CGDisplayModeGetHeight(current_mode)
        refresh = Quartz.CGDisplayModeGetRefreshRate(current_mode)
        pixel_width = Quartz.CGDisplayModeGetPixelWidth(current_mode)
        pixel_height = Quartz.CGDisplayModeGetPixelHeight(current_mode)
        is_builtin = Quartz.CGDisplayIsBuiltin(display_id)
        is_main = Quartz.CGDisplayIsMain(display_id)

        serial = get_display_serial_number(display_id)
        is_hidpi = (pixel_width == width * 2 and pixel_height == height * 2)
        mode_type = "HiDPI" if is_hidpi else "native"

        print(f"\nDisplay ID: {display_id}")
        print(f"  Serial: {serial if serial else 'N/A'}")
        print(f"  Current Mode: {width}x{height}@{refresh}Hz ({mode_type}: {pixel_width}x{pixel_height})")
        print(f"  Built-in: {is_builtin > 0}")
        print(f"  Main Display: {is_main > 0}")

    # Also get display info from system_profiler
    print("\n" + "=" * 70)
    print("System Profiler Display Info:")
    print("=" * 70)

    cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    displays_data = json.loads(result.stdout)

    for item in displays_data.get("SPDisplaysDataType", []):
        if "spdisplays_ndrvs" not in item:
            continue

        for display in item["spdisplays_ndrvs"]:
            name = display.get("_name", "Unknown")
            serial_decimal = display.get("spdisplays_serial_number", "N/A")
            serial_hex = display.get("_spdisplays_display-serial-number", "N/A")
            resolution = display.get("_spdisplays_resolution", "N/A")

            print(f"\nDisplay: {name}")
            print(f"  Serial (decimal): {serial_decimal}")
            print(f"  Serial (hex): {serial_hex}")
            print(f"  Current Resolution: {resolution}")


if __name__ == "__main__":
    list_displays()
