# display-utils

macOS utilities for managing displays and application windows across multiple monitors.

## Tools

### rearrange_windows.py

Automatically moves and resizes application windows to specific positions on designated monitors.

**Features:**
- Maps displays by serial number for consistent configuration
- Supports multiple positioning modes (top, bottom, full screen)
- Configurable window sizes as screen fractions
- Concurrent window movement for fast execution
- Works with both native AppleScript and System Events

**Usage:**
```bash
./rearrange_windows.py
```

**Configuration:**
Edit the script to customize `DISPLAY_MAP` and `APP_LAYOUTS` for your setup.

### change_display_settings.py

Configures display resolution, refresh rate, positioning, and mirroring using the Quartz framework.

**Features:**
- Type-safe configuration with dataclasses (Setup, DisplayConfig, Resolution)
- Support for multiple serial numbers per logical display (portable across locations)
- Configure resolution and refresh rate per display
- HiDPI/Retina mode support (2x pixel density)
- Display positioning (relative coordinates)
- Mirror displays (e.g., mirror built-in display to main)
- Built-in display support
- Single atomic transaction for all display changes

**Requirements:**
```bash
pip install pyobjc-framework-Quartz
```

**Usage:**
```bash
./change_display_settings.py
```

**Configuration:**
Edit the `SETUP` object in the script:
```python
SETUP = Setup(
    logical_to_serial={
        "horizontal": ["serial1", "serial2"],  # Maps logical IDs to serial numbers
        "vertical": ["serial3"],
    },
    displays={
        "horizontal": DisplayConfig(
            resolution=Resolution(2560, 1440, 120),
            main=True,
        ),
        "vertical": DisplayConfig(
            resolution=Resolution(1440, 2560, 120),
            position=(-1440, -384),  # Relative to main display
        ),
        "builtin": DisplayConfig(
            mirror='main',  # Mirror the main display
        ),
    }
)
```

## Requirements

- macOS
- Python 3.11+
- For `change_display_settings.py`: `pyobjc-framework-Quartz`

## Notes

Both scripts identify displays by serial number to ensure consistent behavior even when display order changes. You can find your display serial numbers by running either script - they will print detected displays with their serial numbers.
