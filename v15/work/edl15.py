"""OUT OF TIME — The Flash × Eyedress "Jealous" (voidfx v15, 9:16). Single source of truth: the renderer, audio builder
and QC read only this file. Scaffolded from the v12 BLOOM standard engine.

Concept: OUT OF TIME. The window is the song's "I don't got time" run, its one drum-break bar and the return ("Do whatever
you want, I don't care, don't care, don't even tell me ... I don't really want to know"). The fastest man alive never has
time: he checks his watch, a call comes in, and he runs (the city, the lightning, the suit). On the drum break, time stops
at the moment it all began: the lab strike of S1, frozen mid-air (the lightning, the chemicals, the glass hang still while
the drum fill keeps beating, and the camera steps through the frozen moment on each hit). On the return, time restarts:
the frozen lightning discharges and he opens his eyes full of it. Then the jealousy the song pretends not to feel: Iris
looks at the Flash, he tells himself he doesn't care and tears off; the wind of it blows her hair; the trail rips down
the path. The hero object is THE TIMEPIECE: his real watch (the signature: a lightning second hand ticks on "time" and we
dive through the watch face into the call), the emblem as a clock (EMBLEM CLOCK: the real S5 emblem's bolt winds round
like a clock hand and sweeps the next memory in), and the loop (a glint becomes the watch face, back on frame 0).
Look VIOLET HOUR: lifted violet shadows, peach-gold highlights, the suit's red kept rich, a soft dream bloom, fine grain.
Song window: song half-beats 176 -> 256 (56.84 -> 82.64 s), 80 half-beats, 25.81 s; grid fitted on the drum stem
(song_prep: P = 0.32256 s, offset 0.0699 s, 93.0 BPM; agrees with the map). Groove per bar: kicks on e0, e2.5, e4, e6.5
(e1, e5 lighter); the break bar e32-e40 is drums only (bass and the band drop out) with a kick fill.
Lyrics (Whisper large-v3 on the vocal stem): "time" lands on e2.9, e11.1, e19.2, e27.0; "Do whatever you want" e43-e47;
"I don't care, don't care" e49-e56; "don't even tell me" e62-e64; "I don't really want to know" e74.4-e79.5.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v15", "out_of_time"          # folder + output name: v15/out/out_of_time_voidfx_9x16.mp4
SONG = f"{ROOT}/src/jealous.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 0.000
FPS, W, H = 60, 1080, 1920
SRC = {"fs2t": (f"{ROOT}/src/flash_s2_topaz.mp4", 30.0, 1280, 720), "fbk": (f"{ROOT}/src/flash_blitzkrieg.mp4", 60.0, 1280, 720),
       "fs5": (f"{ROOT}/src/flash_s5.mp4", 23.976, 1280, 720), "fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720),
       "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720), "fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720),
       "fs4": (f"{ROOT}/src/flash_s4.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.322560, 0.0699
H0, H1 = 176, 256
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 40; DROP_HB = HDROP; T_STOP = DUR      # the return after the drum break (time restarts)
E_STOP = 32                                    # the drum break: time stops (e32-e40)
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 0, 32
E_LOOP = H1 - H0 - 4                           # the loop set piece (the beat camera rests from here)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
KICKS = [0.0, 2.5, 4.0, 6.5]                   # the groove's strong kicks in each 8-e bar (drum stem)
KICKS_SOFT = [1.0, 5.0]
FILL = [32.0, 33.0, 33.5, 34.5, 35.5, 37.0, 37.5, 38.5, 39.5]   # the break bar's kick fill (the frozen world steps on these)
TIMES = [2.9, 11.1, 19.2, 27.0]                # "time" (sung)

VO = []
VO_STEM = None; VO_STEM_T0 = 0.0

def vel(e0, e1, a, b, lo=0.45, hi=2.4, tau=0.08, n=96, beats=None):
    """a speed burst on each kick in the shot (the cut included), smooth slow motion between; the same source range a..b,
    so the speeds scale to fit. Use with lin=True, interp="flow"."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); sp = _np.full_like(ts, lo)
    ks = beats if beats is not None else [e for e in _np.arange(e0, e1, 0.5) if (e % 8) in KICKS]
    for e in ks:
        tb = th(e) - th(e0); sp = sp + (hi - lo) * _np.exp(-_np.clip(ts - tb, 0, None) / tau) * (ts >= tb)
    src = _np.concatenate([[0.0], _np.cumsum((sp[1:] + sp[:-1]) / 2 * _np.diff(ts))]); src /= src[-1]
    return [(float(u), float(a + (b - a) * _np.interp(u * T, ts, src))) for u in _np.linspace(0, 1, n)]

