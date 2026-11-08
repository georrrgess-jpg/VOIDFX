"""LET GO — The Flash × Ark Patrol "Let Go" (ft. Veronika Redd) (voidfx v102, 9:16). Single source of truth.

Concept: he's been holding it back, then he lets go. Cold open on the song's second breakdown (bass + vocal chops, no
drums): time is frozen around an unmasked Barry, sparks hanging in the air; the lightning starts to crawl over him; he
pulls the cowl on; the riser builds under his on-camera line "How's this for power?" (lip-synced). On "power?" time
freezes, a bolt strikes through him and the drop (2:20.56, the song's biggest change, +31 dB) explodes as he unleashes
lightning; LET GO slams in behind him. A speed montage on the drop (runs with afterimages, a speed-ramped run into the
lens, a wall run turned vertical, lightning on his face, the grin, the glowing eyes). Ending: he runs so fast he goes
back in time: the whole edit rewinds in a second (picture and sound together) and lands on the first frame (the loop).
Song window: half-beats 720 -> 848 (16 bars, 163.96 BPM, 2:11.78 -> 2:35.20), drop at h768; the last 6 half-beats are
the rewind, which ends exactly on the edit's first frame and first sample.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v102", "let_go_flash"
SONG = f"{ROOT}/src/let_go.mp3"
FPS, W, H = 60, 1080, 1920
SRC = {"fb": (f"{ROOT}/src/flash_b.mp4", 60.0, 1280, 720), "fa": (f"{ROOT}/src/flash_a.mp4", 25.421, 1280, 720)}

HB, HB_OFF = 0.18297, 0.0366                     # tools/song_map.py (v102/work/song_map.json); bar = 8 half-beats
H0, H1, HDROP = 720, 848, 768
H_RISER = 752                                     # hats build, bass falls away
H_REW = 842                                       # the rewind starts here
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(h): return st(h) - SONG_IN
def fe(t): return int(round(t * FPS))
def fh(h): return fe(th(h))
def s2e(s): return s - SONG_IN
DUR = th(H1); DUR_F = fh(H1)
def te(h): return th(h)
T_STOP = DUR; DROP_HB = HDROP
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
T_DROP = th(HDROP); T_REW = th(H_REW)

# ---- dialogue: "How's this for power?" (fb 110.96-112.00; on camera, checked with tools/lipcheck.py -> v102/frames/lip_power.jpg)
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/fb_100_140/vocals.wav"; VO_STEM_T0 = 100.0
PWR_A = 110.18                                    # power shot source in (1:1 so the lips stay in sync)
PWR_E = th(756)
def pwr_e(src_t): return PWR_E + (src_t - PWR_A)
VO = [(110.88, 112.08, pwr_e(110.88))]
SONG_VOX = f"{ROOT}/{VER}/audio/sep/htdemucs/let_go"; SONG_VOX_T0 = 0.0
VOX_MUTE = (pwr_e(110.88) - 0.12, T_DROP - 0.02)  # the song's riser vocal chops step aside under the line
T_FREEZE = pwr_e(112.02)                          # time stops on "power?"

S = []
def shot(n, src, t0, t1, a, b, **kw):
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "storm"),
             z=kw.pop("z", [(0, 1.00), (1, 1.06)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- cold open: the breakdown (bars 90-93) and the riser (bars 94-95)
shot("still", "fb", th(720), th(732), 37.15, 38.52, tin="rewind_in", z=[(0, 1.02), (1, 1.10)], seg=True, motes=True, eyespark=True)
shot("charge", "fb", th(732), th(744), 83.83, 85.06, tin="bolt_link", z=[(0, 1.00), (1, 1.10)], seg=True, sarcs=0.8)
shot("suit", "fb", th(744), th(756), 69.25, 71.45, tin="overcharge", z=[(0, 1.00), (1, 1.07)])
fz = (T_FREEZE - th(756)) / (th(768) - th(756))
shot("power", "fb", th(756), th(768), PWR_A, 112.38, tmap=[(0, PWR_A), (fz, 112.02), (1, 112.06)], tin="whip",
     z=[(0, 1.00), (fz, 1.08), (1, 1.12)], interp="hold", seg=True, freeze=True)
# ---- the drop: he lets go
shot("throw", "fb", th(768), th(772), 124.20, 124.78, tin="strike", face=None, cx=(790, 760), z=[(0, 1.10), (1, 1.02)],
     title=True, interp="blend")
shot("scream", "fb", th(772), th(776), 127.70, 128.43, z=[(0, 1.06), (1, 1.10)], title=True, interp="blend")
shot("charged", "fb", th(776), th(784), 113.10, 114.56, tin="emblem", z=[(0, 1.00), (1, 1.06)], seg=True, sarcs=0.5)
shot("approach", "fb", th(784), th(796), 65.05, 68.60, tmap=[(0, 65.05), (0.30, 66.55), (0.78, 67.95), (1, 68.60)], tin="remnant",
     z=[(0, 1.00), (1, 1.04)], face=None, cx=(745, 745))
shot("wallrun", "fb", th(796), th(804), 80.85, 82.25, tin="passby", face=None, rot=True, z=[(0, 1.04), (1, 1.10)])
shot("crackle", "fb", th(804), th(812), 89.75, 91.05, tin="bolt_split", z=[(0, 1.00), (1, 1.08)], target=0.33)
shot("darkbolt", "fb", th(812), th(816), 53.40, 54.13, tin="smear", z=[(0, 1.00), (1, 1.04)])
shot("grin", "fb", th(816), th(824), 56.10, 57.56, tin="logo_orig", z=[(0, 1.00), (1, 1.08)])
shot("eyes", "fb", th(824), th(832), 116.62, 118.08, tin="impact", z=[(0, 1.02), (1, 1.12)], seg=True, sarcs=0.6)
shot("final_run", "fb", th(832), th(848), 4.30, 6.13, tmap=[(0, 4.30), ((th(H_REW) - th(832)) / (th(848) - th(832)), 6.13), (1, 6.13)],
     tin="shockwave", tout="rewind_end", z=[(0, 1.04), (1, 1.10)], seg=True, echoes=True, sarcs=0.5)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text: bold, high-contrast two-line captions (WARMPOP style, Flash palette); each word eases in on its spoken time
TEXT = [
    dict(style="cap", words=[("HOW'S", pwr_e(110.96), 0), ("THIS", pwr_e(111.32), 0), ("FOR", pwr_e(111.44), 1), ("POWER?", pwr_e(111.62), 1)],
         end=T_DROP - 0.04, emph=["POWER?"], band=(1300, 1560)),
    dict(style="title", words=[("LET", T_DROP + 0.01, 0), ("GO", th(772) + 0.01, 0)], end=th(776) - 0.40, emph=[], band=(1180, 1640)),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAP_Y = (1360, 1488)

# ---- engine knobs
CAPS = []; END_CAP = []
DROP_TITLE = None
MONTAGE = (HDROP, H_REW)
VANISH_T0 = None
CLOSE_T = None
ACCENTS = [th(h) for h in range(HDROP, H_REW, 4)]   # kick / snare pattern of the drop (every beat)
CHOPS = [th(h) for h in range(724, 768, 3)]         # the breakdown's vocal chops (vocal-stem peaks every 3 half-beats)

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]
        print(f"{s['n']:10s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {ts[0]:7.2f}-{ts[-1]:7.2f} x{(ts[-1] - ts[0]) / (s['t1'] - s['t0']):.2f} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(T_DROP, 3), "freeze", round(T_FREEZE, 3), "rewind", round(T_REW, 3), "VO at", [round(v[2], 2) for v in VO])
    for t_ in TEXT: print(f"  {t_['style']:6s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
