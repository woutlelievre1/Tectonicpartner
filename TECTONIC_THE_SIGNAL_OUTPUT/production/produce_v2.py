"""TECTONIC 2026 - "The Signal" v2 - high-energy partner audio (VO: ElevenLabs "Ben").

Same toolkit as produce.py (v1): VO edit (pause insertion only) -> VO processing ->
bar-accurate edit of Stereo Color "Inspiring Cinematic Trailer" -> filter/gain/duck
automation -> synthesized sound design -> mix -> master. Also writes the timed
captions + loudness envelope for the landing page.

usage: python3 produce_v2.py <workdir>     (workdir holds vo.wav + stereo.wav, 44.1 kHz)
"""
import json, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, sosfilt, fftconvolve, resample_poly
from scipy.ndimage import minimum_filter1d
import pyloudnorm as pyln

SR = 44100
W = sys.argv[1] if len(sys.argv) > 1 else "work"
rng = np.random.default_rng(2026)
db = lambda d: 10 ** (d / 20)

# ----------------------------------------------------------------------------
# helpers (identical to v1)
# ----------------------------------------------------------------------------
def sos(kind, f, order=2):
    return butter(order, f, kind, fs=SR, output="sos")
def lp(x, f, o=2):  return sosfiltfilt(sos("lowpass", f, o), x, axis=0)
def hp(x, f, o=2):  return sosfiltfilt(sos("highpass", f, o), x, axis=0)
def bp(x, a, b, o=2): return sosfiltfilt(sos("bandpass", [a, b], o), x, axis=0)

def peq(x, f0, gain_db, q=1.0):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A]); a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return sosfilt(np.hstack([b / a[0], a / a[0]])[None, :], x, axis=0)

def shelf(x, f0, gain_db, high=True):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / 2 * np.sqrt(2)
    c = np.cos(w); s = 2 * np.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * c + s), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - s)]
        a = [(A + 1) - (A - 1) * c + s, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - s]
    else:
        b = [A * ((A + 1) - (A - 1) * c + s), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - s)]
        a = [(A + 1) + (A - 1) * c + s, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - s]
    b = np.array(b) / a[0]; a = np.array(a) / a[0]
    return sosfilt(np.hstack([b, a])[None, :], x, axis=0)

def env_follow(level, att, rel, rate):
    aa = np.exp(-1 / (att * rate)); ar = np.exp(-1 / (rel * rate)); out = np.empty_like(level); g = level[0]
    for i, v in enumerate(level):
        g = aa * g + (1 - aa) * v if v > g else ar * g + (1 - ar) * v
        out[i] = g
    return out

def ctrl_to_audio(c, rate, n):
    return np.interp(np.arange(n) / SR, np.arange(len(c)) / rate, c)

