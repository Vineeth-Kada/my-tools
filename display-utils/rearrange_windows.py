#!/usr/bin/env python3
"""
Move application windows to specific monitors with configured layouts.
"""

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum


class Position(Enum):
    """Window position on screen."""

    TOP = "top"
    BOTTOM = "bottom"
    FULL = "full"


# Configuration: Map serial numbers to display IDs
DISPLAY_MAP = {
    "4237464c": 1,  # DELL U2725QE (horizontal)
    "4236574c": 2,  # DELL U2725QE (vertical)
}

# Configuration: Application window layouts
# Format: application_name: (display_id, position, fraction, use_system_events)
# - display_id: which display to use (1, 2, etc.)
# - position: Position.TOP, Position.BOTTOM, or Position.FULL
# - fraction: portion of screen height (e.g., 2/3) - ignored for Position.FULL
# - use_system_events: True for apps that need System Events (like VSCode), False for native AppleScript apps
APP_LAYOUTS = {
    # Dispaly 2
    "iTerm2": (2, Position.BOTTOM, 2 / 3, False),
    "Google Chrome": (2, Position.TOP, 2 / 3, False),
    # Display 1
    "Slack": (1, Position.FULL, 1, True),
    "Code": (1, Position.FULL, 1, True),
    "Outline": (1, Position.FULL, 1, True),
}


def get_displays():
    """Get information about all connected displays using system_profiler."""
    cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def find_display_by_serial(serial_number):
    """Find display by serial number (hex or decimal format).

    Returns dict with width, height, name, and serial, or None if not found.
    """
    displays_data = get_displays()

    search_serials = [serial_number]
    try:
        decimal_val = int(serial_number)
        hex_val = f"{decimal_val:08x}"
        search_serials.append(hex_val)
    except ValueError:
        try:
            decimal_val = int(serial_number, 16)
            search_serials.append(str(decimal_val))
        except ValueError:
            pass

    for item in displays_data.get("SPDisplaysDataType", []):
        if "spdisplays_ndrvs" in item:
            for display in item["spdisplays_ndrvs"]:
                display_serial = display.get("spdisplays_serial_number", "")
                display_serial_hex = display.get(
                    "_spdisplays_display-serial-number", ""
                )

                if (
                    display_serial in search_serials
                    or display_serial_hex in search_serials
                ):
                    resolution_str = display.get("_spdisplays_resolution", "")
                    if " x " in resolution_str:
                        parts = resolution_str.split(" x ")
                        width = int(parts[0].strip())
                        height_part = parts[1].split("@")[0].strip()
                        height = int(height_part)

                        return {
                            "width": width,
                            "height": height,
                            "name": display.get("_name", "Unknown"),
                            "serial": display_serial_hex or display_serial,
                        }

    return None


