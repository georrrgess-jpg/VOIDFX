"""MR. BLUE SKY — The Flash × Electric Light Orchestra "Mr. Blue Sky" (voidfx v17, 9:16). Single source of truth: the
renderer, audio builder and QC read only this file. Scaffolded from the v12 BLOOM standard engine.

Concept: MR. BLUE SKY (after the storm). The Flash was made in a storm; this is the day after it. Frame 0 is storm clouds
lit by lightning; on "Hey!" the sun breaks through them (SUN BREAK) and he is running down the avenue through a sunny
city, a new scene on every beat. "See how the sun shines brightly": THE SUN (the focal piece) rises behind him through his
matte, its rays turning on the beat, and its lens flare lines up into a chain of ghosts; one ghost opens into the next
shot (GHOST IRIS). "Where once was pity": the hurt days, a raindrop, then the clouds part (CLOUD BREAK) on "Mr. Blue Sky":
Barry looks up at the sky. The happy days: Flash Day, the ball game, Team Flash laughing. The chorus: the real emblem on
his chest glints and blazes into the sun (EMBLEM SUN) and the camera rises into the sky after it. "You had to hide away
for so long": the clouds roll back over the sun (CLOUD OVER, the loop) and they are frame 0's storm. The hero is THE SUN:
the sun break, the focal piece, the emblem, the loop.
Look BLUE SKY: high-key and clean; skies pushed to cerulean, sunny gold highlights, the suit's red rich, skin kept natural;
a soft warm bloom round the light, fine grain. The storm in cool grey.
Song window: song half-beats 177 -> 321 (30.512 -> 55.207 s), 144 half-beats, 24.69 s; grid fitted on the Demucs drum stem
(song_prep: P = 0.171490 s, offset 0.1590 s, 175 BPM). The kick is on every other half-beat, so the window starts on 177:
even e are the beats (a kick on each). Lyrics (Whisper large-v3 on the vocal stem, edit half-beat e): "Hey" e0.9,
"Running down the avenue" e7.6-e16.3, "see how the sun shines brightly" e22.6-e39.2, "and the city on the streets where
once was pity" e45.3-e64.5, "Mr. Blue Sky is living here today, hey" e68.9-e91.2, "Mr. Blue Sky, please tell us why you
had to hide away for so long" e105.0-e138.1; "Where did we go wrong" starts at e143.3 (faded out of the loop's last frames
on the vocal stem). Excluded on the owner's brief: the shot of Barry with lightning in his eyes (flash_b_hq ~116.5-119.5 s).
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v17", "blue_sky"          # folder + output name: v17/out/blue_sky_voidfx_9x16.mp4
SONG = f"{ROOT}/src/mr_blue_sky.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 21.781
FPS, W, H = 60, 1080, 1920
SRC = {"fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720), "fbk": (f"{ROOT}/src/flash_blitzkrieg.mp4", 60.0, 1280, 720),
       "fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720), "fs2": (f"{ROOT}/src/flash_s2.mp4", 60.0, 1280, 720),
       "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720), "fs5": (f"{ROOT}/src/flash_s5.mp4", 23.976, 1280, 720),
       "fa": (f"{ROOT}/src/flash_a.mp4", 25.421, 1280, 720), "fs2t": (f"{ROOT}/src/flash_s2_topaz.mp4", 30.0, 1280, 720)}

HB, HB_OFF = 0.171490, 0.1590
H0, H1 = 177, 321
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 0; DROP_HB = HDROP; T_STOP = DUR      # drums from the first frame
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 0, 0
E_LOOP = 136                                   # CLOUD OVER: the loop set piece (the beat camera rests from here)
E_SUN = 32                                     # THE SUN rises (e32) and opens as GHOST IRIS on e40
E_CHORUS = 104                                 # EMBLEM SUN: e104 -> e110 ("Mr. Blue Sky")
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
KICKS = [0.0, 2.0, 4.0, 6.0]                   # a kick on every beat (even e)
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
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "sky"),
             z=kw.pop("z", [(0, 1.00), (1, 1.04)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- "Hey!" (e0): the storm breaks; "Running down the avenue" (e7.6-e16)
shot("storm", "fs5", 0, 4, 105.82, 106.52, tin="loop17", seg=False, face=None, cx=(640, 600), lin=True, tmap=[(-0.5, 105.78), (0, 105.82), (1, 106.52)], tneg=True,
     z=LinZ([(0, 1.04), (1, 1.08)]), look="storm", anim="sunbreak")                        # frame 0: storm clouds lit by lightning; the sun breaks through
shot("avenue", "fbh", 4, 8, 64.80, 66.30, tin="sun_burst", seg=True, face=None, cx=(640, 640), tmap=vel(4, 8, 64.80, 66.30), lin=True, interp="hold")   # he runs down the avenue at us (lightning flicker: its own cadence)
shot("race", "fa", 8, 12, 50.00, 51.40, tin="run_by", seg=True, face=None, cx=(560, 640), tmap=vel(8, 12, 50.00, 51.40), lin=True, flowmax=40, flowfall="blend")
shot("runlit", "fbh", 12, 16, 4.55, 6.10, tin="speed_zoom", seg=True, tmap=vel(12, 16, 4.55, 6.10), lin=True, flowmax=40, flowfall="blend")
shot("wave", "fbh", 16, 20, 6.90, 8.20, tin="glint_sweep", seg=True, anim="shine")                         # he turns and grins at us
shot("run5", "fs5", 20, 24, 108.60, 110.00, tin="sky_whip", seg=True, tmap=vel(20, 24, 108.60, 110.00), lin=True, flowmax=40, flowfall="blend")
# ---- "see how the sun shines brightly" (e22.6-e39.2): golden hour, THE SUN
shot("golden", "fs1", 24, 28, 123.40, 124.40, tin="flare_cut", seg=True, anim="shine")
shot("grin", "fs3", 28, 32, 44.07, 45.07, tin="ray_rake", seg=True, anim="shine")             # the S2 suit, grinning in the daylight
shot("sun", "fbk", 32, 40, 141.93, 142.85, tin="bloom_cut", seg=True, tmap=slow(32, 40, 141.93, 142.85, 0.2), lin=True, flowmax=40, suitred=1.0, z=LinZ([(0, 1.00), (1, 1.06)]))   # THE SUN rises behind him
# ---- "and the city, on the streets where once was pity" (e45-e64.5)
shot("ledge", "fbh", 40, 44, 87.60, 88.60, tin="ghost_iris", seg=True, face=None, cx=(760, 760))   # the Flash crouched on the ledge (not the officer below)
shot("streets", "fs2", 44, 48, 168.70, 169.70, tin="prism", seg=True)                       # "on the streets": he lands in the street
shot("lookdown", "fbh", 48, 52, 69.00, 70.00, tin="whip_pan", seg=True, anim="shine")
shot("arm", "fbk", 52, 56, 170.60, 171.80, tin="bolt_crack", seg=True, suitred=1.0)
shot("hurt", "fs1", 56, 60, 278.40, 279.40, tin="rain_ripple", seg=True)                  # "where once was pity"
shot("masked1", "fs1", 60, 64, 287.40, 288.40, tin="tilt_up", seg=True, tmap=slow(60, 64, 287.40, 288.40, 0.3), lin=True)
shot("greysky", "fs3", 64, 68, 8.90, 9.90, tin="cloud_shadow", seg=True)                      # he walks under a grey sky; the clouds gather ...
# ---- "Mr. Blue Sky is living here today, hey" (e68.9-e91.2): the clouds part
shot("lookup", "fbk", 68, 72, 94.05, 94.75, tin="cloud_break", seg=True, anim="rays")       # ... and part: Barry looks up at the sky
shot("sunny", "fs2t", 72, 76, 34.85, 35.85, tin="sun_open", seg=True, anim="shine")          # "living here today": Barry in the sunshine
shot("crossed", "fbh", 76, 80, 92.50, 93.50, tin="sun_whip", seg=True)
shot("flashday", "fs2", 80, 84, 42.20, 43.40, tin="balloon_rise", seg=True)
shot("baseball", "fs5", 84, 88, 91.50, 92.60, tin="light_streak", seg=True)
shot("laugh", "fs5", 88, 92, 29.00, 30.20, tin="throw_whip", seg=True)
shot("xs", "fs5", 92, 96, 14.60, 15.60, tin="light_leak17", seg=True)
shot("wally", "fs3", 96, 100, 93.70, 94.70, tin="spin_roll", seg=True)
shot("speedforce", "fs3", 100, 104, 132.90, 133.90, tin="blue_bloom", seg=True)
# ---- the chorus: "Mr. Blue Sky, please tell us why you had to hide away for so long" (e105-e138)
shot("emblem", "fbh", 104, 110, 82.40, 83.75, tin="punch_cut", seg=True)                    # EMBLEM SUN: the chest emblem glints and blazes into the sun
shot("leap", "fs1", 110, 116, 199.55, 201.95, tin="emblem_sun", seg=True, face=None, cx=(700, 760), tmap=vel(110, 116, 199.55, 201.95), lin=True, flowmax=40, flowfall="blend")
shot("device", "fbh", 116, 120, 49.95, 51.20, tin="horizon_slide", seg=True)                 # the S2 suit, the chest device lit, grinning
shot("tux", "fs5", 120, 124, 102.30, 103.60, tin="bokeh_rack", seg=True)
shot("skyward", "fa", 124, 128, 0.30, 1.30, tin="glare_wash", seg=True)                    # the S5 suit against the open sky
shot("smilelit", "fbh", 128, 132, 90.10, 91.30, tin="hide_peek", seg=True)                # "hide away"
shot("runface", "fa", 132, 136, 62.40, 63.60, tin="smear17", seg=True, tmap=vel(132, 136, 62.40, 63.60), lin=True, flowmax=40, flowfall="blend")
shot("last", "fs1", 136, 144, 207.00, 208.40, tin="split_slide", seg=True, face=None, cx=(485, 640), tmap=slow(136, 144, 207.00, 208.40, 0.2), lin=True)   # "so long": he stands on the airfield; the clouds roll back over the sun

EMB_TRACK = [(82.3, 448.6, 420.6, 78.9), (82.35, 452.4, 423.0, 77.7), (82.4, 459.1, 427.5, 74.3), (82.45, 465.4, 433.1, 70.9), (82.5, 469.5, 437.7, 69.1), (82.55, 472.4, 441.5, 69.6), (82.6, 472.1, 442.2, 69.6), (82.65, 472.6, 444.3, 67.0), (82.7, 475.9, 448.7, 63.6), (82.75, 480.7, 453.3, 61.4), (82.8, 482.0, 455.9, 61.6), (82.85, 481.5, 458.0, 61.5), (82.9, 479.6, 459.3, 62.3), (82.95, 478.3, 461.1, 62.5), (83.0, 476.9, 463.5, 62.5), (83.05, 476.0, 465.0, 60.9), (83.1, 475.0, 466.9, 60.3), (83.15, 480.8, 471.2, 59.8), (83.2, 489.6, 476.3, 59.0), (83.25, 490.4, 478.2, 58.4), (83.3, 476.5, 474.6, 58.7), (83.35, 460.6, 473.4, 59.2), (83.4, 461.1, 477.0, 58.6), (83.45, 456.8, 480.1, 58.7), (83.5, 447.1, 482.1, 59.4), (83.55, 437.3, 484.4, 60.3), (83.6, 433.9, 486.8, 60.4), (83.65, 431.8, 489.0, 60.3), (83.7, 430.4, 491.6, 60.3), (83.75, 429.6, 493.1, 60.2)]   # the chest emblem in flash_b_hq 82.3-83.75 s (Hough circle per source frame, smoothed): (t, x, y, r)
SET_PIECES = [("sun_break", th(0), th(6)), ("the_sun", th(32), th(42)), ("cloud_break", th(65), th(70)), ("emblem_sun", th(104), th(112)), ("loop", th(136), th(144))]
HERO = ["sun_draw"]
HERO_TINS = ["sun_burst", "ghost_iris", "emblem_sun", "loop17"]
SIGNATURE = ["ghost_iris", "emblem_sun"]
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
