"""Schematic ECG strip generator for ECG Means.

Draws teaching illustrations (not patient tracings) on standard ECG paper:
25 mm/s, 10 mm/mV. Each figure is built from explicit P / QRS / ST / T / U
components so the morphology matches the finding the page explains.
"""
import math, random
from html import escape as _esc

FS = 500  # samples per second
MM_PER_S = 25.0
MM_PER_MV = 10.0

def g(t, a, c, s):
    return a * math.exp(-0.5 * ((t - c) / s) ** 2)

def ag(t, a, c, s1, s2):
    """asymmetric gaussian: s1 before peak, s2 after"""
    s = s1 if t < c else s2
    return a * math.exp(-0.5 * ((t - c) / s) ** 2)

def sig(x):
    return 1 / (1 + math.exp(-x))

# ---------------- morphology presets ----------------
NORMAL = dict(
    qrs=[(-0.08, 0.012, 0.007), (1.0, 0.038, 0.010), (-0.22, 0.066, 0.010)],
    j=0.09, st=0.0, st_shape="flat", t=(0.30, 0.30, 0.055, 0.040), u=0.0, jwave=0.0,
)

def M(**kw):
    m = dict(NORMAL); m.update(kw); return m

def wide(comps, factor):
    return [(a, c * factor, s * factor) for a, c, s in comps]

PVC = M(qrs=[(1.25, 0.07, 0.030), (-0.35, 0.14, 0.022)], j=0.17,
        t=(-0.45, 0.36, 0.060, 0.050))

# ---------------- beat rendering ----------------
def qrs_t(t, m):
    """complex value at time t relative to QRS onset"""
    v = 0.0
    for a, c, s in m["qrs"]:
        if abs(t - c) < 6 * s:
            v += g(t, a, c, s)
    j = m["j"]
    tt = m["t"]  # (amp, peak_time, rise_sigma, fall_sigma)
    if -0.2 < t - tt[1] < 0.4:
        v += ag(t, tt[0], tt[1], tt[2], tt[3])
    if m.get("t2"):  # biphasic second lobe
        a2, c2, s2 = m["t2"]
        v += g(t, a2, c2, s2)
    if m["st"]:
        end = tt[1] - 0.02
        shape = sig((t - j) / 0.006) * sig((end - t) / 0.03)
        if m["st_shape"] == "concave":
            frac = min(max((t - j) / max(end - j, 1e-3), 0), 1)
            shape *= 0.6 + 0.4 * frac
        elif m["st_shape"] == "down":
            frac = min(max((t - j) / max(end - j, 1e-3), 0), 1)
            shape *= 0.75 + 0.35 * frac
        elif m["st_shape"] == "convex":
            frac = min(max((t - j) / max(end - j, 1e-3), 0), 1)
            shape *= 1.0 - 0.25 * (frac - 0.5) ** 2 * 4
        v += m["st"] * shape
    if m["u"]:
        v += g(t, m["u"], tt[1] + 0.17, 0.035)
    if m["jwave"]:
        v += g(t, m["jwave"], j + 0.005, 0.014)
    if m.get("delta"):
        v += m["delta"] * sig((t - 0.0) / 0.012) * sig((0.05 - t) / 0.012)
    return v

def p_wave(t, kind="normal"):
    if kind == "normal":
        return g(t, 0.13, 0.05, 0.020)
    if kind == "peaked":
        return g(t, 0.30, 0.045, 0.016)
    if kind == "mitrale":
        return g(t, 0.12, 0.035, 0.018) + g(t, 0.12, 0.10, 0.02)
    if kind == "inverted":
        return g(t, -0.12, 0.05, 0.020)
    if kind == "small":
        return g(t, 0.07, 0.045, 0.016)
    if kind == "biphasic":
        return g(t, 0.09, 0.035, 0.015) + g(t, -0.08, 0.075, 0.015)
    if kind == "tall_narrow":
        return g(t, 0.18, 0.04, 0.014)
    return 0.0

class Strip:
    def __init__(self, dur=6.0, lead="II", top=1.6, bottom=1.0):
        self.dur = dur; self.lead = lead; self.top = top; self.bottom = bottom
        self.p = []      # (time, kind)
        self.q = []      # (time, morph)
        self.base = None # callable(t) -> mV
        self.labels = [] # (t, mv, text)
        self.brackets = []  # (t1, t2, mv, text)

    def signal(self):
        n = int(self.dur * FS)
        ys = []
        for i in range(n):
            t = i / FS
            v = 0.0
            for pt, kind in self.p:
                if -0.05 < t - pt < 0.2:
                    v += p_wave(t - pt, kind)
            for qt, m in self.q:
                if -0.05 < t - qt < 0.75:
                    v += qrs_t(t - qt, m)
            if self.base:
                v += self.base(t)
            ys.append(v)
        return ys

