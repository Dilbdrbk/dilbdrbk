#!/usr/bin/env python3
"""Build dilbdrbk.com.np from the sources in _src/.

    python _src/build.py

Reads _src/site.json (identity, contact, profiles), _src/faq.json,
_src/pages/*.html (page bodies) and _src/posts/*.html (blog posts), then writes
the static site into the repo root: one index.html per page, 404.html,
sitemap.xml, robots.txt and llms.txt. GitHub Pages ignores _src/ because the
folder name starts with an underscore.
"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
FAQ = json.loads((SRC / "faq.json").read_text(encoding="utf-8"))
GLOSSARY = json.loads((SRC / "glossary.json").read_text(encoding="utf-8"))
BASE = SITE["url"].rstrip("/")
PERSON_ID = f"{BASE}/#person"
WEBSITE_ID = f"{BASE}/#website"
PORTRAIT = "/assets/img/dil-bahadur-bk.jpg"
OG_IMAGE = "/assets/img/og-dil-bahadur-bk.jpg"
KEYWORDS = "Dil Bahadur B.K., Semantic SEO Specialist, SEO Specialist, Semantic SEO, Entity SEO, Topical Authority, Technical SEO, Local SEO, Nepal"

NAV = [
    ("/expertise/", "Expertise"),
    ("/how-search-works/", "How Search Works"),
    ("/experience/", "Experience"),
    ("/industries/", "Industries"),
    ("/about/", "About"),
    ("/blog/", "Blog"),
]

# Every page: where it lives, its body file and its search snippet.
# `updated` feeds sitemap lastmod; bump it when a page's content changes.
PAGES = [
    dict(path="/", body="home.html", crumb="Home", updated="2026-10-10", kind="home",
         title="Dil Bahadur B.K. | Semantic SEO Specialist in Kathmandu, Nepal",
         description="Semantic SEO specialist in Kathmandu, Nepal. I build topical authority with entity-first, technical and local SEO for local service and e-commerce websites."),
    dict(path="/about/", body="about.html", crumb="About", updated="2026-10-10", kind="profile",
         title="About Dil Bahadur B.K. | Semantic SEO Specialist From Nepal",
         description="Who Dil Bahadur B.K. is: a semantic SEO specialist from Kathmandu who grew from link building into entity-based SEO, topical authority and AI search."),
    dict(path="/expertise/", body="expertise.html", crumb="Expertise", updated="2026-10-10", kind="page",
         title="SEO Expertise: Semantic, Technical, Local & AI Search | Dil B.K.",
         description="Twelve areas of SEO expertise: semantic and entity SEO, topical maps, technical, on-page, local and off-page SEO, programmatic SEO, GEO, AEO and Reddit SEO."),
    dict(path="/how-search-works/", body="how-search-works.html", crumb="How Search Works", updated="2026-10-10", kind="guide",
         title="How Search Works: 5 Diagrams on Ranking & AI Answers | Dil B.K.",
         description="How a page is crawled, understood and ranked, how AI search builds an answer, how an entity becomes a topical map, and how I test SEO ideas."),
    dict(path="/experience/", body="experience.html", crumb="Experience", updated="2026-10-10", kind="page",
         title="SEO Experience at One Percent Digital & RankMeTop | Dil B.K.",
         description="Semantic SEO Specialist at One Percent Digital since July 2026, after five roles at RankMeTop from link building to SEO team lead. Plus education.",
         # Site-wide files (llms.txt) name no employers; only the Experience page itself does.
         summary="SEO career since December 2023, from link building to semantic SEO specialist, plus education."),
    dict(path="/industries/", body="industries.html", crumb="Industries", updated="2026-10-10", kind="page",
         title="Industries: Local, Nationwide & E-commerce SEO | Dil Bahadur B.K.",
         description="SEO across 25+ industries: current e-commerce and B2B projects, local services such as plumbing and HVAC, and nationwide niches such as SaaS and finance."),
    dict(path="/blog/", body="blog.html", crumb="Blog", updated="2026-10-10", kind="blog",
         title="SEO Blog | Dil Bahadur B.K.",
         description="Notes on semantic SEO, topical authority, local SEO and AI search by Dil Bahadur B.K., semantic SEO specialist from Kathmandu, Nepal."),
    dict(path="/profiles/", body="profiles.html", crumb="Profiles", updated="2026-10-10", kind="page",
         title="Dil Bahadur B.K. Online: LinkedIn, GitHub & Other Profiles",
         description="Every official profile of Dil Bahadur B.K., semantic SEO specialist from Kathmandu, Nepal, in one place: LinkedIn, GitHub and more."),
    dict(path="/contact/", body="contact.html", crumb="Contact", updated="2026-10-10", kind="contact",
         title="Contact Dil Bahadur B.K. | Semantic SEO Specialist, Kathmandu",
         description="Reach Dil Bahadur B.K. by email, phone or LinkedIn. Based in Kathmandu, Nepal (NPT, UTC+5:45)."),
]

# The dbk. wordmark, made by make_images.py at 3x its 24 px display height.
def asset(path: str) -> str:
    """Path plus a short content hash, so browsers refetch the file whenever it changes."""
    digest = hashlib.md5((ROOT / path.lstrip("/")).read_bytes()).hexdigest()[:8]
    return f"{path}?v={digest}"


LOGO_IMG = f'<img class="brand-logo" src="{asset("/assets/img/logo-dbk.webp")}" width="63" height="24" alt="Dil Bahadur B.K., home">'


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def absolute(path: str) -> str:
    return BASE + path


# ---------------------------------------------------------------- schema.org

def person_node() -> dict:
    node = {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": SITE["name"],
        "alternateName": SITE["alternateNames"],
        "givenName": SITE["givenName"],
        "familyName": SITE["familyName"],
        "jobTitle": SITE["jobTitle"],
        "description": PAGES[0]["description"],
        "url": BASE + "/",
        "mainEntityOfPage": absolute("/about/"),
        "image": {"@type": "ImageObject", "url": absolute(PORTRAIT), "width": 480, "height": 480},
        "email": "mailto:" + SITE["email"],
        "telephone": SITE["phoneHref"],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": SITE["locality"],
            "addressRegion": SITE["region"],
            "addressCountry": SITE["country"],
        },
        "nationality": {"@type": "Country", "name": SITE["countryName"]},
        "hasOccupation": {
            "@type": "Occupation",
            "name": SITE["jobTitle"],
            "occupationLocation": {"@type": "City", "name": SITE["locality"]},
            "skills": ", ".join(SITE["knowsAbout"]),
        },
        "alumniOf": [{"@type": "EducationalOrganization", "name": e["name"]} for e in SITE["education"]],
        "hasCredential": [
            {
                "@type": "EducationalOccupationalCredential",
                "name": c["name"],
                "credentialCategory": "certificate",
                "recognizedBy": {"@type": "Person", "name": c["issuer"]},
            }
            for c in SITE["certifications"]
        ] + [
            {
                "@type": "EducationalOccupationalCredential",
                "name": e["credential"],
                "credentialCategory": "diploma" if "Diploma" in e["credential"] else "certificate",
                "recognizedBy": {"@type": "EducationalOrganization", "name": e["name"]},
            }
            for e in SITE["education"]
        ],
        "knowsAbout": SITE["knowsAbout"],
        "sameAs": [p["url"] for p in SITE["profiles"] if not p.get("listing")],
    }
    return node


def website_node() -> dict:
    return {
        "@type": "WebSite",
        "@id": WEBSITE_ID,
        "url": BASE + "/",
        "name": SITE["name"],
        "alternateName": "dilbdrbk.com.np",
        "inLanguage": "en",
        "publisher": {"@id": PERSON_ID},
        "author": {"@id": PERSON_ID},
    }


def breadcrumb_node(page: dict, trail: list[tuple[str, str]]) -> dict:
    items = [("Home", "/")] + trail
    return {
        "@type": "BreadcrumbList",
        "@id": absolute(page["path"]) + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": absolute(path)}
            for i, (name, path) in enumerate(items, start=1)
        ],
    }


def page_type(kind: str) -> str:
    return {
        "home": "WebPage",
        "profile": "ProfilePage",
        "contact": "ContactPage",
        "blog": "CollectionPage",
        "post": "WebPage",
    }.get(kind, "WebPage")


def page_graph(page: dict, trail: list[tuple[str, str]], extra: list[dict]) -> dict:
    url = absolute(page["path"])
    webpage = {
        "@type": page_type(page["kind"]),
        "@id": url + "#webpage",
        "url": url,
        "name": page["title"],
        "description": page["description"],
        "inLanguage": "en",
        "isPartOf": {"@id": WEBSITE_ID},
        "about": {"@id": PERSON_ID},
        "primaryImageOfPage": {"@type": "ImageObject", "url": absolute(OG_IMAGE)},
        "dateModified": page["updated"],
    }
    if page["kind"] == "profile":
        webpage["mainEntity"] = {"@id": PERSON_ID}
    graph = [website_node(), person_node(), webpage]
    if trail:
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        graph.append(breadcrumb_node(page, trail))
    graph.extend(extra)
    return {"@context": "https://schema.org", "@graph": graph}


def faq_node() -> dict:
    return {
        "@type": "FAQPage",
        "@id": BASE + "/#faq",
        "mainEntity": [
            {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
            for q in FAQ
        ],
    }


def json_ld(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, indent=1)
    return raw.replace("</", "<\\/")


# ---------------------------------------------------------------- layout

def head(page: dict, schema: dict, noindex: bool = False) -> str:
    url = absolute(page["path"])
    og_type = {"home": "profile", "profile": "profile", "post": "article", "guide": "article"}.get(page["kind"], "website")
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"
    canonical = "" if page["path"] == "/404" else f'\n<link rel="canonical" href="{url}">'
    verification = (
        f'\n<meta name="google-site-verification" content="{esc(SITE["googleSiteVerification"])}">'
        if SITE.get("googleSiteVerification") else ""
    )
    article = ""
    if page["kind"] == "post":
        article = (
            f'\n<meta property="article:published_time" content="{page["date"]}">'
            f'\n<meta property="article:author" content="{absolute("/about/")}">'
        )
    if og_type == "profile":
        article = (
            f'\n<meta property="profile:first_name" content="{esc(SITE["givenName"])}">'
            f'\n<meta property="profile:last_name" content="{esc(SITE["familyName"])}">'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page["title"])}</title>
<meta name="description" content="{esc(page["description"])}">
<link rel="author" href="{absolute("/about/")}">
<meta name="author" content="{esc(SITE["name"])}">
<meta name="keywords" content="{esc(KEYWORDS)}">
<meta name="robots" content="{robots}">{canonical}{verification}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(SITE["name"])}">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(page["title"])}">
<meta property="og:description" content="{esc(page["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{absolute(OG_IMAGE)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(SITE["name"])}, {esc(SITE["jobTitle"])}">{article}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page["title"])}">
<meta name="twitter:description" content="{esc(page["description"])}">
<meta name="twitter:image" content="{absolute(OG_IMAGE)}">
<meta name="twitter:image:alt" content="{esc(SITE["name"])}, {esc(SITE["jobTitle"])}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/icon.png" type="image/png" sizes="96x96">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
<meta name="theme-color" content="#262626">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..100,400..900&display=swap">
<link rel="stylesheet" href="{asset("/assets/css/site.css")}">
<script>document.documentElement.classList.add('js')</script>
<script type="application/ld+json">
{json_ld(schema)}
</script>
</head>"""