def compress(x, thr_db, ratio, att=0.008, rel=0.15, knee=6.0, rate=1000):
    mono = x if x.ndim == 1 else x.mean(1)
    hop = SR // rate; n = len(mono) // hop + 1
    pad = np.pad(mono, (0, n * hop - len(mono)))
    lvl = 10 * np.log10((pad.reshape(n, hop) ** 2).mean(1) + 1e-12)
    over = lvl - thr_db
    gr = np.where(over <= -knee / 2, 0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                  (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    gr = env_follow(gr, att, rel, rate)
    g = db(-ctrl_to_audio(gr, rate, len(mono)))
    return x * (g if x.ndim == 1 else g[:, None]), gr

def place(buf, sig, t, gain=1.0):
    i = int(round(t * SR))
    if sig.ndim == 1 and buf.ndim == 2: sig = np.stack([sig, sig], 1)
    j0 = max(0, i); j1 = min(len(buf), i + len(sig))
    if j1 > j0: buf[j0:j1] += sig[j0 - i:j1 - i] * gain

def pan(sig, p):
    a = (p + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], 1)

def curve(points, n):
    t = np.arange(n) / SR; ts, vs = zip(*points)
    return np.interp(t, ts, vs)

def paulstretch(x, stretch, win_s=0.35):
    win = int(win_s * SR) // 2 * 2; h = win // 2
    w = np.hanning(win)
    hop_in = h / stretch; out = np.zeros(int(len(x) * stretch) + win); pos = 0.0; k = 0
    while int(pos) + win < len(x):
        seg = x[int(pos):int(pos) + win] * w
        F = np.abs(np.fft.rfft(seg)); ph = rng.uniform(0, 2 * np.pi, len(F))
        out[k * h:k * h + win] += np.fft.irfft(F * np.exp(1j * ph)) * w
        pos += hop_in; k += 1
    return out[:k * h + win]

def stereo_stretch(x, k, lo, hi):
    a, b = (bp(paulstretch(x, k), lo, hi, 2) for _ in range(2)); n = min(len(a), len(b))
    return np.stack([a[:n], b[:n]], 1)

def make_ir(rt60, length, pre=0.02, hf_rt=None, stereo=True, seed=1):
    r = np.random.default_rng(seed); n = int(length * SR); t = np.arange(n) / SR
    hf_rt = hf_rt or rt60 * 0.45
    chans = []
    for c in range(2 if stereo else 1):
        nz = r.standard_normal(n)
        lo = lp(nz, 3000) * np.exp(-6.9 * t / rt60); hi = hp(nz, 3000) * np.exp(-6.9 * t / hf_rt)
        ir = lo + hi; ir[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
        chans.append(np.concatenate([np.zeros(int(pre * SR)), ir]))
    ir = np.stack(chans, 1); return ir / np.sqrt((ir ** 2).sum(0).mean())

def reverb(x, ir):
    if x.ndim == 1: return np.stack([fftconvolve(x, ir[:, c]) for c in range(ir.shape[1])], 1)
    return np.stack([fftconvolve(x[:, c], ir[:, c]) for c in range(ir.shape[1])], 1)

def fit(x, n):
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:])])

# ----------------------------------------------------------------------------
# 1. VOICE-OVER: word onsets (ASR + waveform refinement) and pause insertion
# ----------------------------------------------------------------------------
vo, sr = sf.read(f"{W}/vo.wav"); vo = vo.mean(1) if vo.ndim == 2 else vo
assert sr == SR

V = dict(hey=0.05, take=7.60, turn=8.40, volume=9.23, up=9.645, up_end=9.90, warning=10.31, minutes_end=14.0,
         laugh=14.94, just=15.60, look=17.99, but=29.85, ride=41.015, ride_end=41.52, lets=41.835, noise=42.43, end=43.23)
# phrase captions in original VO time (phrase onsets/ends from the waveform, gaps are digital silence)
PHRASES = [(0.05, 0.97, "Hey, you!"), (1.235, 2.21, "Yes, you!"), (2.575, 3.53, "Found the QR code?"), (3.805, 4.49, "Nice!"),
           (4.835, 7.26, "Now, see that JBL speaker in your box?"), (7.60, 8.05, "Take it out."), (8.40, 8.88, "Turn it on."),
           (9.23, 9.90, "Volume up."), (10.31, 10.85, "Warning."), (11.145, 14.0, "Your gift box will self-destruct in two minutes."),
           (15.55, 16.35, "Just kidding."), (16.84, 17.56, "Probably."),
           (17.99, 21.25, "Look, we know you’ve put a lot of time, energy,"), (21.52, 24.22, "and let’s be real, money into Tectonic."),
           (24.565, 26.82, "And for that, a massive thank you."), (27.08, 27.81, "Seriously."), (28.095, 29.50, "We couldn’t do this without you."),
           (29.85, 31.10, "But October 21st?"), (31.35, 32.20, "Forget the meetings."), (32.46, 33.81, "Forget the PowerPoints."),
           (34.075, 34.85, "Bring your energy."), (35.215, 36.06, "Bring your people."), (36.27, 38.05, "And get ready for something different."),
           (38.365, 39.27, "You’ve done the work."), (39.51, 41.52, "Now it’s time to enjoy the ride."), (41.835, 43.23, "Let’s make some noise!")]