# ---------------- rhythm helpers ----------------
def sinus(s, hr=75, pr=0.16, start=0.35, morph=NORMAL, pkind="normal", rr=None):
    t = start
    k = 0
    while t < s.dur - 0.25:
        s.p.append((t - pr, pkind)); s.q.append((t, morph))
        step = rr(k) if rr else 60.0 / hr
        t += step; k += 1
    return s

# ---------------- SVG ----------------
def render(rows, title, width_mm=None, footer=None):
    """rows: list of Strip or ('panel', [(label, Strip)])"""
    row_h = []
    for r in rows:
        st = r if isinstance(r, Strip) else r[1][0][1]
        row_h.append((st.top + st.bottom) * MM_PER_MV + 2)
    if width_mm is None:
        width_mm = max((r.dur if isinstance(r, Strip) else sum(x[1].dur for x in r[1])) for r in rows) * MM_PER_S
    H = sum(row_h) + 3.5
    W = width_mm
    k = max(0.62, min(1.0, W / 150))
    title = _esc(title)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W*4:.0f}" height="{H*4:.0f}" role="img" aria-label="{title}">',
           f'<title>{title}</title>',
           f'<rect width="{W:.0f}" height="{H:.0f}" fill="#fff8f8"/>']
    # grid
    minor, major = [], []
    for x in range(0, int(W) + 1):
        (major if x % 5 == 0 else minor).append(f'M{x} 0V{H:.0f}')
    for y in range(0, int(H) + 1):
        (major if y % 5 == 0 else minor).append(f'M0 {y}H{W:.0f}')
    out.append(f'<path d="{"".join(minor)}" stroke="#f6c9cd" stroke-width="0.1"/>')
    out.append(f'<path d="{"".join(major)}" stroke="#ec9ea6" stroke-width="0.25"/>')
    y0 = 0
    for r, h in zip(rows, row_h):
        if isinstance(r, Strip):
            segs = [(r.lead, r)]
        else:
            segs = r[1]
        x0 = 0.0
        for label, st in segs:
            base = y0 + 1 + st.top * MM_PER_MV
            ys = st.signal()
            pts = []
            for i, v in enumerate(ys):
                if i % 2: continue
                x = x0 + i / FS * MM_PER_S
                y = base - v * MM_PER_MV
                pts.append(f'{x:.2f},{y:.2f}')
            out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#1b1b1b" stroke-width="0.42" stroke-linejoin="round" stroke-linecap="round"/>')
            out.append(f'<text x="{x0+1.5:.1f}" y="{y0+4.2:.1f}" font-family="Arial,Helvetica,sans-serif" font-size="{3.4*k:.2f}" font-weight="700" fill="#7a1010">{_esc(label)}</text>')
            for t, mv, text in st.labels:
                out.append(f'<text x="{x0+t*MM_PER_S:.1f}" y="{base - mv*MM_PER_MV:.1f}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="{3*k:.2f}" font-weight="700" fill="#b91c1c">{_esc(text)}</text>')
            for t1, t2, mv, text in st.brackets:
                xa, xb = x0 + t1 * MM_PER_S, x0 + t2 * MM_PER_S
                yy = base - mv * MM_PER_MV
                out.append(f'<path d="M{xa:.1f} {yy-1:.1f}V{yy:.1f}H{xb:.1f}V{yy-1:.1f}" fill="none" stroke="#1d4ed8" stroke-width="0.35"/>')
                out.append(f'<text x="{(xa+xb)/2:.1f}" y="{yy+3.4*k:.1f}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="{2.8*k:.2f}" font-weight="700" fill="#1d4ed8">{_esc(text)}</text>')
            if not isinstance(r, Strip):
                out.append(f'<path d="M{x0:.1f} {y0+1:.1f}V{y0+h-1:.1f}" stroke="#7a1010" stroke-width="0.3"/>' if x0 > 0 else '')
            x0 += st.dur * MM_PER_S
        y0 += h
    ft = footer or ("Schematic illustration · 25 mm/s · 10 mm/mV · ecgmeans.com" if W >= 110 else "Schematic · ecgmeans.com")
    out.append(f'<text x="{W-1.5:.1f}" y="{H-1.0:.1f}" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="{2.3*k:.2f}" fill="#8a5a5e">{_esc(ft)}</text>')
    out.append('</svg>')
    return "\n".join(out)

