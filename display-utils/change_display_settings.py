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
import time
from dataclasses import dataclass
from typing import Optional

import objc
import Quartz

# Load MonitorPanel private framework for rotation support
MonitorPanel = objc.loadBundle(
    'MonitorPanel',
    bundle_path='/System/Library/PrivateFrameworks/MonitorPanel.framework',
    module_globals=globals()
)
MPDisplay = objc.lookUpClass('MPDisplay')

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================


@dataclass
class Resolution:
    width: int
    height: int
    refresh_rate: int
    hidpi: bool = True
    rotation: int = 0  # 0, 90, 180, or 270 degrees


@dataclass
class DisplayConfig:
    resolution: Optional[Resolution] = None
    position: Optional[tuple[int, int]] = None
    main: bool = False
    mirror: Optional[str] = None


@dataclass
class Setup:
    logical_to_serial: dict[str, list[str]]  # logical_id -> [serial_number, ...]
    displays: dict[str, DisplayConfig]


# Define your setup here
SETUP = Setup(
    logical_to_serial={
        "horizontal": ["4237464c", "office_horizontal"],
        "vertical": ["4236574c", "office_vertical"],
    },
    displays={
        "horizontal": DisplayConfig(
            resolution=Resolution(2560, 1440, 120),
            main=True,
        ),
        "vertical": DisplayConfig(
            resolution=Resolution(1440, 2560, 120, rotation=90),
            position=(-1440, -384),
        ),
        "builtin": DisplayConfig(
            mirror="main",
        ),
    },
)

# =============================================================================


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

    Maps serial number to Quartz's internal display ID by matching serial numbers.
    This ensures correct identification even when multiple displays have the same resolution.

    Args:
        serial_number: Display serial number (hex string or decimal)

    Returns:
        Quartz display ID (integer) or None if not found
    """
    # Convert hex serial to decimal for comparison with Quartz serial
    try:
        target_serial_dec = int(serial_number, 16)
    except ValueError:
        # If not hex, try as decimal
        try:
            target_serial_dec = int(serial_number)
        except ValueError:
            return None

    # Get all active displays from Quartz
    (err, displays, num_displays) = Quartz.CGGetActiveDisplayList(10, None, None)

    # Find display with matching serial number
    for display_id in displays:
        quartz_serial = Quartz.CGDisplaySerialNumber(display_id)
        if quartz_serial == target_serial_dec:
            return display_id

    return None


def set_display_mode(
    display_id, target_width, target_height, target_refresh, use_hidpi=False
):
    """Set display to specified resolution and refresh rate.

    Automatically tries swapping width/height if the requested mode doesn't exist.
    This handles rotated displays where config specifies logical orientation.

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

    # Helper function to find a mode
    def find_mode(width, height):
        for mode in modes:
            mode_width = Quartz.CGDisplayModeGetWidth(mode)
            mode_height = Quartz.CGDisplayModeGetHeight(mode)
            refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
            pixel_width = Quartz.CGDisplayModeGetPixelWidth(mode)
            pixel_height = Quartz.CGDisplayModeGetPixelHeight(mode)

            if mode_width != width or mode_height != height or refresh != target_refresh:
                continue

            is_hidpi = pixel_width == mode_width * 2 and pixel_height == mode_height * 2
            if use_hidpi == is_hidpi:
                return mode
        return None

    # Try requested dimensions first
    best_match = find_mode(target_width, target_height)

    # Try swapping width/height for rotated displays
    if not best_match and target_width != target_height:
        best_match = find_mode(target_height, target_width)

    if not best_match:
        mode_type = "HiDPI" if use_hidpi else "native"
        print(
            f"  ❌ No {mode_type} mode found for {target_width}x{target_height}@{target_refresh}Hz"
        )
        return False

    # Begin display configuration transaction
    config = Quartz.CGBeginDisplayConfiguration(None)
    if config[0] != 0:
        print("  ❌ Failed to begin display configuration")
        return False

    config_ref = config[1]

    # Configure the display mode
    result = Quartz.CGConfigureDisplayWithDisplayMode(
        config_ref, display_id, best_match, None
    )
    if result != 0:
        print(f"  ❌ Failed to configure display: error {result}")
        Quartz.CGCancelDisplayConfiguration(config_ref)
        return False

    # Apply configuration (kCGConfigureForSession = temporary, until reboot/re-login)
    result = Quartz.CGCompleteDisplayConfiguration(
        config_ref, Quartz.kCGConfigureForSession
    )
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


