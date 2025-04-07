"""
Platform module for Myth server.

Defines platform-specific constants and utilities.
Copyright (c) 1997-2002 Bungie Studios
"""

import sys
import platform
import enum

class Platform(enum.Enum):
    """Supported platforms"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "darwin"

def get_current_platform() -> Platform:
    """Get the current platform"""
    system = sys.platform.lower()
    if system.startswith("win"):
        return Platform.WINDOWS
    elif system.startswith("linux"):
        return Platform.LINUX
    elif system.startswith("darwin"):
        return Platform.MACOS
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

def is_64bit() -> bool:
    """Check if running on 64-bit platform"""
    return sys.maxsize > 2**32

def get_platform_info() -> dict:
    """Get detailed platform information"""
    return {
        "platform": get_current_platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_64bit": is_64bit()
    }
