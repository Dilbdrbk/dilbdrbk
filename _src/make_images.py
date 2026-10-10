#!/usr/bin/env python3
"""Generate the site's image assets.

    python _src/make_images.py                 # portrait, logo, favicons, social card
    python _src/make_images.py --kit <dir>     # also export the logo kit to <dir>

The logo is the "dbk." wordmark: lowercase dbk in Segoe UI Black with a lime
dot. Only needs re-running when the photo, logo or headline changes.
"""
import pathlib
import random
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
FONTS = pathlib.Path("C:/Windows/Fonts")

BG = (38, 38, 38)
INK = (245, 245, 244)
INK_DARK = (28, 28, 28)
MUTED = (154, 152, 152)
MUTED_DARK = (105, 103, 103)
LINE = (66, 66, 66)
ACCENT = (201, 242, 93)
ACCENT_DARK = (95, 140, 0)   # lime reads poorly on light backgrounds
LIGHT_BG = (244, 243, 239)
SS = 3                       # supersampling for the vector-like drawing


def font(name, size, variation=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if variation:
        f.set_variation_by_name(variation)
    return f


def grain(img, amount=10, seed=7):
    """Overlay fine monochrome noise, the site's background texture."""
    rnd = random.Random(seed)
    noise = Image.new("L", img.size)
    noise.putdata([128 + rnd.randint(-amount, amount) for _ in range(img.width * img.height)])
    return Image.blend(img, noise.convert("RGB"), 0.08)


def downsample(im, pad=0):
    """Crop to the drawn content (+pad), then shrink by SS without dark fringes."""
    box = im.getbbox()
    p = pad * SS
    box = (max(box[0] - p, 0), max(box[1] - p, 0), min(box[2] + p, im.width), min(box[3] + p, im.height))
    im = im.crop(box).convert("RGBa")
    return im.resize((max(im.width // SS, 1), max(im.height // SS, 1)), Image.LANCZOS).convert("RGBA")


def to_height(im, h):
    im = im.convert("RGBa")
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS).convert("RGBA")


# ---------------------------------------------------------------- logo

def wordmark(ink=INK, accent=ACCENT, tagline=None, muted=MUTED, pad=0):
    """The dbk. wordmark on a transparent background (about 760 px wide)."""
    im = Image.new("RGBA", (1100 * SS, 480 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font("seguibl.ttf", 300 * SS)
    x, base = 20 * SS, 330 * SS
    for ch in "dbk":
        d.text((x, base), ch, font=f, fill=ink, anchor="ls")
        x += f.getlength(ch) - 12 * SS
    d.ellipse([x + 14 * SS, base - 62 * SS, x + 76 * SS, base], fill=accent)
    if tagline:
        tf = font("bahnschrift.ttf", 28 * SS, "SemiBold")
        tx = 30 * SS
        for ch in tagline:
            d.text((tx, 400 * SS), ch, font=tf, fill=muted, anchor="ls")
            tx += tf.getlength(ch) + 7 * SS
    return downsample(im, pad)


def icon(size, bg=(28, 28, 28), radius=0.22):
    """Square app icon: a lowercase d and the lime dot."""
    S = size * SS
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if radius:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * radius), fill=bg)
    else:
        d.rectangle([0, 0, S - 1, S - 1], fill=bg)
    f = font("seguibl.ttf", int(S * 0.78))
    glyph_w = f.getlength("d")
    dot = S * 0.17
    total = glyph_w + dot * 0.35 + dot
    x = (S - total) / 2
    l, t, r, b = d.textbbox((0, 0), "d", font=f, anchor="ls")
    base = (S - (b - t)) / 2 - t
    d.text((x, base), "d", font=f, fill=INK, anchor="ls")
    dx = x + glyph_w + dot * 0.2
    d.ellipse([dx, base - dot, dx + dot, base], fill=ACCENT)
    im = im.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")
    return im


def header_logo():
    """Light wordmark for the dark site header, at 3x of its 24 px display height."""
    logo = to_height(wordmark(), 72)
    logo.save(IMG / "logo-dbk.webp", "WEBP", lossless=True, method=6)
    return logo.size


def favicons():
    icon(96).save(ROOT / "icon.png")
    flat = Image.new("RGB", (180, 180), (28, 28, 28))
    flat.paste(icon(180, radius=0), (0, 0))
    flat.save(ROOT / "apple-touch-icon.png")
    icon(48).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


# ---------------------------------------------------------------- photo + card

def portrait():
    """Square crop from inside the circular resume photo."""
    src = Image.open(ROOT / "_src" / "photo-source.png").convert("RGB")
    face = src.crop((170, 180, 650, 660))
    face.save(IMG / "dil-bahadur-bk.jpg", quality=86, optimize=True, progressive=True)
    face.save(IMG / "dil-bahadur-bk.webp", quality=82, method=6)
    return face


def og_card(face):
    W, H = 1200, 630
    im = grain(Image.new("RGB", (W, H), BG))
    d = ImageDraw.Draw(im)
    d.line([(400, 0), (400, H)], fill=LINE, width=1)
    for y in (64, H - 64):
        d.line([(0, y), (W, y)], fill=LINE, width=1)

    photo = ImageOps.grayscale(face).convert("RGB").resize((280, 280), Image.LANCZOS)
    im.paste(photo, (60, 112))

    logo = to_height(wordmark(), 34)
    im.paste(logo, (60, 16), logo)

    small = font("arial.ttf", 22)
    mono = font("consola.ttf", 22)
    d.text((W - 60, 22), "Kathmandu, Nepal", font=small, fill=MUTED, anchor="ra")
    d.ellipse((60, 420, 74, 434), fill=ACCENT)
    d.text((86, 416), "Semantic SEO Specialist", font=small, fill=INK)
    d.text((60, 452), "In SEO since 2023", font=small, fill=MUTED)

    d.text((440, 104), "Dil Bahadur B.K.", font=font("arialbd.ttf", 84), fill=INK)
    y = 236
    for ln in ["Semantic SEO specialist building", "topical authority with entity-first,", "technical and local SEO."]:
        d.text((440, y), ln, font=font("arialbd.ttf", 44), fill=MUTED)
        y += 58
    d.text((60, H - 46), "Semantic SEO  /  Technical SEO  /  Local SEO  /  GEO & AEO", font=small, fill=MUTED)
    d.text((W - 60, H - 46), "dilbdrbk.com.np", font=mono, fill=INK, anchor="ra")
    im.save(IMG / "og-dil-bahadur-bk.jpg", quality=88, optimize=True)


# ---------------------------------------------------------------- kit

def kit(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tag = "DIL BAHADUR B.K.  /  SEMANTIC SEO"
    files = {
        "dbk-logo-with-tagline_dark-bg.webp": wordmark(tagline=tag, pad=24),
        "dbk-logo-with-tagline_light-bg.webp": wordmark(INK_DARK, ACCENT_DARK, tagline=tag, muted=MUTED_DARK, pad=24),
        "dbk-logo_dark-bg.webp": wordmark(pad=24),
        "dbk-logo_light-bg.webp": wordmark(INK_DARK, ACCENT_DARK, pad=24),
    }
    for name, im in files.items():
        im.save(out / name, "WEBP", lossless=True, method=6)

    # Profile picture: fits inside the circle LinkedIn and Gravatar crop to.
    pic = grain(Image.new("RGB", (1024, 1024), BG))
    mark = wordmark()
    mark = mark.convert("RGBa").resize((660, round(mark.height * 660 / mark.width)), Image.LANCZOS).convert("RGBA")
    pic.paste(mark, ((1024 - mark.width) // 2, (1024 - mark.height) // 2 + 10), mark)
    pic.save(out / "dbk-profile-picture.webp", "WEBP", quality=95, method=6)
    pic.save(out / "dbk-profile-picture.png")

    app = icon(512)
    app.save(out / "dbk-icon.webp", "WEBP", lossless=True, method=6)
    app.save(out / "dbk-icon.png")
    for f in sorted(out.iterdir()):
        with Image.open(f) as im:
            print(f"  {f.name:42} {im.width}x{im.height}")


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    face = portrait()
    print("header logo", header_logo())
    favicons()
    og_card(face)
    print("site images written to", IMG)
    if "--kit" in sys.argv:
        kit(sys.argv[sys.argv.index("--kit") + 1])
