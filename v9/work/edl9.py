"""NIGHT BLOOM — Dexter × fakemink "Night, Blooming Jasmine" (voidfx v9, 9:16). Single source of truth: the renderer,
audio builder and QC read only this file.

Concept: "Some things only bloom at night." The Trinity season (S4 packs p9/p10 + the owner's "Trinity Finds Out" clip). A blood moon over Miami; Dexter
looks up at it: "I had to evolve. It was the only way to survive." He walks through a night garden of white jasmine and
stops, staring into the lens. The song cuts to dead silence: a camera shutter snaps and Arthur Mitchell himself is frozen in
the frame, the petals hanging in the air: "Hello, Arthur Mitchell." On the drop the frozen frame BLOOMS open like a flower and the kill begins: a montage of the
hunt cut on the 808s and claps -> "I swear I'm on a mission" -> NIGHT BLOOM / JASMINE -> he raises Trinity's blood slide;
the drop of blood on it swells into the blood moon, and the edit loops.
Look: MOONBLOOM (new): violet-black night, moon-silver highlights with a soft white Pro-Mist bloom, jasmine-white petals,
crimson kept for blood and the hook; strobing only on the drop (the song is "a smeared, strobing take on deep house").
Type: bold, high-contrast two-line captions (Inter Display Black), every word eased in; one designed hero title.

Song: src/night_blooming_jasmine.mp3 (234.7 s), 102.79 BPM, half-beat P = 0.29185 s. The second half is on its own grid
(the silence before the drop is not a whole number of beats): HB_OFF puts half-beat 482 on the drop onset (140.839 s).
Window, two segments spliced on the beat grid (the instrumental repeats on a 4-bar cycle; bar h506 == bar h634, r=0.98):
  A  h448 -> h506 (130.92 -> 147.84 s): filtered breakdown, build at 137.78, DEAD SILENCE 139.38 -> 140.83, the drop.
  B  h634 -> h650 (185.20 -> 189.87 s): "I swear I'm on a mission / Night bloom jasmine, second name Yasmin".
Edit half-beat e: e0-e58 = segment A (song h = 448 + e), e58-e74 = segment B (song h = 576 + e). 74 hb = 21.60 s.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v9", "night_bloom_dexter"
SONG = f"{ROOT}/src/night_blooming_jasmine.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/night_blooming_jasmine"
FPS, W, H = 60, 1080, 1920
SRC = {"p9": (f"{ROOT}/src/pack9_s4_best.mp4", 60.0, 1280, 720), "p10": (f"{ROOT}/src/pack10_s4_24p.mp4", 24.0, 1280, 720),
       "tg": (f"{ROOT}/src/trinity_goodbye.mp4", 60.0, 1280, 720)}                        # "Trinity Finds Out Who Dexter Is" (owner upload)

HB, HB_OFF = 0.29185, 0.1673                 # half-beat 482 = the drop onset 140.839 s (local grid fit, 140.8-222 s)
H0, H1 = 448, 650
def st(h): return HB_OFF + h * HB            # song seconds of song half-beat h
def th(e): return e * HB                     # edit seconds of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
E_SPLICE, E_END = 58, 74
SONG_IN = st(H0)
SONG_SEGS = [(st(448), st(506), 0.0), (st(634), st(650), th(E_SPLICE))]   # (song in, song out, edit at)
def s2e(s):                                  # song seconds -> edit seconds (either segment)
    for a, b, at in SONG_SEGS:
        if a - 1e-6 <= s <= b + 1e-6: return at + s - a
    raise ValueError(s)
DUR = th(E_END); DUR_F = fh(E_END)
HDROP = 34; DROP_HB = HDROP; T_STOP = DUR    # the drop, in edit half-beats
E_SIL = 29                                   # dead silence e29 -> e34 (139.38 -> 140.84 s)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

# ---- dialogue: (stem, src in, src out, edit at) — Demucs vocal stems of the pack audio (studio/packs/tr_p9.json)
VOD = f"{ROOT}/{VER}/audio/sep/htdemucs"
VO = [(f"{VOD}/evolve/vocals.wav", 129.9, 1.18, 4.25, th(3) + 0.10),     # "I had to evolve. It was the only way to survive."
      (f"{VOD}/hello/vocals.wav", 222.4, 0.86, 2.30, th(E_SIL) - 0.02)]   # "Hello, Arthur Mitchell."  (in the dead silence)
# (stem, stem's source start, in, out [s into the stem], edit at)

# ---- song vocal word times (Demucs stem + Whisper with a title prompt, song seconds)
W_MISSION = [("I", 185.36), ("SWEAR", 185.50), ("I'M", 185.82), ("ON", 186.20), ("A", 186.40), ("MISSION", 186.56)]
W_HOOK = [("NIGHT", 187.12), ("BLOOM", 187.36), ("JASMINE", 187.82)]
W_YASMIN = [("SECOND", 188.56), ("NAME", 188.78), ("YASMIN", 189.12)]

# VO word times, edit seconds (stem word times + offsets)
def _vo(i, t_src): return VO[i][4] + (t_src - VO[i][1] - VO[i][2])
W_EVOLVE = [("I", _vo(0, 131.24)), ("HAD", _vo(0, 131.30)), ("TO", _vo(0, 131.50)), ("EVOLVE.", _vo(0, 131.68))]
W_SURVIVE = [("IT", _vo(0, 132.00)), ("WAS", _vo(0, 132.40)), ("THE", _vo(0, 132.62)), ("ONLY", _vo(0, 132.74)),
             ("WAY", _vo(0, 133.00)), ("TO", _vo(0, 133.24)), ("SURVIVE.", _vo(0, 133.38))]
W_HELLO = [("HELLO,", _vo(1, 223.30)), ("ARTHUR", _vo(1, 223.62)), ("MITCHELL.", _vo(1, 224.00))]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot (v9 set:
    loop_in tilt foliage petals bloom strobe whip beam blinds logo_orig roll m99 impact smear), tout="drop_moon" on the last."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "moonbloom"),
             z=kw.pop("z", [(0, 1.00), (1, 1.07)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- cold open: the filtered breakdown (one continuous take: moon -> tilt down -> garden -> the stare)
shot("moon", "p9", 0, 3, 230.00, 230.50, face=None, cx=(640, 640), tin="loop_in", graphic="moon")
shot("look_up", "p9", 3, 14, 230.75, 233.95, z=[(0, 1.02), (1, 1.12)], tin="tilt", petals=0.6, seg=True)
shot("garden", "p9", 14, 20, 82.25, 84.00, z=[(0, 1.04), (1, 1.10)], tin="foliage", petals=0.8, seg=True)
shot("stare", "p9", 20, E_SIL, 117.60, 120.20, z=[(0, 1.00), (1, 1.10)], tin="petals", seg=True, petals=1.0, frame_petals=True)
# ---- the silence: a camera shutter snaps on the dead stop -> ARTHUR MITCHELL himself, frozen: "Hello, Arthur Mitchell."
shot("arthur", "tg", E_SIL, 34, 103.40, 103.40, z=[(0, 1.10), (1, 1.18)], tin="shutter", seg=True, freeze_e=E_SIL, petals=1.0, frame_petals=True)
# ---- the drop: the frozen frame blooms open; the hunt, cut on the 808s and claps
shot("table", "p9", 34, 38, 103.25, 104.45, z=[(0, 1.14), (1, 1.04)], tin="bloom")
shot("swing", "p9", 38, 42, 180.15, 181.10, z=[(0, 1.00), (1, 1.07)], tin="strobe")
shot("torch", "p9", 42, 44, 186.60, 187.20, z=[(0, 1.02), (1, 1.06)], tin="whip")
shot("blinds", "p9", 44, 48, 101.20, 102.40, z=[(0, 1.00), (1, 1.06)], tin="beam", ev=0.30)
shot("glove", "p10", 48, 50, 36.15, 36.60, z=[(0, 1.00), (1, 1.05)], tin="blinds")
shot("table_lt", "p9", 50, 54, 145.80, 146.72, z=[(0, 1.00), (1, 1.10)], tin="logo_orig", face=None, cx=(700, 680), ev=-0.7)
shot("upside", "p9", 54, 58, 126.00, 127.20, z=[(0, 1.00), (1, 1.05)], tin="roll", face=None, cx=(640, 640))
# ---- segment B: "I swear I'm on a mission" / "Night bloom jasmine" / "second name Yasmin"
shot("mission", "p10", 58, 64, 66.36, 67.93, z=[(0, 1.00), (1, 1.07)], tin="m99")
shot("hero", "p9", 64, 70, 222.90, 224.65, z=[(0, 1.00), (1, 1.08)], tin="impact", petals=0.7, seg=True)
shot("slide", "p10", 70, 74, 164.00, 165.40, z=[(0, 1.00), (1, 1.06)], tin="smear", tout="drop_moon", spot=(510, 320))
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text: bold two-line captions (style "cap": words [(WORD, edit t, line)], emph = crimson words) + the hero title
TEXT = [
    dict(style="cap", words=[(w, t, 0 if i < 3 else 1) for i, (w, t) in enumerate(W_EVOLVE)], end=2.16, emph=["EVOLVE."]),
    dict(style="cap", words=[(w, t, 0 if i < 4 else 1) for i, (w, t) in enumerate(W_SURVIVE)], end=th(14) - 0.20, emph=["SURVIVE."], **{"from": 2.22}),
    dict(style="cap", words=[(w, t, 0 if i < 1 else 1) for i, (w, t) in enumerate(W_HELLO)], end=th(HDROP) - 0.03, emph=[], big=True),
    dict(style="cap", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_MISSION)], end=th(64) - 0.10, emph=["MISSION"]),
    dict(style="hero", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_HOOK)], end=th(70) - 0.08, emph=["JASMINE"]),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, 58)
VO_STEM = None; VO_STEM_T0 = 0.0
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:8s} e{s['e0']:2d}-e{s['e1']:2d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']:3s} {s['tmap'][0][1]:7.2f}-{s['tmap'][-1][1]:7.2f} x{sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "silence", round(th(E_SIL), 3), "drop", round(th(HDROP), 3), "splice", round(th(E_SPLICE), 3))
    print("song A", [round(x, 3) for x in SONG_SEGS[0]], "B", [round(x, 3) for x in SONG_SEGS[1]])
    for t_ in TEXT: print(f"  {t_['style']:5s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(f"{w}@{t:.2f}" for w, t, _ in t_["words"]))
