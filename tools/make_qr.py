"""Make logo-coloured QR codes for both sites.

    python tools/make_qr.py                      # current GitHub Pages addresses
    python tools/make_qr.py https://lightlab.in  # after moving to a custom domain

Writes qr/ with, per site:
  *_qr.png          square QR code (2000 px, white background) for slides and documents
  *_qr.svg          plain single-colour vector QR for professional printing
  *_card.png        print-ready card (logo, QR, caption) for posters and the door nameplate
Every PNG is decoded after it is made, to prove it scans.
Needs: pip install segno opencv-python-headless
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "qr"
LOGO = ROOT / "shared" / "brand" / "logo.webp"
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://nareshr9169.github.io").rstrip("/")

# LiGHT letter colours (deeper shades of the logo hues, for scanner contrast)
STOPS = [(0xD9, 0x1C, 0x3C), (0x8B, 0x2F, 0xD8), (0x1F, 0x6F, 0xE0), (0x07, 0x7F, 0xA3), (0x0A, 0x8A, 0x5E)]
NAVY = (0x1E, 0x1B, 0x4B)
NEON = ["#f92445", "#b555f2", "#2a84fa", "#11cfe8", "#12d99a"]


def gradient(t):
    t = min(max(t, 0.0), 1.0) * (len(STOPS) - 1)
    i = min(int(t), len(STOPS) - 2)
    f = t - i
    return tuple(round(a + (b - a) * f) for a, b in zip(STOPS[i], STOPS[i + 1]))


def font(names, size):
    for n in names:
        for d in (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")):
            if (d / n).exists():
                return ImageFont.truetype(str(d / n), size)
    return ImageFont.load_default()


def qr_image(url, px=2000):
    qr = segno.make(url, error="h", micro=False)
    m = np.array(list(qr.matrix), dtype=bool)
    n = m.shape[0]
    border = 4
    cell = px // (n + 2 * border)
    size = cell * (n + 2 * border)
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)
    finders = [(0, 0), (0, n - 7), (n - 7, 0)]

    def in_finder(r, c):
        return any(fr <= r < fr + 7 and fc <= c < fc + 7 for fr, fc in finders)

    for r in range(n):
        for c in range(n):
            if m[r, c] and not in_finder(r, c):
                x, y = (c + border) * cell, (r + border) * cell
                col = gradient((c + r * 0.35) / (n * 1.35))
                # Softly rounded, nearly touching modules. Round dots and heavily rounded
                # finder patterns looked nicer but failed to decode in testing.
                pad = cell * 0.02
                d.rounded_rectangle((x + pad, y + pad, x + cell - pad, y + cell - pad), radius=cell * 0.3, fill=col)
    for fr, fc in finders:
        x, y = (fc + border) * cell, (fr + border) * cell
        d.rounded_rectangle((x, y, x + 7 * cell, y + 7 * cell), radius=cell * 1.2, fill=NAVY)
        d.rounded_rectangle((x + cell, y + cell, x + 6 * cell, y + 6 * cell), radius=cell * 0.7, fill="white")
        col = gradient((fc + fr * 0.35 + 3) / (n * 1.35))
        d.rounded_rectangle((x + 2 * cell, y + 2 * cell, x + 5 * cell, y + 5 * cell), radius=cell * 0.3, fill=col)

    # centre logo on a white oval (well within the 30 % error-correction budget)
    logo = Image.open(LOGO).convert("RGBA")
    lw = int(size * 0.22)  # larger logos failed to decode for the shorter (smaller) lab code
    logo = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
    cx, cy = size // 2, size // 2
    pw, ph = int(lw * 1.10), int(logo.height * 1.16)
    d.ellipse((cx - pw // 2, cy - ph // 2, cx + pw // 2, cy + ph // 2), fill="white")
    img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
    return img, qr


def colored_light(d, xy, size, prefix="", suffix=""):
    """Draw '<prefix>LiGHT<suffix>' with LiGHT in the logo colours; returns total width."""
    f = font(["georgiab.ttf", "DejaVuSerif-Bold.ttf"], size)
    x, y = xy
    parts = [(prefix, "white")] + list(zip("LiGHT", NEON)) + [(suffix, "white")]
    for txt, col in parts:
        if txt:
            d.text((x, y), txt, font=f, fill=col)
            x += d.textlength(txt, font=f)
    return x - xy[0]


def card(qr_img, title_kind, url_text, sub):
    W, H = 1800, 2400
    c = Image.new("RGB", (W, H), (7, 9, 24))
    d = ImageDraw.Draw(c)
    for i in range(H):  # subtle vertical glow
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(7 + 18 * (1 - t)), int(9 + 6 * (1 - t)), int(24 + 40 * (1 - t))))
    bar = Image.new("RGB", (W, 14))
    bd = ImageDraw.Draw(bar)
    for x in range(W):
        bd.line([(x, 0), (x, 14)], fill=gradient(x / W))
    c.paste(bar, (0, 0)); c.paste(bar, (0, H - 14))

    logo = Image.open(LOGO).convert("RGBA")
    lw = 620
    logo = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
    c.paste(logo, ((W - lw) // 2, 90), logo)
    y = 90 + logo.height + 40
    if title_kind == "lab":
        f = font(["georgiab.ttf", "DejaVuSerif-Bold.ttf"], 66)
        w = d.textlength("LiGHT Lab", font=f)
        colored_light(d, ((W - w) // 2, y), 66, suffix=" Lab")
        y += 92
        f2 = font(["georgiai.ttf", "DejaVuSerif-Italic.ttf"], 40)
        t = "Light in Guided-wave Healthcare & Testing"
        d.text(((W - d.textlength(t, font=f2)) // 2, y), t, font=f2, fill=(199, 205, 234))
    else:
        f = font(["georgiab.ttf", "DejaVuSerif-Bold.ttf"], 64)
        t = "Dr. Naresh Kumar Ravichandran"
        d.text(((W - d.textlength(t, font=f)) // 2, y), t, font=f, fill="white")
        y += 92
        f2 = font(["segoeui.ttf", "DejaVuSans.ttf"], 40)
        w = d.textlength("Assistant Professor · PI, LiGHT Lab", font=f2)
        x0 = (W - w) // 2
        pre = "Assistant Professor · PI, "
        d.text((x0, y), pre, font=f2, fill=(199, 205, 234))
        x = x0 + d.textlength(pre, font=f2)
        for ch, col in zip("LiGHT", NEON):
            d.text((x, y), ch, font=f2, fill=col); x += d.textlength(ch, font=f2)
        d.text((x, y), " Lab", font=f2, fill=(199, 205, 234))
    y += 90

    q = qr_img.resize((1240, 1240), Image.LANCZOS)
    panel = Image.new("RGB", (q.width + 80, q.height + 80), "white")
    mask = Image.new("L", panel.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *panel.size), radius=60, fill=255)
    panel.paste(q, (40, 40))
    c.paste(panel, ((W - panel.width) // 2, y), mask)
    y += panel.height + 60

    f3 = font(["segoeuib.ttf", "DejaVuSans-Bold.ttf"], 52)
    d.text(((W - d.textlength("Scan to visit", font=f3)) // 2, y), "Scan to visit", font=f3, fill="white")
    y += 78
    f4 = font(["consola.ttf", "DejaVuSansMono.ttf"], 44)
    d.text(((W - d.textlength(url_text, font=f4)) // 2, y), url_text, font=f4, fill=(165, 180, 252))
    y += 70
    f5 = font(["segoeui.ttf", "DejaVuSans.ttf"], 36)
    d.text(((W - d.textlength(sub, font=f5)) // 2, y), sub, font=f5, fill=(148, 163, 184))
    return c


def decodes(path, expected):
    """True only if the code decodes to `expected` at full, half and quarter size (print to phone-screen range)."""
    img = cv2.imread(str(path))
    detectors = [cv2.QRCodeDetector()] + ([cv2.QRCodeDetectorAruco()] if hasattr(cv2, "QRCodeDetectorAruco") else [])
    hits = []
    for scale in (1.0, 0.5, 0.25):
        im = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale != 1 else img
        found = ""
        for det in detectors:
            found = det.detectAndDecode(im)[0]
            if found:
                break
        hits.append(found)
    return all(h == expected for h in hits), f"{sum(h == expected for h in hits)}/3 sizes: {expected}"


def main():
    OUT.mkdir(exist_ok=True)
    host = BASE.split("://", 1)[-1]
    sites = [
        ("lightlab", BASE + "/", "lab", host, "Department of Engineering Design · IIT Madras"),
        ("naresh", BASE + "/personal/", "personal", host + "/personal", "Department of Engineering Design · IIT Madras"),
    ]
    ok = True
    for name, url, kind, url_text, sub in sites:
        img, qr = qr_image(url)
        img.save(OUT / f"{name}_qr.png", optimize=True)
        qr.save(str(OUT / f"{name}_qr.svg"), scale=10, border=4, dark="#1e1b4b")
        card(img, kind, url_text, sub).save(OUT / f"{name}_card.png", optimize=True)
        for f in (f"{name}_qr.png", f"{name}_card.png"):
            good, text = decodes(OUT / f, url)
            ok &= good
            print(f"{f:22} -> {text or 'NOT DECODED'} {'OK' if good else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