BAR = 2.85739; B = lambda k: 1.4804 + BAR * k        # bar grid of the source track (verified sample-exact vs v1)
VO_OFF = 2.90                                        # signal pings + intro pickup before "Hey, you!"
INS_RIDE = 1.15                                      # dramatic near-silence between "ride." and "Let's make some noise!"
# Pause inserts (gap centre, seconds). Warning/ride-pauses are solved below so the bar grid lands on the words.
GAP_UP, GAP_MIN, GAP_YOUVE, GAP_RIDE = 10.13, 14.30, 38.21, 41.68
# Constraints (output time):
#   bar 29 = "But"     bar 33 = "ride"     bar 25 = bar 29 - 4 bars,  bar 7 = bar 25 - 1 bar (lands on "Just")
#   bar 9 ("Volume UP" drop) = bar 7 - 2.5 bars (the warning silence keeps the quarter-note grid)
#   bar 0 = bar 9 hit - 4 bars (intro bars 0-3 run straight into the drop)
ins_youve = (4 * BAR) - (V["ride"] - V["but"])                    # stretch But..ride to exactly 4 bars
ins_warn = 2.5 * BAR - ((V["but"] - 5 * BAR) - V["up"])            # up .. bar7 must be 2.5 bars
assert ins_youve >= 0 and ins_warn >= 0
inserts = sorted([(GAP_UP, ins_warn * 0.74), (GAP_MIN, ins_warn * 0.26), (GAP_YOUVE, ins_youve), (GAP_RIDE, INS_RIDE)])
pieces, last = [], 0
for c, d in inserts:
    i = int(c * SR); pieces += [vo[last:i], np.zeros(int(round(d * SR)))]; last = i
pieces.append(vo[last:])
vo_ed = np.concatenate(pieces)
def ed(t):  # original VO time -> output time
    return t + sum(d for c, d in inserts if c < t) + VO_OFF

out = {}
out[29] = ed(V["but"]); out[33] = ed(V["ride"]); out[25] = out[29] - 4 * BAR; out[7] = out[25] - BAR
out[9] = out[7] - 2.5 * BAR; out[0] = out[9] - 4 * BAR
E33 = (ed(V["noise"]) - 0.02) - (out[33] + BAR)                       # elastic silence in the break bar (may be < 0)
out[34] = out[33] + BAR + E33; out[35] = out[34] + BAR; out[48] = out[35] + BAR; out[50] = out[48] + 2 * BAR
print("inserts:", [(c, round(d, 3)) for c, d in inserts], " E33 = %.3f" % E33)
for k, w in [(0, None), (9, "up"), (7, "just"), (25, "look"), (29, "but"), (33, "ride"), (34, "noise")]:
    print(f"  bar {k:2d} at {out[k]:7.3f}" + (f"   word '{w}' at {ed(V[w]):7.3f}" if w else ""))
assert abs(out[9] - ed(V["up"])) < 1e-6 and out[0] > 0.5 and E33 > -0.45

# ----------------------------------------------------------------------------
# 2. VOICE PROCESSING (as v1; the new read is brighter, so a touch less presence)
# ----------------------------------------------------------------------------
v = hp(vo_ed, 75, 2)
v = peq(v, 280, -1.5, 0.9)
v = peq(v, 3600, +1.0, 0.8)
v = shelf(v, 11000, +0.5, True)
sib = bp(v, 5500, 9500, 2); hop = 44
n = len(sib) // hop; lev = 10 * np.log10((np.pad(sib, (0, (n + 1) * hop - len(sib))).reshape(n + 1, hop) ** 2).mean(1) + 1e-12)
full = 10 * np.log10((np.pad(v, (0, (n + 1) * hop - len(v))).reshape(n + 1, hop) ** 2).mean(1) + 1e-12)
red = env_follow(np.clip((lev - full + 6) * 0.8, 0, 6), 0.002, 0.06, SR / hop)
v = v - sib * (1 - db(-ctrl_to_audio(red, SR / hop, len(v))))
v, _ = compress(v, -26, 2.4, att=0.008, rel=0.16, knee=8)
v = v / np.sqrt(np.mean(v[np.abs(v) > 1e-4] ** 2)) * db(-20.5)
_need = np.minimum(1.0, db(-10.0) / np.maximum(np.abs(v), 1e-9))
_g = minimum_filter1d(_need, int(0.003 * SR) * 2 + 1)
_g = np.convolve(_g, np.hanning(int(0.006 * SR)) / np.hanning(int(0.006 * SR)).sum(), mode="same")
v = v * np.minimum(_g, 1.0)

