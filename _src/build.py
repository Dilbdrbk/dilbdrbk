#!/usr/bin/env python3
"""Build dilbdrbk.com.np from the sources in _src/.

    python _src/build.py

Reads _src/site.json (identity, contact, profiles), _src/faq.json,
_src/pages/*.html (page bodies) and _src/posts/*.md or *.html (blog posts),
then writes the static site into the repo root: one index.html per page,
404.html, sitemap.xml, robots.txt and llms.txt. GitHub Pages ignores _src/
because the folder name starts with an underscore.

Markdown posts are converted by _src/mdpost.py. Their [[tool:x]] and
[[chart:x]] lines insert _src/blocks/tool-x.html and chart-x.html; post images
live in assets/img/blog/ and are made by `python _src/make_images.py --blog`.
"""
from __future__ import annotations

import datetime
import hashlib
import html
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
sys.path.insert(0, str(SRC))
sys.dont_write_bytecode = True  # keep _src/ free of __pycache__
import mdpost  # noqa: E402  (lives next to this file)

BLOCKS = SRC / "blocks"
BLOG_IMG = "/assets/img/blog"
SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
FAQ = json.loads((SRC / "faq.json").read_text(encoding="utf-8"))
GLOSSARY = json.loads((SRC / "glossary.json").read_text(encoding="utf-8"))
RESUME = json.loads((SRC / "resume.json").read_text(encoding="utf-8"))
RESUME_PDF = "/assets/dil-bahadur-bk-resume.pdf"  # made by _src/make_resume_pdf.py
BASE = SITE["url"].rstrip("/")
PERSON_ID = f"{BASE}/#person"
PORTRAIT = "/assets/img/dil-bahadur-bk.jpg"
OG_IMAGE = "/assets/img/og-dil-bahadur-bk.jpg"
KEYWORDS = "Dil Bahadur B.K., Semantic SEO Specialist, SEO Specialist, Semantic SEO, Entity SEO, Topical Authority, Technical SEO, Local SEO, Nepal"

NAV = [
    ("/expertise/", "Expertise"),
    ("/how-search-works/", "How Search Works"),
    ("/resume/", "Resume"),
    ("/industries/", "Industries"),
    ("/about/", "About"),
    ("/blog/", "Blog"),
    ("/tools/", "Tools"),
    ("/checklists/", "Checklists"),
]

# Every page: where it lives, its body file and its search snippet.
# `updated` feeds sitemap lastmod; bump it when a page's content changes.
# The header, footer and Person schema sit on every page. Bump this when they change so the
# sitemap lastmod stays accurate for pages whose own content did not change.
LAYOUT_UPDATED = "2026-10-31"

