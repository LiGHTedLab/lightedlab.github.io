# LiGHT lab and personal websites

Two static sites, both built from one data folder:

| Folder | Site |
|---|---|
| `LiGHT_lab/` | LiGHT lab (Light in Guided-wave Healthcare & Testing), IIT Madras |
| `personal/` | Personal academic site of Naresh Kumar Ravichandran, including the career roadmap |
| `data/` | **The only place to edit content**: `profile.json`, `publications.json`; `publications.bib` is generated |
| `shared/` | Design system (`base.css`), renderer (`render.js`), illustrations (`art/`), roadmap figures (`roadmap/`), portrait |
| `tools/add_doi.py` | Adds a paper to `publications.json` from its DOI, using Crossref |
| `build.py` | Validates the data and copies everything into each site's `assets/` |
| `SOURCES.md` | Where every fact came from |

Plain HTML/CSS/JS: no framework, no Node, nothing to install beyond Python 3 (already on this PC).

## Update content

1. Edit `data/profile.json` (bio, people, grants, news, teaching, roadmap and so on).
   Every entry has a `source`; keep it filled.
   A string that starts with `[PLACEHOLDER]` shows on the site as a yellow marker. Fill these in before publishing.
2. Add a new paper:
   ```
   python tools/add_doi.py 10.1364/OE.xxxxxx
   ```
   Then open `data/publications.json` and set `"corresponding": true` or `"cofirst": true` if they apply.
   A paper without a DOI can be added by hand; copy the two `ijaer-*` entries as a template.
3. Rebuild:
   ```
   python build.py
   ```
   This regenerates `assets/` in both sites and lists any placeholders still left.

Never edit files inside `LiGHT_lab/assets/` or `personal/assets/`; `build.py` overwrites them.

### Common edits
- **Lab members**: add objects to `people.members`, e.g.
  `{"name": "...", "role": "Ph.D. scholar (2025–)", "interest": "...", "photo": "assets/people/xyz.jpg"}`.
  Put photos in `shared/people/`, then rebuild.
- **Photo**: replace `shared/portrait.jpg` with a sharper square headshot. The current one is cropped from the roadmap deck and is about 150 px.
- **CV PDF**: copy it to `personal/cv.pdf` and set `person.cv_pdf` to `"cv.pdf"`.
- **Cross-links** between the sites: `sites.lab` / `sites.personal`. Set these to full URLs once the sites are hosted.

## Preview locally

```
python -m http.server 8780
```
Then open http://localhost:8780/LiGHT_lab/ and http://localhost:8780/personal/.
Double-clicking `index.html` also works, because the data is a `.js` file rather than fetched JSON.

## Live site (GitHub Pages, automatic)

This folder is the `<username>.github.io` repository. Every push to `main` runs `.github/workflows/deploy.yml`, which:
1. refreshes the Google Scholar numbers (`tools/update_metrics.py` updates `data/metrics.json`),
2. builds both sites (`tools/package.py`),
3. publishes them: the lab site at `https://<username>.github.io/` and the personal site at `/personal/`.

The workflow also runs every Monday, so citations, h-index and i10-index stay current even with no edits.
To force an update now: GitHub → *Actions* → *Build and deploy* → *Run workflow*.

To update content: edit `data/*.json`, then commit and push. The site rebuilds in about a minute.

Never pushed (see `.gitignore`): `SOURCES.md` (it has local paths and private notes) and the generated `assets/` and `deploy/` folders.

## Private visit tracking (GoatCounter)

1. Create a free account at https://www.goatcounter.com/signup and pick a code, e.g. `lightlab`.
   The dashboard is then at `https://lightlab.goatcounter.com`, visible only after you log in.
2. Put that code in `data/profile.json` → `"analytics": {"goatcounter": "lightlab"}`, then commit and push.
3. The dashboard shows each visit's time, page (lab or personal), referrer, country, browser and screen size.
   GoatCounter uses no cookies, so no consent banner is needed. Visits from localhost are not counted.

## Ready-to-upload packages (`python tools/package.py`)

`tools/package.py` rebuilds everything and writes `deploy/`:

| File | What it is | Use it for |
|---|---|---|
| `deploy/LiGHT_websites.zip` | Both sites in one folder: the lab site at the root, the personal site at `/personal/` (links between them already set) | Netlify Drop, Cloudflare Pages, GitHub Pages, any static host |
| `deploy/site/` | The same, unzipped | Drag-and-drop hosts that want a folder |
| `deploy/single-file/index.html` | Lab site as **one** self-contained file (styles, scripts, data, images inside) | Hosts that accept a single HTML file |
| `deploy/single-file/personal.html` | Personal site as one file; links to `index.html` | Upload alongside the lab file, or on its own |

Rerun `python tools/package.py` after every content change, then upload again.

### Quickest free options
- **Netlify Drop** (https://app.netlify.com/drop): drag the `deploy/site` folder onto the page.
  Sign in with a free account so the site stays up, then rename it under *Site settings*,
  e.g. `light-iitm.netlify.app`.
- **Cloudflare Pages**: *Workers & Pages → Create → Pages → Upload assets*, then drop `LiGHT_websites.zip`.
- **GitHub Pages**: upload the contents of `deploy/site/` to a repository (see below).
- **Single-file hosts**: upload `deploy/single-file/index.html` (about 4.6 MB), and `personal.html` too if you want both.
  Check the host's size limit first.
- **Google Sites**: add a button that links to the hosted URL. Its embed box is too small for these pages.

## Deploy on GitHub Pages (free)

Each site is self-contained after `python build.py`.

1. Create a GitHub repository, e.g. `light-lab` (and `nareshr` for the personal site).
2. Copy the **contents** of `deploy/site/` (both sites, cross-links already set) into the repository root, then commit and push.
   To host the two sites separately instead, copy `LiGHT_lab/` and `personal/` into their own repositories.
3. In the repository, open Settings → Pages → Source: *Deploy from a branch* → `main` / root.
   The site goes live at `https://<username>.github.io/light-lab/`.
4. Repeat for `personal/`. Or name a repository `<username>.github.io` to serve the personal site at the root URL.
5. Put the live URLs in `data/profile.json → sites`, rebuild, and push again.

Custom domain: add a `CNAME` file containing the domain, and point a DNS CNAME record at `<username>.github.io`.

## Google Sites

Google Sites cannot host raw HTML pages, so use one of these:
- **Link** (recommended): keep the Google Site and add a button or link to the GitHub Pages URL.
- **Embed**: in Google Sites choose *Insert → Embed → By URL* and paste the GitHub Pages URL.
  This shows the site in an iframe, and the page's own scrollbar sits inside the frame.

## Before publishing: checklist

- [ ] Fill the remaining `[PLACEHOLDER]`s (`python build.py` lists them).
- [ ] Approve the research-theme wording and the grant titles. Keep unpublished work off the site.
- [ ] Check the roadmap figures. They are your own publication figures. Open-access (CC BY) papers are fine; for Elsevier, Optica (OSA) and Springer figures, confirm the publisher's author-reuse terms or swap in your own photos.
- [ ] Confirm the course terms and levels.
- [ ] Replace the portrait with a high-resolution photo.