# ----------------------------------------------------------------------------
# 3. MUSIC EDIT  (Stereo Color - Inspiring Cinematic Trailer)
# ----------------------------------------------------------------------------
mus, _ = sf.read(f"{W}/stereo.wav")
N = int((out[50] + 8.2) * SR)
M = np.zeros((N, 2))
XF_BAR, XF_SIL, PRE = 0.034, 0.30, 0.006
SIL33 = B(33) + 1.25
T_STOP = ed(V["warning"]) - 0.06                      # tape stop finishes just before "Warning."
D_STOP = 0.42
segs = [  # (src_start, src_end, src_anchor, out_anchor, join_with_previous)
    (0.00,  B(4),                     B(0),  out[0],  None),    # intro pulse: "Hey, you!" .. "Turn it on."
    (B(9),  B(9) + (T_STOP - out[9]) + 0.05, B(9), out[9], "bar"),  # first drop on "Volume UP" (then tape stop)
    (B(7),  B(8),                     B(7),  out[7],  "in"),    # "Just kidding." - the pulse is back
    (B(25), SIL33 + E33 + XF_SIL,     B(25), out[25], "bar"),   # breakdown -> build -> boom on "ride"
    (SIL33, B(36),                    B(34), out[34], "sil"),   # final drop on "NOISE!"
    (B(48), len(mus) / SR,            B(48), out[48], "bar"),   # last climax bars + natural ending
]
for i, (s0, s1, sa, oa, join) in enumerate(segs):
    early = XF_BAR if join in ("bar", "in") else 0.0
    s0e = s0 - early
    x = mus[int(round(s0e * SR)):int(round(s1 * SR))].copy()
    if join:
        L = int((XF_SIL if join == "sil" else XF_BAR) * SR); x[:L] *= np.sin(np.linspace(0, np.pi / 2, L))[:, None]
    nxt = segs[i + 1][4] if i + 1 < len(segs) else None
    if nxt == "bar":
        x = x[:len(x) - int(PRE * SR)]; L = int(XF_BAR * SR)
    elif nxt == "sil":
        L = int(XF_SIL * SR)
    else:
        L = int(0.03 * SR)
    x[-L:] *= np.cos(np.linspace(0, np.pi / 2, L))[:, None]
    place(M, x, oa + (s0e - sa))
M[:int(0.35 * SR)] *= np.sin(np.linspace(0, np.pi / 2, int(0.35 * SR)))[:, None]   # soft start inside the pickup
pe = segs[3][3] + (segs[3][1] - segs[3][2]); ps = segs[4][3] + (segs[4][0] - segs[4][2])
assert abs((pe - ps) - XF_SIL) < 1e-6, pe - ps

# ---- automation (low-pass cutoff + gain) on the edited timeline ------------------
o = out
lpf_pts = [(0, 700), (o[0], 1300), (ed(V["take"]) - 0.02, 1300), (ed(V["take"]), 2000), (ed(V["turn"]) - 0.02, 2000), (ed(V["turn"]), 3200),
           (ed(V["volume"]), 5000), (o[9] - 0.01, 5000), (o[9], 20000), (T_STOP, 20000),
           (o[7] - 0.01, 3500), (o[7], 3500), (o[7] + BAR * 0.7, 9000), (o[25] - 0.01, 9000), (o[25], 12000), (N / SR, 20000)]
gain_pts = [(0, -9), (o[0], -5.5), (ed(V["take"]), -5.0), (ed(V["turn"]), -4.0), (o[9] - 0.01, -3.5), (o[9], -0.5),
            (T_STOP, -1.0), (o[7], -4.0), (o[25] - 0.1, -4.0), (o[25], -3.5), (o[29], -3.5), (o[29] + 2 * BAR, -2.5),
            (o[33] - 0.05, -1.0), (o[33] + 0.85, -1.0), (o[33] + 1.45, -14.0), (o[34] - 0.66, -14.0), (o[34] - 0.06, -6.0),
            (o[34] - 0.004, -0.5), (o[35], -1.0), (o[48], -1.5), (N / SR, -1.5)]
