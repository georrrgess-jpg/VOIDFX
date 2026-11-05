"""BOP — The Flash × DaBaby "BOP" (voidfx v11, 9:16). Single source of truth: the renderer, audio builder and QC read only
this file. Built on the v10 LET IT HAPPEN standard engine (motion pass, restored source, v9 type construction).

Concept: THE RIVAL. The song's spoken intro says "I mean, they're like, Harrison…" — Harrison Wells, the man who was the
Reverse-Flash. So the cold open belongs to him, in red: Wells' face on the word "Harrison", the beat hits and his
mask's red eyes come up, Thawne smirks, the red lightning leaves. On the dip Barry answers ("Let's go!"), and on the
drop the frame splits along a lightning-bolt seam, red against gold, and the gold side wins. The verse is Barry's
swagger and speed in gold: the smile, the night run, the wedding-fight lightning, a time freeze among the soldiers,
the smirk, the flight through fire (a Speed Force moment), the final stare. Then the red lightning snatches the frame
back to Harrison: the rivalry loops.
Look: VOLTAGE — deep clean blacks, crimson suit, warm gold lightning with bloom, cool teal in the shadows; the rival's
shots go RED (red-shifted highlights, his red lightning and eyes).
Type: almost none (the verse is explicit and the owner asked for few or no subtitles): two designed words, LET'S GO and BOP.

Song: src/bop.mp3 (DaBaby "BOP", 2:40), 127.0 BPM, half-beat P = 0.23622 s, offset 0.1890. Window h32 -> h120
(7.75 -> 28.54 s, 11 bars, 20.79 s):
   7.75  intro talk over the bass-less intro: "I mean, they're like, Harrison (9.60), baby on baby drop, man"
   9.64  the beat drops in (+24.8 dB)                        e8   1.89 s
  13.42  the dip (bass out); "Let's go!" at 14.34             e24  5.67 s   (e28 6.61 s)
  15.31  THE DROP: the verse, "I needed some shit with some bop in it"   e32  7.56 s
  28.54  bar line, between two lines (clean end) -> tape stop -> the loop
Edit half-beat e = song half-beat - 32.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v11", "bop_flash"
SONG = f"{ROOT}/src/bop.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/bop"
FPS, W, H = 60, 1080, 1920
SRC = {"s4": (f"{ROOT}/src/flash_s4.mp4", 60.0, 1280, 720),          # Flash S4 pack (24p content in a 60 fps container)
       "rf": (f"{ROOT}/src/reverse_flash.mp4", 60.0, 1280, 720)}      # Reverse-Flash pack: true 60 fps, a 600x600 inset

HB, HB_OFF = 0.23621950113378684, 0.18897560090702947
H0, H1 = 32, 120
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 32; DROP_HB = HDROP; T_STOP = DUR
E_BEAT = 8                                     # the beat drops in
E_DIP = 24                                     # the dip before the drop
E_LOOP = 82                                    # rev 3: REVERSE — the red strikes his emblem (the beat camera rests from here)
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
VO = []; VO_STEM = None; VO_STEM_T0 = 0.0

def vel(e0, e1, a, b, lo=0.30, hi=3.2, tau=0.07, n=96):
    """velocity: a speed burst on every beat of the shot (the cut included), smooth slow motion between beats."""
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
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "voltage"),
             z=kw.pop("z", [(0, 1.00), (1, 1.07)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

RF = dict(look="rival", face=None)             # the inset: fixed framing inside the 600x600 panel (no watermark)
# ---- cold open: the rival (red)
shot("wells", "rf", 0, 8, 13.05, 13.96, z=[(0, 1.26), (1, 1.36)], cx=(642, 642), interp="flow", tin="loop_in", ev=0.55, ember=0.55, **RF)
shot("rfmask", "rf", 8, 14, 15.02, 15.96, z=[(0, 1.26), (1, 1.40)], cx=(660, 660), interp="flow", tin="red_phase", seg=True, red_arcs=0.6, ember=0.8, **RF)
shot("thawne", "s4", 14, 20, 95.50, 96.72, z=[(0, 1.04), (1, 1.12)], tin="red_link", seg=True, red_arcs=0.5, look="rival", ember=0.6)
shot("eobard", "rf", 20, 24, 34.00, 34.93, z=[(0, 1.26), (1, 1.32)], cx=(640, 640), interp="flow", tin="red_streak", seg=True, red_arcs=0.7, ev=0.25, ember=0.8, **RF)
# ---- the answer: Barry, on the dip ("Let's go!")
shot("answer", "s4", 24, 28, 93.90, 94.84, z=[(0, 1.02), (1, 1.10)], tin="red_eye_dive", seg=True, dust=0.4)
shot("letsgo", "s4", 28, 32, 100.12, 101.00, z=[(0, 1.00), (1, 1.14)], tin="dolly", seg=True, arcs=0.4, dust=0.5)
# ---- THE DROP: red against gold along a lightning-bolt seam; the verse in gold (velocity on every shot)
shot("drop", "s4", 32, 38, 28.70, 30.12, z=[(0, 1.06), (1, 1.00)], tin="bolt_split", seg=True, trails=0.6, arcs=0.5, wave=True, ev=-0.15, speed=0.5,
     tmap=vel(32, 38, 28.70, 30.12), lin=True, interp="flow", rays=0.8)
shot("smile", "s4", 38, 42, 31.40, 32.35, z=[(0, 1.00), (1, 1.06)], tin="strobe_echo", seg=True, arcs=0.3, dust=0.4, aura=1.0,
     tmap=vel(38, 42, 31.40, 32.35), lin=True, interp="flow")
shot("run", "s4", 42, 46, 122.95, 123.45, z=[(0, 1.04), (1, 1.10)], tin="whip", seg=True, ev=-0.55, face=None, cx=(815, 815), speed=1.0, trails=0.35,
     tmap=vel(42, 46, 122.95, 123.45, lo=0.25, hi=1.6), lin=True, interp="flow")
shot("runlow", "s4", 46, 50, 137.20, 138.15, z=[(0, 1.00), (1, 1.06)], tin="bolt_trace", face=None, cx=(500, 540), ev=-0.15, speed=0.45,
     tmap=vel(46, 50, 137.20, 138.15), lin=True, interp="flow")
# the time freeze among the soldiers: time stops on the beat, the camera glides through it (bullet time), time resumes
shot("freeze", "s4", 50, 56, 0, 0, tmap=[(0, 140.95), (1 / 3, 141.40), (2 / 3, 141.40), (1, 141.85)], lin=True, frozen=True,
     z=[(0, 1.02), (1, 1.10)], tin="freeze_in", seg=True, face=None, cx=(470, 470), ev=-0.1, drain=0.45)
shot("smirk", "s4", 56, 60, 62.90, 63.85, z=[(0, 1.00), (1, 1.06)], tin="restart", seg=True, arcs=0.3, dust=0.4, remnants=1.0,
     tmap=vel(56, 60, 62.90, 63.85), lin=True, interp="flow")
shot("bar", "s4", 60, 64, 155.80, 156.75, z=[(0, 1.00), (1, 1.08)], tin="ignite", seg=True, arcs=0.3, charge=1.0,
     tmap=vel(60, 64, 155.80, 156.75), lin=True, interp="flow")
# the Speed Force moment: the flight through fire
shot("firewide", "s4", 64, 70, 171.76, 173.20, z=[(0, 1.00), (1, 1.12)], tin="rift", face=None, cx=(560, 700), ev=-0.55, fire=0.9,
     tmap=vel(64, 70, 171.76, 173.20), lin=True, interp="flow", warp=0.8)
shot("fireclose", "s4", 70, 74, 173.40, 174.35, z=[(0, 1.00), (1, 1.08)], tin="heat_haze", seg=True, ev=-0.25, fire=0.8,
     tmap=vel(70, 74, 173.40, 174.35), lin=True, interp="flow", warp=0.6)
# the gold beats the red: Barry slams Thawne into the pillar
shot("punch", "s4", 74, 78, 90.45, 91.30, z=[(0, 1.06), (1, 1.00)], tin="clash", face=None, cx=(930, 960), ev=0.3,
     tmap=vel(74, 78, 90.45, 91.30), lin=True, interp="flow")
# the final stare; the red lightning takes the frame back to Harrison (the loop)
shot("stare", "s4", 78, 88, 146.40, 147.68, z=[(0, 1.00), (1, 1.12)], tin="emblem_flash", seg=True, orbit=1.0, interp="flow", dust=0.6)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text: two designed words only
TEXT = [
    dict(style="letsgo", words=[("LET'S", s2e(14.34), 0), ("GO", s2e(14.70), 0)], end=th(HDROP) - 0.02, emph=["GO"], rides=True),
    dict(style="bop", words=[("BOP", s2e(17.52), 0)], end=th(45), emph=["BOP"]),
]
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, H1 - H0)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3))
    for t_ in TEXT: print(f"  {t_['style']:6s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(f"{w}@{t:.2f}" for w, t, _ in t_["words"]))