def header(current: str) -> str:
    def here(href: str) -> str:
        return ' aria-current="page"' if href == current else ""

    items = "\n".join(f'      <li><a href="{href}"{here(href)}>{label}</a></li>' for href, label in NAV)
    contact_current = here("/contact/")
    return f"""<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <a class="brand" href="/">{LOGO_IMG}</a>
  <nav class="nav" aria-label="Main">
    <ul id="nav-list">
{items}
      <li class="nav-contact"><a href="/contact/"{contact_current}>Contact</a></li>
    </ul>
  </nav>
  <a class="hire-btn" href="/contact/" data-open-form{contact_current}><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M21 11.5a8.5 8.5 0 0 1-12.3 7.6L3.5 20.5l1.4-4.9A8.5 8.5 0 1 1 21 11.5Z"/></svg><span>Hire Me</span></a>
  <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav-list">Menu</button>
</header>
<main id="main">"""


def lead_dialog() -> str:
    """'Hire me' pop-up. Without a formEndpoint in site.json it opens the visitor's
    email app with the message filled in; with one, it posts there directly."""
    endpoint = esc(SITE.get("formEndpoint", ""))
    key = SITE.get("formAccessKey", "")
    key_input = f'\n      <input type="hidden" name="access_key" value="{esc(key)}">' if key else ""
    return f"""<dialog class="lead" id="lead-dialog" aria-labelledby="lead-title">
  <div class="lead-inner">
    <button class="lead-close" type="button" data-close-form aria-label="Close">&times;</button>
    <p class="lead-kicker">Request a review</p>
    <h2 class="lead-title" id="lead-title">Tell me about your site</h2>
    <p class="lead-sub">Share where your site is now and what you want from search. I read every message and reply myself.</p>
    <form class="lead-form" data-endpoint="{endpoint}" data-email="{SITE["email"]}">{key_input}
      <input class="lead-hp" type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
      <div class="lead-row">
        <label>Name <span aria-hidden="true">*</span><input name="name" type="text" autocomplete="name" required placeholder="Your name"></label>
        <label>Email <span aria-hidden="true">*</span><input name="email" type="email" autocomplete="email" required placeholder="you@company.com"></label>
      </div>
      <label>Website<input name="website" type="text" inputmode="url" autocomplete="url" placeholder="yourbusiness.com"></label>
      <label>What do you want to improve? <span aria-hidden="true">*</span><textarea name="message" rows="4" required placeholder="Where traffic is now, your goals, what seems stuck"></textarea></label>
      <button class="btn btn-arrow lead-submit" type="submit">Send request</button>
      <p class="lead-status" role="status" aria-live="polite"></p>
    </form>
    <p class="lead-alt">Prefer email? <a href="mailto:{SITE["email"]}">{SITE["email"]}</a><br>I only use your details to reply.</p>
  </div>
</dialog>"""


