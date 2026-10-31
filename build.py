"""Build both websites from data/.

    python build.py

1. Validates data/profile.json and data/publications.json.
2. Writes assets/data.js into each site (a JS file, so pages also work when
   opened straight from disk, where browsers block fetch() of JSON).
3. Copies shared/ (CSS, renderer, illustrations) into each site's assets/.
4. Regenerates data/publications.bib.
5. Lists every remaining [PLACEHOLDER].
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SITES = [ROOT / "LiGHT_lab", ROOT / "personal"]


def load():
    profile = json.loads((DATA / "profile.json").read_text(encoding="utf-8"))
    pubs = json.loads((DATA / "publications.json").read_text(encoding="utf-8"))
    return profile, pubs


def validate(profile, pubs):
    problems = []
    known = set(profile["sources"]) | {"publications"}
    for p in pubs:
        for k in ("id", "type", "year", "title", "authors", "venue", "sources"):
            if not p.get(k):
                problems.append(f"publication {p.get('id')}: missing {k}")
        if p.get("type") not in ("journal", "conference", "preprint", "chapter", "other"):
            problems.append(f"publication {p['id']}: unknown type {p.get('type')}")
        if not any("Ravichandran" in a for a in p.get("authors", [])):
            problems.append(f"publication {p['id']}: Ravichandran not in author list")

    def walk(node, path):
        if isinstance(node, dict):
            src = node.get("source")
            if isinstance(src, str) and src:
                for s in re.split(r",\s*", src):
                    key = s.split(" ")[0]
                    if key not in known:
                        problems.append(f"{path}: unknown source '{key}'")
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(profile, "profile")
    return problems


def placeholders(profile):
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and node.startswith("[PLACEHOLDER]"):
            found.append(f"{path}: {node}")

    walk(profile, "profile")
    return found


def bibtex(pubs):
    kinds = {"journal": "article", "conference": "inproceedings", "preprint": "misc", "chapter": "incollection"}
    venue_field = {"journal": "journal", "conference": "booktitle", "chapter": "booktitle", "preprint": "howpublished"}
    out = []
    for p in pubs:
        first = re.sub(r"[^A-Za-z]", "", p["authors"][0].split()[-1]) or "anon"
        word = re.sub(r"[^A-Za-z]", "", p["title"].split()[0]).lower()
        key = f"{first}{p['year']}{word}"
        fields = [
            ("title", "{" + p["title"] + "}"),
            ("author", " and ".join(p["authors"])),
            (venue_field.get(p["type"], "note"), p["venue"]),
            ("year", str(p["year"])),
            ("volume", p.get("volume", "")),
            ("number", p.get("issue", "")),
            ("pages", p.get("pages", "")),
            ("doi", p.get("doi", "")),
            ("url", p.get("url", "")),
        ]
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields if v)
        out.append(f"@{kinds.get(p['type'], 'misc')}{{{key},\n{body}\n}}")
    return "\n\n".join(out) + "\n"


def strip_internal(node):
    """Drop editor-only fields (`_readme`, `*_note`, `*_source`, `source`, `sources`) from published data."""
    if isinstance(node, dict):
        return {k: strip_internal(v) for k, v in node.items()
                if not (k.startswith("_") or k.endswith("_note") or k.endswith("_source") or k in ("source", "sources"))}
    if isinstance(node, list):
        return [strip_internal(v) for v in node]
    return node


def load_metrics(profile):
    """Google Scholar metrics kept current by tools/update_metrics.py (weekly GitHub Action)."""
    f = DATA / "metrics.json"
    if f.exists():
        m = json.loads(f.read_text(encoding="utf-8"))
        profile["metrics"] = {**profile.get("metrics", {}), **m}
    return profile


def make_payload(profile, pubs, sites=None):
    """The contents of assets/data.js. `sites` overrides the cross-links between the two sites."""
    public = strip_internal(load_metrics(json.loads(json.dumps(profile))))
    for k in ("email", "email_alt"):
        public["person"].pop(k, None)
    if sites:
        public["sites"] = {**public.get("sites", {}), **sites}
    return "window.SITE_DATA = " + json.dumps({"profile": public, "publications": pubs}, ensure_ascii=False) + ";\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    profile, pubs = load()
    problems = validate(profile, pubs)
    if problems:
        print("Data problems:\n  " + "\n  ".join(problems))
        sys.exit(1)
    pubs.sort(key=lambda p: (-p["year"], p["title"]))
    payload = make_payload(profile, pubs)
    for site in SITES:
        assets = site / "assets"
        if assets.exists():
            shutil.rmtree(assets)
        shutil.copytree(ROOT / "shared", assets)
        (assets / "data.js").write_text(payload, encoding="utf-8")
        (assets / "publications.bib").write_text(bibtex(pubs), encoding="utf-8")
        print("built", site.name)
    (DATA / "publications.bib").write_text(bibtex(pubs), encoding="utf-8")
    print(f"{len(pubs)} publications, {len(profile['patents'])} patent(s), "
          f"{len(profile['grants_current'])} current grants")
    ph = placeholders(profile)
    if ph:
        print(f"\n{len(ph)} placeholder(s) still to fill:")
        for line in ph:
            print("  -", line)


if __name__ == "__main__":
    main()