# ---------------- per-finding figures ----------------
def one_beat(m=NORMAL, pkind="normal", pr=0.16, lead="II", dur=1.2, top=1.6, bottom=1.0, p=True, at=0.3):
    s = Strip(dur=dur, lead=lead, top=top, bottom=bottom)
    if p: s.p.append((at - pr, pkind))
    s.q.append((at, m))
    return s

def panel(items):
    return ("panel", items)

def fig(slug):
    R = random.Random(hash(slug) % 1000)
    N = NORMAL
    if slug == "sinus-rhythm":
        return [sinus(Strip(), hr=72)]
    if slug == "sinus-bradycardia":
        return [sinus(Strip(), hr=46)]
    if slug == "sinus-tachycardia":
        return [sinus(Strip(), hr=118, pr=0.13, morph=M(t=(0.28, 0.24, 0.045, 0.035)))]
    if slug == "sinus-arrhythmia":
        return [sinus(Strip(), rr=lambda k: 0.85 + 0.22 * math.sin(k * 1.1))]
    if slug == "if-ecg-is-normal-is-my-heart-ok":
        return [sinus(Strip(), hr=70)]
    if slug == "sinus-rhythm-with-pac":
        s = Strip()
        for t in [0.35, 1.18, 2.01]:
            s.p.append((t - 0.16, "normal")); s.q.append((t, N))
        s.p.append((2.62 - 0.14, "biphasic")); s.q.append((2.62, N))  # early PAC
        for t in [3.5, 4.33, 5.16]:
            s.p.append((t - 0.16, "normal")); s.q.append((t, N))
        s.labels.append((2.55, 1.35, "PAC"))
        return [s]
    if slug == "sinus-pause-arrest":
        s = Strip(dur=7.0)
        for t in [0.35, 1.2, 2.05, 4.75, 5.6, 6.45]:
            s.p.append((t - 0.16, "normal")); s.q.append((t, N))
        s.brackets.append((2.05, 4.75, -0.75, "pause 2.7 s"))
        return [s]
    if slug == "ectopic-atrial-rhythm":
        return [sinus(Strip(), hr=68, pr=0.14, pkind="inverted")]
    if slug in ("wandering-atrial-pacemaker", "multifocal-atrial-tachycardia"):
        s = Strip()
        kinds = ["normal", "inverted", "peaked", "biphasic", "small", "mitrale"]
        hr = 80 if slug.startswith("wandering") else 118
        t = 0.35; k = 0
        while t < s.dur - 0.25:
            kind = kinds[k % len(kinds)]
            pr = [0.16, 0.12, 0.19, 0.14, 0.17, 0.13][k % 6]
            s.p.append((t - pr, kind)); s.q.append((t, M(t=(0.28, 0.26, 0.05, 0.038))))
            t += 60 / hr * R.uniform(0.85, 1.15); k += 1
        return [s]
    if slug == "atrial-tachycardia":
        return [sinus(Strip(), hr=160, pr=0.12, pkind="tall_narrow",
                      morph=M(t=(0.22, 0.22, 0.04, 0.03)))]
    if slug == "atrial-fibrillation":
        s = Strip()
        t = 0.3
        while t < s.dur - 0.25:
            s.q.append((t, M(t=(0.22, 0.27, 0.05, 0.04)))); t += R.uniform(0.42, 1.05)
        ph = [R.uniform(0, 6.28) for _ in range(3)]
        s.base = lambda x: 0.035 * math.sin(2 * math.pi * 6.3 * x + ph[0]) + 0.025 * math.sin(2 * math.pi * 8.1 * x + ph[1]) + 0.02 * math.sin(2 * math.pi * 4.7 * x + ph[2])
        return [s]
    if slug == "atrial-flutter":
        s = Strip()
        f = 5.0  # 300/min
        def saw(x):
            ph = (x * f) % 1.0
            return -0.32 * (ph if ph < 0.75 else (1 - ph) * 3) + 0.12
        s.base = saw
        t = 0.36
        while t < s.dur - 0.25:
            s.q.append((t, M(t=(0.12, 0.25, 0.05, 0.04)))); t += 0.8  # 4:1
        return [s]
    if slug == "junctional-rhythm":
        return [sinus(Strip(), hr=48, pr=0, pkind=None)]
    if slug == "accelerated-junctional-rhythm":
        s = Strip(); t = 0.35
        while t < s.dur - 0.25:
            s.q.append((t, N)); s.p.append((t + 0.09, "inverted")); t += 60 / 82
        return [s]
    if slug == "junctional-tachycardia":
        s = Strip(); t = 0.3
        while t < s.dur - 0.25:
            s.q.append((t, M(t=(0.25, 0.22, 0.04, 0.032)))); t += 60 / 128
        return [s]
    if slug == "idioventricular-rhythm":
        s = Strip(); t = 0.4
        while t < s.dur - 0.3:
            s.q.append((t, PVC)); t += 60 / 38
        return [s]
    if slug in ("bigeminy", "trigeminy"):
        s = Strip(dur=7.0); t = 0.35; k = 0
        n = 2 if slug == "bigeminy" else 3
        while t < s.dur - 0.4:
            if k % n == n - 1:
                s.q.append((t, PVC)); s.labels.append((t + 0.07, 1.45, "PVC")); t += 1.2
            else:
                s.p.append((t - 0.16, "normal")); s.q.append((t, N)); t += 0.6 if (k % n == n - 2) else 0.82
            k += 1
        return [s]
    if slug == "first-degree-av-block":
        s = sinus(Strip(), hr=70, pr=0.30)
        s.brackets.append((0.05 + 60/70, 0.35 + 60/70, -0.55, "PR 300 ms"))
        return [s]
    if slug == "second-degree-av-block-type-1":
        s = Strip(dur=7.5); t = 0.3
        for cycle in range(2):
            for pr in (0.18, 0.28, 0.34):
                s.p.append((t, "normal")); s.q.append((t + pr, N)); t += 0.8
            s.p.append((t, "normal")); s.labels.append((t + 0.05, 0.45, "dropped")); t += 0.8
        return [s]
    if slug == "second-degree-av-block-type-2":
        s = Strip(dur=7.0); t = 0.3; m = M(qrs=wide(N["qrs"], 1.35), j=0.12)
        for k in range(8):
            s.p.append((t, "normal"))
            if k in (3, 7):
                s.labels.append((t + 0.05, 0.45, "dropped"))
            else:
                s.q.append((t + 0.18, m))
            t += 0.82
        return [s]
    if slug == "2-1-av-block":
        s = Strip(); t = 0.25
        for k in range(9):
            s.p.append((t, "normal"))
            if k % 2 == 0: s.q.append((t + 0.18, N))
            else: s.labels.append((t + 0.05, 0.45, "P"))
            t += 0.66
        return [s]
    if slug == "third-degree-av-block":
        s = Strip(dur=7.0); t = 0.12
        while t < s.dur - 0.1:
            s.p.append((t, "tall_narrow")); s.labels.append((t + 0.04, 0.42, "P")); t += 0.72
        t = 0.55; m = M(qrs=wide([(1.0, 0.05, 0.022), (-0.3, 0.11, 0.02)], 1.0), j=0.14, t=(-0.3, 0.36, 0.06, 0.05))
        while t < s.dur - 0.4:
            s.q.append((t, m)); t += 1.63
        return [s]
    if slug == "right-bundle-branch-block":
        m = M(qrs=[(0.28, 0.025, 0.010), (-0.32, 0.058, 0.011), (0.85, 0.105, 0.018)], j=0.13, t=(-0.22, 0.32, 0.06, 0.045))
        return [sinus(Strip(lead="V1"), hr=72, morph=m, pkind="biphasic")]
    if slug == "left-bundle-branch-block":
        m = M(qrs=[(0.85, 0.045, 0.022), (0.9, 0.105, 0.022)], j=0.15, st=-0.12, t=(-0.32, 0.36, 0.06, 0.05))
        return [sinus(Strip(lead="V6"), hr=72, morph=m)]
    if slug == "intraventricular-conduction-delay":
        m = M(qrs=wide(N["qrs"], 1.75), j=0.15, t=(0.25, 0.34, 0.06, 0.045))
        return [sinus(Strip(lead="V5"), hr=72, morph=m)]
    if slug == "left-anterior-fascicular-block":
        rS = M(qrs=[(0.25, 0.025, 0.01), (-0.9, 0.06, 0.013)], t=(0.18, 0.30, 0.055, 0.04))
        qR = M(qrs=[(-0.12, 0.012, 0.007), (0.9, 0.04, 0.011), (-0.05, 0.07, 0.01)])
        return [panel([("I", one_beat(qR, lead="I", dur=1.5)), ("II", one_beat(rS, lead="II", dur=1.5)),
                       ("aVF", one_beat(rS, lead="aVF", dur=1.5)), ("aVL", one_beat(qR, lead="aVL", dur=1.5))])]
    if slug == "left-posterior-fascicular-block":
        rS = M(qrs=[(0.2, 0.025, 0.01), (-0.75, 0.06, 0.013)], t=(0.15, 0.30, 0.055, 0.04))
        qR = M(qrs=[(-0.12, 0.012, 0.007), (1.1, 0.04, 0.011), (-0.05, 0.07, 0.01)])
        return [panel([("I", one_beat(rS, lead="I", dur=1.5)), ("aVL", one_beat(rS, lead="aVL", dur=1.5)),
                       ("III", one_beat(qR, lead="III", dur=1.5)), ("aVF", one_beat(qR, lead="aVF", dur=1.5))])]
    if slug in ("left-axis-deviation", "right-axis-deviation"):
        pos = N; neg = M(qrs=[(0.2, 0.03, 0.01), (-0.85, 0.06, 0.013)], t=(0.15, 0.3, 0.055, 0.04))
        if slug == "left-axis-deviation":
            return [panel([("I", one_beat(pos, lead="I", dur=1.5)), ("II", one_beat(neg, lead="II", dur=1.5)), ("aVF", one_beat(neg, lead="aVF", dur=1.5))])]
        return [panel([("I", one_beat(neg, lead="I", dur=1.5)), ("II", one_beat(pos, lead="II", dur=1.5)), ("aVF", one_beat(pos, lead="aVF", dur=1.5))])]
    if slug == "pr-interval":
        s = one_beat(dur=1.9, at=0.6); s.brackets.append((0.44, 0.60, -0.5, "PR 120–200 ms"))
        return [s]
    if slug == "short-pr-interval":
        s = sinus(Strip(), hr=72, pr=0.10); s.brackets.append((0.25 + 60/72, 0.35 + 60/72, -0.5, "PR 100 ms"))
        return [s]
    if slug == "delta-wave":
        m = M(qrs=[(0.32, 0.035, 0.024), (0.8, 0.085, 0.012), (-0.12, 0.11, 0.01)], j=0.13)
        s = sinus(Strip(), hr=72, pr=0.10, morph=m); s.labels.append((0.35 + 60/72 - 0.17, 0.62, "delta"))
        return [s]
    if slug == "qrs-interval":
        s = one_beat(dur=1.9, at=0.6); s.brackets.append((0.6, 0.69, -0.55, "QRS under 120 ms"))
        return [s]
    if slug == "qt-interval":
        s = one_beat(dur=1.9, at=0.6); s.brackets.append((0.6, 1.0, -0.55, "QT interval"))
        return [s]
    if slug in ("what-is-an-ekg", "how-to-read-ecg-report", "abnormal-ecg", "borderline-ecg", "ekg-vs-echocardiogram", "normal-ecg-values"):
        s = one_beat(dur=1.9, top=1.4, bottom=1.5, at=0.6)
        s.labels += [(0.49, 0.3, "P"), (0.638, 1.12, "R"), (0.57, -0.28, "Q"), (0.7, -0.38, "S"), (0.9, 0.45, "T")]
        s.brackets += [(0.44, 0.60, -0.62, "PR"), (0.6, 1.0, -1.05, "QT")]
        return [s]
    if slug == "st-elevation":
        return [sinus(Strip(lead="V2"), hr=78, morph=M(qrs=[(0.5, 0.035, 0.01), (-0.35, 0.065, 0.011)], st=0.42, st_shape="flat", t=(0.45, 0.29, 0.07, 0.045)))]
    if slug == "st-depression":
        return [sinus(Strip(lead="V5"), hr=72, morph=M(st=-0.2, st_shape="down", t=(0.08, 0.36, 0.05, 0.04)))]
    if slug in ("t-wave-inversion",):
        return [sinus(Strip(lead="V3"), hr=72, morph=M(t=(-0.32, 0.30, 0.055, 0.045)))]
    if slug == "nonspecific-t-wave-abnormality":
        return [sinus(Strip(lead="V5"), hr=72, morph=M(t=(0.06, 0.30, 0.06, 0.05)))]
    if slug == "peaked-t-waves":
        return [sinus(Strip(lead="V3"), hr=72, morph=M(t=(0.95, 0.27, 0.035, 0.03)))]
    if slug == "biphasic-t-wave":
        return [sinus(Strip(lead="V2"), hr=72, morph=M(t=(0.22, 0.24, 0.035, 0.03), t2=(-0.25, 0.34, 0.035)))]
    if slug == "u-wave":
        s = sinus(Strip(lead="V3"), hr=66, morph=M(t=(0.16, 0.30, 0.05, 0.04), u=0.14))
        s.labels.append((0.35 + 0.47, 0.4, "U"))
        return [s]
    if slug == "osborn-wave":
        s = sinus(Strip(lead="V4"), hr=48, morph=M(jwave=0.38, t=(0.2, 0.34, 0.06, 0.045)))
        s.labels.append((0.35 + 0.1, 1.2, "J"))
        return [s]
    if slug == "electrical-alternans":
        s = Strip(); t = 0.3; k = 0
        while t < s.dur - 0.25:
            amp = 1.0 if k % 2 == 0 else 0.55
            s.p.append((t - 0.14, "normal")); s.q.append((t, M(qrs=[(-0.05, 0.012, 0.007), (amp, 0.038, 0.01), (-0.15, 0.066, 0.01)], t=(0.2, 0.25, 0.045, 0.035))))
            t += 60 / 110; k += 1
        return [s]
    if slug == "s1q3t3":
        I = M(qrs=[(0.55, 0.035, 0.01), (-0.45, 0.07, 0.012)])
        III = M(qrs=[(-0.3, 0.015, 0.009), (0.45, 0.045, 0.011)], t=(-0.22, 0.3, 0.055, 0.045))
        b1 = one_beat(I, lead="I", dur=1.5); b1.labels.append((0.37, -0.75, "S"))
        b3 = one_beat(III, lead="III", dur=1.5); b3.labels.append((0.31, -0.6, "Q")); b3.labels.append((0.6, -0.6, "T"))
        return [panel([("I", b1), ("III", b3)])]
    if slug == "early-repolarization":
        return [sinus(Strip(lead="V4"), hr=62, morph=M(jwave=0.12, st=0.17, st_shape="concave", t=(0.55, 0.31, 0.06, 0.045)))]
    if slug == "pericarditis-ecg":
        s = Strip(); t = 0.35
        m = M(st=0.26, st_shape="concave", t=(0.42, 0.30, 0.06, 0.045))
        while t < s.dur - 0.25:
            s.p.append((t - 0.16, "normal")); s.q.append((t, m)); t += 60 / 92
        s.base = lambda x: 0.0
        # PR depression: small negative segment before each QRS
        orig = s.q[:]
        s.p = [(pt, "normal") for pt, _ in s.p]
        def prdep(x, qs=[q[0] for q in orig]):
            return sum(-0.11 * sig((x - (q - 0.09)) / 0.008) * sig((q - 0.005 - x) / 0.008) for q in qs)
        s.base = prdep
        return [s]
    if slug in ("septal-infarct", "anteroseptal-infarct", "anterior-infarct-age-undetermined"):
        QS = M(qrs=[(-0.9, 0.045, 0.016)], t=(0.18, 0.3, 0.055, 0.045))
        rs = M(qrs=[(0.15, 0.025, 0.01), (-0.8, 0.06, 0.014)])
        RS = M(qrs=[(0.6, 0.035, 0.011), (-0.6, 0.065, 0.012)])
        leads = {"septal-infarct": [("V1", QS), ("V2", QS), ("V3", RS), ("V4", N)],
                 "anteroseptal-infarct": [("V1", QS), ("V2", QS), ("V3", QS), ("V4", RS)],
                 "anterior-infarct-age-undetermined": [("V1", rs), ("V2", QS), ("V3", QS), ("V4", QS)]}[slug]
        return [panel([(l, one_beat(m, lead=l, dur=1.5)) for l, m in leads])]
    if slug in ("inferior-infarct-age-undetermined", "lateral-infarct"):
        Q = M(qrs=[(-0.45, 0.025, 0.014), (0.6, 0.07, 0.012), (-0.05, 0.095, 0.01)], j=0.11, t=(-0.12, 0.31, 0.055, 0.045))
        leads = [("II", Q), ("III", Q), ("aVF", Q)] if slug.startswith("inferior") else [("I", Q), ("aVL", Q), ("V6", Q)]
        return [panel([(l, one_beat(m, lead=l, dur=1.5)) for l, m in leads])]
    if slug == "poor-r-wave-progression":
        seq = [0.08, 0.12, 0.16, 0.22, 0.5, 0.8]
        return [panel([(f"V{i+1}", one_beat(M(qrs=[(r, 0.03, 0.01), (-(0.9 - r), 0.06, 0.013)]), lead=f"V{i+1}", dur=1.0)) for i, r in enumerate(seq)])]
    if slug == "left-atrial-enlargement":
        s = sinus(Strip(), hr=70, pr=0.22, pkind="mitrale"); s.labels.append((0.35 + 60/70 - 0.30, 0.55, "notched P"))
        return [s]
    if slug == "right-atrial-enlargement":
        s = sinus(Strip(), hr=72, pkind="peaked"); s.labels.append((0.35 + 60/72 - 0.27, 0.62, "tall P"))
        return [s]
    if slug == "left-ventricular-hypertrophy":
        m = M(qrs=[(-0.1, 0.012, 0.007), (2.6, 0.042, 0.011), (-0.2, 0.072, 0.01)], j=0.1, st=-0.12, t=(-0.25, 0.32, 0.06, 0.045))
        return [sinus(Strip(lead="V5", top=2.8, bottom=0.8), hr=70, morph=m)]
    if slug == "right-ventricular-hypertrophy":
        m = M(qrs=[(1.1, 0.04, 0.012), (-0.25, 0.075, 0.011)], st=-0.06, t=(-0.22, 0.31, 0.055, 0.045))
        return [sinus(Strip(lead="V1"), hr=78, morph=m, pkind="peaked")]
    if slug == "low-voltage-qrs":
        m = M(qrs=[(-0.03, 0.012, 0.007), (0.35, 0.038, 0.01), (-0.08, 0.066, 0.01)], t=(0.1, 0.3, 0.055, 0.04))
        return [sinus(Strip(lead="II", top=1.1, bottom=0.8), hr=76, morph=m, pkind="small")]
    if slug == "pvc-vs-pac":
        s = Strip(dur=7.0)
        for t in [0.35, 1.17]:
            s.p.append((t - 0.16, "normal")); s.q.append((t, N))
        s.p.append((1.77 - 0.14, "biphasic")); s.q.append((1.77, N)); s.labels.append((1.72, 1.35, "PAC"))
        for t in [2.6, 3.42]:
            s.p.append((t - 0.16, "normal")); s.q.append((t, N))
        s.q.append((4.0, PVC)); s.labels.append((4.07, 1.45, "PVC"))
        for t in [5.06, 5.88]:
            s.p.append((t - 0.16, "normal")); s.q.append((t, N))
        return [s]
    if slug == "svt-vs-vtach":
        a = Strip(dur=5.0, lead="SVT"); t = 0.3
        while t < a.dur - 0.2:
            a.q.append((t, M(t=(0.22, 0.2, 0.035, 0.03)))); t += 60 / 170
        b = Strip(dur=5.0, lead="VT", top=1.6, bottom=1.1); t = 0.3
        vt = M(qrs=[(1.1, 0.07, 0.03), (-0.6, 0.15, 0.03)], j=0.19, t=(-0.2, 0.25, 0.04, 0.03))
        while t < b.dur - 0.25:
            b.q.append((t, vt)); t += 60 / 170
        return [a, b]
    return None

