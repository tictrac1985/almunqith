"""Runtime UAC elevation helper (Windows).

Reading raw devices (\\\\.\\PhysicalDriveN) requires administrator rights.
Rather than force elevation via the exe manifest (which prompts even for a
self-test), the app checks at startup and relaunches itself elevated only
when needed.
"""
import ctypes
import sys


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """Relaunch the current program elevated. Returns True if a relaunch was
    started (caller should exit); False if already admin or relaunch failed."""
    if is_admin():
        return False
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        return rc > 32          # >32 means ShellExecute succeeded
    except Exception:
        return False
