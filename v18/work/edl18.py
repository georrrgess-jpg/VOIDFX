"""CREEP — The Flash × Radiohead "Creep" (voidfx v18, 9:16). Single source of truth: the renderer, audio builder and QC
read only this file. Scaffolded from the v12 BLOOM standard engine; v17's toolkit is carried in sec18.py.

Concept: I WISH I WAS SPECIAL. Before the lightning, Barry Allen is an ordinary man in a cold, colourless world, and the
only colour in it belongs to the speedster: a gold streak, a red suit. Frame 0: Barry on a night street, and a gold
streak tears past behind him (THE HOOK: the future Flash, running back in time, passes his younger self). "I wish I was
special": the dusk, the lab, Barry by the lamp, looking at Iris. "You're so f***ing special": her hair blows (the Flash
has just passed her), and it is the Flash she sees, masked, his red the one colour in the frame; it drains away and he is
Barry again, alone in the dark. The guitar's two crunches: THE STRIKE (crunch 1, e28: the lightning hits him and the
colour floods out of it into the world, along veins of current: COLOUR STRIKE) and the wake (crunch 2, e33, a heartbeat
ring from his chest). "But I'm a creep": THE DROP on the distorted chorus (e37): current climbs the frame and he is the
Flash. The chorus in full colour, a new scene on every beat; "I'm a weirdo": Barry lowers his sunglasses. "What the hell
am I doing here": the real chest emblem's bolt lifts off, turns and flies at the lens, and through it is the Speed Force
(EMBLEM BOLT); Iris in tears. "I don't belong here": he runs back in time, and his lightning tears the frame open onto
frame 0: the streak behind Barry in the street is him (THE TIME TEAR, the loop; the end causes the start).
The hero asset is THE TIME STREAK: the hook, the strike's front, the loop.
Looks: ORDINARY (the verse): cold slate blue, colour gone except the speedster's red and gold. SPECIAL (from the strike):
full colour, warm gold highlights, deep red suit, teal shadows. Speed Force: the colour look, its blue kept.
Song window: song half-beats 148 -> 228 (48.59 -> 74.71 s), 80 half-beats, 26.12 s; grid fitted on the Demucs drum stem
(song_prep: P = 0.326460 s, offset 0.2741 s, 91.9 BPM). Even e are the beats; bars every 8 e. Lyrics (Whisper large-v3 on
the vocal stem, edit half-beat e): "I wish I was special" e0.8-e8, "You're so f***ing special" e14.8-e24, the guitar
crunches e28 and e33, "But I'm a creep" e31.5-e44 (the distorted chorus from e37), "I'm a weirdo" e48.4-e56, "What the
hell am I doing here" e56-e72; the vocal is silent from e74 (the window ends before "I don't belong here").
Excluded on the owner's brief: Barry with lightning in his eyes (fbh 116.5-119.5, fbh 54.4-56, fa 87.6-89.9); the
Blitzkrieg pack's faces; Wally and XS.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v18", "creep"          # folder + output name: v18/out/creep_voidfx_9x16.mp4
SONG = f"{ROOT}/src/creep.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 40.565
FPS, W, H = 60, 1080, 1920
SRC = {"fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720),
       "fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720), "fs2": (f"{ROOT}/src/flash_s2.mp4", 60.0, 1280, 720),
       "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720), "fs5": (f"{ROOT}/src/flash_s5.mp4", 23.976, 1280, 720),
       "fbk": (f"{ROOT}/src/flash_blitzkrieg.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.326460, 0.2741
H0, H1 = 148, 228
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 37; DROP_HB = HDROP; T_STOP = DUR      # the distorted chorus
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 0, 0
E_STRIKE = 28                                   # crunch 1: THE STRIKE (COLOUR STRIKE)
E_WAKE = 33                                     # crunch 2: the wake
E_DROP = 37                                     # "creep": THE DROP, the chorus in colour
E_LOOP = 76                                     # THE TIME TEAR (the beat camera rests from e72)
E_REST = 72
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
KICKS = [0.0, 2.0, 4.0, 6.0]
KICKS_SOFT = []

VO = []
VO_STEM = None; VO_STEM_T0 = 0.0

def vel(e0, e1, a, b, lo=0.55, hi=1.9, tau=0.08, n=96, beats=None):
    """a speed burst on each beat in the shot (the cut included), smooth slow motion between; the same source range a..b,
    so the speeds scale to fit. Use with lin=True, interp="flow"."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); sp = _np.full_like(ts, lo)
    ks = beats if beats is not None else [e for e in _np.arange(e0, e1, 0.5) if (e % 2) == 0]
    for e in ks:
        tb = th(e) - th(e0); sp = sp + (hi - lo) * _np.exp(-_np.clip(ts - tb, 0, None) / tau) * (ts >= tb)
    src = _np.concatenate([[0.0], _np.cumsum((sp[1:] + sp[:-1]) / 2 * _np.diff(ts))]); src /= src[-1]
    return [(float(u), float(a + (b - a) * _np.interp(u * T, ts, src))) for u in _np.linspace(0, 1, n)]

