# Site source

Everything that makes dilbdrbk.com.np lives in this folder. GitHub Pages does not publish it, because the folder name starts with an underscore.

| File | What it holds |
| --- | --- |
| `site.json` | Name, role, contact details, profiles, skills, education. Change your details here and they update on every page and in the schema. |
| `faq.json` | The FAQ on the home page and its FAQPage schema. |
| `pages/*.html` | The body of each page. `{{email}}`, `{{faq}}` and similar tokens are filled in by the build. |
| `posts/*.html` | Blog posts. Copy `_TEMPLATE.html`, fill in the header, and write the post. |
| `build.py` | Builds every page, `404.html`, `sitemap.xml`, `robots.txt` and `llms.txt`. Each page's title and meta description are set in its `PAGES` list. |
| `make_images.py` | Rebuilds the portrait, the social share card and the favicons from `photo-source.png`. |

## Rebuild after a change

```bash
python _src/build.py
```

Run it from the repo root, then commit the changed files.

## Blog

The blog page stays `noindex` and out of the sitemap until the first post exists. After you add a post and rebuild, the blog page becomes indexable, the post gets `BlogPosting` schema, and both are added to `sitemap.xml` and `llms.txt` automatically.
