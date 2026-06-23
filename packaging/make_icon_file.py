"""Generate app.ico (the installer / exe icon) at the repo root."""
import os
from PIL import Image, ImageDraw


def mic(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    d.ellipse((s * 0.14, s * 0.14, s * 0.86, s * 0.86), fill=(46, 204, 113, 255))
    d.rounded_rectangle((s * 0.40, s * 0.27, s * 0.60, s * 0.64), radius=s * 0.1,
                        fill=(255, 255, 255, 235))
    d.rectangle((s * 0.47, s * 0.62, s * 0.53, s * 0.80), fill=(255, 255, 255, 235))
    d.rectangle((s * 0.40, s * 0.79, s * 0.60, s * 0.83), fill=(255, 255, 255, 235))
    return img


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO_ROOT, "app.ico")
sizes = [256, 128, 64, 48, 32, 16]
mic(256).save(OUT, format="ICO", sizes=[(s, s) for s in sizes])
print("app.ico written ->", OUT)
