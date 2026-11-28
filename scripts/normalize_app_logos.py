"""Normalize launcher logos at build time, preserving their aspect ratios."""
from pathlib import Path
from PIL import Image
import cairosvg
import io
import ast
import base64

root = Path("addon/resources/app-logos")
out = root / "normalized-v4"
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
    # Extract the original brand marks from the existing transparent wordmarks.
    if path.stem in ("apple-tv", "itvx"):
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            image = image.crop(bbox)
            # Find the transparent vertical gap between the symbol and lettering.
            alpha = image.getchannel("A")
            occupied = [alpha.crop((x, 0, x+1, image.height)).getbbox() is not None
                        for x in range(image.width)]
            gaps = []
            start = None
            for x, used in enumerate(occupied + [True]):
                if not used and start is None:
                    start = x
                elif used and start is not None:
                    if start > image.width * .12 and x < image.width * .95:
                        gaps.append((start, x))
                    start = None
            if path.stem == "apple-tv":
                candidates = [(a,b) for a,b in gaps if .25 < a/image.width < .65]
                if candidates:
                    cut = max(candidates, key=lambda g: g[1]-g[0])[0]
                    image = image.crop((0, 0, cut, image.height))
            else:
                candidates = [(a,b) for a,b in gaps if .50 < b/image.width < .85]
                if candidates:
                    cut = max(candidates, key=lambda g: g[1]-g[0])[1]
                else:
                    cut = round(image.width * .60)
                image = image.crop((cut, 0, image.width, image.height))
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise ValueError(f"Empty logo: {path}")
    print(f"{path.name}: {image.size}, visible bounds {bounds}")
    image = image.crop(bounds)
    # Keep launcher marks monochrome while retaining their original alpha edges.
    alpha = image.getchannel("A")
    image = Image.new("RGBA", image.size, "white")
    image.putalpha(alpha)
    max_w, max_h = (440, 420)
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

# Rounded hub artwork
from PIL import ImageChops
hub_marks = {"movies":"<rect x=\"10\" y=\"35\" width=\"80\" height=\"55\" rx=\"10\"/><path d=\"M10 25L80 8L87 29L16 45Z\"/><path d=\"M42 48L66 62L42 76Z\" fill=\"black\"/>","tv":"<rect x=\"9\" y=\"12\" width=\"82\" height=\"60\" rx=\"13\"/><path d=\"M40 25L67 42L40 59Z\" fill=\"black\"/><path d=\"M34 85H66\" stroke=\"white\" stroke-width=\"8\" stroke-linecap=\"round\"/>","kids":"<path d=\"M50 8L63 32L90 36L71 55L75 82L50 69L25 82L29 55L10 36L37 32Z\" stroke=\"white\" stroke-width=\"5\" stroke-linejoin=\"round\"/><circle cx=\"40\" cy=\"45\" r=\"3\" fill=\"black\"/><circle cx=\"60\" cy=\"45\" r=\"3\" fill=\"black\"/><path d=\"M40 55Q50 66 60 55\" stroke=\"black\" stroke-width=\"4\" fill=\"none\"/>","networks":"<rect x=\"9\" y=\"12\" width=\"36\" height=\"32\" rx=\"8\"/><path d=\"M22 20l13 8 -13 8Z\" fill=\"black\"/><rect x=\"55\" y=\"12\" width=\"36\" height=\"32\" rx=\"8\"/><path d=\"M68 20l13 8 -13 8Z\" fill=\"black\"/><rect x=\"9\" y=\"56\" width=\"36\" height=\"32\" rx=\"8\"/><path d=\"M22 64l13 8 -13 8Z\" fill=\"black\"/><rect x=\"55\" y=\"56\" width=\"36\" height=\"32\" rx=\"8\"/><path d=\"M68 64l13 8 -13 8Z\" fill=\"black\"/>","pvr":"<circle cx=\"50\" cy=\"35\" r=\"9\"/><path d=\"M30 15Q10 35 30 55M70 15Q90 35 70 55M17 5Q-9 35 17 65M83 5Q109 35 83 65\" stroke=\"white\" stroke-width=\"6\" fill=\"none\" stroke-linecap=\"round\"/><path d=\"M50 48L29 91H71Z\"/>","music":"<path d=\"M16 58V45A34 34 0 0 1 84 45V58\" stroke=\"white\" stroke-width=\"10\" fill=\"none\"/><rect x=\"9\" y=\"48\" width=\"24\" height=\"38\" rx=\"9\"/><rect x=\"67\" y=\"48\" width=\"24\" height=\"38\" rx=\"9\"/>","games":"<path d=\"M29 25H71Q89 25 94 65Q98 87 80 82L63 67H37L20 82Q2 87 6 65Q11 25 29 25Z\"/><path d=\"M30 36V58M19 47H41\" stroke=\"black\" stroke-width=\"7\"/><circle cx=\"70\" cy=\"40\" r=\"5\" fill=\"black\"/><circle cx=\"81\" cy=\"51\" r=\"5\" fill=\"black\"/>","favourites":"<path d=\"M50 88L13 49C-8 17 28 0 50 28C72 0 108 17 87 49Z\"/>","documentaries":"<circle cx=\"50\" cy=\"50\" r=\"42\"/><path d=\"M19 24L42 17L50 29L38 42L43 52L27 57L14 43ZM57 44L80 35L89 51L74 65L67 83L53 71L48 54Z\" fill=\"black\"/>","custom":"<rect x=\"10\" y=\"10\" width=\"35\" height=\"35\" rx=\"9\"/><rect x=\"55\" y=\"10\" width=\"35\" height=\"35\" rx=\"9\"/><rect x=\"10\" y=\"55\" width=\"35\" height=\"35\" rx=\"9\"/><rect x=\"55\" y=\"55\" width=\"35\" height=\"35\" rx=\"9\"/>"}
for key, mark in hub_marks.items():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="white">' + mark + '</svg>'
    image = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=440, output_height=440))).convert('RGBA')
    alpha = ImageChops.multiply(image.getchannel('A'), image.convert('L'))
    image = Image.new('RGBA', image.size, 'white')
    image.putalpha(alpha)
    canvas = Image.new('RGBA', (512,512))
    canvas.alpha_composite(image, (36,36))
    canvas.save(out / ('hub-rounded-' + key + '.png'))
