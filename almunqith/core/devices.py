"""Windows drive enumeration via PowerShell (no external deps)."""
import json
import subprocess
import sys
from dataclasses import dataclass, field

# In a frozen windowed app, launching a console program (powershell) pops a
# console window unless we suppress it. This keeps drive enumeration silent.
_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0   # CREATE_NO_WINDOW


@dataclass
class DriveInfo:
    number: int
    path: str
    size: int
    bus: str
    friendly: str
    letters: list = field(default_factory=list)
    is_system: bool = False


def _as_list(js: str):
    if not js.strip():
        return []
    data = json.loads(js)
    return data if isinstance(data, list) else [data]


def parse_drives(disks_json: str, partitions_json: str):
    letters: dict[int, list] = {}
    for p in _as_list(partitions_json):
        letter = p.get("DriveLetter")
        if letter:
            letters.setdefault(p["DiskNumber"], []).append(str(letter))
    drives = []
    for d in _as_list(disks_json):
        n = d["Number"]
        drives.append(DriveInfo(
            number=n,
            path=rf"\\.\PhysicalDrive{n}",
            size=int(d["Size"]),
            bus=str(d.get("BusType", "")),
            friendly=str(d.get("FriendlyName", "")),
            letters=sorted(letters.get(n, [])),
            is_system=bool(d.get("IsBoot", False)),
        ))
    drives.sort(key=lambda x: x.number)
    return drives


def _ps(cmd: str) -> str:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=60, creationflags=_NO_WINDOW)
    return out.stdout


def list_drives():
    # one PowerShell process instead of two — process startup dominates cost
    combined = _ps(
        "$d = Get-Disk | Select-Object Number,FriendlyName,BusType,Size,IsBoot; "
        "$p = Get-Partition | Select-Object DiskNumber,DriveLetter; "
        "[pscustomobject]@{disks=@($d); parts=@($p)} | ConvertTo-Json -Depth 4")
    try:
        obj = json.loads(combined) if combined.strip() else {}
    except json.JSONDecodeError:
        obj = {}
    disks = json.dumps(obj.get("disks", []))
    parts = json.dumps(obj.get("parts", []))
    return parse_drives(disks, parts)