def footer() -> str:
    nav = "\n".join(f'        <li><a href="{h}">{l}</a></li>' for h, l in [("/", "Home")] + NAV + [("/profiles/", "Profiles"), ("/contact/", "Contact")])
    profiles = "\n".join(
        f'        <li><a href="{esc(p["url"])}" rel="me noopener" target="_blank">{esc(p["platform"])}</a></li>'
        for p in SITE["profiles"][:4]
    ) + '\n        <li><a href="/profiles/">All profiles</a></li>'
    return f"""</main>
<footer class="footer">
  <div class="footer-cta">
    <p class="label">Get in touch</p>
    <p class="footer-big"><a href="mailto:{SITE["email"]}">{SITE["email"]}</a></p>
  </div>
  <div class="footer-cols">
    <div>
      <p class="label">Navigate</p>
      <ul>
{nav}
      </ul>
    </div>
    <div>
      <p class="label">Profiles</p>
      <ul>
{profiles}
      </ul>
    </div>
    <div>
      <p class="label">Contact</p>
      <ul>
        <li><a href="mailto:{SITE["email"]}">Email</a></li>
        <li><a href="tel:{SITE["phoneHref"]}">{SITE["phone"]}</a></li>
        <li>{SITE["locality"]}, {SITE["countryName"]}</li>
      </ul>
    </div>
  </div>
  <div class="footer-base">
    <span>&copy; <span data-year>2026</span> {esc(SITE["name"])}</span>
    <span>{SITE["locality"]} <time data-clock>--:--</time> NPT</span>
  </div>
</footer>
{lead_dialog()}
<script src="{asset("/assets/js/site.js")}" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- content

TOKEN = re.compile(r"\{\{(\w+)\}\}")


def fill(text: str, tokens: dict) -> str:
    def sub(m: re.Match) -> str:
        if m.group(1) not in tokens:
            raise KeyError(f"unknown token {{{{{m.group(1)}}}}}")
        return tokens[m.group(1)]
    return TOKEN.sub(sub, text)


def faq_html() -> str:
    return "\n".join(
        f'<details class="faq-item"><summary><span>{esc(q["q"])}</span></summary><p>{esc(q["a"])}</p></details>'
        for q in FAQ
    )


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def glossary_html() -> str:
    return "\n".join(
        f'      <div id="term-{slug(g["term"])}"><dt>{esc(g["term"])}</dt><dd>{esc(g["definition"])}</dd></div>'
        for g in GLOSSARY
    )


def glossary_node() -> dict:
    url = absolute("/expertise/")
    return {
        "@type": "DefinedTermSet",
        "@id": url + "#glossary",
        "name": "SEO glossary",
        "url": url + "#glossary",
        "hasDefinedTerm": [
            {
                "@type": "DefinedTerm",
                "@id": url + "#term-" + slug(g["term"]),
                "name": g["term"],
                "description": g["definition"],
                "inDefinedTermSet": {"@id": url + "#glossary"},
            }
            for g in GLOSSARY
        ],
    }


def guide_node(page: dict) -> dict:
    url = absolute(page["path"])
    return {
        "@type": "TechArticle",
        "@id": url + "#article",
        "headline": page["title"].split(" | ")[0],
        "description": page["description"],
        "url": url,
        "datePublished": page["updated"],
        "dateModified": page["updated"],
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": PERSON_ID},
        "mainEntityOfPage": {"@id": url + "#webpage"},
        "image": absolute(OG_IMAGE),
        "inLanguage": "en",
        "about": ["Search engine optimization", "Semantic SEO", "Generative Engine Optimization", "Topical map"],
    }


def profiles_html(detailed: bool) -> str:
    """Profile tiles: platform + arrow; the Profiles page also shows each handle."""
    rows = []
    for p in SITE["profiles"]:
        rel = "noopener" if p.get("listing") else "me noopener"
        handle = f'<span class="web-tile-handle">{esc(p["handle"])}</span>' if detailed else ""
        rows.append(
            f'      <li><a class="web-tile" href="{esc(p["url"])}" rel="{rel}" target="_blank">'
            f'<span class="web-tile-name">{esc(p["platform"])}{handle}</span>'
            f'<span class="web-tile-arrow" aria-hidden="true">&rarr;</span></a></li>'
        )
    return "\n".join(rows)


POST_META = re.compile(r"\A\s*<!--(.*?)-->", re.S)


def load_posts() -> list[dict]:
    posts = []
    for f in sorted((SRC / "posts").glob("*.html")):
        if f.name.startswith("_"):
            continue
        raw = f.read_text(encoding="utf-8")
        m = POST_META.match(raw)
        if not m:
            raise ValueError(f"{f.name}: missing the JSON header comment")
        meta = json.loads(m.group(1))
        posts.append(dict(
            meta,
            slug=f.stem,
            path=f"/blog/{f.stem}/",
            crumb=meta["title"],
            kind="post",
            updated=meta.get("updated", meta["date"]),
            title_tag=f'{meta["title"]} | {SITE["name"]}',
            body_html=raw[m.end():].strip(),
        ))
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def posts_list_html(posts: list[dict]) -> str:
    if not posts:
        return (
            '<div class="empty">'
            '<p class="empty-title">Posts are on their way from LinkedIn.</p>'
            '<p>I write about semantic SEO, topical authority, local SEO and AI search on LinkedIn. '
            'Those posts will be collected here. Until then, you can read them where they started.</p>'
            f'<p><a class="btn" href="{SITE["linkedinActivity"]}" rel="noopener" target="_blank">Read my posts on LinkedIn</a></p>'
            '</div>'
        )
    items = []
    for p in posts:
        items.append(
            f'<li class="post-row"><a href="{p["path"]}">'
            f'<time datetime="{p["date"]}">{p["date"]}</time>'
            f'<span class="post-title">{esc(p["title"])}</span>'
            f'<span class="post-desc">{esc(p["description"])}</span></a></li>'
        )
    return '<ul class="post-list">' + "\n".join(items) + "</ul>"


def post_body(post: dict) -> str:
    source = ""
    if post.get("linkedin"):
        source = (
            f'<p class="post-source">First published on '
            f'<a href="{esc(post["linkedin"])}" rel="noopener" target="_blank">LinkedIn</a>.</p>'
        )
    return f"""<section class="frame page-head">
  <div class="rail">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/blog/">Blog</a></nav>
    <p class="label">Published</p>
    <p class="value"><time datetime="{post["date"]}">{post["date"]}</time></p>
  </div>
  <div class="body">
    <h1 class="page-title">{esc(post["title"])}</h1>
    <p class="lede">{esc(post["description"])}</p>
  </div>
