# TECTONIC 2026 — "The Signal" v2 · Production Report

| File | Format | Notes |
|---|---|---|
| `TECTONIC_THE_SIGNAL_MASTER.wav` | 24-bit PCM, 44.1 kHz, stereo | Lossless master |
| `TECTONIC_THE_SIGNAL_FINAL.mp3` | 320 kbps CBR | Used by the landing page / QR code |
| `TECTONIC_THE_SIGNAL_PREVIEW.mp3` | 128 kbps | For quick sharing (WhatsApp, e-mail) |

**Length:** 1:07.6. **Loudness:** −14.0 LUFS integrated, true peak −1.15 dBTP (MP3) / −1.2 dBTP (WAV). **Mono fold-down:** −1.2 LU.
The MP3s are pre-compensated for the encoder delay, so they are sample-aligned with the page's caption timings (measured offset 0.0 ms).

v2 replaces the v1 voice-over (British narrator, "Every great movement begins with a spark…") with the new
ElevenLabs read **"Ben — Vibrant and High-Energy"** (44 s, playful script: *"Hey, you! Found the QR code? … Volume up.
Warning. Your gift box will self-destruct in two minutes. Just kidding. … Let's make some noise!"*).
v1 is in the git history (`produce.py`); v2 is `production/produce_v2.py`.

## 1. Assets

| Asset | Use |
|---|---|
| ElevenLabs VO "Ben" (`ElevenLabs_2026-10-10T17_47_43_Ben…mp3`) | Foundation. −26.6 LUFS, every pause is digital silence (−90 dB), so pauses can be lengthened without seams. |
| Stereo Color — *Inspiring Cinematic Trailer* (Pixabay) | Music bed, same track as v1. Re-downloaded from Pixabay; verified sample-exact against the v1 edit (0.0 ms offset), so v1's calibrated bar grid (84 BPM, bar = 2.857 s) is reused. Not committed (licence), lives in `production/work/` (git-ignored). |
| v1 sound design | All synthesized in code and reused: signal pings, heartbeat, reverse swells, sub impact, data ticks, riser, frozen-chord pads. New: tape stop, countdown clock. |

Word timings: faster-whisper (small.en, offline) for the words, refined against the waveform (phrase onsets ±5 ms).

## 2. Voice-over: untouched words, four pauses added

No words were cut, changed or regenerated. Silence was inserted inside existing pauses only (2.6 s in total):

| Where | Added | Why |
|---|---|---|
| "Volume up." → "Warning." | 0.91 s | Lets the "Volume UP" drop actually play before the tape stop. |
| "…two minutes." → (laugh) "Just kidding." | 0.32 s | Keeps the countdown on the quarter-note grid so the music lands back on "Just". |
| "…something different." → "You've done the work." | 0.27 s | Puts the boom exactly on "ride". |
| "…enjoy the ride." → "Let's make some noise!" | 1.15 s | The reveal silence (boom → near-silence → drop). |

Processing as v1 (HPF 75 Hz, de-mud, presence +1 dB, air +0.5 dB, de-esser, 2.4:1 compression, peak control, short room),
+1.5 dB and a reverb throw on "Let's make some noise!", a throw on "Warning.".

## 3. Timeline

| Time | Moment | What happens |
|---|---|---|
| 0:00 | The Signal | Two "signal" pings (D6 → G6 answer), frozen G-minor pad, the track's intro pulse fades in, heavily filtered. |
| 0:02.9 | "Hey, you! Yes, you! Found the QR code? Nice!" | Intro bars 0–3 under the voice (low-pass 1.3 kHz). |
| 0:10.5 | "Take it out. Turn it on." | The filter opens one step per command (2 kHz → 3.2 kHz → 5 kHz). |
| **0:12.5** | **"Volume UP."** | Reverse swell + small sub hit; the track's **first drop (bar 9) lands exactly on "up"**, full-band and loud. |
| 0:13.6 | | **Tape stop**: the drop winds down to nothing in 0.42 s… |
| **0:14.1** | **"Warning."** | …and "Warning." stands in silence with a reverb throw. |
| 0:14.7–19.6 | "…self-destruct in two minutes." | Countdown: dark frozen drone, clock ticks on every quarter note, heartbeat thumps; all rising slowly. |
| **0:19.7** | (laugh) **"Just kidding."** | The pulse is back (bar 7) on "Just", with playful 8th-note ticks. |
| 0:22.5 | "Look, we know you've put a lot of time, energy…" | Breakdown (bars 25–28) starts between "Look," and "we know"; bar hits land on "energy, \| and" and on "tecto**nic**". |
| 0:28.7 | "And for that, a massive thank you. Seriously. We couldn't do this without you." | Warm frozen chord swells underneath. |
| **0:34.0** | **"But October 21st?"** | Bar 29 lands on "But": the build starts. 8th-note ticks; bar hits on "Forget the **Power**Points" and "Bring your **peo**ple". |
| 0:39.7 | "Bring your energy… something different. You've done the work." | Ticks double to 16ths, band-swept noise riser over two bars. |
| **0:45.4** | "Now it's time to enjoy the **ride**." | **Boom** (bar 33) exactly on "ride"; the music then falls to near-silence (−49 dB); one signal ping. |
| 0:47.4 | "Let's make some…" | Reverse swell rises into… |
| **0:47.95** | **"…NOISE!"** | **Final drop** (bar 34) + designed sub impact, 20 ms before "noise". The page reveals the Tectonic logo here. |
| 0:48–0:59 | Climax | Two bars of the drop, then the track's last climax bars (48–49). |
| 0:59–1:07.6 | Resolution | The track's natural ending; frozen final chord, last signal ping. |

## 4. Measurements (I cannot listen in this environment — please check by ear)

- **Voice vs music in the speech band (1–4 kHz), per phrase:** median 17 dB. Tightest by design: "Volume up." 7.1 dB (on the drop) and "Probably." 8.1 dB. Everything else ≥ 10 dB.
- **Music bed level (stem, RMS):** intro −26 dB, drop on "up" −14 dB, countdown −31 dB, breakdown −26 dB, build −24 dB, reveal silence −49 dB, final drop −14 dB.
- **Limiter:** max 1.4 dB gain reduction, active (> 0.5 dB) for 0.26 s in total (only on the impacts).
- Edits only on bar lines (34 ms equal-power crossfade) or inside silence (300 ms); see `production/timeline_v2.png`.

Listen especially to: the tape stop before "Warning.", the level of the countdown clock, and whether the 1.5 s silence before "Let's make some noise!" feels right.

## 5. Reproducing

```
python3 production/produce_v2.py production/work
```
`production/work/` must contain `vo.wav` (the ElevenLabs file) and `stereo.wav` (the Pixabay track), 44.1 kHz.
Dependencies: numpy, scipy, soundfile, pyloudnorm (MP3 encoding: lameenc). The script also writes
`work/timeline_v2.json` with the page's captions, story moments and loudness envelope
(copied to `landing/src/captions.json`, `landing/src/envelope.txt` and the `T` table in `landing/src/index.html`).

**Licence:** check that the Pixabay Content License covers the intended use (a promotional gift for partners). The source track is not redistributed in this repository.