cut = curve(lpf_pts, N); gdb = curve(gain_pts, N)
bank_f = [600, 900, 1500, 2400, 4200, 6500, 9000, 14000]
bank = [lp(M, f, 2) for f in bank_f] + [M]
lf = np.log(np.clip(cut, bank_f[0], 20000)); grid = np.log(np.array(bank_f + [20000.0]))
idx = np.clip(np.searchsorted(grid, lf) - 1, 0, len(grid) - 2); fr = (lf - grid[idx]) / (grid[idx + 1] - grid[idx])
Mf = np.zeros_like(M)
for k in range(len(grid) - 1):
    m = idx == k
    Mf[m] = bank[k][m] * (1 - fr[m, None]) + bank[k + 1][m] * fr[m, None]
del bank
Mf *= db(gdb)[:, None]

# ---- tape stop: the "Volume UP" drop winds down before "Warning." ----------------
i0, i1 = int((T_STOP - D_STOP) * SR), int(T_STOP * SR)
rate = np.linspace(1, 0, i1 - i0) ** 1.6                  # playback speed 1 -> 0
pos = i0 + np.cumsum(rate)
for c in range(2):
    Mf[i0:i1, c] = np.interp(pos, np.arange(len(Mf)), Mf[:, c]) * np.linspace(1, 0.2, i1 - i0)
Mf[i1:int((o[7] - XF_BAR - 0.01) * SR)] = 0

# ---- VO in the output timeline + sidechain ducking -----------------------------
VOX = np.zeros(N); place(VOX, v, VO_OFF)
VOX *= db(curve([(0, 0), (ed(V["lets"]) - 0.03, 0), (ed(V["lets"]), 1.5), (ed(V["end"]), 1.5), (ed(V["end"]) + 0.05, 0), (N / SR, 0)], N))
rate_c = 1000; hop = SR // rate_c; n = N // hop
lvl = 10 * np.log10((VOX[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
act = env_follow(np.clip((lvl + 52) / 16, 0, 1), 0.025, 0.35, rate_c)
depth = curve([(0, 5), (o[9], 5.5), (o[7], 6.5), (o[25], 7.0), (o[29], 7.5), (o[33], 4.5), (o[34] - 0.8, 7), (o[34], 8.5), (N / SR, 8.5)], N)
actA = ctrl_to_audio(act, rate_c, N)
duck = db(-depth * actA)
mid = bp(Mf, 900, 4200, 2)
carve = curve([(0, 3.0), (o[34] - 0.05, 3.0), (o[34], 7.0), (N / SR, 7.0)], N)
Mf = Mf - mid * (1 - db(-carve * actA))[:, None]
Mf *= duck[:, None]

# ----------------------------------------------------------------------------
# 4. SOUND DESIGN (v1 effects, re-placed for the new script)
# ----------------------------------------------------------------------------
FX = np.zeros((N, 2))
t_ = lambda d: np.arange(int(d * SR)) / SR
ir_hall = make_ir(3.2, 4.0, pre=0.035, seed=3)

def ping(f=1174.66, dur=0.9):
    t = t_(dur); e = np.exp(-t / 0.16) * (1 - np.exp(-t / 0.002))
    return (np.sin(2 * np.pi * f * t) + db(-14) * np.sin(2 * np.pi * 2 * f * t) + db(-20) * np.sin(2 * np.pi * 1.5 * f * t)) * e
def signal(bus, t0, g_db, taps=7, fb=0.52, f=1174.66):
    p = ping(f); d = BAR / 16 * 3
    for k in range(taps):
        s = p * fb ** k
        if k: s = lp(s, 6000 / (1 + 0.5 * k))
        place(bus, pan(s, (-0.55 if k % 2 else 0.55) if k else 0.0), t0 + k * d, db(g_db))
def with_hall(bus, wet_db=-9):
    return bus + fit(reverb(bus, ir_hall), N) * db(wet_db)

# 4a. "The Signal": the opening beacon, a lonely ping in the reveal silence, the last echo
sig = np.zeros((N, 2))
signal(sig, 0.08, -24); signal(sig, 0.08 + BAR / 4, -30, taps=4, f=1567.98)        # D6 + G6 answer
signal(sig, o[33] + 0.95, -30, taps=5, fb=0.45)
signal(sig, o[50] + 2.0, -31, taps=6, fb=0.5)
FX += with_hall(sig)

# 4b. intro atmosphere: frozen version of the soundtrack's own G-minor chord (fades out on the drop)
src_chord = mus[int(2.0 * SR):int(4.2 * SR)].mean(1)
pad = stereo_stretch(src_chord, 9.0, 140, 4500); pad /= np.abs(pad).max()
L = int((o[9] + 0.2) * SR); pad = fit(pad, L)
FX[:L] += pad * curve([(0, 0), (1.0, 1), (o[0] + 2, 0.7), (o[9] - 0.6, 0.55), (o[9], 0), (L / SR, 0)], L)[:, None] * db(-21)

# 4c. reverse swell + small sub hit into "Volume UP"
def rev_swell(dur, lo, hi, seed=0):
    r = np.random.default_rng(seed); t = t_(dur)
    s = bp(r.standard_normal((len(t), 2)), lo, hi, 2) * np.exp(-t / (dur / 4))[:, None]
    s = fit(reverb(s, make_ir(1.6, 2.0, seed=seed + 5)), len(t) + int(1.5 * SR))[::-1]
    s = s[-int(dur * SR):]; return s / np.abs(s).max()
def impact(dur=3.6, f0=46, f1=42, seed=0):
    r = np.random.default_rng(seed); t = t_(dur)
    sub = np.sin(2 * np.pi * np.cumsum(f0 + f1 * np.exp(-t / 0.09)) / SR) * np.exp(-t / 0.85) * (1 - np.exp(-t / 0.002))
    sub = np.tanh(1.8 * sub) / np.tanh(1.8)
    click = hp(r.standard_normal(len(t)), 1500) * np.exp(-t / 0.006) * 0.6
    air = hp(lp(r.standard_normal((len(t), 2)), 2500) * np.exp(-t / 0.9)[:, None] * (1 - np.exp(-t / 0.03))[:, None], 4500)
    return np.stack([sub + click * 0.5, sub + click * 0.5], 1) * db(-10) + air / np.abs(air).max() * db(-31)
sw = rev_swell(0.9, 600, 8000, 1); place(FX, sw, o[9] - len(sw) / SR - 0.005, db(-30))
place(FX, impact(1.4, seed=4), o[9] - 0.003, db(-5))

# 4d. "Warning." - self-destruct countdown: dark frozen drone, heartbeat, clock ticks on the quarter grid
src_dark = mus[int(13.0 * SR):int(15.4 * SR)].mean(1)
drone = stereo_stretch(src_dark, 3.0, 70, 900); drone /= np.abs(drone).max()
d0, d1 = T_STOP - 0.1, o[7] + 0.4; Ld = int((d1 - d0) * SR); drone = fit(drone, Ld)
place(FX, drone * curve([(0, 0), (0.5, 1), (d1 - d0 - 0.5, 1), (d1 - d0, 0)], Ld)[:, None], d0, db(-19))
def thump(f=49.0, dur=0.45):
    t = t_(dur); ph = 2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-t / 0.03))) / SR
    s = np.sin(ph) * np.exp(-t / 0.13) * (1 - np.exp(-t / 0.003))
    return np.tanh(2.2 * s) / np.tanh(2.2)