PAGES = [
    dict(path="/", body="home.html", crumb="Home", updated="2026-10-29", kind="home",
         title="Semantic SEO Specialist in Nepal | Dil Bahadur B.K.",
         description="Dil Bahadur B.K., a semantic SEO specialist in Nepal, drives organic traffic and leads with topical authority and entity-based, technical and local SEO."),
    dict(path="/about/", body="about.html", crumb="About", updated="2026-10-25", kind="profile",
         title="About Dil Bahadur B.K. | Semantic SEO Specialist From Nepal",
         description="Who Dil Bahadur B.K. is: a semantic SEO specialist from Kathmandu who grew from link building into entity-based SEO, topical authority and AI search."),
    dict(path="/expertise/", body="expertise.html", crumb="Expertise", updated="2026-10-25", kind="page",
         title="SEO Expertise: Semantic, Local & AI Search | Dil Bahadur B.K.",
         description="Twelve areas of SEO expertise: semantic and entity SEO, topical maps, technical, on-page, local and off-page SEO, programmatic SEO, GEO, AEO and Reddit SEO."),
    dict(path="/how-search-works/", body="how-search-works.html", crumb="How Search Works", updated="2026-10-25", kind="guide",
         title="How Search Works: Ranking & AI Answers | Dil Bahadur B.K.",
         description="How a page is crawled, understood and ranked, how AI search composes an answer, how an entity becomes a topical map, and how I test SEO ideas."),
    # Employer names appear only in the body of the Resume page, never in its
    # title, description, schema or llms.txt summary.
    dict(path="/resume/", body="resume.html", crumb="Resume", updated="2026-10-16", kind="page",
         title="Resume: Dil Bahadur B.K., Semantic SEO Specialist in Nepal",
         description="Resume of Dil Bahadur B.K., semantic SEO specialist in Nepal: six roles since 2023, skills, tools, 25+ industries and education. Download the PDF.",
         summary="Resume: SEO career since December 2023, from link building to semantic SEO specialist; skills, tools, industries and education, with a PDF to download."),
    dict(path="/industries/", body="industries.html", crumb="Industries", updated="2026-10-25", kind="page",
         title="Industries: Local, Nationwide & E-commerce SEO | Dil Bahadur B.K.",
         description="SEO across 25+ industries: current e-commerce and B2B projects, local services such as plumbing and HVAC, and nationwide niches such as SaaS and finance."),
    dict(path="/blog/", body="blog.html", crumb="Blog", updated="2026-10-25", kind="blog",
         title="SEO Blog | Dil Bahadur B.K.",
         description="Notes on semantic SEO, topical authority, local SEO and AI search by Dil Bahadur B.K., semantic SEO specialist from Kathmandu, Nepal."),
    dict(path="/profiles/", body="profiles.html", crumb="Profiles", updated="2026-11-01", kind="page",
         title="Dil Bahadur B.K. Online: LinkedIn, GitHub & Other Profiles",
         description="Every official profile of Dil Bahadur B.K., semantic SEO specialist from Kathmandu, Nepal, in one place: LinkedIn, GitHub and more."),
    dict(path="/contact/", body="contact.html", crumb="Contact", updated="2026-10-25", kind="contact",
         title="Contact Dil Bahadur B.K. | Semantic SEO Specialist, Kathmandu",
         description="Reach Dil Bahadur B.K. by email, phone or LinkedIn. Based in Kathmandu, Nepal (NPT, UTC+5:45)."),
    dict(path="/tools/", body="tools.html", crumb="Tools", updated="2026-11-03", kind="page",
         title="Free SEO Tools | Dil Bahadur B.K.",
         description="Free SEO tools run in your browser with no sign-up and no data sent, starting with a SERP snippet preview that checks titles and meta descriptions."),
    dict(path="/tools/serp-snippet-preview/", body="serp-snippet-preview.html", crumb="SERP Snippet Preview", updated="2026-11-03", kind="page",
         title="Free SERP Snippet Preview Tool | Dil Bahadur B.K.",
         description="The SERP snippet preview tool shows your title and meta description as Google displays them on desktop and mobile, with pixel meters and cut-off marks."),
    dict(path="/checklists/", body="checklists.html", crumb="Checklists", updated="2026-11-01", kind="page",
         title="Free SEO Checklists | Dil Bahadur B.K.",
         description="Free SEO checklists turn audits into tickable steps, starting with a 56-point SEO audit checklist for technical, on-page, local and AI search."),
    dict(path="/seo-audit-checklist/", body="seo-audit-checklist.html", crumb="SEO Audit Checklist", updated="2026-10-31", kind="page",
         title="SEO Audit Checklist: 56 Checks | Dil Bahadur B.K.",
         description="An SEO audit checklist of 56 checks covers technical SEO, on-page, content, local, off-page and AI search, so you find and fix what blocks rankings."),
    dict(path="/editorial-policy/", body="editorial-policy.html", crumb="Editorial Policy", updated="2026-10-29", kind="page",
         title="Editorial Policy: How SEO Guides Are Checked | Dil Bahadur B.K.",
         description="How Dil Bahadur B.K. researches, fact-checks and updates every SEO guide: a six-tier source hierarchy, claim-by-claim checks, AI use and corrections."),
    dict(path="/privacy-policy/", body="privacy-policy.html", crumb="Privacy Policy", updated="2026-10-29", kind="page",
         title="Privacy Policy: No Cookies, No Tracking | Dil Bahadur B.K.",
         description="The privacy policy of dilbdrbk.com.np: no cookies, no analytics and no stored form data, plus what Cloudflare, GitHub Pages and Google Fonts process."),
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


def human_date(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')} {d.year}"


# ---------------------------------------------------------------- schema.org

def person_node() -> dict:
    node = {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": SITE["name"],
        # Name spellings first, then role titles that the site's own content backs.
        "alternateName": SITE["alternateNames"] + SITE["alternateTitles"],
        "givenName": SITE["givenName"],
        "familyName": SITE["familyName"],
        "jobTitle": SITE["jobTitle"],
        "description": "Semantic SEO specialist in Nepal who drives organic traffic and leads through topical authority and entity-based, technical and local SEO.",
        "url": BASE + "/",
        "mainEntityOfPage": absolute("/about/"),
        "image": {"@type": "ImageObject", "url": absolute(PORTRAIT), "width": 480, "height": 480},
        "email": "mailto:" + SITE["email"],
        "telephone": SITE["phoneHref"],
        "address": {"@type": "PostalAddress", "addressCountry": SITE["country"]},
        "nationality": {"@type": "Country", "name": SITE["countryName"]},
        "hasOccupation": {
            "@type": "Occupation",
            "name": SITE["jobTitle"],
            "occupationLocation": {"@type": "Country", "name": SITE["countryName"]},
            "skills": ", ".join(SITE["knowsAbout"]),
        },
        "alumniOf": [{"@type": e.get("type", "EducationalOrganization"), "name": e["name"]} for e in SITE["education"]],
        "hasCredential": [
            {
                "@type": "EducationalOccupationalCredential",
                "name": e["credential"],
                "credentialCategory": "diploma" if "Diploma" in e["credential"] else "certificate",
                "recognizedBy": {"@type": e.get("type", "EducationalOrganization"), "name": e["name"]},
            }
            for e in SITE["education"]
        ],
        "knowsAbout": SITE["knowsAbout"],
        "sameAs": [p["url"] for p in SITE["profiles"] if not p.get("listing") and p.get("sameAs", True)],
    }
    return node


def person_ref() -> dict:
    """Short Person for author, publisher and founder fields; the @id ties it to the full Person block."""
    return {"@type": "Person", "@id": PERSON_ID, "name": SITE["name"], "url": BASE + "/"}


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


# The service cards on the home page are the list of offers, so the schema always matches them.
SERVICE_CARD = re.compile(r'<li class="card"><a href="(/expertise/#[^"]+)"><span class="idx">\d+</span><h3>(.*?)</h3>')
SERVICE_DESCRIPTION = ("Semantic SEO services that earn rankings in Google and a place in AI answers through "
                       "entity-based SEO, topical maps and technical, on-page, local and off-page SEO.")


def service_node(home_body: str) -> dict:
    """Home page ProfessionalService: what is offered, by whom and where."""
    offers = [(href, html.unescape(name)) for href, name in SERVICE_CARD.findall(home_body)]
    if not offers:
        raise ValueError("no service cards found on the home page for the ProfessionalService offers")
    return {
        "@type": "ProfessionalService",
        "@id": BASE + "/#service",
        "name": f'{SITE["name"]}, {SITE["jobTitle"]}',
        "url": BASE + "/",
        "image": absolute(OG_IMAGE),
        "description": SERVICE_DESCRIPTION,
        "founder": person_ref(),
        "address": {"@type": "PostalAddress", "addressCountry": SITE["country"]},
        "telephone": SITE["phoneHref"],
        "areaServed": SITE["areaServed"],
        "makesOffer": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": name, "url": absolute(href)}}
            for href, name in offers
        ],
    }


def schema_blocks(page: dict, body: str = "", graph: list[dict] | None = None) -> list[dict]:
    """One JSON-LD block per job, the same pattern on every page: the Person everywhere,
    the ProfessionalService on the home page, and a post's BlogPosting with its breadcrumb."""
    context = {"@context": "https://schema.org"}
    blocks = [{**context, **person_node()}]
    if page["kind"] == "home":
        blocks.append({**context, **service_node(body)})
    if graph:
        blocks.append({**context, "@graph": graph})
    return blocks


def ld_scripts(blocks: list[dict]) -> str:
    return "\n".join(f'<script type="application/ld+json">\n{json_ld(block)}\n</script>' for block in blocks)


def json_ld(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, indent=1)
    return raw.replace("</", "<\\/")


# ---------------------------------------------------------------- layout

def head(page: dict, schema: list[dict], noindex: bool = False) -> str:
    url = absolute(page["path"])
    og_type = {"home": "profile", "profile": "profile", "post": "article", "guide": "article"}.get(page["kind"], "website")
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"
    canonical = "" if page["path"] == "/404" else f'\n<link rel="canonical" href="{url}">'
    verification = (
        f'\n<meta name="google-site-verification" content="{esc(SITE["googleSiteVerification"])}">'
        if SITE.get("googleSiteVerification") else ""
    )
    image = absolute(page.get("og_image", OG_IMAGE))
    image_alt = esc(page.get("og_image_alt", f'{SITE["name"]}, {SITE["jobTitle"]}'))
    keywords = ", ".join(page["keywords"]) if page.get("keywords") else KEYWORDS
    article = ""
    if page["kind"] == "post":
        article = (
            f'\n<meta property="article:published_time" content="{page["date"]}">'
            f'\n<meta property="article:modified_time" content="{page["updated"]}">'
            f'\n<meta property="article:author" content="{absolute("/about/")}">'
        )
        if page.get("section"):
            article += f'\n<meta property="article:section" content="{esc(page["section"])}">'
        article += "".join(f'\n<meta property="article:tag" content="{esc(k)}">' for k in page.get("keywords", []))
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
<meta name="keywords" content="{esc(keywords)}">
<meta name="robots" content="{robots}">{canonical}{verification}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(SITE["name"])}">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(page["title"])}">
<meta property="og:description" content="{esc(page["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{image_alt}">{article}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page["title"])}">
<meta name="twitter:description" content="{esc(page["description"])}">
<meta name="twitter:image" content="{image}">
<meta name="twitter:image:alt" content="{image_alt}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/icon.png" type="image/png" sizes="96x96">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
<meta name="theme-color" content="#262626">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..100,400..900&display=swap">
<link rel="stylesheet" href="{asset("/assets/css/site.css")}">
<script>document.documentElement.classList.add('js')</script>
{ld_scripts(schema)}
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
    <h2 class="lead-title" id="lead-title">Start your semantic SEO project</h2>
    <p class="lead-sub">Share where your site is now and what you want from search. I read every message and reply myself.</p>
    <form class="lead-form" data-endpoint="{endpoint}" data-email="{SITE["email"]}">{key_input}
      <input class="lead-hp" type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
      <input type="hidden" name="subject" value="Website review request">
      <div class="lead-row">
        <label>Name <span aria-hidden="true">*</span><input name="name" type="text" autocomplete="name" required placeholder="Your name"></label>
        <label>Email <span aria-hidden="true">*</span><input name="email" type="email" autocomplete="email" required placeholder="you@company.com"></label>
      </div>
      <label>Website<input name="website" type="text" inputmode="url" autocomplete="url" placeholder="yourbusiness.com"></label>
      <label>What do you want to improve? <span aria-hidden="true">*</span><textarea name="message" rows="4" required placeholder="Where traffic is now, your goals, what seems stuck"></textarea></label>
      <button class="btn btn-arrow lead-submit" type="submit">Send request</button>
      <p class="lead-status" role="status" aria-live="polite"></p>
    </form>
    <p class="lead-alt">Prefer email? <a href="mailto:{SITE["email"]}">{SITE["email"]}</a><br>I only use your details to reply. <a href="/privacy-policy/">Privacy policy</a></p>
  </div>
