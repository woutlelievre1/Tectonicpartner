# TECTONIC 2026 — partner landing page ("The Signal")

The page partners land on when they scan the QR code on their thank-you card.

- `site/` — the published static site (index.html, the-signal.mp3, og.png). No trackers, cookies or third-party requests.
- `src/` — page template, caption timings and loudness envelope used by the visualiser.
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
