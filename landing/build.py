"""Build the static partner landing page into landing/site/.

usage: python3 landing/build.py [BASE_URL]
BASE_URL is the public address the QR code points to (default: GitHub Pages).
"""
import json, re, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import segno

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "site"
BRAND, FONTS = SRC / "brand", SRC / "fonts"
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://woutlelievre1.github.io/Tectonicpartner/").rstrip("/") + "/"
AUDIO = ROOT.parent / "TECTONIC_THE_SIGNAL_OUTPUT" / "TECTONIC_THE_SIGNAL_FINAL.mp3"

# Official Tectonic wordmark (tectonicconf.eu/assets/tectonic-logo.svg): list of (d, evenodd)
LOGO_SVG = (BRAND / "tectonic-logo.svg").read_text(encoding="utf-8")
LOGO_PATHS = [(m.group(2), "evenodd" in m.group(1)) for m in re.finditer(r'<path([^>]*?)\bd="([^"]+)"', LOGO_SVG)]
EO = ' fill-rule="evenodd"'
logo_symbol = "".join('<path%s d="%s" fill="currentColor"/>' % (EO if eo else "", d) for d, eo in LOGO_PATHS)

OUT.mkdir(exist_ok=True)
html = (SRC / "index.html").read_text(encoding="utf-8")
html = html.replace("__CAPS__", json.dumps(json.loads((SRC / "captions.json").read_text(encoding="utf-8")), ensure_ascii=False))
html = html.replace("__ENV__", (SRC / "envelope.txt").read_text().strip()).replace("__BASE_URL__", BASE).replace("__LOGO__", logo_symbol)
(OUT / "index.html").write_text(html, encoding="utf-8")
shutil.copyfile(AUDIO, OUT / "the-signal.mp3")
shutil.copyfile(BRAND / "favicon.svg", OUT / "favicon.svg")
(OUT / "fonts").mkdir(exist_ok=True)
for f in ("anybody-normal.woff2", "anybody-italic.woff2", "OFL.txt"):
    shutil.copyfile(FONTS / f, OUT / "fonts" / f)
(OUT / ".nojekyll").write_text("")


# --- minimal SVG path rasteriser (absolute M/L/H/V/C/Z, as used by the logo) -------
def subpaths(d, steps=24):
    toks = re.findall(r"[MLHVCZ]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, cur, i, cmd, p = [], [], 0, None, (0.0, 0.0)
    while i < len(toks):
        if toks[i] in "MLHVCZ":
            cmd = toks[i]; i += 1
            if cmd == "Z":
                if cur: out.append(cur); cur = []
                continue
        if cmd == "M":
            if cur: out.append(cur)
            p = (float(toks[i]), float(toks[i + 1])); i += 2; cur = [p]; cmd = "L"
        elif cmd == "L": p = (float(toks[i]), float(toks[i + 1])); i += 2; cur.append(p)
        elif cmd == "H": p = (float(toks[i]), p[1]); i += 1; cur.append(p)
        elif cmd == "V": p = (p[0], float(toks[i])); i += 1; cur.append(p)
        elif cmd == "C":
            c = [float(t) for t in toks[i:i + 6]]; i += 6
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p, c[0:2], c[2:4], c[4:6]
            for s in range(1, steps + 1):
                t = s / steps; u = 1 - t
                cur.append((u**3*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t**3*x3, u**3*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t**3*y3))
            p = (x3, y3)
    if cur: out.append(cur)
    return out

def logo_mask(size, height, x, y, ss=4):
    """Anti-aliased L-mask of the wordmark, `height` px tall with its top-left at (x, y)."""
    k = height * ss / 24
    m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    for d, _ in LOGO_PATHS:
        layer = Image.new("1", m.size, 0)
        for sp in subpaths(d):  # XOR of subpaths == even-odd fill (the loop's hole)
            one = Image.new("1", m.size, 0)
            ImageDraw.Draw(one).polygon([(x * ss + px * k, y * ss + py * k) for px, py in sp], fill=1)
            layer = ImageChops.logical_xor(layer, one)
        m = ImageChops.lighter(m, layer.convert("L"))
    return m.resize(size, Image.LANCZOS)

def anybody(size, wdth=90, wght=600):
    f = ImageFont.truetype(str(FONTS / "Anybody.ttf"), size)
    try:
        names = [a["name"].decode() if isinstance(a["name"], bytes) else str(a["name"]) for a in f.get_variation_axes()]
        f.set_variation_by_axes([wdth if "id" in n.lower() else wght for n in names])  # Width / Weight
    except Exception:
        pass
    return f


# --- social preview image (WhatsApp / LinkedIn / iMessage) ---------------------
W, H = 1200, 630
img = Image.new("RGB", (W, H), (5, 10, 43))
glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
g.ellipse((180, -330, 1020, 230), fill=(17, 55, 234))       # blue stage light from above
g.ellipse((860, 40, 1380, 420), fill=(0, 97, 246))          # side wash
g.ellipse((260, 500, 940, 880), fill=(2, 227, 222))         # cyan horizon glow
img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(110)).point(lambda v: int(v * .55)))
hz = Image.new("RGB", (W, 110)); ha = Image.new("L", (W, 110)); hd, had = ImageDraw.Draw(hz), ImageDraw.Draw(ha)
for yy in range(110):                                       # footer-style horizon band, fading in
    t = yy / 109
    hd.line([(0, yy), (W, yy)], fill=tuple(int(a + (b - a) * t ** 3) for a, b in zip((0, 97, 246), (80, 255, 251))))
    had.line([(0, yy), (W, yy)], fill=int(255 * t ** 2.4))
img.paste(hz, (0, H - 110), ha)
d = ImageDraw.Draw(img)
def ctext(s, y, font, fill):
    d.text(((W - d.textlength(s, font=font)) / 2, y), s, font=font, fill=fill)
ctext("For our partners", 120, anybody(34, 90, 700), (60, 255, 247))
lh = 112; lw = lh * 149 / 24; lx, ly = int((W - lw) / 2), 196
m = logo_mask((W, H), lh, lx, ly)
img.paste((2, 227, 222), mask=m.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * .45)))
img.paste((255, 255, 255), mask=m)
d = ImageDraw.Draw(img)
ctext("The Signal", 348, anybody(48, 83, 600), (255, 255, 255))
ctext("October 21 2026  ·  Wintercircus & De Vooruit, Ghent", 428, anybody(30, 90, 500), (255, 255, 255))
img.save(OUT / "og.png", optimize=True)

# --- QR codes (high error correction so a small logo/print damage still scans) ---
qr = segno.make(BASE, error="h")
qrdir = ROOT / "qr"; qrdir.mkdir(exist_ok=True)
qr.save(qrdir / "tectonic-signal-qr.svg", scale=10, border=4, dark="#050a2b", light="#ffffff")
qr.save(qrdir / "tectonic-signal-qr.png", scale=24, border=4, dark="#050a2b", light="#ffffff")
qr.save(qrdir / "tectonic-signal-qr-print.pdf", scale=10, border=4)
(qrdir / "URL.txt").write_text(BASE + "\n")
print("built", OUT, "->", BASE)