def slow(e0, e1, a, b, ease=0.35, n=64):
    import numpy as _np
    u = _np.linspace(0, 1, n); s = 1 - (1 - u) ** (1 + ease)
    return [(float(x), float(a + (b - a) * y)) for x, y in zip(u, s)]

class LinZ(list):
    """zoom keys read as a straight line (constant speed, valid outside 0..1)."""
    linear = True

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "colour"),
             z=kw.pop("z", [(0, 1.00), (1, 1.04)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- "I wish I was special" (e0.8-e8): ORDINARY, cold; the only colour is the speedster's
shot("street", "fs3", 0, 4, 3.75, 4.86, tin="loop18", seg=True, lin=True, tmap=[(-0.5, 3.195), (0, 3.75), (1, 4.86)], tneg=True,
     z=LinZ([(0, 1.02), (1, 1.06)]), look="cold", anim="hook")                    # frame 0: Barry on a night street; THE HOOK: a gold streak tears past behind him
shot("dusk", "fs3", 4, 6, 115.00, 115.90, tin="bokeh_bloom", seg=True, face=None, cx=(540, 560), look="cold", anim="breath")     # alone outside at night
shot("lab", "fs1", 6, 8, 66.00, 66.80, tin="window_glow", seg=True, look="cold")                    # "special": at work in the CCPD lab
shot("brick", "fs1", 8, 11, 10.50, 11.90, tin="vertigo", seg=True, look="cold", anim="drift")      # by a brick wall, fidgeting: ordinary
shot("skyward", "fs1", 11, 15, 125.40, 126.30, tin="ray_rake", seg=True, look="cold", anim="skyrays")   # "You're": he looks up at the sky
shot("airfield", "fs1", 15, 19, 199.60, 200.90, tin="streak_wipe", seg=True, face=None, cx=(680, 800), look="cold", keepred=1.0, keepgold=1.0)   # "so": the speedster runs, his gold and red the only colour
shot("mask", "fs1", 19, 23, 221.75, 222.95, tin="crash_zoom", seg=True, look="cold", keepred=1.0, anim="crackle")   # "f***ing special": the Flash she sees, his red the one colour
shot("alone", "fs1", 23, 28, 74.00, 75.60, tin="colour_drain", seg=True, look="cold", anim="stormlight")   # Barry alone in the dark; the storm builds outside
# ---- the crunches: THE STRIKE (e28) and the wake (e33)
shot("strike", "fbh", 28, 33, 10.42, 12.05, tin="sky_crack", seg=True, look="strike")               # COLOUR STRIKE: the colour floods out of the lightning
shot("wake", "fs1", 33, 37, 4.45, 4.98, tin="heartstart", seg=True, lin=True)                       # he gasps awake
# ---- "But I'm a creep" (the distorted chorus from e37): SPECIAL, full colour, a new scene on every beat
shot("hero", "fbh", 37, 40, 109.80, 110.95, tin="current_climb", seg=True, anim="crackle")          # THE DROP: he is the Flash
shot("sfrun", "fs2", 40, 42, 144.55, 145.40, tin="lightbar_streak", seg=False, face=None, cx=(1040, 1000), tmap=vel(40, 42, 144.55, 145.40), lin=True, flowmax=40, flowfall="blend")
shot("charge", "fs5", 42, 44, 180.00, 180.90, tin="spark_jump", seg=True)
shot("city", "fbk", 44, 46, 70.25, 71.25, tin="cube_turn", seg=False, face=None, cx=(700, 680))   # the city at night, his streak across it
shot("loft", "fs3", 46, 48, 48.20, 48.95, tin="arc_sweep", seg=True, face=None, cx=(810, 800), face_hint=(540, 560, 150))                                # he vanishes into a streak
shot("shades", "fs3", 48, 52, 28.74, 29.28, tin="streak_carry", seg=True, anim="glare")            # "I'm a weirdo": he lowers his sunglasses
shot("lobby", "fs1", 52, 54, 249.80, 250.70, tin="shades_glint", seg=True, face=None, cx=(420, 520))   # the S1 suit walks in
shot("fire", "fbh", 54, 56, 84.45, 85.05, tin="flicker_cut", seg=True, anim="embers")              # Barry in the suit, lightning round him
shot("fly", "fbh", 56, 58, 81.00, 81.90, tin="ember_burn", seg=True, face=None, cx=(600, 640), tmap=vel(56, 58, 81.00, 81.90), lin=True, flowmax=40, flowfall="blend")   # "What"
shot("run", "fs5", 58, 60, 72.00, 72.90, tin="smear17", seg=True, tmap=vel(58, 60, 72.00, 72.90), lin=True, flowmax=40, flowfall="blend")
shot("emblem", "fbh", 60, 64, 82.50, 83.75, tin="bokeh_rack", seg=True)                             # EMBLEM BOLT: the real emblem's bolt lifts off
# ---- "the hell am I doing here" (e66-e72): the Speed Force
shot("sf", "fs3", 64, 68, 129.00, 129.85, tin="emblem_bolt", seg=True, look="force", anim="mist")    # inside the bolt: the Speed Force
shot("vault", "fs1", 68, 72, 145.60, 147.60, tin="mist_pass", seg=True, face=None, cx=(300, 300), anim="vaultpulse")   # "am I doing here": alone in the pipeline cell
# ---- "I don't belong here": he runs back in time (THE TIME TEAR, the loop)
shot("timerun", "fs1", 72, 80, 139.80, 142.60, tin="lamp_bloom", seg=True, face=None, cx=(600, 640), face_hint=(520, 420, 220), lin=True, flowmax=40, ev=0.45)   # he runs back in time; THE TIME TEAR

EMB_TRACK = [(82.3, 448.6, 420.6, 78.9), (82.35, 452.4, 423.0, 77.7), (82.4, 459.1, 427.5, 74.3), (82.45, 465.4, 433.1, 70.9), (82.5, 469.5, 437.7, 69.1), (82.55, 472.4, 441.5, 69.6), (82.6, 472.1, 442.2, 69.6), (82.65, 472.6, 444.3, 67.0), (82.7, 475.9, 448.7, 63.6), (82.75, 480.7, 453.3, 61.4), (82.8, 482.0, 455.9, 61.6), (82.85, 481.5, 458.0, 61.5), (82.9, 479.6, 459.3, 62.3), (82.95, 478.3, 461.1, 62.5), (83.0, 476.9, 463.5, 62.5), (83.05, 476.0, 465.0, 60.9), (83.1, 475.0, 466.9, 60.3), (83.15, 480.8, 471.2, 59.8), (83.2, 489.6, 476.3, 59.0), (83.25, 490.4, 478.2, 58.4), (83.3, 476.5, 474.6, 58.7), (83.35, 460.6, 473.4, 59.2), (83.4, 461.1, 477.0, 58.6), (83.45, 456.8, 480.1, 58.7), (83.5, 447.1, 482.1, 59.4), (83.55, 437.3, 484.4, 60.3), (83.6, 433.9, 486.8, 60.4), (83.65, 431.8, 489.0, 60.3), (83.7, 430.4, 491.6, 60.3), (83.75, 429.6, 493.1, 60.2)]   # the chest emblem in flash_b_hq 82.3-83.75 s (Hough circle per source frame, smoothed): (t, x, y, r)
SET_PIECES = [("hook", th(-1), th(3)), ("colour_strike", th(28), th(33)), ("the_drop", th(35), th(39)), ("emblem_bolt", th(61), th(66)), ("time_tear", th(76), th(80))]
HERO = ["streak_draw"]
HERO_TINS = ["streak_wipe", "loop18"]
SIGNATURE = ["emblem_bolt", "current_climb"]
PLAN_ACCEPT = {}
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
        ts = [k[1] for k in s["tmap"] if k[0] >= 0]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:10s} e{s['e0']:5.1f}-e{s['e1']:5.1f} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']:4s} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "song in", round(SONG_IN, 3), "shots", len(SHOTS))
