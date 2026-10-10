#!/usr/bin/env python3
"""Generate the site's image assets from _src/photo-source.png.

Run from anywhere:  python _src/make_images.py
Writes the portrait, the Open Graph card and the favicon set. Only needs
re-running when the photo, name or headline changes.
"""
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
FONTS = pathlib.Path("C:/Windows/Fonts")

BG = (38, 38, 38)
INK = (245, 245, 244)
MUTED = (154, 152, 152)
LINE = (66, 66, 66)
ACCENT = (201, 242, 93)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def grain(img, amount=10, seed=7):
    """Overlay fine monochrome noise, the site's background texture."""
    rnd = random.Random(seed)
    noise = Image.new("L", img.size)
    noise.putdata([128 + rnd.randint(-amount, amount) for _ in range(img.width * img.height)])
    return Image.blend(img, noise.convert("RGB"), 0.08)


def portrait():
    """Square crop from inside the circular resume photo."""
    src = Image.open(ROOT / "_src" / "photo-source.png").convert("RGB")
    face = src.crop((170, 180, 650, 660))
    face.save(IMG / "dil-bahadur-bk.jpg", quality=86, optimize=True, progressive=True)
    face.save(IMG / "dil-bahadur-bk.webp", quality=82, method=6)
    return face


def mark(size):
    """Entity-graph glyph: a hub entity linked to three attribute nodes."""
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 32
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=7 * u, fill=(28, 28, 28, 255))
    hub = (16, 16)
    nodes = [(7.5, 8.5), (25, 9.5), (12, 25)]
    for n in nodes:
        d.line([(hub[0] * u, hub[1] * u), (n[0] * u, n[1] * u)], fill=INK, width=round(1.7 * u))
    for x, y in nodes:
        r = 2.7 * u
        d.ellipse((x * u - r, y * u - r, x * u + r, y * u + r), fill=(28, 28, 28), outline=INK, width=round(1.7 * u))
    r = 4.4 * u
    d.ellipse((hub[0] * u - r, hub[1] * u - r, hub[0] * u + r, hub[1] * u + r), fill=ACCENT)
    return im.resize((size, size), Image.LANCZOS)


def favicons():
    mark(96).save(ROOT / "icon.png")
    flat = Image.new("RGB", (180, 180), (28, 28, 28))
    flat.paste(mark(180), (0, 0), mark(180))
    flat.save(ROOT / "apple-touch-icon.png")
    mark(48).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


def og_card(face):
    W, H = 1200, 630
    im = grain(Image.new("RGB", (W, H), BG))
    d = ImageDraw.Draw(im)
    # Hairline grid, echoing the site's panel layout.
    for x in (400,):
        d.line([(x, 0), (x, H)], fill=LINE, width=1)
    for y in (64, H - 64):
        d.line([(0, y), (W, y)], fill=LINE, width=1)

    photo = ImageOps.grayscale(face).convert("RGB").resize((280, 280), Image.LANCZOS)
    im.paste(photo, (60, 112))

    small = font("arial.ttf", 22)
    mono = font("consola.ttf", 22)
    d.text((60, 22), "dilbdrbk.com.np", font=mono, fill=INK)
    d.text((W - 60, 22), "Kathmandu, Nepal", font=small, fill=MUTED, anchor="ra")
    d.ellipse((60, 420, 74, 434), fill=ACCENT)
    d.text((86, 416), "Semantic SEO Specialist", font=small, fill=INK)
    d.text((60, 452), "In SEO since 2023", font=small, fill=MUTED)

    big = font("arialbd.ttf", 84)
    d.text((440, 104), "Dil Bahadur B.K.", font=big, fill=INK)
    sub = font("arialbd.ttf", 44)
    lines = ["Semantic SEO specialist building", "topical authority with entity-first,", "technical and local SEO."]
    y = 236
    for ln in lines:
        d.text((440, y), ln, font=sub, fill=MUTED)
        y += 58
    tags = "Semantic SEO  /  Technical SEO  /  Local SEO  /  GEO & AEO"
    d.text((60, H - 46), tags, font=small, fill=MUTED)
    im.save(IMG / "og-dil-bahadur-bk.jpg", quality=88, optimize=True)


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    face = portrait()
    favicons()
    og_card(face)
    print("images written to", IMG)