# alt text / caption (what the drawing shows)
DESCR = {
 "sinus-rhythm": "regular sinus rhythm at about 72 beats per minute, every QRS preceded by an upright P wave",
 "sinus-bradycardia": "regular sinus rhythm at about 46 beats per minute with normal P waves",
 "sinus-tachycardia": "regular sinus rhythm at about 118 beats per minute with normal P waves",
 "sinus-arrhythmia": "sinus rhythm whose beat-to-beat spacing gently speeds up and slows down",
 "if-ecg-is-normal-is-my-heart-ok": "a normal ECG strip in sinus rhythm",
 "sinus-rhythm-with-pac": "sinus rhythm with one early beat that has a differently shaped P wave (a PAC)",
 "sinus-pause-arrest": "sinus rhythm interrupted by a pause of about 2.7 seconds with no P wave",
 "ectopic-atrial-rhythm": "regular rhythm with inverted P waves in lead II before each QRS",
 "wandering-atrial-pacemaker": "rhythm under 100 per minute with P waves that change shape from beat to beat",
 "multifocal-atrial-tachycardia": "irregular rhythm over 100 per minute with at least three different P-wave shapes",
 "atrial-tachycardia": "fast regular rhythm around 160 per minute with abnormal-looking P waves",
 "atrial-fibrillation": "irregularly irregular rhythm with no P waves and a wavy fibrillatory baseline",
 "atrial-flutter": "sawtooth flutter waves at 300 per minute with a QRS after every fourth wave",
 "junctional-rhythm": "slow regular narrow-complex rhythm at about 48 per minute with no visible P waves",
 "accelerated-junctional-rhythm": "regular narrow-complex rhythm around 82 per minute with inverted P waves just after each QRS",
 "junctional-tachycardia": "fast regular narrow-complex rhythm around 128 per minute without visible P waves",
 "idioventricular-rhythm": "slow regular rhythm of wide, bizarre QRS complexes with no P waves",
 "bigeminy": "every second beat is a wide, early premature ventricular complex (PVC)",
 "trigeminy": "every third beat is a wide, early premature ventricular complex (PVC)",
 "first-degree-av-block": "sinus rhythm with a long but constant PR interval of about 300 ms",
 "second-degree-av-block-type-1": "PR interval lengthening beat by beat until one P wave is not followed by a QRS (Wenckebach)",
 "second-degree-av-block-type-2": "constant PR interval with occasional P waves suddenly not conducted (Mobitz II)",
 "2-1-av-block": "every second P wave not followed by a QRS (2:1 conduction)",
 "third-degree-av-block": "P waves and wide QRS complexes marching independently of each other (complete heart block)",
 "right-bundle-branch-block": "lead V1 with a wide rSR' ('M-shaped') QRS and an inverted T wave",
 "left-bundle-branch-block": "lead V6 with a broad, notched R wave and a T wave pointing the opposite way",
 "intraventricular-conduction-delay": "a QRS complex wider than normal without a typical bundle branch block shape",
 "left-anterior-fascicular-block": "upright qR complexes in I and aVL with deep rS complexes in II and aVF",
 "left-posterior-fascicular-block": "rS complexes in I and aVL with tall qR complexes in III and aVF",
 "left-axis-deviation": "upright QRS in lead I with mainly negative QRS complexes in II and aVF",
 "right-axis-deviation": "mainly negative QRS in lead I with upright QRS complexes in II and aVF",
 "pr-interval": "one heartbeat with the PR interval marked from the start of the P wave to the start of the QRS",
 "short-pr-interval": "sinus rhythm with a short PR interval of about 100 ms",
 "delta-wave": "short PR interval with a slurred upstroke (delta wave) at the start of a widened QRS",
 "qrs-interval": "one heartbeat with the QRS duration marked",
 "qt-interval": "one heartbeat with the QT interval marked from the start of the QRS to the end of the T wave",
 "what-is-an-ekg": "one heartbeat labelled P, Q, R, S and T with the PR and QT intervals marked",
 "how-to-read-ecg-report": "one heartbeat labelled P, Q, R, S and T with the PR and QT intervals marked",
 "abnormal-ecg": "a normal heartbeat labelled P, Q, R, S and T, the reference that report findings are judged against",
 "borderline-ecg": "a normal heartbeat labelled P, Q, R, S and T, the reference that report findings are judged against",
 "ekg-vs-echocardiogram": "one EKG heartbeat labelled P, Q, R, S and T, the electrical signal an EKG records",
 "st-elevation": "lead V2 with the ST segment raised well above the baseline",
 "st-depression": "lead V5 with a horizontal-to-downsloping ST segment pushed below the baseline",
 "t-wave-inversion": "lead V3 with T waves pointing downward",
 "nonspecific-t-wave-abnormality": "lead V5 with low, flattened T waves",
 "peaked-t-waves": "lead V3 with tall, narrow, pointed T waves",
 "biphasic-t-wave": "lead V2 with T waves that go up and then down",
 "u-wave": "lead V3 with a small extra U wave after a flattened T wave",
 "osborn-wave": "slow rhythm with a hump (Osborn or J wave) at the end of each QRS",
 "electrical-alternans": "QRS height alternating tall and short from beat to beat",
 "s1q3t3": "an S wave in lead I with a Q wave and an inverted T wave in lead III",
 "early-repolarization": "lead V4 with a notched J point, concave ST elevation and tall T waves",
 "pericarditis-ecg": "lead II with widespread concave ST elevation and PR-segment depression (lead aVR typically shows the mirror image)",
 "septal-infarct": "QS complexes (no R wave) in V1 and V2 with normal R waves in V3 and V4",
 "anteroseptal-infarct": "QS complexes in V1 to V3 with an R wave returning in V4",
 "anterior-infarct-age-undetermined": "QS complexes across V2 to V4",
 "inferior-infarct-age-undetermined": "wide Q waves with inverted T waves in leads II, III and aVF",
 "lateral-infarct": "wide Q waves with inverted T waves in leads I, aVL and V6",
 "poor-r-wave-progression": "R waves that stay small from V1 to V4 before growing in V5 and V6",
 "left-atrial-enlargement": "broad, notched P waves (P mitrale) in lead II",
 "right-atrial-enlargement": "tall, peaked P waves (P pulmonale) in lead II",
 "left-ventricular-hypertrophy": "very tall R waves in V5 with downsloping ST depression and inverted T waves (strain)",
 "right-ventricular-hypertrophy": "a dominant tall R wave in V1 with an inverted T wave",
 "low-voltage-qrs": "QRS complexes much smaller than usual",
 "pvc-vs-pac": "sinus rhythm with one early narrow beat (PAC) and one early wide beat (PVC)",
 "normal-ecg-values": "one normal heartbeat labelled P, Q, R, S and T with the PR and QT intervals marked",
 "svt-vs-vtach": "a fast narrow-complex rhythm (SVT, top) compared with a fast wide-complex rhythm (VT, bottom)",
}

LEAD_NOTE = {}
