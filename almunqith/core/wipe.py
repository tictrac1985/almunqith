"""Secure disk wipe — the deliberate opposite of recovery.

Overwrites an entire removable/data disk with multiple passes so previous
files cannot be recovered (even by AlMunqith itself), then re-creates an empty
filesystem so the disk is usable again.

SAFETY: this is the ONLY module that writes to a device. It refuses to touch a
system/boot disk, and the UI additionally requires the user to type the drive
letter to confirm. On internal SSDs, wear-levelling means overwrite is not a
perfect guarantee (documented in the UI); on cards/flash it is effective.
"""
import os
import subprocess
import sys

_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

# 3-pass scheme: zeros, ones, random — then a fresh format.
PASSES_3 = ("zeros", "ones", "random")
PASSES_1 = ("random",)

_CHUNK = 4 * 1024 * 1024


class SystemDiskError(Exception):
    """Raised when a wipe is attempted on a system/boot disk."""


def assert_wipeable(drive_info):
    """Guard: never wipe the system/boot disk."""
    if drive_info.is_system:
        raise SystemDiskError("refusing to wipe the system disk")
    if "C" in [x.upper() for x in drive_info.letters]:
        raise SystemDiskError("refusing to wipe the drive holding C:")


def _pattern_block(kind: str, length: int) -> bytes:
    if kind == "zeros":
        return b"\x00" * length
    if kind == "ones":
        return b"\xff" * length
    if kind == "random":
        return os.urandom(length)
    raise ValueError(f"unknown pattern {kind}")


def write_passes(fileobj, size: int, passes, *, chunk: int = _CHUNK,
                 on_progress=lambda done, total, idx, name: None):
    """Overwrite `size` bytes of an open writable `fileobj` with each pass
    pattern in turn. Testable against a regular file. Returns bytes written
    on the final pass."""
    total = size * len(passes)
    written_all = 0
    for idx, name in enumerate(passes):
        fileobj.seek(0)
        remaining = size
        # random needs fresh bytes each block; fixed patterns reuse one buffer
        fixed = None if name == "random" else _pattern_block(name, min(chunk, size))
        while remaining > 0:
            n = min(chunk, remaining)
            block = _pattern_block("random", n) if name == "random" else fixed[:n]
            fileobj.write(block)
            remaining -= n
            written_all += n
            on_progress(written_all, total, idx, name)
        fileobj.flush()
        try:
            os.fsync(fileobj.fileno())
        except OSError:
            pass
    return size


def _run_ps(cmd: str, timeout: int = 600):
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout,
        creationflags=_NO_WINDOW)


def set_disk_offline(disk_number: int, offline: bool):
    state = "$true" if offline else "$false"
    _run_ps(f"Set-Disk -Number {disk_number} -IsOffline {state}")


def format_script(disk_number: int, fs: str = "exFAT",
                  label: str = "CLEAN") -> str:
    """PowerShell that reinitialises the disk and lays down a fresh, empty
    filesystem spanning the whole disk. Pure function — unit-testable."""
    return (
        f"Set-Disk -Number {disk_number} -IsOffline $false -ErrorAction SilentlyContinue; "
        f"Clear-Disk -Number {disk_number} -RemoveData -RemoveOEM -Confirm:$false "
        f"-ErrorAction SilentlyContinue; "
        f"Initialize-Disk -Number {disk_number} -PartitionStyle MBR "
        f"-ErrorAction SilentlyContinue; "
        f"$p = New-Partition -DiskNumber {disk_number} -UseMaximumSize "
        f"-AssignDriveLetter; "
        f"Format-Volume -Partition $p -FileSystem {fs} "
        f"-NewFileSystemLabel '{label}' -Confirm:$false"
    )


def format_disk(disk_number: int, fs: str = "exFAT", label: str = "CLEAN"):
    return _run_ps(format_script(disk_number, fs, label))


def secure_wipe(drive_info, *, passes=PASSES_3, fs="exFAT", label="CLEAN",
                on_progress=lambda done, total, idx, name: None,
                on_log=lambda key, **kw: None):
    """Full secure-wipe orchestration for a real device (Windows).

    drive_info: DriveInfo (must not be a system disk).
    Steps: guard -> take disk offline -> multi-pass raw overwrite ->
    reinitialise + format -> bring online. Returns a summary dict.
    """
    assert_wipeable(drive_info)
    n = drive_info.number
    on_log("wipe_started", passes=len(passes))
    set_disk_offline(n, True)
    try:
        with open(drive_info.path, "r+b", buffering=0) as dev:
            write_passes(dev, drive_info.size, passes, on_progress=on_progress)
    finally:
        on_log("formatting")
        result = format_disk(n, fs, label)
    ok = result.returncode == 0
    on_log("wipe_finished", ok=ok)
    return {"ok": ok, "passes": len(passes),
            "stderr": (result.stderr or "").strip()}
