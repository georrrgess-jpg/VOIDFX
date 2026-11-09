"""KEEPSAKES — The Flash × C418 "Mice on Venus" (voidfx v14, 9:16), rev 2. Single source of truth: the renderer, audio
builder and QC read only this file. Scaffolded from the v12 BLOOM standard engine.

Concept: KEEPSAKES. Nostalgia for where it all began. The edit opens on the night Barry woke from the coma (S1): the
dark medical bay at S.T.A.R. Labs, the lights flicker on, he gasps awake, and an achievement pops up: "Achievement Made!
The Beginning?" (THE WAKE, the focal set piece at the start; the owner's toast, drawn with our own pixel font and icon).
Then the years run as memories: the CSI lab, the first suit, laughing in S.T.A.R. Labs. In the song's quiet pause, the
new hero object: THE LENSBALL, a glass sphere that holds his memories upside down (a real ball lens inverts the scene
behind it). The laugh is drawn into it, Barry now (S5, golden window light) stands behind it out of focus, and on each
soft piano note the ball turns to another memory (Iris by the water, the loft, the sea at sunset). On the pickup we fall
into the ball and the picture flips upright as the theme returns full-frame on the sea run. The S1 emblem then gets the
slow EMBLEM GLINT: the camera finds it, a corrected, lit bolt (fitted to the real S1 bolt) catches the light, lightning
crawls along its zigzag, and the disc opens on his face. The loop: the lights of the last memory flicker, the dark
medical bay flashes through, and the lights go out on frame 0, where they flicker back on and he wakes again.
The print (the instant photo) is used once, fast: PRINT DIVE between the lab and the first suit.
Look SUNFADE: golden hour on faded film. Overlay: a faint Super 8 haze, kept low so the clips stay clear. No text but
the owner's achievement toast. Sound: the song carries it; five quiet effects.

Song window: song half-beats 728 -> 824 (196.56 -> 222.48 s), 96 half-beats, 25.92 s; the build, the quiet pause
(e28-e44: single notes on e30, e34, e38, e42) and the return of the full theme at e46 (song 208.97 s). The section has no
drums: grid fitted on the music stem (song_prep: P = 0.26997 s, offset 0.0100 s, checked on the piano onsets).
Strong onsets in the build (music stem, spectral flux): e4, e10, e12, e14, e16, e22, e26.
Loop wrap: music spectral correlation 0.906 (the best of the candidate windows).
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v14", "keepsakes"          # folder + output name: v14/out/keepsakes_voidfx_9x16.mp4
SONG = f"{ROOT}/src/mice_on_venus.mp3"                 # decoded to v14/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 188.788
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height)
SRC = {"fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720), "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720),
       "fs5": (f"{ROOT}/src/flash_s5.mp4", 23.976, 1280, 720)}

HB, HB_OFF = 0.269970, 0.0100              # music-stem fit (no drums in the window)
H0, H1 = 728, 824
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 46; DROP_HB = HDROP; T_STOP = DUR  # the theme returns (song 208.97 s)
E_BALL = 30                                # THE LENSBALL: the laugh is drawn into the glass on the pause's first note
BALL_NOTES = [30, 34, 38, 42]              # the ball turns to another memory on each soft note; e44 the dive, e46 the return
E_TOAST = 4                                # the achievement pops on the gasp (a strong onset)
E_TOAST_OUT = 13
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 46, 28
E_LOOP = H1 - H0 - 4                       # the loop set piece: the lights flicker out (the beat camera rests from here)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []
VO_STEM = None; VO_STEM_T0 = 0.0

def slow(e0, e1, a, b, ease=0.35, n=64):
    """a gentle speed curve for a nostalgic shot: the same source range a..b, a touch faster at the head and slower at
    the tail (a memory settling). Use with lin=True, interp="flow"."""
    import numpy as _np
    u = _np.linspace(0, 1, n); s = 1 - (1 - u) ** (1 + ease)            # eases out: arrives slowly
    return [(float(x), float(a + (b - a) * y)) for x, y in zip(u, s)]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "sunfade"),
             z=kw.pop("z", [(0, 1.00), (1, 1.04)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- THE WAKE (focal set piece at the start): the dark medical bay, the lights flicker on, he gasps awake (S1)
shot("wake", "fs1", 0, 10, 4.135, 5.02, tin="lights_on14", seg=True, lin=True, flowfall="blend",
     tmap=[(0, 4.135), (0.15, 4.18), (0.40, 4.55), (1.0, 5.02)], z=[(0, 1.00), (1, 1.05)])
shot("woke", "fs1", 10, 14, 7.30, 8.50, tin="focus_rack14", seg=True)
# ---- S1: the first year
shot("lab", "fs1", 14, 20, 68.80, 70.45, tin="double_exp", seg=True, z=[(0, 1.02), (1, 1.06)])
shot("hood", "fs1", 20, 26, 124.00, 125.60, tin="print_dive", seg=True, tmap=slow(20, 26, 124.00, 125.60), lin=True)
shot("laugh", "fs1", 26, 30, 214.45, 215.50, tin="film_burn", seg=True)
# ---- THE LENSBALL (the song's pause): Barry now, behind the glass; his memories turn inside it on the soft notes
shot("ball", "fs5", 30, 46, 89.82, 90.90, tin="lens_in14", seg=True, tmap=slow(30, 46, 89.82, 90.90), lin=True, z=[(0, 1.00), (1, 1.03)])
# ---- the theme returns: the sea run at sunset, out of the ball
shot("searun", "fs1", 46, 52, 116.42, 118.05, tin="lens_dive14", seg=True, face=None, cx=(700, 420), flowmax=24, flowfall="blend")
shot("shore", "fs1", 52, 56, 120.30, 121.45, tin="ripple", seg=True, face=None, cx=(590, 610))
shot("emblem", "fs1", 56, 64, 226.78, 227.95, tin="sun_flare", seg=True, tmap=slow(56, 64, 226.78, 227.95), lin=True, z=[(0, 1.00), (1, 1.00)])
# ---- the years after
shot("smile3", "fs3", 64, 70, 3.30, 5.20, tin="emblem_glint", seg=True)
shot("ballgame", "fs5", 70, 76, 91.20, 92.90, tin="speed_whip14", seg=True)
shot("shades", "fs3", 76, 82, 26.90, 28.50, tin="light_leak14", seg=True)
shot("tux", "fs5", 82, 88, 101.40, 102.95, tin="dolly", seg=True)
shot("today", "fs5", 88, 96, 0.05, 2.25, tin="afterimage14", seg=True, z=[(0, 1.00), (1, 1.03)])

# the memories inside THE LENSBALL: (note, pack, source a, source b, source x centre of the 9:16 crop)
BALL = [(30, "fs1", 215.50, 216.30, None),            # the laugh, carried into the glass (the previous shot's crop)
        (34, "fs1", 229.50, 231.10, 610),             # Iris and Barry by the water (S1)
        (38, "fs3", 46.40, 48.10, 690),               # the loft, warm lamps (S3)
        (42, "fs1", 116.37, 116.42, 700)]             # the sea run's lead-in (the sun on the water): the memory we fall into at e44-e46

# the real S1 chest emblem in flash_s1.mp4 (226.73-228.0 s), measured on the source: circle centre per source frame
# (template-tracked, 5-tap smoothed), radius, and the bolt as a polygon in units of the radius about the centre, traced
# on the real emblem (a point-symmetric zigzag: top tip past the ring at the upper right, a step, bottom tip lower left).
EMB_R = 74.5
EMB_BOLT = [(0.884, -1.179), (-0.436, -0.074), (-0.075, -0.095), (-0.862, 0.763), (0.458, -0.342), (0.097, -0.321)]
EMB_TRACK = [(226.733, 435.8, 698.9), (226.767, 437.8, 699.5), (226.833, 440.6, 700.2), (226.867, 443.7, 700.9), (226.900, 446.3, 701.4),
             (226.933, 448.2, 701.8), (226.967, 449.4, 702.3), (227.000, 450.1, 703.0), (227.033, 450.2, 703.6), (227.067, 449.5, 704.1),
             (227.100, 447.8, 704.5), (227.167, 445.4, 704.9), (227.200, 442.7, 705.3), (227.233, 440.1, 705.7), (227.267, 437.9, 706.3),
             (227.333, 436.2, 706.9), (227.367, 434.9, 707.3), (227.400, 433.7, 707.6), (227.433, 432.8, 707.9), (227.467, 432.0, 708.4),
             (227.500, 431.3, 709.2), (227.533, 430.8, 709.7), (227.567, 430.4, 709.6), (227.600, 430.1, 708.9), (227.667, 429.7, 707.8),
             (227.700, 429.3, 706.5), (227.733, 428.7, 705.5), (227.767, 428.4, 704.7), (227.833, 428.1, 704.2), (227.867, 427.9, 703.6),
             (227.900, 427.7, 702.9), (227.933, 427.5, 702.1), (228.000, 427.2, 701.5)]

SET_PIECES = [("the_wake", th(0), th(14)), ("lensball", th(30), th(47)), ("emblem_glint", th(58), th(65)), ("loop", th(92), th(96))]
HERO = ["lens_ball"]
HERO_TINS = ["lens_in14", "lens_dive14"]
SIGNATURE = ["lens_dive14"]
PLAN_ACCEPT = {
    "density": "a slow, nostalgic piano piece: 14 designed transitions plus the lensball's three turns; the owner asked to see the clips",
    "retake:ball/ballgame": "different scenes (golden window vs the ballgame), split by a source cut at 90.92/90.97 s",
    "dead:ball": "THE LENSBALL: the ball forms, bobs, and turns to a new memory on each soft note (e30, e34, e38, e42)",
    "dead:wake": "THE WAKE: the lights flicker on (frames 8-24), he rises and gasps (the slow-motion sit-up), the achievement pops up on e4 and animates through e13",
    "dead:today": "the loop: the lights flicker on e92 and e94 with the dark medical bay flashing through, then go out from frame 1535",
    "sig_time:lens_dive14": "the lensball is on screen from frame 486 to the cut at 745 (4.3 s); the check times only the dive",
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
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "return", round(th(HDROP), 3), "song in", round(SONG_IN, 3))
