"""FOREVER — Dexter × Foo Fighters "Everlong" (voidfx v103, 9:16). Single source of truth.

Concept (rev 4): "How is it I can kill people and feel no regret?" The only place anything feels real to him is the kill, and
he keeps every one forever: he photographs it. The Gulf Stream keeps the rest. Three showpieces: THE RIP (drop: the
kill-room plastic tears open), THE EVIDENCE PHOTOS (hook), THE GULF STREAM (loop). See v103/README.md for the pre-render check.
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
H0, H_SPL_OUT, H_SPL_IN, H1 = 1008, 1080, 1096, 1152  # rev 2: starts one bar later (less quiet lead-in)
K_SPL = H_SPL_OUT - H0                              # edit half-beat of the splice (72)
K_END = K_SPL + (H1 - H_SPL_IN)                     # 128
HDROP = 48                                          # edit half-beats from here on (k)
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

# ---- dialogue (rev 2): "How is it I can kill people and feel no regret?" (p9 212.84-215.30; Dexter's narration, so it plays
#      as VO over shots where he isn't speaking). It ends on a natural question fall with 2.6 s of silence after it, so
#      nothing is cut off (rev 1's "...about anything," was mid-sentence and sounded clipped). Stem: Demucs of p9 205-225 s.
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/p9_205/vocals.wav"; VO_STEM_T0 = 205.0
VO_A, VO_B = 212.74, 215.46
VO_AT = 1.20
def vo_e(src): return VO_AT + (src - VO_A)
VO = [(VO_A, VO_B, VO_AT)]
SONG_VOX = f"{ROOT}/{VER}/audio/sep/htdemucs/everlong"; SONG_VOX_T0 = 0.0
VOX_MUTE = (VO_AT - 0.10, vo_e(VO_B) + 0.15)        # the bridge's faint whispers step aside under his line

S = []
def shot(n, src, k0, k1, a, b=None, **kw):
    if b is None: b = a + (k1 - k0) * HB             # 1:1 by default
    d = dict(n=n, src=src, t0=th(k0), t1=th(k1), tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "undertow"),
             z=kw.pop("z", [(0, 1.00), (1, 1.06)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- cold open: the whispered bridge -> the guitars come back at k18 -> the build. VO over the first three shots.
shot("boat", "p10", 0, 10, 111.00, 112.38, tin="surface", z=[(0, 1.10), (1, 1.02)], caustics=1.0)
shot("stare", "p9", 10, 18, 117.45, tin="wave", z=[(0, 1.00), (1, 1.08)], caustics=0.5, snow=True)
shot("green", "p8", 18, 26, 152.15, tin="ripple", z=[(0, 1.04), (1, 1.12)], caustics=0.35, target=0.42, desat=0.85)
shot("overhead", "p8", 26, 34, 31.70, tin="lamp_on", face=None, cx=(640, 640), z=[(0, 1.12), (1, 1.02)], swing=True)
shot("kitchen", "p8", 34, 40, 111.25, tin="light_sweep", z=[(0, 1.02), (1, 1.10)], target=0.40)
shot("lean", "p9", 40, 44, 104.45, tin="wrap", z=[(0, 1.02), (1, 1.10)])
# rev 4: in the plastic kill room; the sheeting is pulled over the lens as the build peaks, and rips open on the drop
shot("plasticroom", "p10", 44, 48, 167.60, tin="strobe", z=[(0, 1.00), (1, 1.10)], target=0.38, plastic=(th(45.0), th(47.6)))
# ---- the drop: THE RIP -> the montage on the riff (a move every 4 half-beats)
shot("drill", "p9", 48, 54, 180.25, tin="plastic_rip", z=[(0, 1.10), (1, 1.02)])
shot("menace", "p8", 54, 58, 347.30, tin="impact", z=[(0, 1.00), (1, 1.06)])
shot("knife", "p9", 58, 62, 178.30, tin="glass_shatter", z=[(0, 1.02), (1, 1.08)])
shot("torch", "p9", 62, 66, 185.40, tin="whip", z=[(0, 1.00), (1, 1.06)], flare=1.0)
shot("lookup", "p8", 66, 72, 355.40, tin="tape", z=[(0, 1.00), (1, 1.08)])
# ---- over the splice (under the logo) -> "And I wonder" -> THE EVIDENCE PHOTOS -> THE GULF STREAM (loop)
shot("drive", "p8", 72, 77, 316.10, tin="logo_orig", z=[(0, 1.00), (1, 1.06)])
shot("smirk", "p8", 77, 82, 283.32, tin="zipper", z=[(0, 1.00), (1, 1.08)])
shot("wonder", "p9", 82, 88, 230.70, tin="rainfocus", z=[(0, 1.00), (1, 1.08)], rain=True)
shot("moon", "p9", 88, 92, 229.98, 230.54, tin="whip_up", face=None, cx=(640, 640), z=[(0, 1.00), (1, 1.10)], moonglow=True)
shot("desk", "p8", 92, 98, 78.20, tin="bubbles_up", z=[(0, 1.02), (1, 1.10)], caustics=0.4)
# ---- rev 4 hook: THE EVIDENCE PHOTOS (replaces the slide archive). He raises the forensic camera; the ring flash fires on
#      "IF" and the frame becomes a photograph tossed away; a shutter; his wall of photos; the last flash takes us to the boat.
shot("camera", "p9", 98, 106, 120.75, tin="roll", face=None, cx=(700, 700), z=[(0, 1.00), (1, 1.10)])
shot("mirror", "p9", 106, 112, 158.30, tin="photo", z=[(0, 1.02), (1, 1.10)], target=0.40)
shot("photowall", "p10", 112, 116, 178.90, tin="shutter", z=[(0, 1.00), (1, 1.06)])
shot("overboard", "p8", 116, 128, 259.00, 260.65, tmap=[(0, 259.00), (0.62, 260.40), (1, 260.65)], tin="photo_l", face=None,
     cx=(700, 760), z=[(0, 1.00), (1, 1.08)], dayfornight=True, sink=True)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
# AAC pads the audio to 1024-sample blocks: trim the loop by up to 3 frames so the padding stays under ~12 ms (< 1 frame)
for _d in range(4):
    if (1024 - round((fh(K_END) - _d) / FPS * 48000) % 1024) % 1024 <= 576: break
DUR_F = fh(K_END) - _d; DUR = DUR_F / FPS; T_STOP = DUR
SHOTS[-1]["f1"] = DUR_F; SHOTS[-1]["t1"] = DUR

# ---- showpiece timing
T_SURFACE = 1.10                                    # the camera breaks the surface
T_SPLASH = s2e(218.36) - 0.55                       # the bag hits the water (as "forever" ends)
T_RIP = th(HDROP)                                   # the kill-room plastic rips open on the drop
PULSE_K = list(range(18, 48, 2))                    # a heartbeat pulse on every beat of the build
BEAT_PUNCH = [(k, 1.0 if k % 4 == 0 else 0.5) for k in range(HDROP, 82, 2)] + [(k, 0.45 if k % 4 == 0 else 0.0) for k in range(82, 98, 2)] \
    + [(k, 0.9 if k % 4 == 0 else 0.45) for k in range(98, 116, 2)]   # rev 4: the camera punches on the beat (riff, verse, hook)
CHOPS = []

# ---- text (rev 2): ONLY words that are clearly spoken or sung, each word on its time (v9 standard style).
#      Removed: EXCEPT THIS. (not a lyric) and the BREATHE OUT captions (a whisper that is barely audible and that Whisper
#      can't verify on the isolated vocal).
def sw(sng): return s2e(sng)
TEXT = [
    dict(style="cap", words=[("HOW", vo_e(212.84), 0), ("IS", vo_e(212.98), 0), ("IT", vo_e(213.06), 0), ("I", vo_e(213.14), 0), ("CAN", vo_e(213.24), 0),
                             ("KILL", vo_e(213.38), 0), ("PEOPLE", vo_e(213.66), 0), ("AND", vo_e(214.02), 1), ("FEEL", vo_e(214.28), 1),
                             ("NO", vo_e(214.54), 1), ("REGRET?", vo_e(214.78), 1)], end=vo_e(215.30) + 0.45, emph=["KILL", "REGRET?"], band=(1330, 1545)),
    dict(style="cap", words=[("AND", sw(210.40), 0), ("I", sw(210.84), 0), ("WONDER", sw(211.08), 1)], end=sw(213.05), emph=["WONDER"], big=True, ys=(1452, 1568), band=(1400, 1615)),
    dict(style="cap", words=[("IF", sw(214.55), 0), ("EVERYTHING", sw(214.80), 0), ("COULD", sw(215.26), 0), ("EVER", sw(215.60), 0),
                             ("FEEL", sw(215.96), 1), ("THIS", sw(216.26), 1), ("REAL", sw(216.54), 1)], end=sw(216.78) + 0.30, emph=["REAL"], band=(1330, 1545)),
    dict(style="hero", lines=["FOREVER"], words=[("FOREVER", sw(216.78), 0)], end=T_SPLASH + 0.30, exit="bubbles", band=(1080, 1300)),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAP_Y = (1380, 1496)

# ---- engine knobs (older-engine compatibility)
CAPS = []; END_CAP = []; DROP_TITLE = None; VANISH_T0 = None; CLOSE_T = None
MONTAGE = (HDROP, K_SPL)
ACCENTS = [th(k) for k in range(HDROP, K_SPL, 4)]   # the riff's downbeats

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]
        print(f"{s['n']:10s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']:3s} {ts[0]:7.2f}-{ts[-1]:7.2f} x{(ts[-1] - ts[0]) / (s['t1'] - s['t0']):.2f} in={s.get('tin', '')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(T_DROP, 3), "splice", round(T_SPLICE, 3), "splash", round(T_SPLASH, 3))
    for t_ in TEXT: print(f"  {t_['style']:5s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
