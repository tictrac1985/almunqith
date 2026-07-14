"""Rescue imaging: copy a whole (possibly failing) device to an image file so
all further recovery runs against a stable local copy — the card is read once.

Built on ResilientReader: hangs trigger a watchdog that reopens/resets the
device and retries; unreadable regions are zero-filled and recorded as gaps
instead of blocking forever. Resumable: an existing partial image is continued.
"""
import os

from almunqith.core.reader import ResilientReader


def reset_usb_device(instance_id: str):
    """Power-cycle a USB device by instance id (pnputil). Best effort."""
    import subprocess
    for action in ("/disable-device", "/enable-device"):
        try:
            subprocess.run(["pnputil", action, instance_id],
                           capture_output=True, timeout=60)
        except Exception:
            pass


class RescueImager:
    def __init__(self, source_factory, out_path, total_size, *,
                 chunk=4 * 1024 * 1024, timeout_s=25.0,
                 on_event=lambda k, **kw: None):
        self._factory = source_factory
        self._out = out_path
        self._total = total_size
        self._chunk = chunk
        self._timeout = timeout_s
        self._on_event = on_event
        self.gaps = []

    def run(self) -> dict:
        resume = 0
        if os.path.exists(self._out):
            resume = (os.path.getsize(self._out) // self._chunk) * self._chunk
        mode = "r+b" if os.path.exists(self._out) else "wb"

        reader = ResilientReader(
            self._factory(), timeout_s=self._timeout,
            reopen=self._factory,
            on_event=lambda k, d: self._on_event(k, **d))

        gap_bytes = 0
        pos = resume
        with open(self._out, mode) as dst:
            if resume:
                dst.seek(resume)
                self._on_event("resumed", offset=resume)
            while pos < self._total:
                want = min(self._chunk, self._total - pos)
                data = reader.read_at(pos, want)
                if data is None:
                    dst.seek(pos)
                    dst.write(b"\x00" * want)
                    gap_bytes += want
                    self.gaps.append((pos, pos + want))
                    self._on_event("gap", start=pos, end=pos + want)
                else:
                    dst.seek(pos)
                    dst.write(data)
                    if len(data) < want:            # short read near EOF
                        pos += len(data)
                        continue
                pos += want
                if pos % (256 * 1024 * 1024) == 0:
                    self._on_event("progress", done=pos, total=self._total)
        self.gaps = list(reader.gaps) or self.gaps
        self._on_event("done", bytes=pos, gap_bytes=gap_bytes)
        return {"bytes": pos, "gap_bytes": gap_bytes, "gaps": self.gaps,
                "path": self._out}