</dialog>"""


# Line icons (24px, stroked in CSS) for the footer, the post byline, share row and sidebar.
ICONS = {
    "email": '<rect x="3.5" y="5.5" width="17" height="13" rx="2"/><path d="m4 7.5 8 6 8-6"/>',
    "phone": '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
    "message": '<path d="M21 11.5a8.5 8.5 0 0 1-12.3 7.6L3.5 20.5l1.4-4.9A8.5 8.5 0 1 1 21 11.5Z"/>',
    "location": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.4"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "check": '<circle cx="12" cy="12" r="8.5"/><path d="m8.5 12.2 2.3 2.3 4.7-4.9"/>',
    "list": '<path d="M9 6.5h11M9 12h11M9 17.5h11M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01"/>',
    "x": '<path d="M4.5 4.5l15 15M19.5 4.5l-15 15"/>',
    "linkedin": '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M8 10.5V16M8 7.8v.01M11.5 16v-5.5M11.5 13a2.5 2.5 0 0 1 5 0v3"/>',
    "facebook": '<path d="M14.5 3.5H13a3.5 3.5 0 0 0-3.5 3.5v13.5M6.5 10.5h7"/>',
    "whatsapp": '<path d="M20.5 12a8.5 8.5 0 0 1-12.4 7.6L3.5 20.5l1.1-4.3A8.5 8.5 0 1 1 20.5 12Z"/><path d="M9.2 8.6c-.4 2.6 3 6.1 5.7 5.9l.9-1.2-1.8-1-.8.7c-.9-.4-1.7-1.2-2.1-2.1l.7-.8-1-1.8Z"/>',
    "copy": '<path d="M10.5 13.5a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1 1"/><path d="M13.5 10.5a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1-1"/>',
}


def icon(name: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


FOOTER_BIO = ("I'm an entity-first semantic SEO consultant in Nepal. I design clear topical maps and strong technical "
              "foundations, so brands win lasting rankings in Google and a trusted place in AI answers.")


def footer() -> str:
    """Three columns: who (photo, role, bio, profile chips), site links, and contact rows."""
    nav = "\n".join(f'        <li><a href="{h}">{l}</a></li>' for h, l in [("/", "Home")] + NAV + [("/profiles/", "Profiles"), ("/contact/", "Contact")])
    chips = "\n".join(
        f'        <li><a href="{esc(p["url"])}" rel="{"noopener" if p.get("listing") else "me noopener"}" target="_blank">{esc(p["platform"])}</a></li>'
        for p in SITE["profiles"][:4]
    ) + '\n        <li><a class="footer-chip-all" href="/profiles/">All profiles</a></li>'

    def row(name: str, key: str, value: str) -> str:
        return (f'        <li><span class="footer-ico">{icon(name)}</span>'
                f'<span><span class="footer-k">{key}</span>{value}</span></li>')

    rows = "\n".join([
        row("email", "Email", f'<a class="footer-v" href="mailto:{SITE["email"]}">{SITE["email"]}</a>'),
        row("phone", "Phone", f'<a class="footer-v" href="tel:{SITE["phoneHref"]}">{SITE["phone"]}</a>'),
        row("message", "Message", f'<a class="footer-v" href="{esc(SITE["linkedin"])}" rel="me noopener" target="_blank">Message on LinkedIn</a>'),
        row("location", "Based in", f'<span class="footer-v">{SITE["countryName"]}</span>'),
    ])
    return f"""</main>
