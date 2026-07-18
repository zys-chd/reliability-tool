"""Convert icon.png to icon.ico for Windows."""
from pathlib import Path
from PIL import Image

src = Path(__file__).parent.parent / "icon.png"
dst = Path(__file__).parent.parent / "icon.ico"

img = Image.open(src)
# ICO supports multiple sizes; use common ones
img.save(dst, format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
print(f"Converted {src.name} ({src.stat().st_size} bytes) -> {dst.name}")
