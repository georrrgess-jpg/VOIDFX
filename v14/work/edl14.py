"""KEEPSAKES — The Flash × C418 "Mice on Venus" (voidfx v14, 9:16). Single source of truth: the renderer, audio builder and
QC read only this file. Scaffolded from the v12 BLOOM standard engine.

Concept: KEEPSAKES. Nostalgia as a box of instant photos. Barry, now (S5, golden window light), looks back, and the years
develop in front of him like instant prints: the night he woke from the coma, the CSI lab, the first suit in the sun,
laughing in S.T.A.R. Labs, Iris by the water, the loft, the sea run at sunset, and on to the family ballgame and the
tux. The hero object is the print (a lit instant photo with a thick bottom border, paper grain, a soft shadow), a motif
in three places only: the signature graphic (a print develops beside him, then we fall into it), the focal set piece
THE ALBUM (in the song's quiet pause the memory freezes into a print and three more land on it, one per soft piano note;
we fall into the last one as the theme comes back), and the loop (the last memory becomes a print and slides away to
reveal frame 0). Instant-film development is the real phenomenon behind it: the image rises out of the milky reagent.
Every other transition is a different idea: a double exposure, a sun flare, a film burn, a water ripple, a focus rack,
the emblem's glint (the S1 emblem catches the sun and its bolt burns open the next memory), a speed whip, a dolly,
a light leak, an afterimage.
Look SUNFADE: golden hour on faded film (lifted warm blacks, cream highlights, gentle halation). Overlay: a faint
Super 8 haze (fine grain, sub-pixel gate weave, slow light leaks at the frame edges, a few dust specks), kept low so
the clips stay clear (the owner: "don't make the overlay too overbearing"). No text. Sound: the song carries it; four
quiet effects in all (the owner: "keep the sound effects low ... I don't want to overshadow the actual song").

Song window: song half-beats 728 -> 824 (196.56 -> 222.48 s), 96 half-beats, 25.92 s; the build, the quiet pause
(e28-e44: single notes on e30, e34, e38, e42) and the return of the full theme at e46 (song 208.97 s). The section has no
drums: grid fitted on the music stem (song_prep: P = 0.26997 s, offset 0.0100 s, checked on the piano onsets).
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
E_ALBUM = 30                               # THE ALBUM: the memory freezes on the pause's first note
ALBUM_NOTES = [30, 34, 38, 42]             # one print lands on each soft note; e44 is the pickup, e46 the return
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 46, 28
E_LOOP = H1 - H0 - 6                       # the loop set piece (the beat camera rests from here)
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

# ---- NOW: Barry in golden window light looks back; a print develops beside him (the signature graphic)
shot("now", "fs5", 0, 10, 89.82, 90.90, tin="loop_in14", seg=True, tmap=slow(0, 10, 89.82, 90.90), lin=True, z=[(0, 1.00), (1, 1.05)])
# ---- S1: where it started
shot("wake", "fs1", 10, 14, 4.47, 5.01, tin="print_dive", seg=True)
shot("lab", "fs1", 14, 20, 68.80, 70.45, tin="double_exp", seg=True, z=[(0, 1.02), (1, 1.06)])
shot("hood", "fs1", 20, 26, 124.00, 125.60, tin="sun_flare", seg=True, tmap=slow(20, 26, 124.00, 125.60), lin=True)
shot("laugh", "fs1", 26, 30, 214.45, 215.50, tin="film_burn", seg=True)
# ---- THE ALBUM (focal set piece, the song's pause): the laugh freezes into a print; three more land on the soft notes
shot("album", "fs1", 30, 46, 215.50, 215.52, tin="shutter_freeze", seg=True, z=[(0, 1.00), (1, 1.00)])
# ---- the theme returns: the sea run at sunset, out of the last print
shot("searun", "fs1", 46, 52, 116.75, 118.05, tin="album_out", seg=True, face=None, cx=(610, 410), flowmax=24, flowfall="blend")
shot("shore", "fs1", 52, 58, 120.30, 122.05, tin="ripple", seg=True, face=None, cx=(590, 620), tmap=slow(52, 58, 120.30, 122.05), lin=True)
shot("emblem", "fs1", 58, 62, 226.78, 227.95, tin="focus_rack14", seg=True)
# ---- the years after
shot("smile3", "fs3", 62, 68, 3.30, 5.20, tin="emblem_glint", seg=True)
shot("ballgame", "fs5", 68, 74, 91.20, 92.90, tin="speed_whip14", seg=True)
shot("shades", "fs3", 74, 80, 26.90, 28.50, tin="light_leak14", seg=True)
shot("tux", "fs5", 80, 86, 101.40, 102.95, tin="dolly", seg=True)
shot("today", "fs5", 86, 96, 0.05, 2.25, tin="afterimage14", seg=True, tmap=slow(86, 96, 0.05, 2.25), lin=True, z=[(0, 1.00), (1, 1.03)])

# the prints in THE ALBUM (memories that appear only there): (note, pack, source a, source b, landing x, landing y, angle)
ALBUM = [(30, "fs1", 215.50, 215.50, 540, 920, -3.0),          # the laugh, frozen (the previous shot's last frame)
         (34, "fs1", 229.50, 231.20, 505, 880, 5.5),           # Iris and Barry by the water (S1)
         (38, "fs3", 46.40, 48.20, 580, 950, -6.0),            # the loft, warm lamps (S3)
         (42, "fs1", 116.75, 116.75, 545, 900, 2.0)]           # the sea run at sunset: the print we fall into at e44-e46

SET_PIECES = [("print_signature", th(3), th(12)), ("the_album", th(30), th(47)), ("emblem_glint", th(60), th(64)), ("loop", th(90), th(96))]
HERO = ["print_draw"]
HERO_TINS = ["print_dive", "shutter_freeze", "album_out", "loop_in14"]
SIGNATURE = ["print_dive"]
PLAN_ACCEPT = {
    "density": "a slow, nostalgic piano piece: 14 designed transitions plus THE ALBUM's four landings; the owner asked to see the clips",
    "sig_time:print_dive": "the print is on screen from frame 46 to the cut at 162 (1.9 s); the check times only the dive",
    "retake:now/ballgame": "different scenes (golden window vs the ballgame), split by a source cut at 90.92/90.97 s",
    "dead:now": "the signature print rises and develops beside him from frame 46 (a designed animation)",
    "dead:album": "THE ALBUM: a print lands and develops on each soft note (e30, e34, e38, e42)",
    "dead:today": "the loop: the frame becomes a print and slides away from frame 1509",
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