<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand">
      <a class="footer-id" href="/about/">
        <img class="footer-avatar" src="{asset("/assets/img/dil-bahadur-bk.webp")}" width="56" height="56" alt="" loading="lazy">
        <span><span class="footer-name">{esc(SITE["name"])}</span><span class="footer-role">{esc(SITE["jobTitle"])}</span></span>
      </a>
      <p class="footer-bio">{FOOTER_BIO}</p>
      <ul class="footer-chips" aria-label="Profiles">
{chips}
      </ul>
    </div>
    <nav class="footer-col" aria-label="Footer">
      <p class="footer-head">Navigate</p>
      <ul class="footer-links">
{nav}
      </ul>
    </nav>
    <div class="footer-col">
      <p class="footer-head">Get in touch</p>
      <ul class="footer-contact">
{rows}
      </ul>
    </div>
  </div>
  <div class="footer-base">
    <span>&copy; <span data-year>2026</span> {esc(SITE["name"])}</span>
    <span class="footer-legal"><a href="/editorial-policy/">Editorial Policy</a><a href="/privacy-policy/">Privacy Policy</a></span>
    <span>{SITE["countryName"]} <time data-clock>--:--</time> NPT</span>
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


# Old URLs that moved: each gets a small page that sends visitors and crawlers on.
REDIRECTS = {"/experience/": "/resume/"}


