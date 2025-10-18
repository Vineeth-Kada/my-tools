#!/usr/bin/env python3
"""
Change display resolution and refresh rate for macOS displays.

This script uses the Quartz framework to configure display modes based on
serial number identification. It supports both native and HiDPI/Retina modes.

HiDPI Mode: Renders at 2x pixel density (e.g., 5120x2880 displayed as 2560x1440)
            for sharper text and graphics on high-resolution displays.
Native Mode: 1:1 pixel mapping (e.g., 2560x1440 pixels displayed as 2560x1440).

Usage:
    python3 change_display_settings.py
"""

import json
import subprocess
import sys

import Quartz


# Map display serial numbers to logical IDs for configuration
DISPLAY_MAP = {
    "4237464c": 1,  # DELL U2725QE (horizontal)
    "4236574c": 2,  # DELL U2725QE (vertical)
}

# Display settings: (width, height, refresh_rate, use_hidpi)
DISPLAY_SETTINGS = {
    1: (2560, 1440, 120, True),  # 2560x1440 @ 120Hz in HiDPI mode (5120x2880 pixels)
    2: (1440, 2560, 120, True),  # 1440x2560 @ 120Hz in HiDPI mode (2880x5120 pixels)
}


def find_display_by_serial(serial_number):
    """Find display information by serial number.

    Searches system_profiler output for a display matching the given serial number.
    Accepts both hex and decimal serial number formats.

    Args:
        serial_number: Display serial number (hex string like "4237464c" or decimal)

    Returns:
        Dict with keys: width, height, name, serial
        Returns None if display not found
    """
    cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    displays_data = json.loads(result.stdout)

    # Support both hex and decimal serial number formats
    search_serials = [serial_number]
    try:
        decimal_val = int(serial_number)
        search_serials.append(f"{decimal_val:08x}")
    except ValueError:
        try:
            decimal_val = int(serial_number, 16)
            search_serials.append(str(decimal_val))
        except ValueError:
            pass

    # Search through display data
    for item in displays_data.get("SPDisplaysDataType", []):
        if "spdisplays_ndrvs" not in item:
            continue

        for display in item["spdisplays_ndrvs"]:
            display_serial = display.get("spdisplays_serial_number", "")
            display_serial_hex = display.get("_spdisplays_display-serial-number", "")

            if display_serial in search_serials or display_serial_hex in search_serials:
                # Parse resolution string (e.g., "2560 x 1440 @ 120.00Hz")
                resolution_str = display.get("_spdisplays_resolution", "")
                if " x " not in resolution_str:
                    continue

                parts = resolution_str.split(" x ")
                width = int(parts[0].strip())
                height = int(parts[1].split("@")[0].strip())

                return {
                    "width": width,
                    "height": height,
                    "name": display.get("_name", "Unknown"),
                    "serial": display_serial_hex or display_serial,
                }

    return None


def get_quartz_display_id(serial_number):
    """Get Quartz display ID for a display with the given serial number.

    Maps serial number to Quartz's internal display ID by matching current resolution.

    Args:
        serial_number: Display serial number

    Returns:
        Quartz display ID (integer) or None if not found
    """
    display_info = find_display_by_serial(serial_number)
    if not display_info:
        return None

    # Get all active displays from Quartz
    (err, displays, num_displays) = Quartz.CGGetActiveDisplayList(10, None, None)

    # Find display with matching current resolution
    for display_id in displays:
        current_mode = Quartz.CGDisplayCopyDisplayMode(display_id)
        if not current_mode:
            continue

        width = Quartz.CGDisplayModeGetWidth(current_mode)
        height = Quartz.CGDisplayModeGetHeight(current_mode)

        if width == display_info["width"] and height == display_info["height"]:
            return display_id

    return None


