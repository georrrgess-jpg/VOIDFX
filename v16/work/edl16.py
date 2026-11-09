"""GOING HOME — The Flash × Drake ft. Majid Jordan "Hold On, We're Going Home" (voidfx v16, 9:16). Single source of
truth: the renderer, audio builder and QC read only this file. Scaffolded from the v12 BLOOM standard engine; pieces
ported from v15 OUT OF TIME (sec15.py).

Concept: GOING HOME. The fastest man alive can run anywhere, but every run ends at the same place. The edit opens on the
Flash alone on a rooftop over the night city (the song's drumless last verse, "I know exactly who you could be"): somewhere
in those thousands of lit windows is home. He thinks of her (Iris), and on "Oh, just hold on, we're going home" the shot
is held back like a drawn slingshot (HOLD ON); the drums slam back in exactly on "home" and it releases into the run through
the night city. Mid-edit the focal piece, LONG EXPOSURE: the shutter stays open and his lightning paints light trails
across the night, in depth around him, that collapse into the city's own lights. "It's hard to do these things alone": he
is alone, until a searchlight beam crosses the sky behind him: the real Flash signal (S2), a lamp with the bolt over its
lens. THE SIGNAL (the emblem transition): the lamp flares, its light pours through the bolt, and the bolt's shape becomes
the doorway home, the warm lamp of the loft he shares with Iris (S3). "Just hold on, we're going home": the loft, Iris,
the two of them. The loop, HOME LIGHT: the warm loft pulls back until it is one lit window in the city behind him on the
rooftop, frame 0. The hero is THE HOME LIGHT (a warm window, a lamp): frame 0's windows, the signal's lamp into the loft's
lamp, the loop.
Look AFTER HOURS: the night is teal ink with sodium-amber lights and the suit's red kept rich; home is warm tungsten. A
soft pro-mist halation (red-warm fringe round the lights), a faint anamorphic streak on the brightest point lights,
fine grain.
Song window: song half-beats 617 -> 697 (185.28 -> 209.28 s), 80 half-beats, 24.00 s; grid fitted on the drum stem
(song_prep: P = 0.299973 s, offset 0.1950 s, 100.0 BPM). The kick sits on the map's odd half-beats, so the window starts
one half-beat late: even e are the beats. e0-e24 is the drumless verse (a soft clap on every beat); the drums slam back on
e24, exactly on "home". Lyrics (Whisper large-v3 on the vocal stem): "I know exactly who you could be" e2.7-e11.3; "Oh,
just hold on, we're going home" e15.2-e24.0; "Just hold on, we're going home" e31.9-e40.1; "It's hard to do these things
alone" e48.9-e56.1; "Just hold on, we're going home" e63.3-e73.5; "Going home" e75.6-e77.1.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v16", "going_home"          # folder + output name: v16/out/going_home_voidfx_9x16.mp4
SONG = f"{ROOT}/src/hold_on.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 0.000
FPS, W, H = 60, 1080, 1920
SRC = {"fs5": (f"{ROOT}/src/flash_s5.mp4", 23.976, 1280, 720), "fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720),
       "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720), "fs2": (f"{ROOT}/src/flash_s2.mp4", 60.0, 1280, 720),
       "fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720), "fbk": (f"{ROOT}/src/flash_blitzkrieg.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.299973, 0.1950
H0, H1 = 617, 697
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 24; DROP_HB = HDROP; T_STOP = DUR      # the drums slam back on "home"
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 24, 16
E_LOOP = 74                                    # the loop set piece (the beat camera rests from here)
E_HOLD = 20                                    # HOLD ON: the draw-back from "hold" to "home"
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
KICKS = [0.0, 2.0, 4.0, 6.0]                   # four on the floor: every beat (even e) from e24
KICKS_SOFT = []

VO = []
VO_STEM = None; VO_STEM_T0 = 0.0

def vel(e0, e1, a, b, lo=0.45, hi=2.2, tau=0.08, n=96, beats=None):
    """a speed burst on each beat in the shot (the cut included), smooth slow motion between; the same source range a..b,
    so the speeds scale to fit. Use with lin=True, interp="flow"."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); sp = _np.full_like(ts, lo)
    ks = beats if beats is not None else [e for e in _np.arange(e0, e1, 0.5) if (e % 8) in KICKS and e >= HDROP]
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
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "night"),
             z=kw.pop("z", [(0, 1.00), (1, 1.04)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

class LinZ(list):
    """zoom keys read as a straight line (constant speed, valid outside 0..1: the roof's push runs on through the loop's
    virtual frames, so the camera keeps moving across the wrap)."""
    linear = True

# ---- the drumless verse (e0-e24): the rooftop, Iris, the hold-on
shot("roof", "fs5", 0, 4, 138.64, 139.60, tin="loop_in16", seg=True, face=None, cx=(720, 700), lin=True, tmap=[(-1.5, 137.20), (0, 138.64), (1, 139.60)], tneg=True,
     z=LinZ([(0, 1.06), (1, 1.10)]), anim="twinkle")   # the footage and the push-in run on through the loop's virtual frames (the shot starts at 137.14)
shot("thinks", "fbh", 4, 6, 136.55, 137.30, tin="bokeh_drift", seg=True, anim="flares")                            # he thinks of her, the night in bokeh behind him
shot("looks", "fs1", 6, 8, 230.40, 231.20, tin="flare_sweep", seg=True, look="dusk")                         # Barry looks at her
shot("iris", "fs1", 8, 12, 233.95, 234.95, tin="reflection", seg=True, look="dusk")                                  # "who you could be"
shot("mask", "fs3", 12, 16, 59.40, 60.70, tin="headlight_pass", seg=True, anim="flares")
shot("couple", "fs3", 16, 18, 120.80, 121.40, tin="bolt_split", seg=True, anim="flares")                          # "Oh, just hold on": the two of them at night
shot("eyes", "fs1", 18, 19.5, 291.95, 292.70, tin="focus_pull", seg=True, face=None, cx=(343, 343))           # his eye fills with lightning (v12-proven)
shot("charge", "fs5", 19.5, 24, 114.30, 116.30, tin="light_warp", seg=True, tmap=slow(19.5, 24, 114.30, 116.30, 0.9), lin=True, interp="hold")   # strobe-cut source: its own cadence; HOLD ON draws back from e20
# ---- the drums are back on "home" (e24): the run home through the night city, his face and the suit in every other shot
shot("run", "fs2", 24, 26, 144.60, 145.90, tin="release", seg=True, face=None, cx=(1040, 1060), tmap=vel(24, 26, 144.60, 145.90), lin=True, flowmax=40, flowfall="blend")
shot("faceA", "fbh", 26, 28, 53.70, 54.30, tin="arc_jump", seg=True, tmap=vel(26, 28, 53.70, 54.30, lo=0.7, hi=1.6), lin=True, flowmax=40, flowfall="blend")   # masked, the lightning crackling round him
shot("blast", "fbh", 28, 30, 127.55, 128.15, tin="streak_pass", seg=True)                                       # Barry fires the lightning from his hand
shot("wet", "fs2", 30, 32, 77.20, 78.20, tin="drop_whip", seg=True, face=None, cx=(840, 820), flowmax=40, flowfall="blend")
shot("night", "fbk", 32, 34, 136.15, 136.85, tin="ramp", seg=True, anim="flares")
shot("faceB", "fbh", 34, 36, 84.45, 85.05, tin="light_flare", seg=True, anim="sparks")                         # Barry in the suit, lightning round him; sparks drift off it
shot("city", "fbk", 36, 39, 69.95, 70.95, tin="whip_up15", seg=True, face=None, cx=(700, 640), tmap=vel(36, 39, 69.95, 70.95, beats=[36]), lin=True, anim="twinkle")
shot("van", "fbh", 39, 42, 106.40, 107.40, tin="window_hop", seg=True)                           # inside the window: the S5 suit by the van
# ---- LONG EXPOSURE (the focal piece): the shutter opens on his run and stays open across the cut
shot("lrun", "fs5", 42, 45, 119.20, 120.60, tin="city_dive", seg=True, face=None, cx=(930, 860), lin=True, flowmax=90, flowfall="blend",
     head=[(0.0, 294, 904, 211), (0.22, 326, 855, 203), (0.44, 408, 833, 214), (0.67, 480, 810, 214), (1.0, 535, 798, 214)])   # his masked head on screen (YuNet on the render; the end extrapolated): the trails keep off it
shot("lrun2", "fbk", 45, 48, 2.95, 3.95, tin="exposure_cut", seg=True, face=None, cx=(620, 330), lin=True, flowmax=60, flowfall="blend", lexg=0.30,
     head=[(0.45, 200, 895, 0), (0.55, 230, 900, 200), (0.70, 330, 915, 220), (0.85, 470, 928, 238), (1.0, 525, 936, 245)])   # the lightning tears through the bar; the Flash comes out of it   # the lightning tears through the bar
shot("alone", "fs3", 48, 50, 115.00, 116.00, tin="long_exposure", seg=True, anim="windows")                          # "It's hard to do these things alone"
shot("alone2", "fs3", 50, 52, 126.00, 126.70, tin="time_lapse", seg=True, anim="windows")                          # the world rushes past; he stands still
shot("eyes2", "fbh", 52, 54, 117.40, 118.00, tin="sky_strike", seg=True)                                          # the lightning answers: it is in his eyes
shot("lookup", "fs2", 54, 56, 37.00, 37.60, tin="afterglow", seg=True)                                         # Barry at night; the lightning stays burnt on the eye a moment
shot("alonec", "fs3", 56, 58, 39.75, 40.35, tin="face_match", seg=True)                                        # the eye line carried over
# ---- THE SIGNAL (the emblem transition): the real Flash signal lamp, its bolt the doorway home
shot("signal", "fs2", 58, 64, 45.80, 48.40, tin="beam_call", seg=True, face=None, cx=(640, 640), tmap=slow(58, 64, 45.80, 48.40, 0.3), lin=True, z=[(0, 1.00), (1, 1.07)], flowmax=60)
# ---- home (e64-e80): the loft, the two of them, Iris; the loop pulls home back out through a window of the city
shot("loft", "fs3", 64, 68, 41.50, 43.50, tin="emblem_signal", seg=True, look="home", anim="motes")                         # "Just hold on"
shot("iriskit", "fs3", 68, 72, 49.40, 50.35, tin="lamplight", seg=True, look="home", anim="motes")                        # "hold on, we're going"
shot("home", "fs3", 72, 80, 50.60, 52.60, tin="turn_pan", seg=True, look="home", tmap=slow(72, 80, 50.60, 52.60, 0.4), lin=True, z=[(0, 1.00), (1, 1.04)], anim="motes")   # "home ... going home"

# the Flash signal (flash_s2.mp4 45.40-48.40 s): the lamp's lens (centre, radius in source px) and the bolt stencil over it
SIG_TRACK = [(45.4, 617.6, 470.7, 188.8), (45.483, 614.5, 476.5, 188.9), (45.567, 612.6, 481.6, 189.1), (45.65, 614.4, 486.9, 189.0), (45.733, 617.7, 491.2, 188.7), (45.817, 618.6, 494.4, 188.5), (45.9, 615.8, 497.0, 188.6), (45.983, 613.9, 498.9, 188.8), (46.067, 619.3, 500.8, 189.0), (46.15, 629.0, 503.6, 188.8), (46.233, 635.5, 506.4, 188.7), (46.317, 637.0, 507.7, 188.8), (46.4, 637.3, 508.2, 188.8), (46.483, 636.6, 507.8, 188.7), (46.567, 631.4, 507.8, 188.7), (46.65, 625.6, 508.7, 188.7), (46.733, 621.7, 509.5, 188.7), (46.817, 619.8, 510.0, 188.6), (46.9, 617.7, 511.0, 188.6), (46.983, 617.6, 511.0, 188.7), (47.067, 622.7, 512.2, 188.9), (47.15, 632.2, 512.4, 189.0), (47.233, 641.1, 513.2, 188.9), (47.317, 647.0, 512.9, 188.8), (47.4, 651.3, 511.7, 188.8), (47.483, 654.1, 509.7, 188.7), (47.567, 653.1, 506.8, 188.7), (47.65, 648.4, 505.4, 188.8), (47.733, 642.8, 506.8, 188.8), (47.817, 636.3, 508.3, 188.9), (47.9, 628.1, 509.0, 189.0), (47.983, 618.3, 509.4, 189.0), (48.067, 609.1, 510.1, 188.9), (48.15, 600.2, 510.6, 188.8), (48.233, 590.2, 511.6, 187.6), (48.317, 578.6, 512.4, 186.3), (48.4, 564.8, 513.3, 185.3)]   # (source t, lens x, y, radius): the bright disc fitted per frame
SIG_BOLT = [(0.512, -0.762), (0.148, -0.347), (0.391, -0.338), (0.004, 0.011), (0.263, 0.022), (-0.691, 0.700),
            (-0.249, 0.212), (-0.477, 0.208), (-0.095, -0.150), (-0.342, -0.157)]   # the stencil bolt, traced (lens radii)

HOME_WIN = (112.0, 781.0, 57.0, 32.0)          # the lit window in frame 0 the loft pulls back out of (x, y, width, height; measured on frame 0)
SET_PIECES = [("hold_on", th(18), th(26)), ("long_exposure", th(42), th(50)), ("emblem_signal", th(58), th(66)), ("loop", th(74), th(80))]
WH_TRACK = [(70.3, 748.1, 419.5), (70.3333, 750.0, 423.7), (70.3667, 751.8, 427.7), (70.4, 751.8, 427.8), (70.4333, 753.6, 431.6), (70.4667, 755.5, 435.0), (70.5, 757.5, 438.2), (70.5333, 759.4, 441.0), (70.5667, 759.4, 441.0), (70.6, 761.5, 443.6), (70.6333, 763.5, 446.0), (70.6667, 765.5, 448.3), (70.7, 767.7, 450.4), (70.7333, 767.7, 450.4), (70.7667, 770.0, 452.2), (70.8, 772.2, 453.7), (70.8333, 774.6, 455.1), (70.8667, 777.1, 456.4), (70.9, 777.1, 456.4), (70.9333, 779.6, 457.1)]   # WINDOW HOP: the lit window in the city shot (flash_blitzkrieg.mp4), tracked backward with LK on the source (t, x, y)
WH_SIZE = (7.2, 5.4)                            # its half width, half height in source px
HERO = ["home_light"]
HERO_TINS = ["emblem_signal", "window_hop", "loop_in16"]
SIGNATURE = ["long_exposure", "emblem_signal"]
PLAN_ACCEPT = {
    "dead:charge": "HOLD ON: from e20 the shot is drawn back like a slingshot (pinch, tremble, lightning gathering) on the claps, released on the drop",
    "sig_time:long_exposure": "the long exposure runs in the shot from e42 (the shutter opens, the trails build for 1.8 s) before the cut carries them into the city lights",
    "dead:home": "the loop: from e74 HOME LIGHT pulls the camera back out of the loft's window into frame 0's city, in motion every frame",
    "pf:hero motif:the hero asset (home_light) is drawn by ": "a call-graph false positive: these transitions read the neighbouring shot's edge frame (edge15 -> base16), and base16 only calls home_light for the 'home' shot; the home light appears in WINDOW HOP, THE SIGNAL and the loop (HERO_TINS)",
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
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "song in", round(SONG_IN, 3), "shots", len(SHOTS))
