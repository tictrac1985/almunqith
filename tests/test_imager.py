from almunqith.core.imager import RescueImager


class MemSource:
    def __init__(self, data, hang_ranges=()):
        self._data = data
        self.size = len(data)
        self._hang = hang_ranges

    def read_at(self, offset, length):
        for a, b in self._hang:
            if a <= offset < b:
                import time
                time.sleep(5)          # trigger the watchdog
        return self._data[offset:offset + length]

    def close(self):
        pass


def test_images_full_device(tmp_path):
    data = bytes(range(256)) * 4096          # 1 MiB
    out = tmp_path / "img.bin"
    imager = RescueImager(lambda: MemSource(data), str(out), len(data),
                          chunk=64 * 1024, timeout_s=1.0)
    summary = imager.run()
    assert summary["bytes"] == len(data)
    assert summary["gap_bytes"] == 0
    assert out.read_bytes() == data


def test_hang_region_is_zero_filled_and_recorded(tmp_path):
    data = b"A" * (256 * 1024)
    out = tmp_path / "img2.bin"
    # hang on the second 64 KiB chunk; no reopen recovery -> gap
    imager = RescueImager(lambda: MemSource(data, hang_ranges=[(65536, 131072)]),
                          str(out), len(data), chunk=64 * 1024, timeout_s=0.3)
    summary = imager.run()
    assert summary["bytes"] == len(data)
    assert summary["gap_bytes"] >= 64 * 1024
    written = out.read_bytes()
    assert written[65536:131072] == b"\x00" * 65536    # gap zero-filled
    assert written[:65536] == b"A" * 65536             # good data intact