def set_display_mode(display_id, target_width, target_height, target_refresh, use_hidpi=False):
    """Set display to specified resolution and refresh rate.

    Args:
        display_id: Quartz display ID
        target_width: Target UI width in points
        target_height: Target UI height in points
        target_refresh: Target refresh rate in Hz
        use_hidpi: If True, use HiDPI/Retina mode (2x pixel density)

    Returns:
        True if mode change successful, False otherwise
    """
    # CRITICAL: Must pass kCGDisplayShowDuplicateLowResolutionModes to see HiDPI modes
    # Without this option, HiDPI modes are hidden from the modes list
    options = {Quartz.kCGDisplayShowDuplicateLowResolutionModes: True}
    modes = Quartz.CGDisplayCopyAllDisplayModes(display_id, options)

    # Find mode matching target resolution, refresh rate, and HiDPI requirement
    best_match = None
    for mode in modes:
        width = Quartz.CGDisplayModeGetWidth(mode)
        height = Quartz.CGDisplayModeGetHeight(mode)
        refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
        pixel_width = Quartz.CGDisplayModeGetPixelWidth(mode)
        pixel_height = Quartz.CGDisplayModeGetPixelHeight(mode)

        # Check resolution and refresh rate
        if width != target_width or height != target_height or refresh != target_refresh:
            continue

        # HiDPI mode has 2x pixel density
        is_hidpi = (pixel_width == width * 2 and pixel_height == height * 2)

        if use_hidpi == is_hidpi:
            best_match = mode
            break

    if not best_match:
        mode_type = "HiDPI" if use_hidpi else "native"
        print(f"  ❌ No {mode_type} mode found for {target_width}x{target_height}@{target_refresh}Hz")
        return False

    # Begin display configuration transaction
    config = Quartz.CGBeginDisplayConfiguration(None)
    if config[0] != 0:
        print("  ❌ Failed to begin display configuration")
        return False

    config_ref = config[1]

    # Configure the display mode
    result = Quartz.CGConfigureDisplayWithDisplayMode(config_ref, display_id, best_match, None)
    if result != 0:
        print(f"  ❌ Failed to configure display: error {result}")
        Quartz.CGCancelDisplayConfiguration(config_ref)
        return False

    # Apply configuration (kCGConfigureForSession = temporary, until reboot/re-login)
    result = Quartz.CGCompleteDisplayConfiguration(config_ref, Quartz.kCGConfigureForSession)
    if result != 0:
        print(f"  ❌ Failed to apply configuration: error {result}")
        return False

    # Success - show what was configured
    pixel_width = Quartz.CGDisplayModeGetPixelWidth(best_match)
    pixel_height = Quartz.CGDisplayModeGetPixelHeight(best_match)
    mode_desc = f"{target_width}x{target_height}@{target_refresh}Hz"
    if use_hidpi:
        mode_desc += f" (HiDPI: {pixel_width}x{pixel_height})"
    print(f"  ✓ Successfully set to {mode_desc}")
    return True


def main():
    """Configure all displays according to DISPLAY_SETTINGS."""
    print("Display Settings Configuration")
    print("=" * 50)

    success_count = 0
    fail_count = 0

    for serial, config_id in DISPLAY_MAP.items():
        if config_id not in DISPLAY_SETTINGS:
            print(f"\n⚠️  Display {config_id} (serial {serial}): No settings configured")
            continue

        target_width, target_height, target_refresh, use_hidpi = DISPLAY_SETTINGS[config_id]
        print(f"\nDisplay {config_id} (serial {serial}):")

        # Look up display information
        display_info = find_display_by_serial(serial)
        if not display_info:
            print("  ❌ Display not found")
            fail_count += 1
            continue

        print(f"  Name: {display_info['name']}")
        print(f"  Current: {display_info['width']}x{display_info['height']}")

        # Get Quartz display ID
        quartz_id = get_quartz_display_id(serial)
        if quartz_id is None:
            print("  ❌ Could not find Quartz display ID")
            fail_count += 1
            continue

        # Show target configuration
        mode_type = "HiDPI" if use_hidpi else "native"
        print(f"  Target: {target_width}x{target_height}@{target_refresh}Hz ({mode_type})")

        # Apply display mode
        if set_display_mode(quartz_id, target_width, target_height, target_refresh, use_hidpi):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 50)
    print(f"Summary: {success_count} successful, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
