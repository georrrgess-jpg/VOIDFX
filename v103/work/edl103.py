"""FOREVER — Dexter × Foo Fighters "Everlong" (voidfx v103, 9:16). Single source of truth.

Concept: "I don't have feelings about anything." The only place anything feels real to him is the kill, and he keeps
every one forever (a drop of blood on a glass slide). The Gulf Stream keeps the rest. Three showpieces: THE SAMPLE
(drop), THE ARCHIVE (hook), THE GULF STREAM (loop). See v103/README.md for the pre-render check.
Song window: half-beats 1000 -> 1080 + 1096 -> 1152 of "Everlong" (158 BPM), spliced on a downbeat (two riff bars
removed); the drop (full band) at edit half-beat k56.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v103", "forever_dexter"
SONG = f"{ROOT}/src/everlong.mp3"
FPS, W, H = 60, 1080, 1920
SRC = {"p8": (f"{ROOT}/src/pack8_s1.mp4", 60.0, 1280, 720), "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720),
       "p9": (f"{ROOT}/src/pack9_s4_best.mp4", 60.0, 1280, 720), "p10": (f"{ROOT}/src/pack10_s4_24p.mp4", 24.0, 1280, 720)}

HB, HB_OFF = 0.18987, 0.0047                        # tools/song_map.py --bpm 158
H0, H_SPL_OUT, H_SPL_IN, H1 = 1000, 1080, 1096, 1152
K_SPL = H_SPL_OUT - H0                              # edit half-beat of the splice (80)
K_END = K_SPL + (H1 - H_SPL_IN)                     # 136
HDROP = 56                                          # edit half-beats from here on (k)
def st(h): return HB_OFF + h * HB                   # song seconds of song half-beat h
def th(k): return k * HB                            # edit seconds of edit half-beat k
def song_at(e):
    """song seconds heard at edit time e (the splice skips two bars)."""
    return st(H0) + e if e < th(K_SPL) else st(H_SPL_IN) + (e - th(K_SPL))
def s2e(sng):
    """edit time of a song time (on whichever side of the splice it lies)."""
    return sng - st(H0) if sng < st(H_SPL_OUT) else th(K_SPL) + (sng - st(H_SPL_IN))
def fe(t): return int(round(t * FPS))
def fh(k): return fe(th(k))
DUR = th(K_END); DUR_F = fh(K_END)
H1_EDIT = K_END
def te(k): return th(k)
T_STOP = DUR; DROP_HB = HDROP
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
T_DROP = th(HDROP); T_SPLICE = th(K_SPL)

# ---- dialogue: "I don't have feelings about anything," (p8 52.26-53.86; Dexter's narration, so played as VO over a
#      shot where he is not speaking). Stem: Demucs of p8 48-60 s.
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/p8_52/vocals.wav"; VO_STEM_T0 = 48.0
VO_A, VO_B = 52.22, 53.90
VO_AT = 2.05
def vo_e(src): return VO_AT + (src - VO_A)
VO = [(VO_A, VO_B, VO_AT)]
SONG_VOX = f"{ROOT}/{VER}/audio/sep/htdemucs/everlong"; SONG_VOX_T0 = 0.0
VOX_MUTE = (VO_AT - 0.15, vo_e(VO_B) + 0.20)        # the bridge's faint whispers step aside under his line

S = []
def shot(n, src, k0, k1, a, b, **kw):
    d = dict(n=n, src=src, t0=th(k0), t1=th(k1), tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "undertow"),
             z=kw.pop("z", [(0, 1.00), (1, 1.06)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- cold open: the whispered bridge (near-silence -> guitars at k26 -> the build)
shot("boat", "p10", 0, 10, 111.00, 112.38, tin="surface", z=[(0, 1.10), (1, 1.02)], caustics=1.0)
shot("stare", "p9", 10, 26, 117.45, 120.55, tin="wave", z=[(0, 1.00), (1, 1.10)], caustics=0.6, snow=True)
shot("gloving", "p7", 26, 36, 6.20, 8.10, tin="lamp_on", z=[(0, 1.04), (1, 1.12)], interp="flow")
shot("table", "p8", 36, 44, 389.00, 390.36, tin="wrap", z=[(0, 1.00), (1, 1.06)], target=0.36)
shot("lean", "p9", 44, 56, 104.45, 106.75, tin="light_sweep", z=[(0, 1.02), (1, 1.12)], scalpel=True)
# ---- the drop: THE SAMPLE -> the montage on the riff
shot("drill", "p9", 56, 64, 180.25, 181.75, tin="sample", z=[(0, 1.10), (1, 1.02)], spatter=True)
shot("menace", "p8", 64, 68, 347.30, 348.10, tin="impact", z=[(0, 1.00), (1, 1.06)], spatter=True)
shot("knife", "p9", 68, 72, 178.30, 179.10, tin="knife_pass", z=[(0, 1.02), (1, 1.08)], spatter=True)
shot("torch", "p9", 72, 76, 185.40, 186.20, tin="whip", z=[(0, 1.00), (1, 1.06)], spatter=True)
shot("lookup", "p8", 76, 80, 355.40, 356.20, tin="tape", z=[(0, 1.00), (1, 1.06)], spatter=True)
shot("drive", "p8", 80, 90, 316.10, 318.00, tin="logo_orig", z=[(0, 1.00), (1, 1.06)])
# ---- "And I wonder" -> the hook: THE ARCHIVE -> THE GULF STREAM (loop)
shot("wonder", "p9", 90, 102, 230.70, 233.00, tin="rainfocus", z=[(0, 1.00), (1, 1.08)], rain=True)
shot("slide", "p8", 102, 112, 262.40, 264.32, tin="blood_lens", z=[(0, 1.00), (1, 1.04)], pushin=True, spot=(560, 420))
shot("archive", "p8", 112, 124, 264.32, 264.32, tin="drop_out", face=None, graphic="archive")
shot("overboard", "p8", 124, 136, 259.00, 260.65, tmap=[(0, 259.00), (0.62, 260.40), (1, 260.65)], tin="through_slide", face=None,
     cx=(700, 760), z=[(0, 1.00), (1, 1.08)], dayfornight=True, sink=True)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
# AAC pads the audio to 1024-sample blocks; one frame less keeps that padding under a frame (13 ms instead of 18 ms)
DUR_F = fh(K_END) - 1; DUR = DUR_F / FPS; T_STOP = DUR
SHOTS[-1]["f1"] = DUR_F; SHOTS[-1]["t1"] = DUR

# ---- the showpieces' timing
T_SURFACE = 1.10                                    # the camera breaks the surface
T_CUT = th(53)                                      # the scalpel draws the cut (beads well up until the drop)
T_SPLASH = s2e(218.36) - 0.55                       # the bag hits the water (as "forever" ends)
ARCH_IN = th(109)                                   # the push into the slide's drop
ARCH_FLY = th(112)                                  # out of the red into the corridor ("If")
ARCH_END = th(124)                                  # a slide rushes the lens; through it, the boat

# ---- text: v9 standard style. cap = keyline caption (emph words red); hero = per-letter title
def sw(sng): return s2e(sng)
TEXT = [
    dict(style="cap", words=[("I", vo_e(52.26), 0), ("DON'T", vo_e(52.66), 0), ("HAVE", vo_e(52.84), 0), ("FEELINGS", vo_e(52.88), 0),
                             ("ABOUT", vo_e(53.24), 1), ("ANYTHING.", vo_e(53.54), 1)], end=th(25), emph=["ANYTHING."]),
    dict(style="cap", words=[("BREATHE", sw(198.16), 0), ("OUT,", sw(198.64), 0), ("SO", sw(199.16), 1), ("I", sw(199.30), 1), ("CAN", sw(199.42), 1),
                             ("BREATHE", sw(199.52), 1), ("YOU", sw(199.66), 1), ("IN.", sw(199.76), 1)], end=th(54), emph=["BREATHE"]),
    dict(style="hero", lines=["EXCEPT", "THIS."], words=[("EXCEPT", T_DROP + 0.20, 0), ("THIS.", T_DROP + 0.20 + BEAT * 2, 1)], end=th(63) - 0.05,
         exit="blood"),
    dict(style="cap", words=[("AND", sw(210.0), 0), ("I", sw(210.84), 0), ("WONDER", sw(211.08), 1)], end=th(101), emph=["WONDER"], big=True),
    dict(style="cap", words=[("IF", sw(214.50), 0), ("EVERYTHING", sw(214.80), 0), ("COULD", sw(215.26), 0), ("EVER", sw(215.60), 0),
                             ("FEEL", sw(215.96), 1), ("THIS", sw(216.26), 1), ("REAL", sw(216.54), 1)], end=sw(216.78) + 0.30, emph=["REAL"]),
    dict(style="hero", lines=["FOREVER"], words=[("FOREVER", sw(216.78), 0)], end=T_SPLASH + 0.30, exit="bubbles"),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAP_Y = (1380, 1496)

# ---- engine knobs (older-engine compatibility)
CAPS = []; END_CAP = []; DROP_TITLE = None; VANISH_T0 = None; CLOSE_T = None
MONTAGE = (HDROP, K_SPL)
ACCENTS = [th(k) for k in range(HDROP, K_SPL, 4)]   # the riff's downbeats (spatter hits)

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]
        print(f"{s['n']:10s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']:3s} {ts[0]:7.2f}-{ts[-1]:7.2f} x{(ts[-1] - ts[0]) / (s['t1'] - s['t0']):.2f} in={s.get('tin', '')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(T_DROP, 3), "splice", round(T_SPLICE, 3), "splash", round(T_SPLASH, 3))
    for t_ in TEXT: print(f"  {t_['style']:5s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
