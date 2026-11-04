"""THE LESS YOU KNOW — Dexter × Tame Impala "The Less I Know The Better" (voidfx v101, 9:16). Single source of truth.

Concept: Dexter is about to tell you his secret — and the film burns before he can. A 16 mm psychedelic reel (oxblood,
amber and plum, liquid-light projections, film grain, halation). Cold open on the song's 4-bar drum intro: a hooded
figure strikes up out of the projector light, the glove goes on, and Dexter, lit by a liquid-light show on the curtains
behind him, says "I'm gonna tell you something that I've never told anyone before." The projector stalls on his face,
the frame blisters and BURNS THROUGH exactly as the bassline drops (song 10.08 s). THE LESS YOU KNOW lands note by note
on the bass over his strut through the container yard; the montage on the groove shows what he never says (hood, gloves,
knife, blood, the burning photo, the SHIPPING YARD MASSACRE headline, the bag going over the side of the boat, the voidfx
logo, the smirk, the rapture). Ending: he puts a finger to his lips — "shh" — the frame freezes as the groove breaks
into the song's own intro pickup: THE BETTER. The reel runs out, black, and the projector strikes up again (loop).
Song window: half-beats 7 -> 95 (11 bars, 116.99 BPM), drop at h39; the last half bar (h91-h95) is replaced by the
song's intro pickup (h3-h7), so the wrap back to h7 is the song's own first downbeat.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v101", "less_i_know_dexter"          # output: v101/out/less_i_know_dexter_voidfx_9x16.mp4
SONG = f"{ROOT}/src/less_i_know.mp3"
FPS, W, H = 60, 1080, 1920
SRC = {"p8": (f"{ROOT}/src/pack8_s1.mp4", 60.0, 1280, 720), "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720),
       "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720)}
FONTS = f"{ROOT}/{VER}/fonts"

HB, HB_OFF = 0.256441179138322, 0.08334338321995464          # tools/song_map.py (beats fall on odd half-beats)
H0, H1, HDROP = 7, 95, 39
H_BREAK = 91                                                  # groove -> intro pickup (h3..h7) for the last half bar
PICKUP_H = 3
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
T_DROP = th(HDROP)

# ---- dialogue (pack8 seconds; Demucs vocal stem of pack8 318-330 s). Lip-synced on the confession shot.
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/p8_dialogue/vocals.wav"
VO_STEM_T0 = 318.0
CONF_A = 321.21                        # confession shot source in (its cut is 321.18; the show's own jump cut is 325.217)
CONF_E = th(23)                        # edit time the confession shot starts
def conf_e(src_t): return CONF_E + (src_t - CONF_A)
VO = [(321.20, 325.20, conf_e(321.20))]   # "I'm gonna tell you something that I've never told anyone before."
SONG_VOX = f"{ROOT}/{VER}/audio/sep/htdemucs/song_0_60"     # song stems from 0 s (vocals / no_vocals)
SONG_VOX_T0 = 0.0
VOX_MUTE = (conf_e(321.20) - 0.25, conf_e(325.20) + 0.10)   # the song's faint intro vocal steps aside under his line

S = []
def shot(n, src, t0, t1, a, b, **kw):
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "psych"),
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- cold open: the drum intro (4 bars)
shot("hooded", "p1", th(7), th(15), 143.55, 145.02, tmap=[(0, 143.55), (0.5, 144.06), (1, 145.02)], tin="projector_on",
     face=None, cx=(560, 600), z=[(0, 1.10), (1, 1.00)], target=0.78)
shot("gloves", "p1", th(15), th(23), 45.66, 47.58, tin="latex", z=[(0, 1.00), (1, 1.10)])
shot("confess", "p8", th(23), th(39), CONF_A, 325.20, tmap=[(0, CONF_A), ((325.20 - CONF_A) / (th(39) - th(23)), 325.20), (1, 325.20)],
     tin="frameslip", z=[(0, 1.00), (1, 1.10)], seg=True, liquid=True, interp="hold")
# ---- the drop: the film burns through into the groove
shot("strut", "p1", th(39), th(47), 23.55, 25.22, tmap=[(0, 23.55), (0.25, 23.80), (1, 25.22)], tin="filmmelt",
     z=[(0, 1.06), (1, 1.00)], face=None, cx=(560, 600), seg=True, prism=True)
shot("hoodup", "p8", th(47), th(51), 303.55, 304.58, tin="whip", z=[(0, 1.00), (1, 1.10)])
shot("gloving", "p7", th(51), th(55), 6.20, 7.23, tin="hooddark", z=[(0, 1.05), (1, 1.12)], interp="hold", warm=1.0)
shot("knife", "p1", th(55), th(59), 157.95, 158.83, tin="scalpel", z=[(0, 1.00), (1, 1.08)])
shot("bloodslide", "p8", th(59), th(63), 44.55, 45.58, tin="lavalamp", face=None, cx=(600, 640), z=[(0, 1.00), (1, 1.12)], target=0.36)
shot("burnphoto", "p8", th(63), th(67), 221.90, 222.93, tin="slidewipe", z=[(0, 1.00), (1, 1.08)])
shot("newspaper", "p4", th(67), th(71), 75.15, 75.95, tin="newsspin", face=None, cx=(520, 560), z=[(0, 1.00), (1, 1.06)], interp="hold")
shot("boat", "p8", th(71), th(79), 258.60, 260.65, tin="papertear", z=[(0, 1.00), (1, 1.06)])
shot("smirk", "p8", th(79), th(83), 283.32, 284.35, tin="logo_orig", z=[(0, 1.00), (1, 1.08)])
shot("rapture", "p1", th(83), th(87), 147.00, 148.03, tin="oilwheel", z=[(0, 1.00), (1, 1.08)])
shot("shh", "p1", th(87), th(95), 96.30, 97.33, tmap=[(0, 96.30), (0.5, 97.326), (1, 97.33)], tin="facematch", tout="reel_end",
     z=[(0, 1.00), (0.5, 1.10), (1, 1.16)], interp="hold")
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
T_FREEZE = th(H_BREAK)                 # the shh freezes as the groove breaks

# ---- text: every word on its spoken time / a bass note. styles: cap (two-line eased caption; the second one burns with
#      the film on the drop), title (THE LESS / YOU KNOW: liquid-light letters that land on the bassline), better (the end)
def vw(src_t): return conf_e(src_t)
TEXT = [
    dict(style="cap", words=[("I'M", vw(321.27), 0), ("GONNA", vw(321.40), 0), ("TELL", vw(321.52), 0), ("YOU", vw(321.66), 0),
                             ("SOMETHING", vw(321.82), 1)], end=vw(323.25), emph=["SOMETHING"], band=(1290, 1530)),
    dict(style="cap", words=[("THAT", vw(323.57), 0), ("I'VE", vw(323.75), 0), ("NEVER", vw(323.92), 0),
                             ("TOLD", vw(324.06), 1), ("ANYONE", vw(324.34), 1), ("BEFORE.", vw(324.62), 1)], end=T_DROP, emph=["NEVER"], burn=True, band=(1290, 1530)),
    dict(style="title", words=[("THE", s2e(10.153), 0), ("LESS", s2e(10.548), 0), ("YOU", s2e(11.105), 1), ("KNOW", s2e(11.691), 1)],
         end=th(47) - 0.16, emph=[], band=(1220, 1610)),
    dict(style="better", words=[("THE", th(89) + 0.02, 0), ("BETTER.", th(H_BREAK), 0)], end=DUR - 0.30, emph=[], band=(1250, 1540)),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAP_Y = (1352, 1466)

# ---- bassline accents (song seconds, Demucs bass-stem onsets) -> edit seconds: the title bounces and the prism silhouettes pulse on them
ACCENTS = [s2e(x) for x in (10.153, 10.548, 11.105, 11.691, 12.214, 12.713, 13.177, 13.764, 14.629, 14.826, 15.778, 16.295, 16.881,
                            18.054, 18.338, 18.646, 18.750, 19.006, 19.882, 20.434, 20.532, 21.937)]

# ---- engine knobs (older engine compatibility)
CAPS = []; END_CAP = []
DROP_TITLE = None
MONTAGE = (HDROP, H_BREAK)
VANISH_T0 = None
CLOSE_T = None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]
        sp = (ts[-1] - ts[0]) / (s["t1"] - s["t0"])
        print(f"{s['n']:10s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {ts[0]:7.2f}-{ts[-1]:7.2f} x{sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(T_DROP, 3), "freeze", round(T_FREEZE, 3), "VO at", [round(v[2], 2) for v in VO])
    for t_ in TEXT: print(f"  {t_['style']:7s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
