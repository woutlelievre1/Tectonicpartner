"""TECTONIC 2026 - "The Signal" - cinematic partner audio production.

Pipeline: VO edit (pause insertion only) -> VO processing -> bar-accurate music
edit of "Inspiring Cinematic Trailer" -> filter/gain/duck automation ->
synthesized sound design -> mix -> master. All synthesis is done here in numpy,
no third-party samples are used.
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
# helpers
# ----------------------------------------------------------------------------
def sos(kind, f, order=2):
    return butter(order, f, kind, fs=SR, output="sos")

def lp(x, f, o=2):  return sosfiltfilt(sos("lowpass", f, o), x, axis=0)
def hp(x, f, o=2):  return sosfiltfilt(sos("highpass", f, o), x, axis=0)
def bp(x, a, b, o=2): return sosfiltfilt(sos("bandpass", [a, b], o), x, axis=0)

def peq(x, f0, gain_db, q=1.0):
    """RBJ peaking EQ (zero-phase is not needed for VO, keep minimum phase)."""
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
    """one-pole attack/release smoother on a control-rate signal."""
    aa = np.exp(-1 / (att * rate)); ar = np.exp(-1 / (rel * rate)); out = np.empty_like(level); g = level[0]
    for i, v in enumerate(level):
        g = aa * g + (1 - aa) * v if v > g else ar * g + (1 - ar) * v
        out[i] = g
    return out

def ctrl_to_audio(c, rate, n):
    t = np.arange(n) / SR
    return np.interp(t, np.arange(len(c)) / rate, c)

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

def pan(sig, p):  # p in [-1,1], equal power
    a = (p + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], 1)

def curve(points, n, mode="lin"):
    """piecewise curve from [(t, v), ...] sampled at audio rate."""
    t = np.arange(n) / SR; ts, vs = zip(*points)
    return np.interp(t, ts, vs)

def paulstretch(x, stretch, win_s=0.35):
    """Paul's extreme sound stretch (mono) - turns a chord into an ethereal pad."""
    win = int(win_s * SR) // 2 * 2; h = win // 2
    w = np.hanning(win) ** 1.0
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
# 1. VOICE-OVER: insert breathing room at existing (digital-silence) pauses only
# ----------------------------------------------------------------------------
vo, sr = sf.read(f"{W}/vo.wav"); vo = vo.mean(1) if vo.ndim == 2 else vo
assert sr == SR

# word onsets (orig VO seconds) measured from ASR + fine envelope analysis
V = dict(spark=2.62, people=10.88, you=22.625, this=24.445, toour=32.83,
         future=37.01, ghent=41.105, tec=42.885, together=43.91, next_end=46.16)

# music bar grid of the source track (84 BPM 4/4, calibrated on detected hits)
BAR = 2.85739; B = lambda k: 1.4804 + BAR * k
E8, E33 = 0.35, None           # elastic silence added inside break bars 8 and 33
INS_GHENT, INS_WELCOME = 0.86, 0.59
E33 = (V["tec"] - V["ghent"] + INS_GHENT + INS_WELCOME) - (BAR + 0.02)

T0 = 4.50 + V["spark"]          # out time of bar 0 hit (= "spark")
out = {}
out[0] = T0; out[3] = T0 + 3 * BAR; out[4] = out[3]; out[8] = out[4] + 4 * BAR
out[9] = out[8] + BAR + E8; out[11] = out[9] + 2 * BAR; out[24] = out[11]; out[25] = out[24] + BAR
out[26] = out[25] + BAR; out[30] = out[26]; out[31] = out[30] + BAR; out[33] = out[31] + 2 * BAR
out[34] = out[33] + BAR + E33; out[35] = out[34] + BAR; out[36] = out[35] + BAR; out[48] = out[36]
out[49] = out[48] + BAR; out[50] = out[49] + BAR

vo_off = T0 - V["spark"]
targets = [("spark", out[0]), ("people", out[4]), ("you", out[8] + 0.81), ("this", out[9] + 0.10),
           ("toour", out[25] + 0.10), ("future", out[31] + 0.10), ("ghent", out[33]),
           ("tec", out[34] + 0.02), ("together", out[35] + 0.10)]
