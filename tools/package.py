"""Package both sites for free static hosting.

    python tools/package.py

Writes into deploy/:
  LiGHT_websites.zip   both sites in one folder: the lab site at the root, the personal
                       site under /naresh/ (/personal/ redirects there). For Netlify Drop, Cloudflare Pages,
                       GitHub Pages, tiiny.host and similar hosts.
  site/                the same files, unzipped.
  single-file/         index.html (lab) and personal.html: each a self-contained page with
                       CSS, JS, data and images inlined. Upload one or both anywhere.
"""
import base64
import mimetypes
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

DEPLOY = ROOT / "deploy"
LAB, PERSONAL = ROOT / "LiGHT_lab", ROOT / "personal"
ASSET_RE = re.compile(r"assets/[A-Za-z0-9_\-/.]+\.(?:jpg|jpeg|png|webp|svg|bib)")
MIME = {".webp": "image/webp", ".svg": "image/svg+xml", ".bib": "text/plain"}


def data_uri(path, cache={}):
    if path not in cache:
        mime = MIME.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        cache[path] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    return cache[path]


def single_file(site_dir, payload):
    """Inline stylesheets, scripts and every assets/ file into one HTML page."""
    html = (site_dir / "index.html").read_text(encoding="utf-8")

    def style(m):
        href = m.group(1)
        return f"<style>\n{(site_dir / href).read_text(encoding='utf-8')}\n</style>"

    def script(m):
        src = m.group(1)
        code = payload if src.endswith("data.js") else (site_dir / src).read_text(encoding="utf-8")
        # Only a literal "</script" would end the inline block early; escape just that.
        return "<script>\n" + re.sub(r"</(script)", r"<\\/\1", code, flags=re.I) + "\n</script>"

    html = re.sub(r'<link rel="stylesheet" href="((?!https?:)[^"]+)">', style, html)
    html = re.sub(r'<script src="((?!https?:)[^"]+)"></script>', script, html)
    html = ASSET_RE.sub(lambda m: data_uri(site_dir / m.group(0)), html)
    return html


PERSONAL_PATH = "naresh"  # personal site address: <site>/naresh/


def redirect_page(target):
    """A tiny page that forwards visitors (and search engines) to `target`."""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Redirecting…</title>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<script>location.replace({target!r} + location.search + location.hash);</script>
</head><body><p>This page has moved to <a href="{target}">{target}</a>.</p></body></html>
"""


def main():
    build.main()
    profile, pubs = build.load()
    pubs.sort(key=lambda p: (-p["year"], p["title"]))
    if DEPLOY.exists():
        shutil.rmtree(DEPLOY)

    # 1) Folder / zip: lab at the root, personal under /naresh/
    site = DEPLOY / "site"
    shutil.copytree(LAB, site)
    shutil.copytree(PERSONAL, site / PERSONAL_PATH)
    (site / "assets" / "data.js").write_text(build.make_payload(profile, pubs, {"personal": PERSONAL_PATH + "/"}), encoding="utf-8")
    (site / PERSONAL_PATH / "assets" / "data.js").write_text(build.make_payload(profile, pubs, {"lab": "../"}), encoding="utf-8")
    # The personal page used to live at /personal/; keep that address working.
    (site / "personal").mkdir()
    (site / "personal" / "index.html").write_text(redirect_page("../" + PERSONAL_PATH + "/"), encoding="utf-8")
    (site / ".nojekyll").write_text("")  # GitHub Pages: serve files as-is
    zpath = DEPLOY / "LiGHT_websites.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(site.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(site).as_posix())

    # 2) Single self-contained HTML files
    one = DEPLOY / "single-file"
    one.mkdir(parents=True)
    # Each page embeds only the images it shows: the lab page has no roadmap,
    # and the personal page's research cards show one figure per theme.
    lab_prof = {**profile, "roadmap": []}
    per_prof = {**profile, "research_themes": [{**t, "figures": t["figures"][:1]} for t in profile["research_themes"]]}
    pages = [
        (LAB, "index.html", lab_prof, {"personal": "personal.html"}),
        (PERSONAL, "personal.html", per_prof, {"lab": "index.html"}),
    ]
    for site_dir, name, prof, links in pages:
        (one / name).write_text(single_file(site_dir, build.make_payload(prof, pubs, links)), encoding="utf-8")

    mb = lambda p: f"{p.stat().st_size / 1e6:.1f} MB"
    print(f"\nPackaged into {DEPLOY}:")
    print(f"  {zpath.name}  ({mb(zpath)})")
    for f in sorted(one.iterdir()):
        print(f"  single-file/{f.name}  ({mb(f)})")


if __name__ == "__main__":
    main()
