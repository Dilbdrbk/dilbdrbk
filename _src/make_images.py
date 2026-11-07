#!/usr/bin/env python3
"""Generate the site's image assets.

    python _src/make_images.py                 # portrait, logo, favicons, social card
    python _src/make_images.py --kit <dir>     # also export the logo kit to <dir>
    python _src/make_images.py --blog          # only the blog feature images

The logo is the "dbk." wordmark: lowercase dbk in Segoe UI Black with a lime
dot. Only needs re-running when the photo, logo or headline changes.

Blog feature images pair a question and its short answer with a small diagram
and the logo, in Bahnschrift Condensed (the closest installed match to the
site's condensed Archivo). They go to assets/img/blog/.
"""
import math
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
INK_2 = (214, 212, 211)
LINE_STRONG = (98, 98, 98)
RAISE = (46, 46, 46)
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
    d.text((W - 60, 22), "Nepal", font=small, fill=MUTED, anchor="ra")
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


# ---------------------------------------------------------------- blog feature images

BLOG = IMG / "blog"
R = 2                        # blog images are drawn at 2x, then scaled down


def px(v):
    return int(round(v * R))


def bahn(size, style):
    return font("bahnschrift.ttf", px(size), style)


def tracked(d, xy, text, f, fill, tracking, anchor="lm"):
    """Letter-spaced text, for the small uppercase labels."""
    width = sum(f.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    x, y = xy
    if anchor[0] == "r":
        x -= width
    elif anchor[0] == "m":
        x -= width / 2
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += f.getlength(ch) + tracking


def wrap(text, f, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if f.getlength(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur] if cur else lines


def pill(d, cx, cy, text, f, fill=BG, outline=LINE_STRONG, ink=INK, h=46):
    w = f.getlength(text) + px(36)
    d.rounded_rectangle([cx - w / 2, cy - px(h) / 2, cx + w / 2, cy + px(h) / 2], radius=px(h) / 2,
                        fill=fill, outline=outline, width=R)
    d.text((cx, cy), text, font=f, fill=ink, anchor="mm")


def feature_canvas(W, H, split, question, answer, note=None, label="ENTITY SEO GUIDE", divider=True):
    """Shared layout: logo and label on top, question and answer on the left, footer below.
    `question` is two lines; the second one is lime."""
    im = Image.new("RGB", (px(W), px(H)), BG)
    d = ImageDraw.Draw(im)
    for y in (64, H - 64):
        d.line([(0, px(y)), (px(W), px(y))], fill=LINE, width=R)
    if divider:
        d.line([(px(split), px(64)), (px(split), px(H - 64))], fill=LINE, width=R)
    logo = to_height(wordmark(), px(30))
    im.paste(logo, (px(60), px(17)), logo)
    tracked(d, (px(W - 60), px(32)), label, bahn(15, "SemiBold"), MUTED, px(3), anchor="rm")

    size = 100                      # shrink long questions until both lines fit the left column
    while max(bahn(size, "Bold Condensed").getlength(q) for q in question) > px(split - 110) and size > 60:
        size -= 2
    qf = bahn(size, "Bold Condensed")
    d.text((px(60), px(100)), question[0], font=qf, fill=INK, anchor="la")
    d.text((px(60), px(100 + size * 0.96)), question[1], font=qf, fill=ACCENT, anchor="la")
    y = px(346)
    d.line([(px(60), y), (px(106), y)], fill=ACCENT, width=px(3))
    y += px(24)
    af = bahn(30, "SemiCondensed")
    for line in wrap(answer, af, px(split - 120)):
        d.text((px(60), y), line, font=af, fill=INK_2, anchor="la")
        y += px(40)
    if note:
        d.text((px(60), y + px(10)), note, font=bahn(18, "SemiCondensed"), fill=MUTED, anchor="la")

    small = bahn(19, "SemiCondensed")
    d.text((px(60), px(H - 32)), "Dil Bahadur B.K.  /  Semantic SEO Specialist", font=small, fill=MUTED, anchor="lm")
    d.text((px(W - 60), px(H - 32)), "dilbdrbk.com.np/blog", font=small, fill=INK, anchor="rm")
    return im, d


def entity_graph(d, cx, cy):
    """An entity in the middle with the five things entity SEO defines around it."""
    labels = ["Type", "Attributes", "Relations", "Wikidata ID", "sameAs"]
    rx, ry = 165, 170
    nodes = []
    for k, label in enumerate(labels):
        a = math.radians(-90 + k * 72)
        nodes.append((px(cx + rx * math.cos(a)), px(cy + ry * math.sin(a)), label))
    d.ellipse([px(cx - 118), px(cy - 118), px(cx + 118), px(cy + 118)], outline=LINE, width=R)
    for x, y, label in nodes:
        d.line([(px(cx), px(cy)), (x, y)], fill=ACCENT if label == "Attributes" else LINE_STRONG, width=px(2))
    f = bahn(21, "SemiBold SemiCondensed")
    for x, y, label in nodes:
        lime = label == "Attributes"
        pill(d, x, y, label, f, outline=ACCENT if lime else LINE_STRONG, ink=ACCENT if lime else INK)
    d.ellipse([px(cx - 64), px(cy - 64), px(cx + 64), px(cy + 64)], fill=ACCENT)
    d.text((px(cx), px(cy)), "Entity", font=bahn(34, "Bold Condensed"), fill=INK_DARK, anchor="mm")


def record(d, box, qid, name, lines, lime):
    x0, y0, x1, y1 = (px(v) for v in box)
    d.rounded_rectangle([x0, y0, x1, y1], radius=px(18), fill=RAISE, outline=ACCENT if lime else LINE_STRONG, width=R)
    chip_f = bahn(18, "SemiBold SemiCondensed")
    w = chip_f.getlength(qid) + px(24)
    d.rounded_rectangle([x0 + px(24), y0 + px(24), x0 + px(24) + w, y0 + px(56)], radius=px(16),
                        fill=ACCENT if lime else LINE_STRONG)
    d.text((x0 + px(24) + w / 2, y0 + px(40)), qid, font=chip_f, fill=INK_DARK if lime else INK, anchor="mm")
    d.text((x0 + px(24), y0 + px(72)), name, font=bahn(40, "Bold Condensed"), fill=INK, anchor="la")
    y = y0 + px(126)
    for text, color in lines:
        d.text((x0 + px(24), y), text, font=bahn(20, "SemiCondensed"), fill=color, anchor="la")
        y += px(28)


def steps_list(d, x, top, labels, step=76):
    f = bahn(26, "SemiBold SemiCondensed")
    nf = bahn(17, "Bold Condensed")
    d.line([(px(x), px(top)), (px(x), px(top + step * (len(labels) - 1)))], fill=LINE_STRONG, width=R)
    for k, label in enumerate(labels):
        y = top + k * step
        box = [px(x - 21), px(y - 21), px(x + 21), px(y + 21)]
        if k == 0:
            d.ellipse(box, fill=ACCENT)
        else:
            d.ellipse(box, fill=BG, outline=LINE_STRONG, width=R)
        d.text((px(x), px(y)), f"{k + 1:02d}", font=nf, fill=INK_DARK if k == 0 else INK, anchor="mm")
        d.text((px(x + 40), px(y)), label, font=f, fill=INK, anchor="lm")


def dashed(d, a, b, fill, width, dash=9, gap=7):
    """A dashed straight line from a to b (scaled coordinates)."""
    (x0, y0), (x1, y1) = a, b
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0.0
    while pos < length:
        end = min(pos + px(dash), length)
        d.line([(x0 + ux * pos, y0 + uy * pos), (x0 + ux * end, y0 + uy * end)], fill=fill, width=width)
        pos = end + px(gap)


def keyword_entities(d):
    """Three searches that share the word "jaguar", linked to the two entities they can mean."""
    f = bahn(20, "SemiBold SemiCondensed")
    label = bahn(14, "SemiBold")
    qx, ex, r = 830, 1085, 56
    searches = [(200, "jaguar habitat"), (315, "jaguar top speed"), (430, "jaguar f-pace price")]
    cat, car = (225, "Big cat", "Q35694"), (395, "Car brand", "Q21170490")
    tracked(d, (px(qx), px(118)), "KEYWORDS", label, MUTED, px(2.5), anchor="mm")
    tracked(d, (px(ex), px(118)), "ENTITIES", label, MUTED, px(2.5), anchor="mm")

    def edge(y, target):
        """From the right end of a search pill to the rim of an entity circle."""
        right = px(qx) + (f.getlength(dict((s[0], s[1]) for s in searches)[y]) + px(36)) / 2
        ang = math.atan2(px(y) - px(target), right - px(ex))
        return (right + px(4), px(y)), (px(ex) + px(r + 6) * math.cos(ang), px(target) + px(r + 6) * math.sin(ang))

    d.line(edge(200, cat[0]), fill=ACCENT, width=px(2))
    d.line(edge(430, car[0]), fill=INK_2, width=px(2))
    for target in (cat[0], car[0]):
        dashed(d, *edge(315, target), fill=MUTED, width=px(2))
    for y, text in searches:
        pill(d, px(qx), px(y), text, f, outline=LINE_STRONG, ink=INK)
    for (y, name, qid), lime in ((cat, True), (car, False)):
        box = [px(ex - r), px(y - r), px(ex + r), px(y + r)]
        if lime:
            d.ellipse(box, fill=ACCENT)
        else:
            d.ellipse(box, fill=RAISE, outline=INK_2, width=px(2))
        d.text((px(ex), px(y)), name, font=bahn(25, "Bold Condensed"), fill=INK_DARK if lime else INK, anchor="mm")
        d.text((px(ex), px(y + r + 20)), qid, font=bahn(15, "SemiBold SemiCondensed"), fill=MUTED, anchor="mm")
    tracked(d, (px(945), px(526)), "ONE WORD, TWO ENTITIES", label, MUTED, px(2.5), anchor="mm")


def authority_compare(d):
    """Top: a topic with its connected subtopic pages. Bottom: a 1 to 100 score bar fed by links."""
    label = bahn(14, "SemiBold")
    small = bahn(17, "SemiBold SemiCondensed")
    cx, cy = 945, 190
    tracked(d, (px(cx), px(92)), "TOPICAL AUTHORITY", label, MUTED, px(2.5), anchor="mm")
    subs = ["Cost", "Permits", "Season", "Route", "Risks", "Gear"]
    rx, ry = 150, 68
    pts = []
    for k, s in enumerate(subs):
        a = math.radians(-90 + 30 + k * 60)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), s))
    for k, (x, y, _) in enumerate(pts):                      # ring of internal links between neighbours
        x2, y2, _ = pts[(k + 1) % len(pts)]
        dashed(d, (px(x), px(y)), (px(x2), px(y2)), fill=LINE_STRONG, width=R)
    for x, y, _ in pts:
        d.line([(px(cx), px(cy)), (px(x), px(y))], fill=ACCENT, width=px(2))
    for x, y, s in pts:
        pill(d, px(x), px(y), s, small, ink=INK, h=36)
    d.ellipse([px(cx - 44), px(cy - 44), px(cx + 44), px(cy + 44)], fill=ACCENT)
    d.text((px(cx), px(cy)), "Topic", font=bahn(26, "Bold Condensed"), fill=INK_DARK, anchor="mm")
    d.text((px(cx), px(cy + 112)), "Depth on one subject", font=small, fill=INK_2, anchor="mm")

    d.line([(px(720), px(338)), (px(1170), px(338))], fill=LINE, width=R)
    tracked(d, (px(cx), px(370)), "DOMAIN AUTHORITY", label, MUTED, px(2.5), anchor="mm")
    x0, x1, y = 760, 1130, 448
    d.rounded_rectangle([px(x0), px(y - 12), px(x1), px(y + 12)], radius=px(12), fill=RAISE, outline=LINE_STRONG, width=R)
    fill_to = x0 + (x1 - x0) * 0.62
    d.rounded_rectangle([px(x0), px(y - 12), px(fill_to), px(y + 12)], radius=px(12), fill=INK_2)
    for v, x in ((1, x0), (100, x1)):
        d.text((px(x), px(y + 34)), str(v), font=small, fill=MUTED, anchor="mm")
    d.text((px(fill_to), px(y - 34)), "62", font=bahn(30, "Bold Condensed"), fill=INK, anchor="mm")
    for k in range(5):                                      # backlinks arriving from the left
        ly = y - 40 + k * 20
        d.line([(px(722), px(ly)), (px(752), px(y))], fill=LINE_STRONG, width=R)
    d.text((px(cx), px(520)), "A tool score built from backlinks", font=small, fill=INK_2, anchor="mm")