# cut points (centres of existing silent gaps) and their share of each interval's insert
cuts = {("spark", "people"): [(3.46, .2), (4.70, .2), (7.92, .3), (10.66, .3)],
        ("people", "you"): [(22.38, 1.)],
        ("you", "this"): [(24.19, 1.)],
        ("this", "toour"): [(32.59, 1.)],
        ("toour", "future"): [(33.86, .15), (35.28, .25), (36.81, .60)],
        ("future", "ghent"): [(38.60, .33), (40.03, .36), (41.055, .31)],
        ("ghent", "tec"): [(41.75, INS_GHENT / (INS_GHENT + INS_WELCOME)), (42.60, INS_WELCOME / (INS_GHENT + INS_WELCOME))],
        ("tec", "together"): [(43.77, 1.)]}
inserts = []
for (a, ta), (b, tb) in zip(targets[:-1], targets[1:]):
    need = (tb - ta) - (V[b] - V[a])
    assert need >= -1e-6, (a, b, need)
    for c, w in cuts[(a, b)]: inserts.append((c, need * w))
inserts.sort()
pieces, last = [], 0
for c, d in inserts:
    i = int(c * SR); pieces += [vo[last:i], np.zeros(int(round(d * SR)))]; last = i
pieces.append(vo[last:])
vo_ed = np.concatenate(pieces)
def ed(t):  # orig VO time -> output time
    return t + sum(d for c, d in inserts if c < t) + vo_off
print("inserts:", [(c, round(d, 3)) for c, d in inserts])
print("E33 = %.3f" % E33)
for k, t in targets: print(f"  {k:9s} target {t:7.3f}  got {ed(V[k]):7.3f}")

# ----------------------------------------------------------------------------
# 2. VOICE PROCESSING (premium + natural)
# ----------------------------------------------------------------------------
v = hp(vo_ed, 75, 2)
v = peq(v, 280, -1.5, 0.9)          # de-mud
v = peq(v, 3600, +1.5, 0.8)         # presence / intelligibility on small speakers
v = shelf(v, 11000, +1.0, True)     # air
# split-band de-esser
sib = bp(v, 5500, 9500, 2); hop = 44
n = len(sib) // hop; lev = 10 * np.log10((np.pad(sib, (0, (n + 1) * hop - len(sib))).reshape(n + 1, hop) ** 2).mean(1) + 1e-12)
full = 10 * np.log10((np.pad(v, (0, (n + 1) * hop - len(v))).reshape(n + 1, hop) ** 2).mean(1) + 1e-12)
red = np.clip((lev - full + 6) * 0.8, 0, 6)       # only when sibilance dominates
red = env_follow(red, 0.002, 0.06, SR / hop)
v = v - sib * (1 - db(-ctrl_to_audio(red, SR / hop, len(v))))
v, _ = compress(v, -26, 2.2, att=0.010, rel=0.18, knee=8)
v = v / np.sqrt(np.mean(v[np.abs(v) > 1e-4] ** 2)) * db(-20.5)
# transparent peak control: soft lookahead limiter 10.5 dB above the speech RMS
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
XF_BAR = 0.034    # equal-power crossfade just before a bar-line hit
XF_SIL = 0.30     # long crossfade inside the elastic near-silence of a break bar
SIL8, SIL33 = B(8) + 1.40, B(33) + 1.25        # quiet points inside the break bars
segs = [  # (src_start, src_end, src_anchor, out_anchor)
    (0.00,          B(3),                   B(0),  out[0]),
    (B(4),          SIL8 + E8 + XF_SIL,     B(4),  out[4]),
    (SIL8,          B(11),                  B(9),  out[9]),
    (B(24),         B(26),                  B(24), out[24]),
    (B(30),         SIL33 + E33 + XF_SIL,   B(30), out[30]),
    (SIL33,         B(36),                  B(34), out[34]),
    (B(48),         len(mus) / SR,          B(48), out[48]),
]
bar_join = [False, True, False, True, True, False, True]   # join type with previous segment
PRE = 0.006
for i, (s0, s1, sa, oa) in enumerate(segs):
    s0e = s0 - (XF_BAR if bar_join[i] else 0.0)            # incoming starts XF_BAR early
    x = mus[int(round(s0e * SR)):int(round(s1 * SR))].copy()
    if i > 0:
        L = int((XF_BAR if bar_join[i] else XF_SIL) * SR); x[:L] *= np.sin(np.linspace(0, np.pi / 2, L))[:, None]
    if i < len(segs) - 1:
        if bar_join[i + 1]:          # outgoing fade completes 6 ms before the next hit
            x = x[:len(x) - int(PRE * SR)]; L = int(XF_BAR * SR)
        else:
            L = int(XF_SIL * SR)
        x[-L:] *= np.cos(np.linspace(0, np.pi / 2, L))[:, None]
    place(M, x, oa + (s0e - sa))
