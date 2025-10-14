# camapp/utils.py
import numpy as np
import pandas as pd
from io import BytesIO
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from math import pi

# 100 birim = 1 saniye
TIME_UNITS_PER_SECOND = 100.0

PROFILES = [
    "Straight line",
    "Quadratic parabola",
    "Polynomial of 5th degree",
    "Simple sinus",
    "Modified sinus",
]

# ---------------- Core helpers ----------------
def normalized_logistic(u, lam, C):
    """Yumuşak merkez kaydırma (λ). C'ye bağlı ılımlı eğim."""
    k = 2.0 + 8.0*float(C)     # çok agresif değil
    g  = 1.0/(1.0 + np.exp(-k*(u - lam)))
    g0 = 1.0/(1.0 + np.exp(-k*(0 - lam)))
    g1 = 1.0/(1.0 + np.exp(-k*(1 - lam)))
    return (g - g0) / (g1 - g0 + 1e-12)

def base_profile(u, profile, C):
    """0→1 aralığında şekil. C bazı profillerde keskinliği etkiler."""
    if profile == "Straight line":
        return u
    elif profile == "Quadratic parabola":
        return np.where(u < 0.5, 2*u*u, 1 - 2*(1-u)*(1-u))
    elif profile == "Polynomial of 5th degree":
        return 10*u**3 - 15*u**4 + 6*u**5
    elif profile == "Simple sinus":
        return 0.5 - 0.5*np.cos(pi*u)
    elif profile == "Modified sinus":
        p = 1 + 9*float(C)  # C↑ → daha keskin orta
        s = 0.5 - 0.5*np.cos(pi*u)
        sp = np.power(s, p)
        mn, mx = sp.min(), sp.max()
        return (sp - mn)/((mx - mn) + 1e-12)
    return u

def cam_profile_01(u, profile, lam, C):
    # λ=0.5 ise kaydırma yok, değilse yumuşak lojistik bükme
    if abs(lam - 0.5) < 1e-9:
        w = u
    else:
        w = normalized_logistic(u, lam, C)
    f = base_profile(w, profile, C)
    # C=0 → lineer; C=1 → tamamen seçilen profil
    return (1 - C)*w + C*f

# ---------------- Absolute table helpers ----------------
def convert_absolute_rows(rows):
    """
    rows: [{Time(abs unit), Position(abs mm), Lambda, C, Motion Profile}, ...]
    → süre/artış tablosu döndürür.
    """
    out = []
    if not rows:
        return out
    prev_t = 0.0
    prev_x = 0.0
    for i, r in enumerate(rows, 1):
        t_abs = float(r["Time"])
        x_abs = float(r["Position"])
        if t_abs < prev_t:
            raise ValueError(f"Time must be non-decreasing in row {i} (got {t_abs} < {prev_t}).")
        dt_unit = t_abs - prev_t
        dx_mm   = x_abs - prev_x
        out.append({
            "Time": dt_unit,                 # Δt (unit)
            "Position": dx_mm,               # Δx (mm)
            "Lambda": float(r["Lambda"]),
            "C": float(r["C"]),
            "Motion Profile": r["Motion Profile"],
        })
        prev_t = t_abs
        prev_x = x_abs
    return out

# ---------------- Segment generation & stitching ----------------
def generate_segment(T_unit, X_mm, lam, C, profile, npts=100, t0=0.0, x0=0.0):
    n = max(2, int(npts))
    u = np.linspace(0, 1, n)
    s01 = cam_profile_01(u, profile, lam, C)
    T_sec = float(T_unit) / TIME_UNITS_PER_SECOND  # 100→1.0 s
    t = t0 + T_sec * u
    x = x0 + X_mm * s01
    return t, x

def stitch_segments(rows, npts_per_seg=100):
    times, poss, seg_id = [], [], []
    t0 = 0.0
    x0 = 0.0
    for i, r in enumerate(rows, 1):
        T = float(r["Time"])
        X = float(r["Position"])
        lam = float(r["Lambda"])
        C   = float(r["C"])
        prof = r["Motion Profile"]

        t, x = generate_segment(T, X, lam, C, prof, npts=npts_per_seg, t0=t0, x0=x0)

        # ardışık segmentte tekrarlayan ilk örneği at
        if i > 1:
            t = t[1:]
            x = x[1:]

        times.append(t)
        poss.append(x)
        seg_id.extend([i]*len(t))
        t0 = t[-1]
        x0 = x[-1]

    if not times:
        return None

    t = np.concatenate(times)
    x = np.concatenate(poss)

    v = np.gradient(x, t)
    a = np.gradient(v, t)
    j = np.gradient(a, t)

    df = pd.DataFrame({
        "Index": np.arange(1, len(t)+1),
        "Segment": seg_id,
        "t [s]": t,
        "pos [mm]": x,
        "vel [mm/s]": v,
        "acc [mm/s^2]": a,
        "jerk [mm/s^3]": j,
    })
    return df

# ---------------- Plot helpers ----------------
def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return "data:image/png;base64," + b64

def make_plots(df):
    t = df["t [s]"].values
    x = df["pos [mm]"].values
    v = df["vel [mm/s]"].values
    a = df["acc [mm/s^2]"].values

    fig1 = plt.figure(figsize=(7,3)); ax1 = fig1.gca()
    ax1.plot(t, x, label="Position [mm]"); ax1.set_xlabel("Time [s]"); ax1.set_ylabel("Position [mm]"); ax1.grid(True); ax1.legend()

    fig2 = plt.figure(figsize=(7,3)); ax2 = fig2.gca()
    ax2.plot(t, v, label="Velocity [mm/s]"); ax2.set_xlabel("Time [s]"); ax2.set_ylabel("Velocity [mm/s]"); ax2.grid(True); ax2.legend()

    fig3 = plt.figure(figsize=(7,3)); ax3 = fig3.gca()
    ax3.plot(t, a, label="Acceleration [mm/s²]"); ax3.set_xlabel("Time [s]"); ax3.set_ylabel("Acceleration [mm/s²]"); ax3.grid(True); ax3.legend()

    return fig_to_base64(fig1), fig_to_base64(fig2), fig_to_base64(fig3)
