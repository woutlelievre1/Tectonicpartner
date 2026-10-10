"""Build the static partner landing page into landing/site/.

usage: python3 landing/build.py [BASE_URL]
BASE_URL is the public address the QR code points to (default: GitHub Pages).
"""
import json, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import segno

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "site"
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://woutlelievre1.github.io/Tectonicpartner/").rstrip("/") + "/"
AUDIO = ROOT.parent / "TECTONIC_THE_SIGNAL_OUTPUT" / "TECTONIC_THE_SIGNAL_FINAL.mp3"

OUT.mkdir(exist_ok=True)
html = (SRC / "index.html").read_text(encoding="utf-8")
html = html.replace("__CAPS__", json.dumps(json.loads((SRC / "captions.json").read_text(encoding="utf-8")), ensure_ascii=False))
html = html.replace("__ENV__", (SRC / "envelope.txt").read_text().strip()).replace("__BASE_URL__", BASE)
(OUT / "index.html").write_text(html, encoding="utf-8")
shutil.copyfile(AUDIO, OUT / "the-signal.mp3")
(OUT / ".nojekyll").write_text("")

# --- social preview image (WhatsApp / LinkedIn / iMessage) ---------------------
W, H = 1200, 630
img = Image.new("RGB", (W, H), (7, 7, 10)); d = ImageDraw.Draw(img)
glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
g.ellipse((250, 330, 950, 760), fill=(120, 38, 10))
img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(120)), 0.55); d = ImageDraw.Draw(img)
bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; mono = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
F = ImageFont.truetype(bold, 150); f2 = ImageFont.truetype(mono, 26); f3 = ImageFont.truetype(bold, 34)
txt = "TECTONIC"; w = d.textlength(txt, font=F); x0, y0 = (W - w) / 2, 205
top = Image.new("L", (W, H), 0); ImageDraw.Draw(top).text((x0 - 10, y0), txt, font=F, fill=255)
bot = Image.new("L", (W, H), 0); ImageDraw.Draw(bot).text((x0 + 10, y0), txt, font=F, fill=255)
split = Image.new("L", (W, H), 0); ImageDraw.Draw(split).polygon([(0, 0), (W, 0), (W, y0 + 86), (0, y0 + 104)], fill=255)
img.paste((244, 241, 234), mask=Image.composite(top, Image.new("L", (W, H), 0), split))
img.paste((255, 90, 31), mask=Image.composite(Image.new("L", (W, H), 0), bot, split))
def ctext(s, y, font, fill):
    d.text(((W - d.textlength(s, font=font)) / 2, y), s, font=font, fill=fill)
ctext("AN EXCLUSIVE SIGNAL FOR OUR PARTNERS", 140, f2, (255, 90, 31))
ctext("21.10.2026  ·  WINTERCIRCUS  ·  GHENT", 420, f3, (244, 241, 234))
ctext("PRESS PLAY", 492, f2, (141, 138, 133))
pts = [(80, 580), (360, 580), (400, 552), (440, 606), (480, 566), (520, 590), (560, 580), (1120, 580)]
d.line(pts, fill=(255, 90, 31), width=4, joint="curve")
img.save(OUT / "og.png", optimize=True)

# --- QR codes (high error correction so a small logo/print damage still scans) ---
qr = segno.make(BASE, error="h")
qrdir = ROOT / "qr"; qrdir.mkdir(exist_ok=True)
qr.save(qrdir / "tectonic-signal-qr.svg", scale=10, border=4, dark="#07070a", light="#ffffff")
qr.save(qrdir / "tectonic-signal-qr.png", scale=24, border=4, dark="#07070a", light="#ffffff")
qr.save(qrdir / "tectonic-signal-qr-print.pdf", scale=10, border=4)
(qrdir / "URL.txt").write_text(BASE + "\n")
print("built", OUT, "->", BASE)
