import io
import random
from PIL import Image


def make_jpeg(w=64, h=48) -> bytes:
    rnd = random.Random(42)
    img = Image.new("RGB", (w, h))
    img.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256))
                 for _ in range(w * h)])
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()
