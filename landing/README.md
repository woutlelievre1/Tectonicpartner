# TECTONIC 2026 — partner landing page ("The Signal")

The page partners land on when they scan the QR code on their thank-you card.

- `site/` — the published static site (index.html, the-signal.mp3, og.png, favicon.svg, fonts/). No trackers, cookies or third-party requests.
- `src/` — page template, caption timings and loudness envelope used by the visualiser.
  - `src/brand/` — official Tectonic wordmark and favicon orb (from tectonicconf.eu); the wordmark is inlined into the page and drawn into og.png.
  - `src/fonts/` — Anybody, the Tectonic typeface (SIL OFL 1.1, see OFL.txt): woff2 for the page, variable TTF for og.png.

## House style (mirrors tectonicconf.eu)
Anybody (headings 600 @ 100% width, body 90% width, italic @ 83% for emphasis) · page `#050A2B`, depth `#0D1341`/`#17216B`,
brand blue `#1137EA`, electric `#0061F6`, cyan `#02E3DE`/`#3CFFF7` · glass header pill, pill buttons with animated
conic-gradient border, glass "loop" outline, cyan horizon glow, word-by-word reveal (`.55s cubic-bezier(.22,1,.36,1)`).
- `qr/` — QR code (SVG for print, PNG, PDF) pointing to the public URL in `qr/URL.txt`.
- `build.py` — rebuilds `site/` and the QR codes: `python3 landing/build.py [PUBLIC_URL]`
  (needs `pillow` and `segno`). Run it again with a custom domain if you move the page.

## Hosting
Published on GitHub Pages by `.github/workflows/pages.yml`:
**https://woutlelievre1.github.io/Tectonicpartner/**

One-time setup: GitHub → repository **Settings → Pages → Build and deployment → Source: GitHub Actions**,
then re-run the "Publish partner landing page" workflow (Actions tab).

## Before printing the cards
1. Open the URL on a phone outside the company network (4G) and press play.
2. Scan `qr/tectonic-signal-qr.svg` from the printed proof.
3. Print the QR at least 2 × 2 cm with the white quiet zone intact.