def clock(seed, hi=False):
    r = np.random.default_rng(seed); t = t_(0.05)
    s = bp(r.standard_normal(len(t)), 3000 if hi else 2200, 7000, 2) * np.exp(-t / 0.006) * (1 - np.exp(-t / 0.0004))
    return s + 0.5 * np.sin(2 * np.pi * (2400 if hi else 1800) * t) * np.exp(-t / 0.01)
q = BAR / 4
k0 = int(np.ceil((ed(V["warning"]) + 0.6 - o[9]) / q)); k1 = int(round((o[7] - o[9]) / q))
for k in range(k0, k1):
    tt = o[9] + k * q; prog = (k - k0) / max(1, k1 - k0 - 1)
    place(FX, pan(clock(k, hi=k % 2 == 0), 0.3 if k % 2 else -0.3), tt, db(-29 + 4 * prog))
    if k % 2 == 0: place(FX, thump(), tt, db(-21 + 4 * prog))

# 4e. warm frozen chord under "a massive thank you ... without you."
src_g = mus[int(13.0 * SR):int(15.4 * SR)].mean(1)
pad2 = stereo_stretch(src_g, 3.0, 130, 3200); pad2 /= np.abs(pad2).max()
p0 = ed(24.40); D2 = o[29] + 0.3 - p0; pad2 = fit(pad2, int(D2 * SR))
place(FX, pad2 * curve([(0, 0), (1.2, 0.7), (D2 - 0.9, 1.0), (D2 - 0.3, 0.4), (D2, 0)], len(pad2))[:, None], p0, db(-20))

