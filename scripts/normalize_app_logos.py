"""Normalize launcher logos at build time, preserving their aspect ratios."""
from pathlib import Path
from PIL import Image
import cairosvg
import io
import ast
import base64

root = Path("addon/resources/app-logos")
out = root / "normalized"
out.mkdir(exist_ok=True)
for path in sorted(root.iterdir()):
    if path.suffix.lower() not in (".png", ".svg"):
        continue
    if path.name == "paramount-plus.png":
        tree = ast.parse(Path("addon/plugin.py").read_text(encoding="utf-8"))
        value = next(ast.literal_eval(node.value) for node in tree.body
                     if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PARAMOUNT_PLUS_MARK_B64" for t in node.targets))
        image = Image.open(io.BytesIO(base64.b64decode(value))).convert("RGBA")
    elif path.suffix == ".svg":
        image = Image.open(io.BytesIO(cairosvg.svg2png(url=str(path)))).convert("RGBA")
    else:
        image = Image.open(path).convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise ValueError(f"Empty logo: {path}")
    print(f"{path.name}: {image.size}, visible bounds {bounds}")
    image = image.crop(bounds)
    max_w, max_h = {'apple-tv': (330, 165), 'itvx': (340, 165), 'netflix': (230, 260), 'stremio': (350, 165), 'google-play-store': (330, 180), 'geforce-now': (350, 170)}.get(path.stem, (360, 210))
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    # Upscale small assets as well, within the same bounding box.
    scale = min(max_w / image.width, max_h / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (512, 512))
    canvas.alpha_composite(image, ((512-image.width)//2, (512-image.height)//2))
    canvas.save(out / (path.stem + ".png"))

# Hub tiles use the same canvas and white monochrome artwork.
from PIL import ImageDraw, ImageFont
font = ImageFont.truetype("DejaVuSans-Bold.ttf", 44)
for key, lines in {"movies": ["Movie", "Library"], "tv": ["TV", "Library"], "pvr": ["Live TV"], "recordings": ["Recordings"], "music": ["Music"], "favourites": ["Favourites"], "games": ["Games"]}.items():
    canvas = Image.new("RGBA", (512, 512))
    draw = ImageDraw.Draw(canvas)
    draw.multiline_text((256, 256), "\n".join(lines), font=font, fill="white", anchor="mm", align="center", spacing=8)
    canvas.save(out / ("hub-" + key + ".png"))
