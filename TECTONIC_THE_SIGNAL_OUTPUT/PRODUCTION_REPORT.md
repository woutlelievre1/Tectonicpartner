# TECTONIC 2026 — "The Signal" · Production Report

| File | Format | Notes |
|---|---|---|
| `TECTONIC_THE_SIGNAL_MASTER.wav` | 24-bit PCM, 44.1 kHz, stereo | Lossless master |
| `TECTONIC_THE_SIGNAL_FINAL.mp3` | 320 kbps CBR | For the QR code / hosting |
| `TECTONIC_THE_SIGNAL_PREVIEW.mp3` | 128 kbps | For quick sharing (WhatsApp, e-mail) |

**Length:** 1:13. **Loudness:** −14.0 LUFS integrated, true peak −1.1 dBTP (MP3) and −1.2 dBFS (WAV), loudness range 8.8 LU. **Mono fold-down:** −0.9 LU, so it holds up on single-driver JBL speakers.

---

## 1. Analysis of the supplied assets

| Asset | Duration | Tempo / key | Character | Verdict |
|---|---|---|---|---|
| ElevenLabs VO (British) | 46.4 s | — | Clean, digital-silence pauses, −19 LUFS, quite fast delivery | Foundation |
| **Stereo Color — Inspiring Cinematic Trailer** | 2:28 | **84 BPM 4/4**, G minor / B♭ major | A real trailer architecture: pulsing intro → break-boom → full section → breakdown → **boom + 2 s silence → final drop** → ending | **Selected** |
| The Mountain — Cinematic Epic | 1:50 | ~112 BPM, B♭ minor / D♭ | Beautiful, but dynamically flat (−23 to −18 dB). Three similar swells with almost no contrast | Not used |
| Vaitsez — Futuristic Digital Music | 2:21 | ~96 BPM, B♭ major | Dense, constantly loud (−10 LUFS) four-on-the-floor electro. Hardly any space for a voice | Not used |

**Why Stereo Color?** It's the only track whose own dramaturgy matches the script. Above all, at 1:35 it has a *boom → near-silence → drop* sequence, which is exactly the "Welcome… to TECTONIC" moment.

**Why no combination?** I seriously considered layering in the other two tracks.
- *The Mountain* is in B♭ minor / D♭. Against the G minor of the chosen track, D♭ and G♭ clash with D and G.
- *Futuristic Digital* is harmonically compatible (B♭ major), but at 96 vs 84 BPM it has a rhythm that's wholly its own. It would need about 14% of time-stretching, and it has no quiet passages to borrow from.

Both would therefore have added noise rather than value. I created the futuristic layer myself (see §3), tuned to the chosen track's key and bar grid.

**Structure of the chosen track** (determined with onset detection and harmonic analysis per bar): bar = 2.857 s. There's a 4-bar chord cycle **Gm – B♭ – F – E♭/C**. Impacts land on every bar line. The intro bars (0–7) are harmonically identical to the breakdown bars (25–32), so bar-accurate jumps are seamless.

## 2. Voice-over: preserved, given more breathing room

The script hasn't been touched. **No words were cut, changed or regenerated.** The only intervention is that a total of **8.1 s of silence** was inserted *inside existing pauses* (which were digital silence, so there are no edit seams). The original delivery was very fast. The extra space makes it cinematic, and it lets every key phrase land exactly on the music's bar grid.

Processing: high-pass 75 Hz, −1.5 dB at 280 Hz (de-mud), +1.5 dB at 3.6 kHz (presence on small speakers), +1 dB air at 11 kHz, mild split-band de-esser, 2.2:1 compression, transparent peak control, a subtle short room (0.7 s, −21 dB). There's one cinematic reverb "throw" (2.6 s) on **"TECTONIC"** and on the final word **"next"**. On "TECTONIC" the voice is +2 dB.

## 3. Timeline — the four acts

