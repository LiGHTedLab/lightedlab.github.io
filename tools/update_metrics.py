"""Refresh data/metrics.json from the public Google Scholar profile.

    python tools/update_metrics.py

The GitHub Action runs this weekly. Google Scholar has no API and sometimes blocks
automated requests; if it does, the previous values are kept and the run still succeeds.
"""
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metrics.json"
USER = "nh2tv2IAAAAJ"
URL = f"https://scholar.google.com/citations?user={USER}&hl=en"


def fetch():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    cells = [int(x) for x in re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)]
    since = re.search(r'<th class="gsc_rsb_sth">Since (\d{4})</th>', html)
    if len(cells) < 6:
        raise RuntimeError("metrics table not found (blocked or layout changed)")
    return {
        "source": "Google Scholar",
        "url": URL,
        "citations": cells[0], "citations_since": cells[1],
        "h_index": cells[2], "h_index_since": cells[3],
        "i10_index": cells[4], "i10_index_since": cells[5],
        "since_year": int(since.group(1)) if since else None,
        "as_of": datetime.date.today().strftime("%d %b %Y"),
        "updated": datetime.date.today().isoformat(),
    }


def main():
    try:
        m = fetch()
    except Exception as e:  # keep the last good values
        print("Scholar not updated:", e)
        return 0
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    keys = ("citations", "h_index", "i10_index", "citations_since")
    if old and all(old.get(k) == m[k] for k in keys):
        print("No change:", {k: m[k] for k in keys})
        return 0
    OUT.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    print("Updated:", {k: m[k] for k in keys})
    return 0


if __name__ == "__main__":
    sys.exit(main())
