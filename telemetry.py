"""
Pix42 - Anonymous Telemetry
GDPR-compliant, silent usage analytics without terminal windows.
"""

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from urllib import request as urllib_request
    import urllib.request
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

try:
    from PySide6.QtWidgets import QApplication
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


# Constants
TELEMETRY_ENDPOINT = "https://www.demahub.com/pix42/usage/analytics.php"
CRASH_MARKER_FILENAME = ".pix42_session_marker"
TELEMETRY_TIMEOUT = 10  # seconds


# Extension → format group mapping (used by track_file_viewed)
_EXT_TO_FORMAT: dict[str, str] = {
    ".jpg": "jpeg", ".jpeg": "jpeg",
    ".png": "png",
    ".gif": "gif",
    ".webp": "webp",
    ".tif": "tiff", ".tiff": "tiff",
    ".bmp": "bmp",
    ".ico": "ico",
    ".ppm": "ppm", ".pgm": "ppm", ".pbm": "ppm",
    ".psd": "psd",
    ".fit": "fits", ".fits": "fits", ".fts": "fits",
    ".cr2": "raw", ".cr3": "raw", ".nef": "raw", ".nrw": "raw",
    ".arw": "raw", ".srf": "raw", ".sr2": "raw", ".rw2": "raw",
    ".raf": "raw", ".orf": "raw", ".dng": "raw", ".pef": "raw",
    ".x3f": "raw", ".kdc": "raw", ".dcr": "raw", ".mrw": "raw",
    ".3fr": "raw", ".mef": "raw", ".erf": "raw", ".rwl": "raw",
    ".iiq": "raw",
    ".mp4": "video", ".avi": "video", ".mov": "video", ".mkv": "video",
    ".wmv": "video", ".webm": "video", ".m4v": "video", ".flv": "video",
    ".mpeg": "video", ".mpg": "video",
    ".mp3": "audio", ".wav": "audio", ".flac": "audio", ".aac": "audio",
    ".ogg": "audio", ".m4a": "audio", ".wma": "audio", ".opus": "audio",
}


class SessionStats:
    """Track session statistics in memory (singleton pattern)."""

    # Files viewed per format group (e.g. {"jpeg": 12, "raw": 5, ...})
    files_by_format: dict[str, int] = {}

    # Set of unique file paths viewed this session (for deduplication)
    _viewed_paths: set[str] = set()

    crash_detected_at_startup: bool = False
    crash_type: Optional[str] = None

    @classmethod
    def reset(cls) -> None:
        cls.files_by_format = {}
        cls._viewed_paths = set()
        cls.crash_type = None

    @classmethod
    def get_files_by_format(cls) -> dict:
        return {k: v for k, v in cls.files_by_format.items() if v > 0}


def get_user_data_dir() -> Path:
    """Get platform-specific user data directory."""
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    data_dir = Path(base) / "Pix42"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_crash_marker_path() -> Path:
    return get_user_data_dir() / CRASH_MARKER_FILENAME


def get_device_id() -> str:
    """
    Generate anonymous, persistent device identifier.
    Uses SHA256 hash of machine-specific info (non-reversible).
    GDPR-compliant: anonymous, no personal data.
    Returns 16-character hex string.
    """
    try:
        import hashlib
        import uuid

        device_id_file = get_user_data_dir() / ".pix42_device_id"

        if device_id_file.exists():
            device_id = device_id_file.read_text().strip()
            if device_id and len(device_id) == 16:
                return device_id

        machine_data = f"{platform.node()}{uuid.getnode()}{platform.machine()}"
        hash_obj = hashlib.sha256(machine_data.encode('utf-8'))
        device_id = hash_obj.hexdigest()[:16]
        device_id_file.write_text(device_id)
        return device_id

    except Exception:
        import hashlib
        import random
        return hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]


def get_os_version() -> str:
    """Get OS name: 'windows', 'windows-11', or 'mac'."""
    try:
        system = platform.system()
        if system == "Windows":
            try:
                if sys.getwindowsversion().build >= 22000:
                    return "windows-11"
            except (AttributeError, Exception):
                pass
            return "windows"
        elif system == "Darwin":
            return "mac"
        else:
            # Not a target platform, report as-is (won't be counted in analytics)
            return f"{system}-{platform.release()}"
    except Exception:
        return "unknown"


def get_os_language() -> str:
    """Get OS language code (e.g. 'en', 'it', 'de')."""
    try:
        import locale
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            return system_locale.split('_')[0].lower()
        return "unknown"
    except Exception:
        return "unknown"


def get_screen_category() -> str:
    """Get physical screen resolution category."""
    if not PYSIDE6_AVAILABLE:
        return "unknown"
    try:
        app = QApplication.instance()
        if not app:
            return "unknown"
        primary_screen = app.primaryScreen()
        if not primary_screen:
            return "unknown"
        size = primary_screen.size()
        dpr = primary_screen.devicePixelRatio()
        width = int(size.width() * dpr)
        height = int(size.height() * dpr)
        total_pixels = width * height
        if total_pixels >= 20_000_000:
            return ">4K"
        elif total_pixels >= 8_000_000:
            return "4K"
        elif total_pixels >= 3_500_000:
            return "2K"
        elif total_pixels >= 2_000_000:
            return "FHD"
        else:
            return "HD"
    except Exception:
        return "unknown"