| Time | Moment | What happens |
|---|---|---|
| **0:00** | **ACT I — The Awakening** | A "frozen" version of the soundtrack's own G-minor chord (spectral freeze) fades in from nothing, with a deep 49 Hz heartbeat on the bar grid (getting louder) and two soft **"signal" pings** (D6, dotted-eighth stereo echoes in a hall). That's the motif of the title *The Signal*. |
| 0:04.5 | "Every great movement…" | The narrator starts calmly. The music sits heavily low-pass filtered (330→520 Hz): distant, mysterious. |
| **0:07.1** | "…begins with a **spark**." | The soundtrack's first impact lands exactly on *spark*, as the ignition. |
| 0:07–0:15 | "An idea. A belief…" | Minimal: the trailer intro sounds only as a muffled, deep pulse. Just before "People do" the music dips slightly. |
| **0:15.7** | **ACT II — "People do."** | Subtle emphasis: a soft reverse swell leads into the word, a new harmonic cycle (Gm) starts exactly on *People*, and the filter opens up (560 Hz → 2.3 kHz in 0.35 s). Warmth arrives, and the music keeps opening across the following phrases. |
| **0:27.1** | "…before the world did." | The break-boom lands right after *did*. The music then "holds its breath". |
| **0:27.9** | **"You are one of them."** | The emotional moment. The orchestra falls away and, under the voice, a warm frozen chord swells (the same Gm that follows). It's intimate and personal, with no bombast. I lengthened the silence in the break bar by 0.35 s to let the line breathe. |
| **0:30.3** | **ACT III — "This October…"** | The first drop of the track enters on *This*, still filtered (3.8 kHz) and at a modest level. The filter opens fully within a bar. Rhythmic "data" ticks on the 16th grid (8.5–14 kHz, above the sibilance range) grow quietly beneath "bold minds… a future waiting to be built". |
| **0:38.9** | "To our partners: thank you…" | Deliberate pull-back into the breakdown, warmer (6.5 kHz). The gratitude gets room and sincerity. |
| **0:44.6** | **ACT IV — "The future is calling."** | The final build starts on a bar line: the music rises 5 dB in a controlled way, a band-swept noise riser (300 Hz → 7.5 kHz) builds over two bars, and the ticks double from 8ths to 16ths. |
| 0:46–0:50 | "October twenty-first. Wintercircus. Ghent." | The date and location are spaced slightly apart, with the rise continuing between them. |
| **0:50.3** | "**Ghent.**" | The trailer's big boom lands on *Ghent*. |
| 0:51–0:53 | Tension | The music sinks to near-silence (−50 dB). A single "signal" ping echoes through the empty space. **"Welcome…" sounds practically alone.** |
| 0:53.0 | "…to" | The soundtrack's own swell plus a reverse swell rise up. |
| **0:53.54** | **"TECTONIC."** | **Impact.** The final drop of the soundtrack (edited bar-accurately) lands 20 ms before the "T". Layered with it: a designed sub-drop (88→46 Hz, with upper harmonics so it carries on a JBL), a transient and an air tail. The voice gets a reverb throw. Then 2 s in which the climax simply breathes. |
| **0:56.5** | "Together, we shape what's next." | The music ducks deeper (−9.5 dB) so the closing line stands clear. |
| 0:59–1:05 | Climax | The last two bars of the full section (F – C), the musical highlight with no voice. |
| **1:05–1:13** | Resolution | The track's natural ending on Gm. From it, a frozen version of that final chord blooms open and fades out. A last "signal" ping echoes away. |

## 4. How the reveal was built

1. **The track's own structure as the backbone.** The soundtrack's sequence of *boom → silence → drop* (bars 33–34) was placed so that the boom lands on "Ghent" and the drop on "TECTONIC".
2. **Elastic silence.** The gap between those two moments is fixed in the music (2.86 s) but needed 3.21 s in the voice-over. I lengthened the silence inside the break bar by 0.35 s via a 300 ms crossfade in a part that was already silent, so the grid, swell and drop all stay intact.
3. **Gain automation on top.** After the boom the music drops a further 12 dB, so "Welcome…" stands in real near-silence (measured at −51 LUFS for the music).
4. **Layers on the impact.** I placed a reverse swell that ends exactly on "TEC" and a designed sub-impact on top. The impact's air tail is high-passed above 4.5 kHz so the 300 Hz–4 kHz range stays free for the narrator.
5. **Intelligibility check.** In the speech band (1–4 kHz) the voice sits **12.3 dB** above the music on "TECTONIC", despite the impact.

## 5. Mixing and mastering

- **Music edit:** 7 segments, cut only on bar lines (34 ms equal-power crossfade just before the hit) or inside silence (300 ms). Each join was checked for doubled transients, and none were found.
- **Automation:** a time-varying low-pass filter (a bank of 10 zero-phase filters with interpolated cross-mix, so no phase smear), gain automation per act, sidechain ducking on the voice envelope (4–9.5 dB depending on the act), plus an extra dynamic −3 to −7 dB in the 0.9–4.2 kHz band while the narrator speaks.
- **Measured voice-vs-music balance (speech band 1–4 kHz):** at least 6.7 dB everywhere. The tightest spot is "…to", on top of the swell just before the impact; elsewhere it is 8.6–21 dB.
- **Master:** high-pass 31 Hz, −1.8 dB low shelf at 52 Hz (so a JBL doesn't pump; headphones keep their weight), gentle bus compression of 1.6:1, a 4× oversampled lookahead limiter (max 2.4 dB, only on the impact, 0.5 s in total), −14 LUFS.

## 6. Limitations and honest notes

- **I could not listen to the audio myself.** There's no audio playback in this production environment. All decisions were taken and checked by measurement: word-level timing (local speech recognition plus envelope analysis), beat/bar and chord analysis, spectrograms, loudness per phrase, speech-band SNR, transient detection at every edit, limiter activity, mono compatibility and true peak. **Please listen critically on both headphones and the JBL**, especially to:
  - the level of the frozen pads (intro and "You are one of them")
  - the "signal" pings
  - whether the 2-second pause after "TECTONIC" feels right
- **Inserted pauses:** the pacing of the voice-over is slower than the original ElevenLabs file (+8.1 s in pauses; the words themselves are unchanged). If you'd prefer to keep the original pauses, that's possible, but the sync with the music then partly falls away.
- **Not used:** *The Mountain* and *Futuristic Digital Music*, because of key and tempo incompatibility (see §1).
- **Sound effects:** all synthesized in code (pulse, pings, risers, sub-impact, ticks) or derived from the chosen, licensed soundtrack (frozen chords). No external samples, no paid services.
- **Licence:** check that the Pixabay licence covers the intended use (a promotional gift for partners). Pixabay generally allows commercial use without attribution, but the source tracks may not be redistributed separately. That's why they're **not** included in this repository.

## 7. Reproducing

`production/produce.py` contains the complete, deterministic production (fixed random seed). Decode the voice-over to `vo.wav` and the chosen track to `stereo.wav` (44.1 kHz stereo, via ffmpeg) in a single folder, then run:

```
python3 produce.py <folder>
```

Dependencies: numpy, scipy, soundfile, pyloudnorm. `analyze.py` reproduces the measurements. `asr.py` produced the word timing (sherpa-onnx, offline).