# sanity: elastic joins overlap by exactly XF_SIL
for i in (2, 5):
    pe = segs[i-1][3] + (segs[i-1][1] - segs[i-1][2]); ps = segs[i][3] + (segs[i][0] - segs[i][2])
    assert abs((pe - ps) - XF_SIL) < 1e-6, (i, pe - ps)

sf.write(f"{W}/music_raw_edit.wav", M.astype(np.float32), SR, subtype="FLOAT")
# ---- automation (cutoff + gain), keyed to the edited timeline -------------------
o = out
lpf_pts = [(0, 330), (o[0] - 0.9, 330), (o[0], 520), (o[4] - 1.6, 560), (o[4] - 0.02, 560), (o[4] + 0.35, 2300),
           (o[4] + 2 * BAR, 5000), (o[8] - 0.2, 9000), (o[8], 20000), (o[9] - 0.01, 20000), (o[9], 3800),
           (o[9] + BAR * 1.2, 20000), (o[25] - 0.1, 20000), (o[25], 6500), (o[31], 6500), (o[33] - 0.5, 20000),
           (N / SR, 20000)]
gain_pts = [(0, -14), (o[0] - 0.9, -14), (o[0], -10.5), (o[4] - 1.8, -10.5), (o[4] - 0.4, -12.0), (o[4], -7.5),
            (o[8] - 0.1, -6.0), (o[8], -4.0), (o[9] - 0.01, -4.0), (o[9], -9.0), (o[25] - 0.15, -6.5),
            (o[25], -7.0), (o[31], -7.0), (o[33] - 0.05, -2.0), (o[33] + 0.85, -2.0), (o[33] + 1.45, -14.0),
            (o[34] - 0.66, -14.0), (o[34] - 0.06, -6.0), (o[34] - 0.004, -1.5), (o[35] - 0.3, -2.5), (o[35], -4.5),
            (o[35] + 2.45, -4.5), (o[48], -3.0), (o[50], -3.0), (N / SR, -3.0)]
cut = curve(lpf_pts, N); gdb = curve(gain_pts, N)
bank_f = [330, 520, 800, 1250, 2000, 3200, 5000, 8000, 12500]
bank = [lp(M, f, 2) for f in bank_f] + [M]
lf = np.log(np.clip(cut, bank_f[0], 20000)); grid = np.log(np.array(bank_f + [20000.0]))
idx = np.clip(np.searchsorted(grid, lf) - 1, 0, len(grid) - 2); fr = (lf - grid[idx]) / (grid[idx + 1] - grid[idx])
Mf = np.zeros_like(M)
for k in range(len(grid) - 1):
    m = idx == k
    Mf[m] = bank[k][m] * (1 - fr[m, None]) + bank[k + 1][m] * fr[m, None]
del bank
Mf *= db(gdb)[:, None]