def check_crash_detected() -> bool:
    return get_crash_marker_path().exists()


def create_session_marker() -> None:
    try:
        marker_path = get_crash_marker_path()
        marker_path.write_text(datetime.now(timezone.utc).isoformat())
    except Exception:
        pass


def get_session_duration() -> Optional[int]:
    """Return session duration in minutes, or None."""
    try:
        marker_path = get_crash_marker_path()
        if not marker_path.exists():
            return None
        start_time = datetime.fromisoformat(marker_path.read_text().strip())
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        return int(duration_seconds / 60)
    except Exception:
        return None


def remove_session_marker() -> None:
    try:
        marker_path = get_crash_marker_path()
        if marker_path.exists():
            marker_path.unlink()
    except Exception:
        pass


def track_file_viewed(extension: str, path: Optional[str] = None) -> None:
    """
    Track a file being viewed. Call this when a file is successfully loaded.

    Args:
        extension: File extension including dot (e.g. '.jpg', '.cr2')
        path: Optional file path string for deduplication within a session.
              If provided, the same file path won't be counted twice.
    """
    try:
        # Deduplicate by path within the session
        if path is not None:
            if path in SessionStats._viewed_paths:
                return
            SessionStats._viewed_paths.add(path)

        fmt = _EXT_TO_FORMAT.get(extension.lower(), "other")
        SessionStats.files_by_format[fmt] = SessionStats.files_by_format.get(fmt, 0) + 1
    except Exception:
        pass


def _build_session_duration_bucket(minutes: Optional[int]) -> Optional[str]:
    if minutes is None:
        return None
    if minutes < 5:
        return "<5"
    elif minutes < 15:
        return "5-15"
    elif minutes < 30:
        return "15-30"
    elif minutes < 60:
        return "30-60"
    elif minutes < 120:
        return "1-2h"
    else:
        return ">2h"


def build_telemetry_payload(app_version: str) -> dict:
    """Build telemetry payload from the current session."""
    now = datetime.now(timezone.utc)
    timestamp = now.replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    data: dict = {
        "device_id": get_device_id(),
        "timestamp": timestamp,
        "app_version": app_version,
        "os": get_os_version(),
        "crash_detected": SessionStats.crash_detected_at_startup,
    }

    os_lang = get_os_language()
    if os_lang != "unknown":
        data["os_language"] = os_lang

    session_bucket = _build_session_duration_bucket(get_session_duration())
    if session_bucket:
        data["session_duration"] = session_bucket

    screen_cat = get_screen_category()
    if screen_cat != "unknown":
        data["screen"] = screen_cat

    files_by_format = SessionStats.get_files_by_format()
    if files_by_format:
        data["files_by_format"] = files_by_format

    if SessionStats.crash_type:
        data["crash_type"] = SessionStats.crash_type

    return data


def send_telemetry_silent(data: dict, debug: bool = False) -> bool:
    """Send telemetry data silently. Non-blocking, fails silently."""
    if not URLLIB_AVAILABLE:
        return False
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib_request.Request(
            TELEMETRY_ENDPOINT,
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        if debug:
            print(f"Sending to: {TELEMETRY_ENDPOINT}")
            print(f"Payload: {json.dumps(data, indent=2)}")

        proxy_handler = urllib.request.ProxyHandler()
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req, timeout=TELEMETRY_TIMEOUT) as response:
            if debug:
                print(f"Response: {response.status}")
            return response.status == 200
    except Exception as e:
        if debug:
            print(f"Telemetry error: {e}")
        return False


def init_telemetry(app_version: str) -> None:
    """
    Initialize telemetry at application startup.
    Call this as early as possible in main().
    """
    SessionStats.reset()
    SessionStats.crash_detected_at_startup = check_crash_detected()
    create_session_marker()


def cleanup_telemetry(app_version: str, debug: bool = False) -> None:
    """
    Send telemetry and clean up at shutdown.
    Call this when the application is about to exit.
    """
    try:
        data = build_telemetry_payload(app_version)
        if debug:
            print("\n=== Pix42 Telemetry Payload ===")
            print(json.dumps(data, indent=2))
            print("================================\n")
        success = send_telemetry_silent(data, debug=debug)
        if debug:
            print(f"Telemetry: {'sent' if success else 'failed'}")
    except Exception as e:
        if debug:
            print(f"Telemetry cleanup error: {e}")
    finally:
        remove_session_marker()


if __name__ == "__main__":
    # Quick test: show payload without sending
    from __init__ import __version__
    init_telemetry(__version__)
    # Simulate some views
    track_file_viewed(".jpg", "/test/photo1.jpg")
    track_file_viewed(".jpg", "/test/photo2.jpg")
    track_file_viewed(".cr2", "/test/raw1.cr2")
    track_file_viewed(".png", "/test/image.png")
    track_file_viewed(".fits", "/test/star.fits")
    track_file_viewed(".mp4", "/test/video.mp4")

    data = build_telemetry_payload(__version__)
    print(json.dumps(data, indent=2))
