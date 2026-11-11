"""Generate the Tauri icon set from docs/brand/arteliq-mark.svg.

    pip install cairosvg pillow && python desktop/scripts/make_icons.py
"""
import io
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "desktop" / "src-tauri" / "icons"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    png = cairosvg.svg2png(url=str(ROOT / "docs/brand/arteliq-mark.svg"), output_width=1024, output_height=1024)
    base = Image.open(io.BytesIO(png)).convert("RGBA")
    for name, size in {"32x32.png": 32, "128x128.png": 128, "128x128@2x.png": 256, "icon.png": 512}.items():
        base.resize((size, size), Image.LANCZOS).save(OUT / name)
    base.save(OUT / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    base.save(OUT / "icon.icns")


if __name__ == "__main__":
    main()