def get_screen_info():
    """Get screen frame information using NSScreen via JavaScript.

    Returns list of dicts with x, y, width, height for each screen.
    NSScreen uses bottom-left origin with Y increasing upward.
    """
    result = subprocess.run(
        [
            "osascript",
            "-l",
            "JavaScript",
            "-e",
            """
        ObjC.import('Cocoa');
        var screens = $.NSScreen.screens;
        var result = [];
        for (var i = 0; i < screens.count; i++) {
            var screen = screens.objectAtIndex(i);
            var frame = screen.frame;
            result.push([frame.origin.x, frame.origin.y, frame.size.width, frame.size.height]);
        }
        JSON.stringify(result);
        """,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    screen_data = json.loads(result.stdout.strip())
    screens = []
    for x, y, width, height in screen_data:
        screens.append(
            {"x": int(x), "y": int(y), "width": int(width), "height": int(height)}
        )

    return screens


def move_app_windows(
    app_name, target_screen, position, fraction, use_system_events=False
):
    """Move all windows of an application to a specific position on the target screen.

    Coordinate systems:
    - NSScreen: bottom-left origin, Y increases upward
    - AppleScript bounds: {left, top, right, bottom}, top-left origin, Y increases downward

    Returns:
        tuple: (app_name, success_message) or (app_name, None) if failed
    """
    x = target_screen["x"]
    y = target_screen["y"]
    width = target_screen["width"]
    height = target_screen["height"]

    # Get the menubar height from the primary screen's visible frame
    screens = get_screen_info()
    max_ns_y = max(s["y"] + s["height"] for s in screens)

    result = subprocess.run(
        [
            "osascript",
            "-l",
            "JavaScript",
            "-e",
            """
        ObjC.import('Cocoa');
        var mainScreen = $.NSScreen.mainScreen;
        var frame = mainScreen.frame;
        var visible = mainScreen.visibleFrame;
        var menubarHeight = frame.size.height - visible.size.height;
        menubarHeight.toString();
        """,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    menubar_height = int(result.stdout.strip())

    effective_height = height - menubar_height

    # Transform NSScreen coordinates to AppleScript window coordinates
    # NSScreen: bottom-left origin, Y increases upward
    # AppleScript: top-left origin, Y increases downward
    # AppleScript top = max_ns_y - (ns_y + ns_height) + menubar_height
    ns_screen_top = y + height
    as_screen_top = (max_ns_y - ns_screen_top) + menubar_height

    # Calculate window position based on config
    if position == Position.FULL:
        window_top = as_screen_top
        window_bottom = as_screen_top + effective_height
    elif position == Position.TOP:
        window_height = int(effective_height * fraction)
        window_top = as_screen_top
        window_bottom = as_screen_top + window_height
    elif position == Position.BOTTOM:
        # For bottom position: window takes up 'fraction' of screen at the bottom
        # Leave (1 - fraction) empty at the top
        window_height = int(effective_height * fraction)
        window_top = as_screen_top + (effective_height - window_height)
        window_bottom = as_screen_top + effective_height
    else:
        raise ValueError(f"Unknown position: {position}")

    if use_system_events:
        script = f"""
        tell application "System Events"
            tell process "{app_name}"
                set windowCount to count of windows
                set movedCount to 0
                repeat with theWindow in windows
                    try
                        set position of theWindow to {{{x}, {window_top}}}
                        set size of theWindow to {{{width}, {window_bottom - window_top}}}
                        set movedCount to movedCount + 1
                    on error errMsg
                        log "Failed to move window: " & errMsg
                    end try
                end repeat
                return (movedCount as string) & " of " & (windowCount as string)
            end tell
        end tell
        """
    else:
        script = f"""
        tell application "{app_name}"
            set windowCount to count of windows
            set movedCount to 0
            repeat with theWindow in windows
                try
                    set bounds of theWindow to {{{x}, {window_top}, {x + width}, {window_bottom}}}
                    set movedCount to movedCount + 1
                on error errMsg
                    log "Failed to move window: " & errMsg
                end try
            end repeat
            return (movedCount as string) & " of " & (windowCount as string)
        end tell
        """

    # Retry logic to handle timing issues
    max_attempts = 3
    for attempt in range(max_attempts):
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else ""
            if "assistive access" in error_msg or "-1719" in error_msg:
                msg = (
                    f"Failed: {app_name} requires System Events accessibility permission\n"
                    f"  1. Set use_system_events=True in APP_LAYOUTS for '{app_name}'\n"
                    f"  2. Go to System Preferences → Privacy & Security → Accessibility\n"
                    f"  3. Add Terminal or iTerm to the list and grant permission"
                )
                return (app_name, msg)
            else:
                msg = (
                    f"Failed to move {app_name} windows (not running or not accessible)\n"
                    f"  Error: {error_msg if error_msg else 'Unknown error'}\n"
                    f"  Check if {app_name} is running and has windows"
                )
                return (app_name, msg)

        moved_info = result.stdout.strip()

        parts = moved_info.split(" of ")
        if len(parts) == 2:
            moved_count = int(parts[0])
            total_count = int(parts[1])

            if moved_count == total_count:
                pos_desc = (
                    position.value if position != Position.FULL else "full screen"
                )
                return (app_name, f"Moved {moved_info} windows to {pos_desc}")
            else:
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
                else:
                    return (
                        app_name,
                        f"Moved {moved_info} windows (some may have failed)",
                    )
        else:
            return (app_name, f"Moved windows")

    return (app_name, "Completed after retries")


def print_screen_info(screens):
    """Print detailed information about all screens."""
    displays_data = get_displays()
    display_map = {}
    for item in displays_data.get("SPDisplaysDataType", []):
        if "spdisplays_ndrvs" in item:
            for display in item["spdisplays_ndrvs"]:
                resolution_str = display.get("_spdisplays_resolution", "")
                if " x " in resolution_str:
                    parts = resolution_str.split(" x ")
                    width = int(parts[0].strip())
                    height_part = parts[1].split("@")[0].strip()
                    height = int(height_part)
                    key = (width, height)

                    name = display.get("_name", "Unknown")
                    serial = display.get(
                        "_spdisplays_display-serial-number",
                        display.get("spdisplays_serial_number", "N/A"),
                    )
                    resolution = display.get("_spdisplays_resolution", "N/A")

                    if key not in display_map:
                        display_map[key] = []
                    display_map[key].append((name, serial, resolution))

    print(f"Found {len(screens)} screen(s):")
    serials = []
    for i, screen in enumerate(screens):
        key = (screen["width"], screen["height"])
        if key in display_map and display_map[key]:
            display_info_tuple = display_map[key].pop(0)
            name, serial, resolution = display_info_tuple
            print(f"  Screen {i + 1}: {name} (Serial: {serial})")
            print(f"             {resolution} at ({screen['x']}, {screen['y']})")
            serials.append(serial)
        else:
            print(
                f"  Screen {i + 1}: {screen['width']}x{screen['height']} at ({screen['x']}, {screen['y']})"
            )
    return serials


def get_screen_by_display_id(screens, display_id):
    """Get screen by display ID from config."""
    # Find serial number for this display ID
    serial = None
    for ser, did in DISPLAY_MAP.items():
        if did == display_id:
            serial = ser
            break

    if not serial:
        return None

    # Find screen with matching serial
    display_info = find_display_by_serial(serial)
    if not display_info:
        return None

    for screen in screens:
        if (
            screen["width"] == display_info["width"]
            and screen["height"] == display_info["height"]
        ):
            return screen

    return None


def process_app(app_name, display_id, position, fraction, use_system_events, screens):
    """Process a single application's windows. Returns (app_name, message)."""
    target_screen = get_screen_by_display_id(screens, display_id)
    if target_screen:
        return move_app_windows(
            app_name, target_screen, position, fraction, use_system_events
        )
    else:
        return (app_name, f"Could not find display {display_id}")


def main():
    screens = get_screen_info()
    if not screens:
        print("Error: Could not detect any screens")
        sys.exit(1)

    print()
    print_screen_info(screens)
    print("\nMoving windows according to APP_LAYOUTS config...")

    with ThreadPoolExecutor(max_workers=len(APP_LAYOUTS)) as executor:
        futures = {}
        for app_name, (
            display_id,
            position,
            fraction,
            use_system_events,
        ) in APP_LAYOUTS.items():
            future = executor.submit(
                process_app,
                app_name,
                display_id,
                position,
                fraction,
                use_system_events,
                screens,
            )
            futures[future] = app_name

        for future in as_completed(futures):
            app_name, message = future.result()
            print(f"\n{app_name}:")
            print(f"  {message}")

    print("\nDone!")


if __name__ == "__main__":
    main()
