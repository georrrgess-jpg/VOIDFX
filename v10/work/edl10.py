"""LET IT HAPPEN — The Flash × Tame Impala "Let It Happen" (voidfx v10, 9:16). Single source of truth: the renderer,
audio builder and QC read only this file.

Concept: "Let it happen." Barry Allen stops holding on. In the quiet before the storm he stands calm in the dark lab,
looks up, smiles, turns in red light, his own lightning ignites along his suit (rev 2: replaces the lit-up eyes),
the Speed Force crawls over him; on the drop the camera dives through the bolt of
his emblem and he is gone. The hunt of light (throw, run, scream), then LET IT / HAPPEN struck letter by letter by
lightning. A bolt hits him, and on the song's own gated stutter TIME STOPS: the world freezes between beats while he
moves through it. "All this running around": he runs so fast he leaves afterimages, becomes a streak of light and
outruns time itself; the whole edit rewinds and he is back in the dark lab where it began (the loop).
Look: PRISM SPEED (new): graphite-slate shadows, rich suit crimson, white-gold lightning with bloom, a prismatic
time-slice (RGB channels split across time) on the fastest moments; the frozen world drains to steel with gold sparks.
Type: the approved v9 text system (bold keyline captions, per-letter hero title), recoloured: lightning-gold emphasis.

Song: src/let_it_happen.mp3 (radio edit, 4:16), 125.0 BPM, half-beat P = 0.24003 s, offset 0.1920 (grid verified
across the window). Window h392 -> h496 (94.32 -> 119.28 s, 13 bars, 24.96 s):
  94.32  the bass-less "whirlwind" breakdown, "It's gonna carry off all that isn't bound"   (cold open, build)
 100.26  "And when..."   101.94 DROP (bass returns, +26.5 dB): "...it happens, when it happens"
 107.68  "So let it happen, let it happen"                                                 (hero title)
 112.04  the gated stutter (the music cuts out every 4th half-beat)                         (time freeze)
 115.41  second impact (+15 dB): "All this running around"                                  (afterimage run)
 119.28  bar line before "I can't fight it..."                                             (rewind -> loop)
Edit half-beat e = song half-beat - 392.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v10", "let_it_happen_flash"
SONG = f"{ROOT}/src/let_it_happen.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/let_it_happen"
FPS, W, H = 60, 1080, 1920
SRC = {"fb": (f"{ROOT}/src/flash_b.mp4", 60.0, 1280, 720)}          # 24p content in a 60 fps container (hold cadence)

HB, HB_OFF = 0.24002757, 0.19202206
H0, H1 = 392, 496
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 32; DROP_HB = HDROP; T_STOP = DUR
E_STUT, E_RUN, E_REW = 74, 88, 100            # the gated stutter, the second impact, the rewind
STUT_GAPS = [75, 79, 83, 87]                  # half-beats where the music drops out (freeze), song h467/471/475/479
STUT_HITS = [76, 80, 84]                      # half-beats where it kicks back in (time jolts forward)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []                                       # the packs carry no usable dialogue; music-driven
VO_STEM = None; VO_STEM_T0 = 0.0

# ---- lyric word times (song seconds). rev 3: every word re-timed to its sung onset on the Demucs vocal stem (pitch
#      track + spectral-flux onsets, cross-checked with Whisper in short windows and the line's parallel phrasing):
#      Whisper ran ~0.1-0.2 s late on held notes, and "All this running around" starts at 116.36 (the vocal is silent
#      from 114.9), not 115.24. Backing "(I won't be holding on)" stays off screen.
W_CARRY = [("IT'S", 95.45), ("GONNA", 96.47), ("CARRY", 96.74), ("OFF", 97.15)]
W_BOUND = [("ALL", 97.64), ("THAT", 98.15), ("ISN'T", 98.87), ("BOUND", 99.62)]
W_AND = [("AND", 100.06), ("WHEN", 101.53)]
W_HAP1 = [("IT", 102.49), ("HAPPENS", 102.61)]
W_HAP2 = [("WHEN", 103.33), ("IT", 104.38), ("HAPPENS", 104.50)]
W_LET = [("LET", 107.97), ("IT", 108.24), ("HAPPEN", 108.33)]
W_LET2 = [("LET", 109.08), ("IT", 110.10), ("HAPPEN", 110.25)]
W_RUN = [("ALL", 116.36), ("THIS", 116.92), ("RUNNING", 117.36), ("AROUND", 117.93)]

def vel(e0, e1, a, b, lo=0.30, hi=3.2, tau=0.07, n=96):
    """rev 5 velocity: a speed burst on every beat of the shot (the cut included), smooth slow motion between beats;
    the same source range a..b as before, so the speeds scale to fit (burst ~3-4.5x, slow-mo ~0.3-0.6x)."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); sp = _np.full_like(ts, lo)
    for e in range(e0, e1):
        if e % 2 == 0:
            tb = th(e) - th(e0); sp = sp + (hi - lo) * _np.exp(-_np.clip(ts - tb, 0, None) / tau) * (ts >= tb)
    src = _np.concatenate([[0.0], _np.cumsum((sp[1:] + sp[:-1]) / 2 * _np.diff(ts))]); src /= src[-1]
    return [(float(u), float(a + (b - a) * _np.interp(u * T, ts, src))) for u in _np.linspace(0, 1, n)]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "prism"),
             z=kw.pop("z", [(0, 1.00), (1, 1.07)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- cold open: the calm before the whirlwind (bass-less build)
shot("lab", "fb", 0, 4, 38.62, 39.58, z=[(0, 1.12), (1, 1.18)], tin="tunnel_in", seg=True, arcs=0.35, wind=0.55)
shot("look", "fb", 4, 8, 37.16, 38.12, z=[(0, 1.02), (1, 1.10)], tin="phase", seg=True, arcs=0.3, wind=0.7)
shot("smile", "fb", 8, 12, 34.60, 35.56, z=[(0, 1.00), (1, 1.07)], tin="slices", seg=True, arcs=0.5, wind=0.8)
shot("profile", "fb", 12, 16, 136.50, 137.46, z=[(0, 1.00), (1, 1.08)], tin="whirlwind", seg=True, arcs=0.35, wind=1.0)
shot("ignition", "fb", 16, 24, 52.85, 54.30, z=[(0, 1.00), (1, 1.12)], tin="ignite", interp="blend", seg=True, arcs=0.45, wind=0.8, orbit=1.0, rays=0.7)
shot("charge", "fb", 24, 32, 83.85, 85.05, z=[(0, 1.02), (1, 1.16)], tin="lichtenberg", interp="blend", seg=True, arcs=1.0, wind=0.6, rays=0.6,
     emblem=[(83.95, 731, 462), (84.45, 744, 581), (84.95, 744, 625), (85.05, 745, 632)], emblem_r=42)
# ---- the drop: through the bolt of his emblem; the hunt of light
shot("takeoff", "fb", 32, 38, 4.62, 6.12, z=[(0, 1.14), (1, 1.04)], tin="emblem_gate", seg=True, trails=0.8, sparks=0.7, wave=True,
     tmap=vel(32, 38, 4.62, 6.12), lin=True, interp="flow", rays=0.8)
shot("throw", "fb", 38, 40, 124.40, 124.77, z=[(0, 1.00), (1, 1.06)], tin="ramp", tmap=vel(38, 40, 124.40, 124.77), lin=True, interp="flow", rays=1.0)
shot("garage", "fb", 40, 46, 113.55, 114.99, z=[(0, 1.04), (1, 1.12)], tin="lens_shatter", seg=True, trails=0.7, sparks=0.6,
     tmap=vel(40, 46, 113.55, 114.99), lin=True, interp="flow", rays=0.8)
shot("scream", "fb", 46, 50, 127.70, 128.66, z=[(0, 1.00), (1, 1.08)], tin="shock", tmap=vel(46, 50, 127.70, 128.66), lin=True, interp="flow", rays=0.9)
shot("grin", "fb", 50, 54, 56.30, 57.26, z=[(0, 1.00), (1, 1.05)], tin="perimeter", tmap=vel(50, 54, 56.30, 57.26), lin=True, interp="flow")
shot("turn", "fb", 54, 56, 102.86, 103.34, z=[(0, 1.00), (1, 1.06)], tin="ramp", tmap=vel(54, 56, 102.86, 103.34), lin=True, interp="flow")
shot("hero", "fb", 56, 68, 109.76, 112.42, z=[(0, 1.00), (1, 1.10)], tin="logo_orig", seg=True, arcs=0.45, sparks=0.8, orbit=1.0,
     tmap=vel(56, 68, 109.76, 112.42, lo=0.45, hi=2.4), lin=True, interp="flow")
shot("strike", "fb", 68, 74, 10.36, 11.80, z=[(0, 1.00), (1, 1.08)], tin="bolt_strike", tmap=vel(68, 74, 10.36, 11.80), lin=True, interp="flow", rays=0.6)
# ---- the gated stutter: time stops between the beats (source time only advances on the hits)
#      (the music: e74 low, e75 gap, e76-77 hit, e78 low, e79 gap, e80-81 hit, e82 low, e83 gap, e84-85 hit, e86 low, e87 gap)
shot("freeze_a", "fb", 74, 82, 0, 0, tmap=[(0, 13.00), (2 / 8, 13.00), (4 / 8, 14.60), (6 / 8, 14.60), (1, 16.20)],
     lin=True, z=[(0, 1.00), (1, 1.16)], tin="freeze_in", seg=True, frozen=True, face=None, cx=(870, 880))
shot("freeze_b", "fb", 82, 88, 0, 0, tmap=[(0, 28.10), (2 / 6, 28.10), (4 / 6, 29.40), (1, 29.40)],
     lin=True, z=[(0, 1.06), (1, 1.20)], tin="time_particles", seg=True, frozen=True, face=None, cx=(1000, 960), pfocus=(300, 1250))
# ---- "All this running around": afterimages, then he outruns time
shot("run", "fb", 88, 100, 0, 0, tmap=[(0, 80.86), (8 / 12, 81.95), (1, 82.24)], z=[(0, 1.00), (1, 1.10)], tin="restart", face=None, cx=(560, 520),
     interp="blend", seg=True, trails=1.0, arcs=0.6, streak_e=98)
# ---- the loop: the ring of AROUND opens into the Speed Force; he runs back through the edit's own moments to frame 0
shot("tunnel", "fb", 100, 104, 82.10, 82.24, tin="portal", graphic="tunnel", face=None, cx=(640, 640))
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text: the approved v9 system. cap = keyline captions, slam = one hard-hitting word pair, echo = speed-echo
#      caption, hero = per-letter title struck by lightning, speed = words that arrive with afterimage streaks
TEXT = [
    dict(style="carry", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_CARRY)], end=s2e(97.15) + 0.75, emph=["CARRY", "OFF"]),
    dict(style="bound", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_BOUND)], end=s2e(100.06) - 0.03, emph=["BOUND"],
         band=(1330, 1660)),                     # set 50 px lower: the masked face sits low early in the ignition shot
    dict(style="charge", words=[(w, s2e(t), i) for i, (w, t) in enumerate(W_AND)], end=th(32) + 0.02, emph=["WHEN"], rides=True),
    dict(style="slam", words=[(w, s2e(t), 0 if i == 0 else 1) for i, (w, t) in enumerate(W_HAP1)], end=s2e(103.33) - 0.06, emph=["HAPPENS"]),
    dict(style="echo", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_HAP2)], end=th(46) - 0.07, emph=["HAPPENS"]),
    dict(style="hero", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_LET)], end=th(68) - 0.05, emph=["HAPPEN"],
         pulses=[s2e(t) for _, t in W_LET2]),
    dict(style="speed", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_RUN)], end=th(101) + 0.05, emph=["RUNNING", "AROUND"]),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, E_STUT)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "stutter", round(th(E_STUT), 3), "run", round(th(E_RUN), 3), "rewind", round(th(E_REW), 3))
    for t_ in TEXT: print(f"  {t_['style']:5s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(f"{w}@{t:.2f}" for w, t, _ in t_["words"]))