# ---- VO in output timeline + sidechain ducking ---------------------------------
VOX = np.zeros(N); place(VOX, v, vo_off)
VOX *= db(curve([(0, 0), (ed(V["tec"]) - 0.03, 0), (ed(V["tec"]), 2.0), (ed(43.63), 2.0), (ed(43.63) + 0.03, 0), (N / SR, 0)], N))
rate = 1000; hop = SR // rate; n = N // hop
lvl = 10 * np.log10((VOX[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
act = np.clip((lvl + 52) / 16, 0, 1)
act = env_follow(act, 0.025, 0.35, rate)
depth_pts = [(0, 4), (o[4], 4.5), (o[8], 3), (o[9], 8.5), (o[25], 7.0), (o[31], 7.5), (o[33], 4), (o[34] - 0.8, 7), (o[34] - 0.01, 7),
             (o[34], 8.0), (o[35], 9.5), (N / SR, 9.5)]
depth = curve(depth_pts, N)
actA = ctrl_to_audio(act, rate, N)
duck = db(-depth * actA)
# extra mid-band carve (1-4 kHz) where the voice lives
mid = bp(Mf, 900, 4200, 2)
carve = curve([(0, 3.0), (o[34] - 0.05, 3.0), (o[34], 7.0), (N / SR, 7.0)], N)
Mf = Mf - mid * (1 - db(-carve * actA))[:, None]
Mf *= duck[:, None]

# ----------------------------------------------------------------------------
# 4. SOUND DESIGN (all synthesized / derived from the licensed soundtrack)
# ----------------------------------------------------------------------------
FX = np.zeros((N, 2))
t_ = lambda d: np.arange(int(d * SR)) / SR

# 4a. "The Signal": a soft beacon ping with dotted-8th ping-pong echoes
def ping(f=1174.66, dur=0.9):
    t = t_(dur); e = np.exp(-t / 0.16) * (1 - np.exp(-t / 0.002))
    return (np.sin(2 * np.pi * f * t) + db(-14) * np.sin(2 * np.pi * 2 * f * t) + db(-20) * np.sin(2 * np.pi * 1.5 * f * t)) * e
def signal(t0, g_db, taps=7, fb=0.52):
    p = ping(); d = BAR / 16 * 3   # dotted 8th
    for k in range(taps):
        s = p * fb ** k
        if k: s = lp(s, 6000 / (1 + 0.5 * k))
        place(FX, pan(s, (-0.55 if k % 2 else 0.55) if k else 0.0), t0 + k * d, db(g_db))
ir_hall = make_ir(3.2, 4.0, pre=0.035, seed=3)

sig_bus = np.zeros((N, 2)); FX_saved = FX; FX = sig_bus
signal(o[0] - 2 * BAR, -27); signal(o[0] - BAR, -29)
signal(o[33] + 0.92, -31, taps=5, fb=0.45)           # alone in the reveal silence
FX = FX_saved
sig_wet = fit(reverb(sig_bus, ir_hall), N) * db(-9)
FX += sig_bus + sig_wet

# 4b. Act I atmosphere: frozen version of the soundtrack's own G-minor chord
src_chord = mus[int(2.0 * SR):int(4.2 * SR)].mean(1)
pad = stereo_stretch(src_chord, 9.0, 140, 4500)  # decorrelated L/R = wide AND mono-safe
pad /= np.abs(pad).max()
L = int((o[4] + 1.5) * SR); pad = fit(pad, L)
pe = curve([(0, 0), (3.2, 1), (o[0] - 0.5, 1), (o[0] + 2, 0.7), (o[4] - 0.5, 0.55), (o[4] + 1.5, 0)], L)
FX[:L] += pad * pe[:, None] * db(-20)

# 4c. Deep electronic pulse (heartbeat) leading into the music, on the bar grid
def thump(f=49.0, dur=0.45):
    t = t_(dur); ph = 2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-t / 0.03))) / SR
    s = np.sin(ph) * np.exp(-t / 0.13) * (1 - np.exp(-t / 0.003))
    return np.tanh(2.2 * s) / np.tanh(2.2)       # gentle harmonics for small speakers
beat = BAR / 4
for k in range(1, 9):                      # 8 beats before the first impact
    tt = o[0] - k * beat
    place(FX, thump(), tt, db(-18 - 1.5 * k))

# 4d. soft reverse swell into "People"
def rev_swell(dur, lo, hi, seed=0):
    r = np.random.default_rng(seed); t = t_(dur)
    s = bp(r.standard_normal((len(t), 2)), lo, hi, 2) * np.exp(-t / (dur / 4))[:, None]
    s = fit(reverb(s, make_ir(1.6, 2.0, seed=seed + 5)), len(t) + int(1.5 * SR))[::-1]
    s = s[-int(dur * SR):]; return s / np.abs(s).max()
sw = rev_swell(0.9, 500, 6000, 1); place(FX, sw, o[4] - len(sw) / SR - 0.005, db(-33))

# 4e. "You are one of them." - warm frozen chord swelling under the break
src_g = mus[int(13.0 * SR):int(15.4 * SR)].mean(1)
pad2 = stereo_stretch(src_g, 3.0, 130, 3200)
pad2 /= np.abs(pad2).max(); D2 = o[9] + 0.5 - (o[8] + 0.05); pad2 = fit(pad2, int(D2 * SR))
e2 = curve([(0, 0), (0.9, 0.75), (D2 - 0.9, 1.0), (D2 - 0.45, 0.5), (D2, 0)], len(pad2))
place(FX, pad2 * e2[:, None], o[8] + 0.05, db(-17))