def redirect_html(target: str) -> str:
    url = absolute(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved to {esc(target)} | {esc(SITE["name"])}</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace("{target}" + location.hash)</script>
</head>
<body>
<p>This page has moved to <a href="{target}">{url}</a>.</p>
</body>
</html>
"""


# ---------------------------------------------------------------- resume

def month_label(ym: str) -> str:
    d = datetime.date.fromisoformat(ym + "-01")
    return f"{d.strftime('%b')} {d.year}"


def duration_label(start: str, end: str) -> str:
    """Months counted the way LinkedIn does: both the first and the last month count."""
    s, e = datetime.date.fromisoformat(start + "-01"), datetime.date.fromisoformat(end + "-01")
    months = (e.year - s.year) * 12 + (e.month - s.month) + 1
    years, rest = divmod(months, 12)
    parts = ([f"{years} year" + ("s" if years > 1 else "")] if years else []) + \
            ([f"{rest} month" + ("s" if rest > 1 else "")] if rest else [])
    return " ".join(parts)


def career_path_html() -> str:
    """Oldest to newest: each step links to its role below. Works without JavaScript."""
    steps = []
    for role in reversed(RESUME["roles"]):
        current = ' class="is-current"' if not role["end"] else ""
        steps.append(
            f'      <li{current}><a href="#role-{role["id"]}"><span class="cp-dot" aria-hidden="true"></span>'
            f'<span class="cp-date">{month_label(role["start"])}</span><span class="cp-role">{esc(role["path"])}</span></a></li>'
        )
    return '    <ol class="career-path" role="list">\n' + "\n".join(steps) + "\n    </ol>"


def resume_stats_html() -> str:
    first = RESUME["roles"][-1]["start"][:4]
    tools = sum(len(g["items"]) for g in RESUME["tools"])
    stats = [
        ("In SEO since", first, ""),
        ("Roles, from data entry to team lead", str(len(RESUME["roles"])), str(len(RESUME["roles"]))),
        ("Industries worked in", "25+", "25"),
        ("Tools in daily use", str(tools), str(tools)),
    ]
    rows = []
    for label, value, count in stats:
        attrs = f' data-count="{count}"' + (' data-suffix="+"' if value.endswith("+") else "") if count else ""
        rows.append(f"      <div><dt>{esc(label)}</dt><dd{attrs}>{value}</dd></div>")
    return '    <dl class="stats stats-4">\n' + "\n".join(rows) + "\n    </dl>"


def roles_html() -> str:
    items = []
    for role in RESUME["roles"]:
        if role["end"]:
            dates = f'{month_label(role["start"])} to {month_label(role["end"])}'
            meta = [esc(role["company"]), dates, duration_label(role["start"], role["end"]), role["type"]]
        else:
            meta = [esc(role["company"]), f'{month_label(role["start"])} to present', role["type"]]
        if role.get("location"):
            meta.append(role["location"])
        badge = '<span class="role-badge">Current role</span>' if not role["end"] else ""
        bullets = "".join(f"<li>{esc(b)}</li>" for b in role["bullets"])
        items.append(
            f'      <li class="role" id="role-{role["id"]}">\n'
            f'        <div class="role-head">{badge}<h3>{esc(role["title"])}</h3>'
            f'<p class="role-meta">{" <span>&middot;</span> ".join(meta)}</p></div>\n'
            + (f"        <ul>{bullets}</ul>\n" if bullets else "")
            + "      </li>"
        )
    return '    <ol class="timeline resume-roles">\n' + "\n".join(items) + "\n    </ol>"


def resume_tokens() -> dict:
    pdf = asset(RESUME_PDF) if (ROOT / RESUME_PDF.lstrip("/")).exists() else RESUME_PDF
    groups = lambda key: "\n".join(  # noqa: E731
        f'      <div><h3 class="list-title">{esc(g["group"])}</h3><ul class="tags tags-sm" role="list">'
        + "".join(f"<li>{esc(i)}</li>" for i in g["items"]) + "</ul></div>"
        for g in RESUME[key]
    )
    credentials = [("Methodology", m["name"], f'Learned from {m["by"]}') for m in SITE["methodologies"]] + [
        ("Diploma" if "Diploma" in e["credential"] else "Training",
         e["credential"].replace("Diploma in ", "").replace(" Training", ""), e["name"])
        for e in SITE["education"]
    ]
    return {
        "resumeSummary": esc(RESUME["summary"]),
        "resumePdf": pdf,
        "careerPath": career_path_html(),
        "resumeStats": resume_stats_html(),
        "roles": roles_html(),
        "expertiseTags": "\n".join(f"      <li>{esc(t)}</li>" for t in RESUME["expertise"]),
        "knowledgeCards": "\n".join(
            f'      <li class="card card-static"><h3>{esc(k["title"])}</h3><p>{esc(k["text"])}</p></li>'
            for k in RESUME["knowledge"]
        ),
        "toolGroups": groups("tools"),
        "industryGroups": groups("industries"),
        "credentialCards": "\n".join(
            f'      <li class="card card-static"><span class="idx">{kind}</span><h3>{esc(name)}</h3><p>{esc(org)}</p></li>'
            for kind, name, org in credentials
        ),
    }


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


def cta_html(kind: str) -> str:
    if kind == "inline":
        return (
            '<aside class="post-cta" aria-label="Entity SEO service">\n'
            '  <p class="post-cta-kicker">Need this for your site?</p>\n'
            '  <p class="post-cta-title">Get an entity map and a topical map</p>\n'
            '  <p class="post-cta-text">I map your central entity, its attributes and related entities, '
            'then turn them into a page plan with structured data.</p>\n'
            '  <div class="actions"><a class="btn btn-arrow" href="/contact/" data-open-form>Request an entity review</a></div>\n'
            '</aside>'
        )
    if kind == "services":
        return (
            '<div class="actions post-actions"><a class="btn btn-arrow" href="/contact/" data-open-form>Hire Me</a>'
            '<a class="btn btn-ghost" href="/expertise/#semantic-seo">See my expertise</a></div>'
        )
    raise ValueError(f"unknown [[cta:{kind}]]")


def post_block(name: str, args: list[str]) -> str:
    """HTML for a [[name:args]] line in a Markdown post."""
    if name == "cta":
        return cta_html(args[0])
    if name == "figure":
        stem, size, alt, caption = args
        width, height = size.split("x")
        src = asset(f"{BLOG_IMG}/{stem}.webp")
        return (
            f'<figure class="post-figure"><img src="{src}" width="{width}" height="{height}" alt="{esc(alt)}" '
            f'loading="lazy" decoding="async"><figcaption>{esc(caption)}</figcaption></figure>'
        )
    if name in ("tool", "chart"):
        return (BLOCKS / f"{name}-{args[0]}.html").read_text(encoding="utf-8").strip()
    raise ValueError(f"unknown block [[{name}]]")


def load_posts() -> list[dict]:
    posts = []
    for f in sorted((SRC / "posts").iterdir()):
        if f.name.startswith("_") or f.suffix not in (".md", ".html"):
            continue
        raw = f.read_text(encoding="utf-8")
        if f.suffix == ".md":
            doc = mdpost.convert(raw, post_block)
            meta = dict(doc["meta"], title=doc["title"], description=doc["description"])
            body_html, words, links = doc["html"], doc["words"], doc["links"]
            headings = [(level, mdpost.inline(text), hid) for level, text, hid in doc["headings"]]
        else:
            m = POST_META.match(raw)
            if not m:
                raise ValueError(f"{f.name}: missing the JSON header comment")
            meta = json.loads(m.group(1))
            body_html = raw[m.end():].strip()
            words = len(re.sub(r"<[^>]+>", " ", body_html).split())
            links = list(dict.fromkeys(re.findall(r'href="(https?://[^"]+)"', html.unescape(body_html))))
            headings = [(int(lvl), esc(html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()), hid)
                        for lvl, hid, inner in re.findall(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>', body_html, re.S)]
        post = dict(
            meta,
            slug=f.stem,
            path=f"/blog/{f.stem}/",
            crumb=meta["title"],
            kind="post",
            updated=meta.get("updated", meta["date"]),
            title_tag=f'{meta["title"]} | {SITE["name"]}',
            body_html=body_html,
            headings=headings,
            words=words,
            links=links,
            minutes=max(1, round(words / 230)),
        )
        if meta.get("image"):
            post["og_image"] = f'{BLOG_IMG}/{meta["image"]}.jpg'
            post["og_image_alt"] = meta.get("imageAlt", meta["title"])
        posts.append(post)
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
        thumb = ""
        if p.get("image"):
            src = asset(f'{BLOG_IMG}/{p["image"]}-thumb.webp')
            thumb = f'<img class="post-thumb" src="{src}" width="640" height="336" alt="" loading="lazy" decoding="async">'
        items.append(
            f'<li class="post-row"><a href="{p["path"]}">{thumb}<span class="post-row-text">'
            f'<span class="post-row-meta"><time datetime="{p["date"]}">{human_date(p["date"])}</time>'
            f'<span>{p["minutes"]} min read</span></span>'
            f'<span class="post-title">{esc(p["title"])}</span>'
            f'<span class="post-desc">{esc(p["description"])}</span></span></a></li>'
        )
    return '<ul class="post-list">' + "\n".join(items) + "</ul>"


# Free checklists, newest first. Each one is a page in PAGES; its cover comes from make_images.py.
CHECKLISTS = [
    dict(path="/seo-audit-checklist/", image="seo-audit-checklist", date="2026-10-31", checks=56,
         title="SEO Audit Checklist: 56 Checks for Any Website",
         description="A 56-point SEO audit checklist covers technical SEO, on-page, content, local, off-page and AI search, with a running score and a printable PDF."),
]


# Free standalone tools, newest first. Tools that live inside blog posts stay with their posts.
TOOLS = [
    dict(path="/tools/serp-snippet-preview/", image="serp-snippet-preview", label="Tool page",
         title="SERP Snippet Preview Tool",
         description="Preview a title and meta description as Google shows them on desktop and mobile, with pixel meters and cut-off marks."),
]


def tool_cards_html(wide: bool = False, limit: int | None = None) -> str:
    """Tool cards: the Tools page uses a grid, the home Resources tab the wide blog-card layout."""
    cards = []
    for t in TOOLS[:limit]:
        src = asset(f'{BLOG_IMG}/{t["image"]}.webp')
        img = f'<img src="{src}" width="1600" height="840" alt="" loading="lazy" decoding="async">'
        meta = f'<span class="feature-meta"><span>{esc(t["label"])}</span><span>Free, runs in your browser</span></span>'
        more = "Open the tool"
        if wide:
            cards.append(f'<li class="feature-card"><a href="{t["path"]}">{img}<span class="feature-text">'
                         f'<span class="feature-tags"><span>Free tool</span></span>{meta}'
                         f'<span class="feature-title">{esc(t["title"])}</span>'
                         f'<span class="feature-desc">{esc(t["description"])}</span>'
                         f'<span class="feature-more">{more}</span></span></a></li>')
        else:
            cards.append(f'<li class="chk-card"><a href="{t["path"]}">{img}<span class="chk-card-text">{meta}'
                         f'<span class="chk-card-title">{esc(t["title"])} <span aria-hidden="true">&#8599;</span></span>'
                         f'<span class="chk-card-desc">{esc(t["description"])}</span></span></a></li>')
    cls = "feature-posts" if wide else "chk-cards"
    return f'<ul class="{cls}" role="list">\n' + "\n".join(cards) + "\n</ul>"


def checklist_cards_html(wide: bool = False) -> str:
    """Checklist cards: the hub page uses a grid, the home Resources tab the wide blog-card layout."""
    cards = []
    for c in CHECKLISTS:
        src = asset(f'{BLOG_IMG}/{c["image"]}.webp')
        img = f'<img src="{src}" width="1600" height="840" alt="" loading="lazy" decoding="async">'
        meta = (f'<span class="feature-meta"><span>{esc(SITE["name"])}</span>'
                f'<time datetime="{c["date"]}">{human_date(c["date"])}</time><span>{c["checks"]} checks</span></span>')
        if wide:
            cards.append(f'<li class="feature-card"><a href="{c["path"]}">{img}<span class="feature-text">'
                         f'<span class="feature-tags"><span>Checklist</span></span>{meta}'
                         f'<span class="feature-title">{esc(c["title"])}</span>'
                         f'<span class="feature-desc">{esc(c["description"])}</span>'
                         f'<span class="feature-more">Open the checklist</span></span></a></li>')
        else:
            cards.append(f'<li class="chk-card"><a href="{c["path"]}">{img}<span class="chk-card-text">{meta}'
                         f'<span class="chk-card-title">{esc(c["title"])} <span aria-hidden="true">&#8599;</span></span>'
                         f'<span class="chk-card-desc">{esc(c["description"])}</span></span></a></li>')
    cls = "feature-posts" if wide else "chk-cards"
    return f'<ul class="{cls}" role="list">\n' + "\n".join(cards) + "\n</ul>"


def featured_posts_html(posts: list[dict], limit: int = 3) -> str:
    """Home page Resources tab: every post as the same wide card (image left, text right)."""
    if not posts:
        return '<p class="section-note">The first guides are on their way.</p>'
    cards = []
    for p in posts[:limit]:
        image = ""
        if p.get("image"):
            src = asset(f'{BLOG_IMG}/{p["image"]}.webp')
            image = f'<img src="{src}" width="1600" height="840" alt="" loading="lazy" decoding="async">'
        tags = "".join(f"<span>{esc(t)}</span>" for t in p.get("tags", [p["section"]] if p.get("section") else []))
        cards.append(
            f'<li class="feature-card"><a href="{p["path"]}">{image}<span class="feature-text">'
            f'<span class="feature-tags">{tags}</span>'
            f'<span class="feature-meta"><time datetime="{p["date"]}">{human_date(p["date"])}</time>'
            f'<span>{p["minutes"]} min read</span></span>'
            f'<span class="feature-title">{esc(p["title"])}</span>'
            f'<span class="feature-desc">{esc(p["description"])}</span>'
            f'<span class="feature-more">Read the guide</span></span></a></li>'
        )
    return '<ul class="feature-posts">\n' + "\n".join(cards) + "\n</ul>"


def byline(post: dict) -> str:
    photo = asset("/assets/img/dil-bahadur-bk.webp")
    updated = ""
    if post["updated"] != post["date"]:
        updated = f'<span>Updated <time datetime="{post["updated"]}">{human_date(post["updated"])}</time></span>'
    return f"""<div class="byline">
      <img class="byline-photo" src="{photo}" width="48" height="48" alt="">
      <p class="byline-who"><a href="/about/" rel="author">{esc(SITE["name"])}</a><span>{esc(SITE["jobTitle"])}</span></p>
      <p class="byline-meta"><span>Published <time datetime="{post["date"]}">{human_date(post["date"])}</time></span>{updated}<span class="byline-read">{icon("clock")}{post["minutes"]} min read</span></p>
    </div>"""


def author_box() -> str:
    """Written-by box under every post: who wrote it, why they know the topic, where to find them."""
    photo = asset("/assets/img/dil-bahadur-bk.webp")
    method = SITE["methodologies"][0]
    return f"""<aside class="author-box" aria-labelledby="author-name">
      <img class="author-photo" src="{photo}" width="112" height="112" alt="Portrait of {esc(SITE["name"])}" loading="lazy">
      <div>
        <p class="author-kicker">Written by</p>
        <p class="author-name" id="author-name"><a href="/about/" rel="author">{esc(SITE["name"])}</a></p>
        <p class="author-role">{esc(SITE["jobTitle"])}, {SITE["countryName"]}</p>
        <p class="author-bio">I'm {esc(SITE["name"])}, a semantic SEO specialist from Nepal. I plan websites around entities and topical maps, then strengthen them with technical, local, on-page and off-page SEO. My SEO career started in December 2023, and my method follows the {esc(method["name"])} methodology I learned from {esc(method["by"])}.</p>
        <p class="author-links"><a href="/about/">About me</a><a href="{esc(SITE["linkedin"])}" rel="me noopener" target="_blank">LinkedIn</a><a href="/profiles/">All profiles</a><a href="/editorial-policy/">How I research</a><a href="/contact/" data-open-form>Hire Me</a></p>
      </div>
    </aside>"""


def related_links() -> str:
    return """<nav class="post-related" aria-label="Keep reading">
      <p class="label">Keep reading</p>
      <ul>
        <li><a href="/how-search-works/"><span>Guide</span>How search works, from a query to an AI answer</a></li>
        <li><a href="/expertise/#semantic-seo"><span>Expertise</span>Semantic and entity SEO</a></li>
        <li><a href="/expertise/#glossary"><span>Glossary</span>SEO terms in plain words</a></li>
      </ul>
    </nav>"""


def share_html(post: dict) -> str:
    """Share row: plain share links, plus a Copy link button that only shows with JavaScript."""
    url = absolute(post["path"])
    u, t = urllib.parse.quote(url, safe=""), urllib.parse.quote(post["title"], safe="")
    links = [
        ("x", "X", f"https://x.com/intent/tweet?url={u}&text={t}"),
        ("linkedin", "LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={u}"),
        ("facebook", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}"),
        ("whatsapp", "WhatsApp", f"https://wa.me/?text={t}%20{u}"),
    ]
    items = [f'<li><a href="{esc(href)}" target="_blank" rel="noopener">{icon(name)}<span>{label}</span></a></li>'
             for name, label, href in links]
    items.append(f'<li><a href="{esc(f"mailto:?subject={t}&body={u}")}">{icon("email")}<span>Email</span></a></li>')
    items.append(f'<li class="share-copy"><button type="button" data-copy="{esc(url)}">{icon("copy")}<span aria-live="polite">Copy link</span></button></li>')
    joined = "\n      ".join(items)
    return f"""<nav class="post-share" aria-label="Share this guide">
      <p class="post-share-label">Share</p>
      <ul>
      {joined}
      </ul>
    </nav>"""


def takeaways_html(post: dict) -> str:
    """Key takeaways box at the top of the article, from the post header's `takeaways`."""
    if not post.get("takeaways"):
        return ""
    items = "\n".join(f'        <li>{icon("check")}<span>{mdpost.inline(t)}</span></li>' for t in post["takeaways"])
    return f"""<aside class="post-takeaways" aria-labelledby="takeaways-title">
      <p class="post-takeaways-title" id="takeaways-title">Key takeaways</p>
      <ul>
{items}
      </ul>
    </aside>"""


def side_toc_html(post: dict) -> str:
    """'On this page' sidebar with every h2 and its h3s. The links work without
    JavaScript; site.js marks the section in view."""
    groups: list[tuple[str, list[str]]] = []
    for level, label, hid in post.get("headings", []):
        link = f'<a href="#{hid}">{label}</a>'
        if level == 3 and groups:
            groups[-1][1].append(link)
        elif level in (2, 3):
            groups.append((link, []))
    if not groups:
        return ""
    rows = "\n".join(
        f'        <li>{link}' + (f'<ol>{"".join(f"<li>{s}</li>" for s in subs)}</ol>' if subs else "") + "</li>"
        for link, subs in groups
    )
    return f"""<nav class="post-side" aria-label="On this page">
      <div class="post-side-inner" data-post-toc>
        <p class="post-side-title">{icon("list")}On this page</p>
        <ol class="post-side-list">
{rows}
        </ol>
      </div>
    </nav>"""


def post_body(post: dict) -> str:
    source = ""
    if post.get("linkedin"):
        source = (
            f'<p class="post-source">First published on '
            f'<a href="{esc(post["linkedin"])}" rel="noopener" target="_blank">LinkedIn</a>.</p>'
        )
    kicker = ""
    if post.get("section"):
        kicker = f'\n    <p class="kicker"><span class="dot" aria-hidden="true"></span>{esc(post["section"])} guide</p>'
    cover = ""
    if post.get("image"):
        webp = asset(f'{BLOG_IMG}/{post["image"]}.webp')
        jpg = asset(f'{BLOG_IMG}/{post["image"]}.jpg')
        cover = f"""
<section class="frame post-cover-frame">
  <div class="body">
    <figure class="post-cover"><picture><source type="image/webp" srcset="{webp}"><img src="{jpg}" width="1200" height="630" alt="{esc(post.get("imageAlt", post["title"]))}" fetchpriority="high"></picture></figure>
  </div>
</section>"""
    return f"""<article class="post">
<section class="frame page-head post-head">
  <div class="body">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/blog/">Blog</a><span>/</span><span aria-current="page">{esc(post["title"])}</span></nav>{kicker}
    <h1 class="page-title">{esc(post["title"])}</h1>
    <p class="lede">{esc(post["description"])}</p>
    {byline(post)}
    {share_html(post)}
  </div>
</section>{cover}
<section class="frame post-main">
  <div class="body post-layout">
    <div class="post-content">
    {takeaways_html(post)}
    <div class="prose post-body">
{post["body_html"]}
{source}
    </div>
    {author_box()}
    {related_links()}
    </div>
    {side_toc_html(post)}
  </div>
</section>
</article>"""


def post_node(post: dict) -> dict:
    url = absolute(post["path"])
    image = absolute(post.get("og_image", OG_IMAGE))
    node = {
        "@type": "BlogPosting",
        "@id": url + "#article",
        "headline": post["title"],
        "description": post["description"],
        "datePublished": post["date"],
        "dateModified": post["updated"],
        "author": person_ref(),
        "publisher": person_ref(),
        "mainEntityOfPage": url,
        "image": {"@type": "ImageObject", "url": image, "width": 1200, "height": 630},
        "inLanguage": "en",
        "wordCount": post["words"],
        "timeRequired": f'PT{post["minutes"]}M',
    }
    if post.get("section"):
        node["articleSection"] = post["section"]
    if post.get("keywords"):
        node["keywords"] = post["keywords"]
    for key in ("about", "mentions"):
        if post.get(key):
            node[key] = [dict({"@type": "Thing"}, **thing) for thing in post[key]]
    # Sources are named in the text without links; their URLs live in the
    # post header as `citations`. Older posts fall back to their inline links.
    citations = post.get("citations") or post.get("links")
    if citations:
        node["citation"] = citations
    if post.get("linkedin"):
        node["isBasedOn"] = post["linkedin"]
    return node


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
        "featuredPosts": featured_posts_html(posts),
        "checklistCards": checklist_cards_html(),
        "toolCards": tool_cards_html(),
        "toolFeature": tool_cards_html(wide=True, limit=3),
        "checklistFeature": checklist_cards_html(wide=True),
        "email": SITE["email"],
        "phone": SITE["phone"],
        "phoneHref": SITE["phoneHref"],
        "linkedin": SITE["linkedin"],
        "linkedinActivity": SITE["linkedinActivity"],
        "profileCount": str(len(SITE["profiles"])),
        **resume_tokens(),
    }
    indexed = []

    for page in PAGES:
        body = fill((SRC / "pages" / page["body"]).read_text(encoding="utf-8"), tokens)
        noindex = page["kind"] == "blog" and not posts
        write(page["path"], head(page, schema_blocks(page, body), noindex) + "\n" + header(page["path"]) + "\n" + body + "\n" + footer())
        if not noindex:
            indexed.append((page["path"], max(page["updated"], LAYOUT_UPDATED)))

    for post in posts:
        page = dict(post, title=post["title_tag"])
        trail = [("Blog", "/blog/"), (post["title"], post["path"])]
        write(post["path"], head(page, schema_blocks(page, graph=[post_node(post), breadcrumb_node(page, trail)])) + "\n" + header("/blog/") + "\n" + post_body(post) + "\n" + footer())
        indexed.append((post["path"], max(post["updated"], LAYOUT_UPDATED)))

    not_found = dict(path="/404", kind="page", updated="2026-10-10",
                     title=f'Page Not Found | {SITE["name"]}',
                     description="This page does not exist. Head back to the home page of Dil Bahadur B.K.")
    body404 = (SRC / "pages" / "404.html").read_text(encoding="utf-8")
    write("/404", head(not_found, schema_blocks(not_found), noindex=True) + "\n" + header("") + "\n" + body404 + "\n" + footer())

    for old, new in REDIRECTS.items():
        write(old, redirect_html(new))

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
        f"> {SITE['jobTitle']} in {SITE['countryName']}. "
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
