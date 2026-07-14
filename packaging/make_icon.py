"""Generate the AlMunqith app icon (a lifebuoy on deep-blue) as a multi-size .ico.

No external assets — drawn with Pillow so the build is self-contained.
"""
import os
import math
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "almunqith.ico")


def render(size: int) -> Image.Image:
    ss = size * 4  # supersample for smooth edges
    img = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = ss / 2
    r_out = ss * 0.46
    r_in = ss * 0.20

    # rounded background tile
    pad = ss * 0.03
    d.rounded_rectangle([pad, pad, ss - pad, ss - pad],
                        radius=ss * 0.22, fill=(17, 20, 27, 255))

    # red ring (lifebuoy body)
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
              fill=(229, 57, 53, 255))
    # white center hole
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
              fill=(17, 20, 27, 255))

    # four white pads around the ring
    r_mid = (r_out + r_in) / 2
    pad_w = ss * 0.11
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        px, py = cx + r_mid * math.cos(a), cy + r_mid * math.sin(a)
        d.ellipse([px - pad_w, py - pad_w, px + pad_w, py + pad_w],
                  fill=(245, 245, 245, 255))

    # thin blue accent ring on the inner edge
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
              outline=(59, 130, 246, 255), width=max(1, int(ss * 0.012)))

    return img.resize((size, size), Image.LANCZOS)


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [render(s) for s in sizes]
    imgs[0].save(OUT, format="ICO", sizes=[(s, s) for s in sizes],
                 append_images=imgs[1:])
    print("icon written:", OUT)


if __name__ == "__main__":
    main()