def save_scaled(im, name, size, fmt, **opts):
    out = im.resize(size, Image.LANCZOS)
    out = grain(out)
    out.save(BLOG / name, fmt, **opts)
    print(f"  {name:36} {size[0]}x{size[1]}  {(BLOG / name).stat().st_size // 1024} KB")


def blog_images():
    BLOG.mkdir(parents=True, exist_ok=True)

    cover, d = feature_canvas(1200, 630, 690, ("What is", "entity SEO?"),
                              "Optimizing a website so search engines identify its entities, their attributes and their relations.")
    entity_graph(d, 945, 315)
    save_scaled(cover, "what-is-entity-seo.jpg", (1200, 630), "JPEG", quality=88, optimize=True, progressive=True)
    save_scaled(cover, "what-is-entity-seo.webp", (1600, 840), "WEBP", quality=82, method=6)
    save_scaled(cover, "what-is-entity-seo-thumb.webp", (640, 336), "WEBP", quality=80, method=6)

    card, d = feature_canvas(1200, 675, 640, ("What is", "an entity?"),
                             "A thing or concept that is singular, unique, well-defined and distinguishable.",
                             note="Definition from Google patent US10339190B2")
    record(d, (680, 104, 1140, 300), "Q42", "Douglas Adams",
           [("British science fiction writer and humorist", INK_2), ("1952 to 2001", MUTED)], lime=True)
    tracked(d, (px(910), px(338)), "SAME NAME, DIFFERENT ENTITY", bahn(14, "SemiBold"), MUTED, px(2.5), anchor="mm")
    record(d, (680, 376, 1140, 572), "Q28421831", "Douglas Adams",
           [("American environmental engineer", INK_2), ("A separate Wikidata item", MUTED)], lime=False)
    save_scaled(card, "what-is-an-entity.webp", (1200, 675), "WEBP", quality=84, method=6)

    card, d = feature_canvas(1200, 675, 640, ("How to do", "entity SEO?"),
                             "Six steps, from mapping the entity to building its identity across the web.")
    steps_list(d, 712, 148, ["Map the central entity", "Plan the topical map", "Write for entity clarity",
                             "Link entities", "Add structured data", "Build the entity identity"])
    save_scaled(card, "entity-seo-steps.webp", (1200, 675), "WEBP", quality=84, method=6)

    cover, d = feature_canvas(1200, 630, 690, ("Entity SEO vs", "keyword SEO?"),
                              "Keywords are the words people search with. Entities are the things those words mean.")
    keyword_entities(d)
    save_scaled(cover, "entity-seo-vs-keyword-seo.jpg", (1200, 630), "JPEG", quality=88, optimize=True, progressive=True)
    save_scaled(cover, "entity-seo-vs-keyword-seo.webp", (1600, 840), "WEBP", quality=82, method=6)
    save_scaled(cover, "entity-seo-vs-keyword-seo-thumb.webp", (640, 336), "WEBP", quality=80, method=6)

    card, d = feature_canvas(1200, 675, 640, ("Both together", "in 7 steps"),
                             "Collect the searches, map them to entities, then write, link and measure.")
    steps_list(d, 712, 130, ["Collect real searches", "Group them by intent", "Map to entities", "Plan the topical map",
                             "Write answer-first", "Link and mark up", "Measure both"], step=72)
    save_scaled(card, "entity-keyword-workflow.webp", (1200, 675), "WEBP", quality=84, method=6)

    cover, d = feature_canvas(1200, 630, 870, ("Topical authority vs", "domain authority?"),
                              "Topical authority is depth on one subject. Domain authority is a tool score built from backlinks.",
                              label="SEMANTIC SEO GUIDE", divider=False)
    save_scaled(cover, "topical-authority-vs-domain-authority.jpg", (1200, 630), "JPEG", quality=88, optimize=True, progressive=True)
    save_scaled(cover, "topical-authority-vs-domain-authority.webp", (1600, 840), "WEBP", quality=82, method=6)
    save_scaled(cover, "topical-authority-vs-domain-authority-thumb.webp", (640, 336), "WEBP", quality=80, method=6)

    card, d = feature_canvas(1200, 675, 640, ("Topical authority", "in 7 steps"),
                             "Map the topic, cover it answer-first, link the pages, then earn links from relevant sites.",
                             label="SEMANTIC SEO GUIDE")
    steps_list(d, 712, 130, ["Define the central entity", "Map the query network", "Plan the topical map",
                             "Write answer-first", "Link the network", "Update on a schedule", "Earn relevant links"], step=72)
    save_scaled(card, "topical-authority-steps.webp", (1200, 675), "WEBP", quality=84, method=6)

    cover, d = feature_canvas(1200, 630, 870, ("How to get cited", "by ChatGPT?"),
                              "Get indexed, allow the AI search crawlers and answer every fan-out sub-question with sourced facts.",
                              label="AI SEARCH GUIDE", divider=False)
    save_scaled(cover, "how-to-get-cited-by-chatgpt.jpg", (1200, 630), "JPEG", quality=88, optimize=True, progressive=True)
    save_scaled(cover, "how-to-get-cited-by-chatgpt.webp", (1600, 840), "WEBP", quality=82, method=6)
    save_scaled(cover, "how-to-get-cited-by-chatgpt-thumb.webp", (640, 336), "WEBP", quality=80, method=6)

    card, d = feature_canvas(1200, 675, 600, ("Get cited by AI", "in 9 steps"),
                             "Open access, get indexed, answer every sub-question with facts, then track the citations.",
                             label="AI SEARCH GUIDE")
    steps_list(d, 672, 112, ["Allow AI search crawlers", "Get indexed in Google and Bing", "Map the fan-out queries",
                             "Answer each sub-question", "Add facts and sources", "Keep entity facts consistent",
                             "Use HTML text", "Keep content fresh", "Track AI referrals"], step=56)
    save_scaled(card, "ai-citation-steps.webp", (1200, 675), "WEBP", quality=84, method=6)

    cover, d = feature_canvas(1200, 630, 640, ("SEO audit", "checklist"),
                              "56 checks to find what blocks rankings, with a running score.",
                              label="FREE CHECKLIST")
    steps_list(d, 712, 132, ["Technical SEO: 15", "On-page SEO: 10", "Content: 8", "Local SEO: 8", "Off-page SEO: 7", "AI search: 8"], step=72)
    save_scaled(cover, "seo-audit-checklist.webp", (1600, 840), "WEBP", quality=82, method=6)

    cover, d = feature_canvas(1200, 630, 870, ("How to create a", "topical map?"),
                              "Define the central entity, map its attributes, gather real queries and test which ones deserve a page.",
                              label="SEMANTIC SEO GUIDE", divider=False)
    save_scaled(cover, "how-to-create-a-topical-map.jpg", (1200, 630), "JPEG", quality=88, optimize=True, progressive=True)
    save_scaled(cover, "how-to-create-a-topical-map.webp", (1600, 840), "WEBP", quality=82, method=6)
    save_scaled(cover, "how-to-create-a-topical-map-thumb.webp", (640, 336), "WEBP", quality=80, method=6)

    card, d = feature_canvas(1200, 675, 600, ("Topical map", "in 9 steps"),
                             "From the central entity to real queries, page decisions and internal links.",
                             label="SEMANTIC SEO GUIDE")
    steps_list(d, 672, 112, ["Define entity and context", "Map attributes into buckets", "Score relevance",
                             "Collect real queries", "Classify intent", "Derive query templates",
                             "Test page or section", "Split core and outer", "Plan internal links"], step=56)
    save_scaled(card, "topical-map-steps.webp", (1200, 675), "WEBP", quality=84, method=6)

    cover, d = feature_canvas(1200, 630, 640, ("SERP snippet", "preview tool"),
                              "See your title and meta description as Google shows them, with pixel checks.",
                              label="FREE TOOL")
    steps_list(d, 712, 150, ["Title width in pixels", "Description width", "Desktop and mobile", "Keyword in bold", "Copy the HTML tags"], step=80)
    save_scaled(cover, "serp-snippet-preview.webp", (1600, 840), "WEBP", quality=82, method=6)

    cover, d = feature_canvas(1200, 630, 870, ("What is the Google", "Knowledge Graph?"),
                              "Google's database of facts about entities. It feeds knowledge panels and entity matching, and it shapes SEO indirectly.",
                              label="ENTITY SEO GUIDE", divider=False)
    save_scaled(cover, "what-is-the-google-knowledge-graph.jpg", (1200, 630), "JPEG", quality=88, optimize=True, progressive=True)
    save_scaled(cover, "what-is-the-google-knowledge-graph.webp", (1600, 840), "WEBP", quality=82, method=6)
    save_scaled(cover, "what-is-the-google-knowledge-graph-thumb.webp", (640, 336), "WEBP", quality=80, method=6)

    card, d = feature_canvas(1200, 675, 640, ("Knowledge Graph", "in 7 steps"),
                             "One clear source of facts on your site, then matching facts across the web.",
                             label="ENTITY SEO GUIDE")
    steps_list(d, 712, 130, ["Choose one entity home", "State the core facts", "Add schema markup", "Link official profiles",
                             "Match third-party facts", "Earn independent references", "Check and claim"], step=72)
    save_scaled(card, "knowledge-graph-steps.webp", (1200, 675), "WEBP", quality=84, method=6)


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    if "--blog" in sys.argv:
        blog_images()
        sys.exit()
    face = portrait()
    print("header logo", header_logo())
    favicons()
    og_card(face)
    print("site images written to", IMG)
    if "--kit" in sys.argv:
        kit(sys.argv[sys.argv.index("--kit") + 1])
