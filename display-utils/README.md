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

Changes display resolution, refresh rate, and HiDPI mode using the Quartz framework.

**Features:**
- Configure displays by serial number
- Support for HiDPI/Retina modes (2x pixel density)
- Set custom refresh rates
- Handles multiple displays independently

**Requirements:**
```bash
pip install pyobjc-framework-Quartz
```

**Usage:**
```bash
./change_display_settings.py
```

**Configuration:**
Edit the script to customize `DISPLAY_MAP` and `DISPLAY_SETTINGS` for your displays.

## Requirements

- macOS
- Python 3.11+
- For `change_display_settings.py`: `pyobjc-framework-Quartz`

## Notes

Both scripts identify displays by serial number to ensure consistent behavior even when display order changes. You can find your display serial numbers by running either script - they will print detected displays with their serial numbers.