</section>
<section class="frame">
  <div class="rail"><p class="label">By {esc(SITE["name"])}</p></div>
  <div class="body prose">
{post["body_html"]}
{source}
  </div>
</section>"""


# ---------------------------------------------------------------- build

def write(path: str, text: str) -> None:
    if path == "/":
        target = ROOT / "index.html"
    elif path == "/404":
        target = ROOT / "404.html"
    else:
        target = ROOT / path.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def build() -> None:
    posts = load_posts()
    tokens = {
        "faq": faq_html(),
        "glossary": glossary_html(),
        "profiles": profiles_html(True),
        "profileTiles": profiles_html(False),
        "posts": posts_list_html(posts),
        "email": SITE["email"],
        "phone": SITE["phone"],
        "phoneHref": SITE["phoneHref"],
        "linkedin": SITE["linkedin"],
        "linkedinActivity": SITE["linkedinActivity"],
        "profileCount": str(len(SITE["profiles"])),
    }
    indexed = []

    for page in PAGES:
        body = fill((SRC / "pages" / page["body"]).read_text(encoding="utf-8"), tokens)
        trail = [] if page["path"] == "/" else [(page["crumb"], page["path"])]
        extra = []
        if page["kind"] == "home":
            extra.append(faq_node())
        if page["path"] == "/expertise/":
            extra.append(glossary_node())
        if page["kind"] == "guide":
            extra.append(guide_node(page))
        if page["kind"] == "blog" and posts:
            extra.append({
                "@type": "Blog",
                "@id": absolute("/blog/") + "#blog",
                "name": f'{SITE["name"]} SEO Blog',
                "author": {"@id": PERSON_ID},
                "blogPost": [{"@id": absolute(p["path"]) + "#post"} for p in posts],
            })
        noindex = page["kind"] == "blog" and not posts
        write(page["path"], head(page, page_graph(page, trail, extra), noindex) + "\n" + header(page["path"]) + "\n" + body + "\n" + footer())
        if not noindex:
            indexed.append((page["path"], page["updated"]))

    for post in posts:
        page = dict(post, title=post["title_tag"])
        trail = [("Blog", "/blog/"), (post["title"], post["path"])]
        article = {
            "@type": "BlogPosting",
            "@id": absolute(post["path"]) + "#post",
            "headline": post["title"],
            "description": post["description"],
            "datePublished": post["date"],
            "dateModified": post["updated"],
            "author": {"@id": PERSON_ID},
            "publisher": {"@id": PERSON_ID},
            "mainEntityOfPage": {"@id": absolute(post["path"]) + "#webpage"},
            "image": absolute(OG_IMAGE),
            "inLanguage": "en",
        }
        if post.get("linkedin"):
            article["isBasedOn"] = post["linkedin"]
        write(post["path"], head(page, page_graph(page, trail, [article])) + "\n" + header("/blog/") + "\n" + post_body(post) + "\n" + footer())
        indexed.append((post["path"], post["updated"]))

    not_found = dict(path="/404", kind="page", updated="2026-10-10",
                     title=f'Page Not Found | {SITE["name"]}',
                     description="This page does not exist. Head back to the home page of Dil Bahadur B.K.")
    body404 = (SRC / "pages" / "404.html").read_text(encoding="utf-8")
    write("/404", head(not_found, page_graph(not_found, [], []), noindex=True) + "\n" + header("") + "\n" + body404 + "\n" + footer())

    urls = "\n".join(
        f"  <url><loc>{absolute(p)}</loc><lastmod>{d}</lastmod></url>" for p, d in indexed
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n",
        encoding="utf-8", newline="\n",
    )
    (ROOT / "robots.txt").write_text(
        "# Search engines and AI assistants are welcome to crawl and cite this site.\n"
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n",
        encoding="utf-8", newline="\n",
    )
    llms = [
        f"# {SITE['name']}",
        "",
        f"> {SITE['jobTitle']} in {SITE['locality']}, {SITE['countryName']}. "
        "Specializes in semantic and entity-based SEO, topical authority, technical SEO, local SEO, "
        "programmatic SEO and optimization for AI search (GEO and AEO).",
        "",
        "## Pages",
        "",
    ]
    for page in PAGES:
        if page["kind"] == "blog" and not posts:
            continue
        llms.append(f"- [{page['crumb']}]({absolute(page['path'])}): {page.get('summary', page['description'])}")
    if posts:
        llms += ["", "## Blog posts", ""]
        llms += [f"- [{p['title']}]({absolute(p['path'])}): {p['description']}" for p in posts]
    llms += ["", "## Profiles", ""]
    llms += [f"- [{p['platform']}]({p['url']})" for p in SITE["profiles"]]
    (ROOT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8", newline="\n")

    print(f"built {len(PAGES)} pages, {len(posts)} posts, 404, sitemap ({len(indexed)} urls), robots.txt, llms.txt")


if __name__ == "__main__":
    build()