# 4f. Act III / IV: rhythmic "data" ticks on the 16th grid (above sibilance range)
def tick(seed):
    r = np.random.default_rng(seed); t = t_(0.06)
    return bp(r.standard_normal(len(t)), 8500, 14000, 2) * np.exp(-t / 0.012) * (1 - np.exp(-t / 0.0007))
s16 = BAR / 16
tick_bus = np.zeros((N, 2)); FX_saved = FX; FX = tick_bus
def ticks(t_from, n16, g0, g1, step=1):
    for j in range(0, n16, step):
        g = g0 + (g1 - g0) * j / max(1, n16 - 1) + (2.5 if j % 4 == 0 else 0)
        place(FX, pan(tick(j), 0.35 if (j // step) % 2 else -0.35), t_from + j * s16, db(g))
ticks(o[9], 16 * 3, -44, -36)                       # gathering of bold minds
ticks(o[31], 16, -42, -37, step=2)                  # "The future is calling" - 8ths
ticks(o[31] + BAR, 16, -37, -31, step=1)            # date / place - 16ths
FX = FX_saved
FX += tick_bus * duck[:, None] ** 0.5

# 4g. controlled rise: band-swept noise riser + octave-rising frozen chord
Dr = 2 * BAR - 0.02; t = t_(Dr); nz = rng.standard_normal((len(t), 2))
fr_ = 300 * (7500 / 300) ** (t / Dr) ** 1.6
riser = np.zeros_like(nz); blk = 2048
for i in range(0, len(t), blk):
    c = fr_[min(i + blk // 2, len(t) - 1)]
    seg = nz[max(0, i - 512):i + blk + 512]
    f = sosfilt(butter(2, [c / 1.5, min(c * 1.5, 20000)], "bandpass", fs=SR, output="sos"), seg, axis=0)
    off = i - max(0, i - 512); riser[i:i + blk] = f[off:off + min(blk, len(t) - i)]
riser *= (np.exp(3.2 * t / Dr) - 1)[:, None] / (np.exp(3.2) - 1)
riser /= np.abs(riser).max()
place(FX, riser, o[31], db(-27))

# 4h. pre-reveal reverse swell, ending exactly on "TEC"
sw2 = rev_swell(1.15, 700, 10000, 7); place(FX, sw2, o[34] - len(sw2) / SR - 0.004, db(-31))

# 4i. THE IMPACT on "TECTONIC": sub drop + transient + air tail
t = t_(3.6)
f_sub = 46 + 42 * np.exp(-t / 0.09)
sub = np.sin(2 * np.pi * np.cumsum(f_sub) / SR) * np.exp(-t / 0.85) * (1 - np.exp(-t / 0.002))
sub = np.tanh(1.8 * sub) / np.tanh(1.8)
click = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t / 0.006) * 0.6
air = lp(rng.standard_normal((len(t), 2)), 2500) * np.exp(-t / 0.9)[:, None] * (1 - np.exp(-t / 0.03))[:, None]
air = hp(air, 4500)   # leave 300 Hz - 4 kHz to the narrator
imp = np.stack([sub + click * 0.5, sub + click * 0.5], 1) * db(-10) + air / np.abs(air).max() * db(-31)
imp_wet = fit(reverb(hp(imp, 120), ir_hall), len(t) + int(3 * SR)) * db(-14)
place(FX, imp, o[34] - 0.003); place(FX, imp_wet, o[34] - 0.003)

# 4j. resolution: frozen final chord blooming out of the last bar
src_end = mus[int((B(50) + 0.25) * SR):int((B(50) + 2.4) * SR)].mean(1)
pad3 = stereo_stretch(src_end, 5.0, 90, 5000)
pad3 /= np.abs(pad3).max(); D3 = N / SR - (o[50] + 0.4); pad3 = fit(pad3, int(D3 * SR))
e3 = curve([(0, 0), (1.2, 1), (2.8, 0.85), (D3 - 0.3, 0), (D3, 0)], len(pad3)) ** 1.3
place(FX, pad3 * e3[:, None], o[50] + 0.4, db(-15))
sig_bus = np.zeros((N, 2)); FX_saved = FX; FX = sig_bus
signal(o[50] + 2.0, -31, taps=6, fb=0.5)
FX = FX_saved; FX += sig_bus + fit(reverb(sig_bus, ir_hall), N) * db(-9)

# ----------------------------------------------------------------------------
# 5. VO space: subtle room always, cinematic throw on "TECTONIC"
# ----------------------------------------------------------------------------
ir_room = make_ir(0.7, 1.0, pre=0.012, seed=9)
VO2 = np.stack([VOX, VOX], 1)
room = fit(reverb(hp(VOX, 250), ir_room), N) * db(-21)
send = curve([(0, 0), (ed(V["tec"]) - 0.05, 0), (ed(V["tec"]), 1), (ed(43.62), 1), (ed(43.62) + 0.05, 0),
              (ed(45.75), 0), (ed(45.75) + 0.02, 0.55), (ed(46.16), 0.55), (ed(46.16) + 0.05, 0), (N / SR, 0)], N)
throw = fit(reverb(hp(VOX * send, 300), make_ir(2.6, 4.0, pre=0.05, seed=11)), N) * db(-15)
VOB = VO2 + room + throw

# ----------------------------------------------------------------------------
# 6. MIX + MASTER
# ----------------------------------------------------------------------------
MUS_BUS = Mf + FX
MUS_TRIM = float(sys.argv[2]) if len(sys.argv) > 2 else -3.0
mix = VOB + MUS_BUS * db(MUS_TRIM)
end_fade = curve([(0, 1), (N / SR - 2.0, 1), (N / SR - 0.25, 0), (N / SR, 0)], N) ** 2
mix *= end_fade[:, None]
mix = hp(mix, 31, 4)
mix = shelf(mix, 52, -1.8, high=False)      # portable-speaker friendly sub, headphones keep weight
mix, gr_bus = compress(mix, -18, 1.6, att=0.03, rel=0.35, knee=10)   # gentle glue

meter = pyln.Meter(SR)
TARGET = -14.0
mix *= db(TARGET - meter.integrated_loudness(mix))

def limiter(x, ceiling_db=-1.2, look=0.004, rel=0.12):
    up = resample_poly(x, 4, 1, axis=0); pk = np.abs(up).max(1).reshape(-1, 4).max(1)[:len(x)]
    pk = np.pad(pk, (0, len(x) - len(pk)), constant_values=pk[-1] if len(pk) else 0)
    need = np.minimum(1.0, db(ceiling_db) / np.maximum(pk, 1e-9))
    L = int(look * SR); g = minimum_filter1d(need, 2 * L + 1)
    # smooth release at control rate
    hop = 32; gc = g[: len(g) // hop * hop].reshape(-1, hop).min(1)
    gs = 1 - env_follow(1 - gc, 0.0005, rel, SR / hop)
    gs = np.minimum(np.repeat(gs, hop), g[: len(gs) * hop]); gs = np.pad(gs, (0, len(x) - len(gs)), constant_values=1)
    gs = np.convolve(np.pad(gs, L, mode="edge"), np.ones(L) / L, mode="same")[L:-L]; gs = np.minimum(gs, minimum_filter1d(need, 2 * L + 1) + 1e-3)
    return x * gs[:, None], gs
for it in range(3):
    lim, gs = limiter(mix)
    lu = meter.integrated_loudness(lim)
    mix *= db(TARGET - lu)
lim, gs = limiter(mix)
print("limiter max GR dB: %.2f, mean GR in climax: %.2f" % (-20 * np.log10(gs.min()), -20 * np.log10(gs[int(o[34] * SR):int(o[36] * SR)].mean())))

np.save(f"{W}/gr.npy", gs[::441]); sf.write(f"{W}/master.wav", lim.astype(np.float32), SR, subtype="FLOAT")
sf.write(f"{W}/stem_vo.wav", (VOB * db(0)).astype(np.float32), SR, subtype="FLOAT")
sf.write(f"{W}/stem_music.wav", (MUS_BUS * db(MUS_TRIM)).astype(np.float32), SR, subtype="FLOAT")
json.dump(dict(out={str(k): v for k, v in out.items()}, vo={k: ed(t) for k, t in V.items()}, N=N,
               inserts=inserts, E8=E8, E33=E33), open(f"{W}/timeline.json", "w"), indent=1)
print("duration %.2f s" % (N / SR))