def slow(e0, e1, a, b, ease=0.35, n=64):
    import numpy as _np
    u = _np.linspace(0, 1, n); s = 1 - (1 - u) ** (1 + ease)
    return [(float(x), float(a + (b - a) * y)) for x, y in zip(u, s)]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "violet"),
             z=kw.pop("z", [(0, 1.00), (1, 1.04)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- I DON'T GOT TIME (e0-e32): the watch, the call, and he runs
shot("watch", "fs2t", 0, 4, 59.75, 60.75, tin="loop_in15", seg=True, lin=True, flowmax=40, flowfall="blend")
shot("call", "fs2t", 4, 6.5, 127.10, 128.10, tin="vibrate", seg=True)
shot("night", "fs2t", 6.5, 8, 134.10, 134.70, tin="phone_flare", seg=True)                      # he is already out there
shot("runcam", "fbk", 8, 10.5, 20.00, 20.85, tin="streak_pass", seg=True, face=None, cx=(830, 800), flowmax=24, flowfall="blend")
shot("chest", "fs5", 10.5, 12, 180.30, 180.90, tin="time_slice15", seg=True, anim="current")
shot("masked", "fbh", 12, 14.5, 69.00, 69.85, tin="edge_current15", seg=True, tmap=vel(12, 14.5, 69.00, 69.85), lin=True)
shot("charge", "fbk", 14.5, 16, 47.90, 48.45, tin="lightstreak", seg=True)
shot("fpv", "fbk", 16, 18.5, 60.70, 61.90, tin="ramp", seg=True, face=None, cx=(640, 640))
shot("flight", "fbh", 18.5, 20, 80.85, 81.45, tin="bolt_split", seg=True, face=None, cx=(560, 600))
shot("street", "fs3", 20, 22.5, 106.80, 107.80, tin="whip_up15", seg=True, tmap=vel(20, 22.5, 106.80, 107.80), lin=True, anim="flares")
shot("wall", "fbk", 22.5, 24, 74.60, 75.15, tin="arc_link", seg=True, face=None, cx=(640, 640), anim="remnants")
shot("s5night", "fs5", 24, 26.5, 72.00, 72.95, tin="light_leak15", seg=True, tmap=vel(24, 26.5, 72.00, 72.95), lin=True)
shot("city", "fbk", 26.5, 28, 71.72, 72.26, tin="gold_link", seg=True, face=None, cx=(640, 640))
shot("strike", "fbh", 28, 32, 10.33, 11.95, tin="strike_cut", seg=True, tmap=slow(28, 32, 10.33, 11.95, 0.6), lin=True, flowfall="blend")
# ---- TIME STOPS (the drum break, e32-e40): the S1 lab strike, frozen (the strike's own next frame: one continuous moment)
shot("still", "fbh", 32, 40, 11.97, 11.98, tin="time_stop", seg=True, z=[(0, 1.00), (1, 1.00)])   # his hand up against the bolt
# ---- TIME RESTARTS (e40): the return, and the jealousy he says he doesn't feel
shot("eyes", "fbh", 40, 42.5, 116.60, 117.52, tin="time_restart", seg=True)
shot("iris", "fs4", 42.5, 46.5, 117.20, 118.22, tin="eye_iris15", seg=True, anim="bokeh")                      # S4: Iris at work (her life)
shot("look", "fs1", 46.5, 50.5, 236.00, 237.50, tin="speed_whip15", seg=True, tmap=vel(46.5, 50.5, 236.00, 237.50), lin=True, flowmax=30, flowfall="blend", anim="urge")
shot("sunrun", "fs4", 50.5, 53, 2.55, 3.70, tin="turn_away", seg=True, interp="hold")   # the source's own 60p stutter-cut run, straight   # he turns away and runs
shot("hair", "fs1", 53, 56, 237.80, 238.76, tin="wind_gust", seg=True, anim="grit")
shot("trail", "fs1", 56, 58.5, 238.85, 239.65, tin="dust_cloud", seg=True, face=None, cx=(700, 560), flowmax=30, flowfall="blend")
shot("emblem", "fbh", 58.5, 64, 92.30, 93.45, tin="focus_rack15", seg=True, z=[(0, 1.00), (1, 1.00)])
shot("fly", "fbh", 64, 66.5, 119.60, 120.45, tin="emblem_clock", seg=True, face=None, cx=(640, 640))
shot("saves", "fbh", 66.5, 68, 127.70, 128.25, tin="afterimage15", seg=True, anim="shout")
shot("runfs5", "fs5", 68, 70.5, 113.00, 113.85, tin="pendulum", seg=True, face=None, cx=(640, 640), interp="hold")   # the source flickers frame to frame: held 24p at 1.05x
shot("blue", "fbk", 70.5, 72, 124.75, 125.30, tin="whip", seg=True)
shot("hero", "fs4", 72, 74.5, 174.85, 175.75, tin="time_particles", seg=True, face=None, cx=(800, 760), tmap=vel(72, 74.5, 174.85, 175.75), lin=True, anim="embers", face_hint=(410, 640, 150))   # through the fire
U76 = (76 - 74.5) / 5.5                       # time stops once more on "don't" (e76): the source holds (the lenses still clear)
shot("alone", "fbh", 74.5, 80, 147.40, 147.88, tin="dolly", seg=True, tmap=[(0, 147.40), (U76, 147.88), (1, 147.88)], lin=True, z=[(0, 1.00), (1, 1.08)])

# the real S5 emblem in flash_b_hq.mp4 (92.25-93.45 s, steady while his arms are crossed): centre per source frame
# (template-tracked, smoothed), radius (Hough), and the bolt's top tip in units of the radius (traced on the source)
EMB15_R = 55.2
EMB15_TIP = (0.77, -1.30)
# the S5 bolt traced as a polygon on the restored source (emblem shot, frame 1190), in emblem radii from its centre
EMB15_BOLT = [(0.767, -1.316), (0.522, -0.972), (0.399, -0.569), (0.589, -0.549), (-0.058, 0.066), (0.437, 0.048),
              (-0.668, 0.937), (-0.160, 0.315), (-0.490, 0.290), (0.030, -0.269), (-0.350, -0.295)]
EMB15_TIP_DEG = -59.4
EMB15_TRACK = [(92.250, 496.9, 563.7), (92.333, 495.0, 563.9), (92.417, 493.0, 564.2), (92.500, 491.2, 564.4), (92.583, 490.1, 564.5),
               (92.667, 489.5, 564.7), (92.750, 489.1, 564.4), (92.833, 489.3, 564.0), (92.917, 489.6, 563.2), (93.000, 489.4, 562.4),
               (93.083, 488.9, 561.8), (93.167, 488.7, 561.6), (93.250, 488.7, 561.6), (93.333, 488.3, 561.6), (93.417, 486.9, 561.8),
               (93.500, 482.3, 561.8)]

SET_PIECES = [("time_stops", th(30), th(40)), ("time_restarts", th(39.3), th(41.3)),
              ("emblem_clock", th(60), th(65)), ("loop", th(76), th(80))]
LOOP_E0, LOOP_E1 = 76.0, 76.5                  # the loop: time stops once more (e76), then REWIND (e77-e80) into frame 0
REW_CARDS = ["hero", "emblem", "iris", "eyes", "still", "runcam"]   # the memories the rewind flies back past, newest first
HERO = ["timepiece_draw", "still_fx"]
HERO_TINS = ["time_stop", "time_restart", "emblem_clock", "loop_in15"]
SIGNATURE = ["emblem_clock"]
PLAN_ACCEPT = {
    "dead:still": "TIME STOPS: the frozen strike steps on each of the nine kicks of the drum fill, the drops and sparks drift, the lightning pulses",
    "dead:alone": "the last memory and the loop: the dolly in, time stops once more on the e76 kick, then the REWIND flies back past the edit's memories into frame 0",
    "reuse_shot:strike/still": "one continuous moment by design: the strike slows and freezes on its own next frame (time stops)",
}
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

TEXT = []
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, H1 - H0 - 6)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:5.1f}-e{s['e1']:5.1f} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']:5s} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "return", round(th(HDROP), 3), "song in", round(SONG_IN, 3), "shots", len(SHOTS))
