"""MEMORY REBOOT — The Flash × VØJ & Narvent "Memory Reboot" (voidfx v19, 9:16). Single source of truth: the renderer,
audio builder and QC read only this file. Scaffolded from the v12 BLOOM standard engine; v17's and v18's toolkits are carried
in sec19.py.

Concept: MEMORY REBOOT. The Speed Force keeps every moment he has lived. Before the drop we are in his memories: soft,
faded, the colour of an old photograph under neon, and panes of light (memories, each holding a frame of the edit) drift in
the dark behind him. THE HOOK: a memory pane rises out of the city's bokeh behind him, swings toward the lens and we fall
into it. The break (the bass drops out, e16): time stops; in the Speed Force his memories orbit him (MEMORY STORM). They
pour into the real chest emblem, which charges and fires the reboot on the drop (EMBLEM REBOOT, e24): a shock ring runs
out of the emblem and behind it the world is the vivid neon present, a new scene on every beat. THE LOOP: he runs at us
down the avenue; a pane holding frame 0 (live) races toward us past him and fills the lens: his first memory.
The hero asset is THE MEMORY PANES: the hook, the dive into the Speed Force, the emblem reboot, the loop.
Looks: MEMORY (before the drop): lifted blacks, colour faded to 60 %, teal shadows, peach-magenta highlights, a red halation
round the lights. NEON (from the drop): deep violet-blue shadows, rich red, cyan-white highlights, a magenta-cyan bloom.
Song window: song half-beats 392 -> 448 (163.13 -> 186.43 s), 56 half-beats, 23.30 s; grid fitted on the Demucs drum stem
(song_prep: P = 0.416078 s, offset 0.0303 s; 144 BPM, a beat each e). The bass drops out for the bar e16-e24; the drop is
e24. The vocal chops land on every even e from the drop. Barry only (no side characters); the high-bitrate packs (fbh,
fs2, fs5) wherever possible. Excluded on the owner's brief: Barry with lightning in his eyes.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v19", "reboot"          # folder + output name: v19/out/reboot_voidfx_9x16.mp4
SONG = f"{ROOT}/src/memory_reboot.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 155.124
FPS, W, H = 60, 1080, 1920
SRC = {"fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720),
       "fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720), "fs2": (f"{ROOT}/src/flash_s2.mp4", 60.0, 1280, 720),
       "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720), "fs5": (f"{ROOT}/src/flash_s5.mp4", 23.976, 1280, 720)}

HB, HB_OFF = 0.416078, 0.0303
H0, H1 = 392, 448
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 24; DROP_HB = HDROP; T_STOP = DUR
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 0, 0
E_BREAK = 16                                    # the bass drops out: time stops (MEMORY STORM)
E_DROP = 24                                     # the drop: EMBLEM REBOOT
E_STRIKE = 16
E_LOOP = 50.5                                     # THE LOOP: the pane holding frame 0
E_REST = 50
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
KICKS = [0.0, 1.0, 2.0, 3.0]
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
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "neon"),
             z=kw.pop("z", [(0, 1.00), (1, 1.04)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- before the drop (e0-e16): MEMORY, his memories in the dark; panes drift behind him
shot("van", "fbh", 0, 3, 106.40, 107.40, tin="loop19", seg=True, lin=True, tmap=[(-0.12, 106.30), (0, 106.40), (1, 107.40)], tneg=True,
     z=LinZ([(0, 1.02), (1, 1.06)]), look="memory", anim="panes")                  # frame 0: the S5 suit on a wet neon street at night; THE HOOK: a pane rises out of the dark behind him
shot("run5", "fs5", 3, 5, 72.00, 72.90, tin="pane_pass", seg=True, look="memory")                # we fall into the pane: the night run
shot("device", "fbh", 5, 7, 49.95, 50.80, tin="chroma_split", seg=True, look="memory")          # the S2 suit, the chest device lit
shot("s3night", "fs3", 7, 9, 59.40, 60.30, tin="bokeh_rack", seg=True, look="memory", anim="panes")
shot("blast", "fbh", 9, 11, 127.55, 128.15, tin="flare_cut", seg=True, look="memory")           # he fires the lightning from his hand
shot("thinks", "fbh", 11, 13, 136.55, 137.30, tin="crash_zoom", seg=True, look="memory")                # masked, at night, the city behind him
shot("roof", "fs5", 13, 16, 138.64, 139.60, tin="vertigo", seg=True, face=None, cx=(720, 700), look="memory", anim="panes")   # he stands over the city lights
# ---- the break (e16-e24): time stops; the memories orbit him, then pour into the emblem
shot("sf", "fs3", 16, 21, 132.80, 134.30, tin="pane_dive", seg=True, look="memory", anim="storm")  # MEMORY STORM: in the Speed Force his memories orbit him
shot("hero", "fbh", 21, 24, 109.80, 110.95, tin="mist_pass", seg=True, look="memory", anim="converge")   # they pour into the real emblem; it charges
# ---- the drop (e24-e51): NEON, the present, a new scene on every beat
shot("ltrun", "fs2", 24, 26, 144.55, 145.40, tin="emblem_reboot", seg=False, face=None, cx=(1040, 1000), tmap=vel(24, 26, 144.55, 145.40), lin=True, flowmax=40, flowfall="blend")
shot("charge", "fs5", 26, 28, 180.00, 180.90, tin="spark_jump", seg=True, anim="crackle")
shot("s3mask", "fs3", 28, 30, 106.80, 107.70, tin="lightbar_streak", seg=True)
shot("flight", "fbh", 30, 32, 81.00, 81.90, tin="smear17", seg=True, face=None, cx=(600, 640), tmap=vel(30, 32, 81.00, 81.90), lin=True, flowmax=40, flowfall="blend")
shot("fire", "fbh", 32, 34, 84.45, 85.05, tin="glare_wash", seg=True, anim="embers")
shot("airfield", "fs1", 34, 36, 199.60, 200.40, tin="ember_burn", seg=True, face=None, cx=(680, 800))
shot("runlit", "fbh", 36, 38, 4.55, 6.10, tin="lightning_whip", seg=True, tmap=vel(36, 38, 4.55, 6.10), lin=True, flowmax=40, flowfall="blend")
shot("breakout", "fbh", 38, 40, 52.92, 53.62, tin="cube_turn", seg=True, ev=0.25)
shot("lrun", "fs5", 40, 42, 119.20, 120.60, tin="peel17", seg=True, face=None, cx=(930, 860), lin=True, flowmax=90, flowfall="blend")
shot("mgrin", "fs1", 42, 44, 252.25, 253.60, tin="streak_carry", seg=True)                       # the S1 suit grins
shot("wet", "fs2", 44, 46, 77.20, 78.20, tin="zip17", seg=True, face=None, cx=(840, 820), flowmax=40, flowfall="blend")
shot("run5b", "fs5", 46, 48, 113.00, 113.85, tin="speed_zoom", seg=True, flowmax=40, flowfall="blend")
shot("trail", "fs5", 48, 50, 87.90, 88.90, tin="light_streak", seg=True, face=None, cx=(470, 400))
# ---- THE LOOP (e51-e56): he runs at us down the avenue; the pane holding frame 0 races toward us past him and fills the lens
shot("avenue", "fbh", 50, 56, 64.80, 66.30, tin="bolt_window", seg=True, face=None, cx=(640, 640), tmap=vel(50, 56, 64.80, 66.30, lo=0.7, hi=1.4), lin=True, interp="hold")

EMB_TRACK = [(109.75, 552.6, 636.6, 59.3), (109.8, 563.4, 646.2, 58.0), (109.85, 580.0, 650.0, 58.0), (109.9, 600.0, 652.2, 58.0), (109.95, 618.0, 654.6, 58.0),
             (110.0, 633.0, 658.0, 58.5), (110.05, 648.6, 659.4, 58.5), (110.1, 664.0, 662.0, 58.5), (110.15, 680.0, 664.0, 58.5), (110.2, 692.0, 666.0, 58.5),
             (110.25, 702.6, 667.0, 58.5), (110.3, 714.0, 667.5, 58.0), (110.35, 727.0, 668.0, 58.0), (110.4, 738.6, 668.5, 57.5), (110.45, 747.0, 670.2, 57.5),
             (110.5, 756.6, 672.5, 58.0), (110.55, 766.2, 674.0, 57.5), (110.6, 778.0, 676.0, 57.5), (110.65, 786.0, 678.0, 58.0), (110.7, 790.0, 679.5, 58.5),
             (110.8, 785.0, 679.8, 58.5), (110.9, 777.0, 679.8, 58.5), (111.0, 765.0, 679.8, 58.5)]   # the chest emblem in flash_b_hq 109.75-111.0 s (Hough on the source, outliers dropped, smoothed): (t, x, y, r)
SET_PIECES = [("hook", th(0), th(3)), ("memory_storm", th(16), th(21)), ("emblem_reboot", th(21), th(26)), ("pane_loop", th(51), th(56))]
HERO = ["pane_draw"]
HERO_TINS = ["pane_pass", "pane_dive", "emblem_reboot", "loop19"]
SIGNATURE = ["emblem_reboot", "pane_pass"]
PLAN_ACCEPT = {'pf:hero motif:the hero asset (pane_draw) is drawn by 6': "the panes are drawn by pane_pass, pane_dive and the loop; the other transitions only show the edge frame of a memory shot whose living animation has panes drifting in its background"}
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