def set_display_rotation(display_id, degree):
    """Set display rotation using MonitorPanel framework.

    Args:
        display_id: Quartz display ID
        degree: Rotation angle (0, 90, 180, or 270)

    Returns:
        True if successful, False otherwise
    """
    if degree not in [0, 90, 180, 270]:
        print(f"  ❌ Invalid rotation: {degree}")
        return False

    current_rotation = Quartz.CGDisplayRotation(display_id)
    if current_rotation == degree:
        return True  # Already at target rotation

    try:
        # Use autorelease pool for proper memory management
        mp_display = MPDisplay.alloc().initWithCGSDisplayID_(display_id)
        mp_display.setOrientation_(degree)

        # Don't manually release - PyObjC handles this automatically
        # Wait for rotation to complete
        wait_seconds = 10
        begin_time = time.time()

        while Quartz.CGDisplayRotation(display_id) != degree:
            if time.time() - begin_time >= wait_seconds:
                print(f"  ❌ Timeout waiting for rotation")
                return False
            time.sleep(0.1)

        return True

    except Exception as e:
        print(f"  ❌ Rotation error: {e}")
        return False


def get_display_id(serial_or_builtin):
    """Get Quartz display ID for serial number or 'builtin'."""
    if serial_or_builtin == "builtin":
        (err, displays, _) = Quartz.CGGetActiveDisplayList(5, None, None)
        for display_id in list(displays) + [1]:  # 1 is just a coincidence on my system?
            if (
                Quartz.CGDisplayIsBuiltin(display_id) > 0
            ):  # -1 is probably an error code
                return display_id
        return None
    return get_quartz_display_id(serial_or_builtin)


def configure_display(quartz_id, config: DisplayConfig, name: str):
    """Configure resolution and rotation for a single display."""
    if config.mirror or not config.resolution:
        return True

    res = config.resolution
    print(f"\n{name}:")
    mode = "HiDPI" if res.hidpi else "native"
    rotation_info = f", {res.rotation}°" if res.rotation != 0 else ""
    print(f"  Target: {res.width}x{res.height}@{res.refresh_rate}Hz ({mode}{rotation_info})")

    # Set rotation first (displayplacer sets rotation before resolution)
    if res.rotation != 0:
        if not set_display_rotation(quartz_id, res.rotation):
            print("  ❌ Failed to set rotation")
            return False

    # Then set resolution
    success = set_display_mode(
        quartz_id, res.width, res.height, res.refresh_rate, res.hidpi
    )
    if not success:
        print("  ❌ Failed to set mode")
    return success


def apply_arrangement(display_map, displays, main_id):
    """Apply display positioning and mirroring in a single transaction."""
    cfg = Quartz.CGBeginDisplayConfiguration(None)
    if cfg[0] != 0:
        print("\n❌ Failed to begin configuration")
        return False

    config_ref = cfg[1]

    # Set main display at origin
    if main_id:
        Quartz.CGConfigureDisplayOrigin(config_ref, main_id, 0, 0)

    # Position and mirror other displays
    for logical_id, quartz_id in display_map.items():
        config = displays[logical_id]

        if quartz_id == main_id:
            continue

        if config.mirror == "main" and main_id:
            Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, quartz_id, main_id)
        elif config.position:
            x, y = config.position
            Quartz.CGConfigureDisplayOrigin(config_ref, quartz_id, x, y)

    result = Quartz.CGCompleteDisplayConfiguration(
        config_ref, Quartz.kCGConfigureForSession
    )
    return result == 0


def apply_setup(setup: Setup):
    """Apply display setup configuration."""
    print("Display Setup Configuration")
    print("=" * 50)

    displays_to_configure = {}
    main_id = None

    for logical_id, config in setup.displays.items():
        # Determine serial number(s) and find connected display
        quartz_id = None

        if logical_id == "builtin":
            quartz_id = get_display_id("builtin")
        elif logical_id in setup.logical_to_serial:
            # Try each serial number for this logical ID
            for serial in setup.logical_to_serial[logical_id]:
                display_id = get_display_id(serial)
                if display_id:
                    if quartz_id is not None:
                        raise ValueError(
                            f"\n❌ {logical_id}: Multiple displays connected. Only one permitted per logical ID."
                        )
                    quartz_id = display_id
        else:
            raise ValueError(f"\n❌ {logical_id}: No serial mapping found in config")

        # Skip if display not connected
        if not quartz_id:
            print(f"\n⚠️  {logical_id} not connected, skipping")
            continue

        # Configure this display
        configure_display(quartz_id, config, logical_id)
        displays_to_configure[logical_id] = quartz_id

        if config.main:
            if main_id:
                raise ValueError("Two main displays specified")
            else:
                main_id = quartz_id

    if apply_arrangement(displays_to_configure, setup.displays, main_id):
        print("\n✓ Setup complete")
    else:
        print("\n❌ Failed to apply arrangement")


def main():
    """Configure displays according to SETUP."""
    apply_setup(SETUP)


if __name__ == "__main__":
    main()
