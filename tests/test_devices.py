import json
from almunqith.core.devices import parse_drives


DISKS = json.dumps([
    {"Number": 0, "FriendlyName": "Samsung SSD", "BusType": "NVMe",
     "Size": 1024_000_000_000, "IsBoot": True},
    {"Number": 1, "FriendlyName": "Mass Storage Device", "BusType": "USB",
     "Size": 31_457_280_000, "IsBoot": False},
])
PARTS = json.dumps([
    {"DiskNumber": 0, "DriveLetter": "C"},
    {"DiskNumber": 0, "DriveLetter": None},
    {"DiskNumber": 1, "DriveLetter": "E"},
])


def test_parse_drives_maps_letters_and_flags():
    drives = parse_drives(DISKS, PARTS)
    assert len(drives) == 2
    sd = drives[1]
    assert sd.path == r"\\.\PhysicalDrive1"
    assert sd.bus == "USB" and sd.letters == ["E"] and sd.is_system is False
    assert drives[0].is_system is True and drives[0].letters == ["C"]


def test_parse_drives_accepts_single_object():
    single = json.dumps({"Number": 2, "FriendlyName": "X", "BusType": "USB",
                         "Size": 100, "IsBoot": False})
    drives = parse_drives(single, json.dumps([]))
    assert drives[0].number == 2 and drives[0].letters == []
