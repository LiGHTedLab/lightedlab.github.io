"""Add publications to data/publications.json by DOI, using Crossref metadata.

Usage:
    python tools/add_doi.py 10.1364/OE.546629 [more DOIs ...]
    python tools/add_doi.py --file dois.txt

Existing DOIs are skipped. Review the new entries (type, flags) afterwards,
then run `python build.py`.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBS = ROOT / "data" / "publications.json"

TYPE_MAP = {
    "journal-article": "journal",
    "proceedings-article": "conference",
    "posted-content": "preprint",
    "book-chapter": "chapter",
}


def crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "LiGHT-website-builder (mailto:lightlab@smail.iitm.ac.in)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)["message"]


def entry_from(msg):
    authors = []
    for a in msg.get("author", []):
        name = " ".join(p for p in (a.get("given"), a.get("family")) if p) or a.get("name", "")
        authors.append(name)
    issued = (msg.get("published-print") or msg.get("published-online") or msg.get("issued"))["date-parts"][0]
    venue = (msg.get("container-title") or [""])[0]
    if not venue and msg.get("type") == "posted-content":
        venue = (msg.get("institution") or [{}])[0].get("name", "SSRN preprint")
    doi = msg["DOI"].lower()
    return {
        "id": doi,
        "type": TYPE_MAP.get(msg.get("type"), "other"),
        "year": issued[0],
        "title": " ".join((msg.get("title") or [""])[0].split()),
        "authors": authors,
        "venue": venue,
        "volume": msg.get("volume", ""),
        "issue": msg.get("issue", ""),
        "pages": msg.get("page", "") or msg.get("article-number", ""),
        "doi": doi,
        "url": "https://doi.org/" + doi,
        "corresponding": False,
        "cofirst": False,
        "sources": ["crossref"],
    }


def main(args):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if args[:1] == ["--file"]:
        args = [l.strip() for l in Path(args[1]).read_text().splitlines() if l.strip()]
    pubs = json.loads(PUBS.read_text(encoding="utf-8")) if PUBS.exists() else []
    have = {p.get("doi", "").lower() for p in pubs}
    for doi in args:
        if doi.lower() in have:
            print("skip (exists):", doi)
            continue
        try:
            e = entry_from(crossref(doi))
        except Exception as ex:  # network or unknown DOI
            print("FAILED:", doi, ex)
            continue
        pubs.append(e)
        have.add(e["doi"])
        print("added:", e["year"], e["title"][:80])
    pubs.sort(key=lambda p: (-p["year"], p["title"]))
    PUBS.parent.mkdir(parents=True, exist_ok=True)
    PUBS.write_text(json.dumps(pubs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