# 4f. rhythmic "data" ticks building through the final stretch
def tick(seed):
    r = np.random.default_rng(seed); t = t_(0.06)
    return bp(r.standard_normal(len(t)), 8500, 14000, 2) * np.exp(-t / 0.012) * (1 - np.exp(-t / 0.0007))
s16 = BAR / 16
tick_bus = np.zeros((N, 2))
def ticks(t_from, n16, g0, g1, step=1):
    for j in range(0, n16, step):
        g = g0 + (g1 - g0) * j / max(1, n16 - 1) + (2.5 if j % 4 == 0 else 0)
        place(tick_bus, pan(tick(j), 0.35 if (j // step) % 2 else -0.35), t_from + j * s16, db(g))
ticks(o[7], 16, -44, -40, step=2)                    # playful pulse under "Just kidding"
ticks(o[29], 32, -43, -38, step=2)                   # "But October 21st? Forget the meetings..."
ticks(o[29] + 2 * BAR, 32, -38, -31, step=1)         # "Bring your people ... enjoy the ride"
FX += tick_bus * duck[:, None] ** 0.5

# 4g. controlled rise over the two bars into the boom on "ride"
Dr = 2 * BAR - 0.02; t = t_(Dr); nz = rng.standard_normal((len(t), 2))
fr_ = 300 * (7500 / 300) ** (t / Dr) ** 1.6
riser = np.zeros_like(nz); blk = 2048
for i in range(0, len(t), blk):
    c = fr_[min(i + blk // 2, len(t) - 1)]
    seg = nz[max(0, i - 512):i + blk + 512]
    f = sosfilt(butter(2, [c / 1.5, min(c * 1.5, 20000)], "bandpass", fs=SR, output="sos"), seg, axis=0)
    off = i - max(0, i - 512); riser[i:i + blk] = f[off:off + min(blk, len(t) - i)]
riser *= (np.exp(3.2 * t / Dr) - 1)[:, None] / (np.exp(3.2) - 1); riser /= np.abs(riser).max()
place(FX, riser, o[33] - Dr, db(-26))

# 4h. pre-drop reverse swell ending exactly on "NOISE"  +  4i. the impact
sw2 = rev_swell(1.15, 700, 10000, 7); place(FX, sw2, o[34] - len(sw2) / SR - 0.004, db(-29))
imp = impact(seed=11)
place(FX, imp, o[34] - 0.003); place(FX, fit(reverb(hp(imp, 120), ir_hall), len(imp) + 3 * SR) * db(-14), o[34] - 0.003)

# 4j. resolution: frozen final chord blooming out of the last bar
src_end = mus[int((B(50) + 0.25) * SR):int((B(50) + 2.4) * SR)].mean(1)
pad3 = stereo_stretch(src_end, 5.0, 90, 5000); pad3 /= np.abs(pad3).max()
D3 = N / SR - (o[50] + 0.4); pad3 = fit(pad3, int(D3 * SR))
place(FX, pad3 * (curve([(0, 0), (1.2, 1), (2.8, 0.85), (D3 - 0.3, 0), (D3, 0)], len(pad3)) ** 1.3)[:, None], o[50] + 0.4, db(-15))

# ----------------------------------------------------------------------------
# 5. VO space: subtle room, cinematic throws on "Warning." and "NOISE!"
# ----------------------------------------------------------------------------
ir_room = make_ir(0.7, 1.0, pre=0.012, seed=9)
room = fit(reverb(hp(VOX, 250), ir_room), N) * db(-22)
send = curve([(0, 0), (ed(V["warning"]) - 0.03, 0), (ed(V["warning"]), 0.8), (ed(10.85), 0.8), (ed(10.85) + 0.05, 0),
              (ed(V["noise"]) - 0.03, 0), (ed(V["noise"]), 1.0), (ed(V["end"]), 1.0), (ed(V["end"]) + 0.05, 0), (N / SR, 0)], N)
throw = fit(reverb(hp(VOX * send, 300), make_ir(2.6, 4.0, pre=0.05, seed=11)), N) * db(-15)
VOB = np.stack([VOX, VOX], 1) + room + throw

# ----------------------------------------------------------------------------
# 6. MIX + MASTER
# ----------------------------------------------------------------------------
MUS_BUS = Mf + FX
MUS_TRIM = float(sys.argv[2]) if len(sys.argv) > 2 else -2.5
mix = VOB + MUS_BUS * db(MUS_TRIM)
mix *= (curve([(0, 1), (N / SR - 2.0, 1), (N / SR - 0.25, 0), (N / SR, 0)], N) ** 2)[:, None]
mix = hp(mix, 31, 4)
mix = shelf(mix, 52, -1.8, high=False)
mix, gr_bus = compress(mix, -18, 1.6, att=0.03, rel=0.35, knee=10)

meter = pyln.Meter(SR); TARGET = -14.0
mix *= db(TARGET - meter.integrated_loudness(mix))
def limiter(x, ceiling_db=-1.2, look=0.004, rel=0.12):
    up = resample_poly(x, 4, 1, axis=0); pk = np.abs(up).max(1).reshape(-1, 4).max(1)[:len(x)]
    pk = np.pad(pk, (0, len(x) - len(pk)), constant_values=pk[-1] if len(pk) else 0)
    need = np.minimum(1.0, db(ceiling_db) / np.maximum(pk, 1e-9))
    L = int(look * SR); g = minimum_filter1d(need, 2 * L + 1)
    hop = 32; gc = g[: len(g) // hop * hop].reshape(-1, hop).min(1)
    gs = 1 - env_follow(1 - gc, 0.0005, rel, SR / hop)
    gs = np.minimum(np.repeat(gs, hop), g[: len(gs) * hop]); gs = np.pad(gs, (0, len(x) - len(gs)), constant_values=1)
    gs = np.convolve(np.pad(gs, L, mode="edge"), np.ones(L) / L, mode="same")[L:-L]; gs = np.minimum(gs, minimum_filter1d(need, 2 * L + 1) + 1e-3)
    return x * gs[:, None], gs
for it in range(3):
    lim, gs = limiter(mix); mix *= db(TARGET - meter.integrated_loudness(lim))
lim, gs = limiter(mix)
print("limiter max GR %.2f dB, time limiting > 0.5 dB: %.2f s" % (-20 * np.log10(gs.min()), (gs < db(-0.5)).sum() / SR))

sf.write(f"{W}/master_v2.wav", lim.astype(np.float32), SR, subtype="FLOAT")
sf.write(f"{W}/stem_vo_v2.wav", VOB.astype(np.float32), SR, subtype="FLOAT")
sf.write(f"{W}/stem_music_v2.wav", (MUS_BUS * db(MUS_TRIM)).astype(np.float32), SR, subtype="FLOAT")

# ----------------------------------------------------------------------------
# 7. LANDING PAGE DATA: captions, story moments, loudness envelope (30 fps)
# ----------------------------------------------------------------------------
caps = [[round(ed(a), 2), round(ed(b), 2), txt] for a, b, txt in PHRASES]
moments = dict(spark=round(o[0], 2), up=round(o[9], 2), warn=round(ed(V["warning"]), 2), kid=round(o[7], 2), look=round(o[25], 2),
               but=round(o[29], 2), ride=round(o[33], 2), quiet=round(o[33] + 1.0, 2), tec=round(o[34], 2), end=round(o[50], 2))
m = lim.mean(1); hop = SR // 30; nf = len(m) // hop
rms_db = 20 * np.log10(np.sqrt((m[:nf * hop].reshape(nf, hop) ** 2).mean(1)) + 1e-9)
CH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
envelope = "".join(CH[int(round(v))] for v in np.clip((rms_db + 54) / 48 * 61, 0, 61))
json.dump(dict(captions=caps, moments=moments, envelope=envelope, duration=round(N / SR, 2), out={str(k): v for k, v in out.items()},
               inserts=inserts, E33=E33), open(f"{W}/timeline_v2.json", "w"), indent=1, ensure_ascii=False)
print("moments:", moments)
print("duration %.2f s" % (N / SR))
