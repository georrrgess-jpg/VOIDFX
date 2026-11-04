"""WISH YOU WELL — Dexter × Brent Faiyaz "Wish You Well" (voidfx v8, 9:16). Single source of truth.

Concept: "Tonight's the night." Dexter's night drive to the kill, scored like a toxic love song. The R&B hook is his
love letter to the man on the table: "Pick me up, don't know if it's what I need / but it's what I want, God, look out
for me … Darling, I don't wish you well." Look: SODIUM NOCTURNE — deep indigo shadows, warm sodium-vapour streetlight
highlights, rain on glass, passing light sweeps, warm halation; elegant serif-italic type with blood-red accents.

Song: the user's screen recording of the track (36 s, src/wish_you_well_rec.wav). Grid 138 BPM (half-beat 0.21731 s).
Window: half-beats 64 -> 164 (13.96 -> 35.69 s, 21.73 s): the quiet "ooh, ooh, yeah" lead-in (hats out) -> the beat
returns at 19.17 (+16 dB) on "pick me up …" -> the break (27.86, drums thin; "Tonight's the night." from the S1 pilot
sits in the gap) -> "Darling," (30.04, held) -> the near-silent bar (31.34) -> the DROP at 33.08 (+46 dB high band)
-> "I don't wish you well" (34.16-35.12) -> dead stop on the beat after "well" -> loops into the rear-view mirror open.
Footage: true-60 fps shots (p1, p5) may be slowed/ramped with optical flow; 24p-in-60 packs (p8) play at their native
cadence (hold) — no synthesized frames.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v8", "wish_you_well_dexter"
SONG = f"{ROOT}/src/wish_you_well_rec.wav"
FPS, W, H = 60, 1080, 1920
SRC = {"p8": (f"{ROOT}/src/pack8_s1.mp4", 60.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720)}

HB, HB_OFF = 0.21731, 0.0489                 # tools/song_map.py (138.05 BPM)
H0, H1, HDROP = 64, 164, 152
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

# ---- dialogue: the S1 pilot's opening line, in the song's break (pack8 0.00-0.96, Demucs stem of pack8 0-6 s)
VO = [(0.00, 1.02, th(128) + 0.12)]          # "Tonight's the night."
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/p8_open/vocals.wav"; VO_STEM_T0 = 0.0
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

# song vocal word times (Demucs stem + Whisper, song seconds)
W_PICK = [("PICK", 20.26), ("ME", 20.56), ("UP", 20.72)]
W_NEED = [("DON'T", 21.16), ("KNOW", 21.40), ("IF", 21.56), ("IT'S", 21.82), ("WHAT", 22.04), ("I", 22.18), ("NEED", 22.42)]
W_WANT = [("BUT", 22.74), ("IT'S", 23.12), ("WHAT", 23.36), ("I", 23.46), ("WANT", 23.76)]
W_GOD = [("GOD,", 24.18), ("LOOK", 24.48), ("OUT", 24.68), ("FOR", 24.88), ("ME", 25.06)]
W_HOOK = [("I", 34.16), ("DON'T", 34.36), ("WISH", 34.66), ("YOU", 34.88), ("WELL", 35.12)]
DARLING_T = s2e(30.04)
HK = [s2e(t) for _, t in W_HOOK]             # the hook's syllables: the climax cuts land on them

S = []
def shot(n, src, t0, t1, a, b, **kw):
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "nocturne"),
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- act 1: the lead-in ("ooh, ooh, yeah") — the rear-view mirror, the drive, the walk
shot("mirror", "p8", th(64), th(70), 311.00, 312.30, z=[(0, 1.00), (1, 1.06)], tin="mirror_in", rain=True)
shot("street", "p8", th(70), th(80), 2.10, 4.30, z=[(0, 1.04), (1, 1.12)], tin="light_sweep", face=None, cx=(600, 760), rain=True)
shot("kit", "p8", th(80), th(88), 2.20, 2.21, z=[(0, 1.0), (1, 1.0)], tin="wiper", graphic="knife_roll", face=None, cx=(640, 640))   # the kill kit on the passenger seat (graphic)
# ---- act 2: the beat returns — "pick me up, don't know if it's what I need, but it's what I want, God, look out for me"
shot("lights", "p8", th(88), th(97), 230.75, 232.70, z=[(0, 1.00), (1, 1.08)], tin="knife_pass", seg=True, face_x=0.33)
shot("glove", "p1", th(97), th(100), 101.78, 102.44, z=[(0, 1.00), (1, 1.06)], tin="whip")
shot("fence", "p5", th(100), th(104), 49.10, 49.98, z=[(0, 1.02), (1, 1.08)], tin="facematch", interp="flow")
shot("rapture", "p1", th(104), th(111), 133.96, 135.12, z=[(0, 1.00), (1, 1.10)], tin="light_leak", interp="flow", seg=True, ev=-0.35)
shot("look_up", "p8", th(111), th(118), 355.40, 356.92, z=[(0, 1.00), (1, 1.07)], tin="whip_up")
shot("kill_lamp", "p8", th(118), th(122), 99.00, 99.87, z=[(0, 1.05), (1, 1.12)], tin="logo_orig")
shot("plastic", "p8", th(122), th(125), 130.55, 131.20, z=[(0, 1.00), (1, 1.06)], tin="wrap")
shot("mask", "p1", th(125), th(128), 58.56, 59.17, z=[(0, 1.00), (1, 1.06)], tin="impact", interp="flow")
# ---- act 3: the break — "Tonight's the night." / "Darling," / the drop of blood falls
shot("tonight", "p8", th(128), th(136), 0.05, 1.90, z=[(0, 1.02), (1, 1.12)], tin="rainfocus", face=None, cx=(1010, 990), rain=True, sweeps=True, ev=-0.30)
shot("darling", "p8", th(136), th(144), 0, 0, tmap=[(0, 109.50), (0.25, 109.93), (1, 109.95)], z=[(0, 1.00), (0.25, 1.05), (1, 1.12)],
     tin="lamp_on", seg=True, freeze=DARLING_T)
shot("drop", "p8", th(144), th(152), 0, 0, tmap=[(0, 109.95), (1, 109.96)], z=[(0, 1.12), (1, 1.22)], seg=True, dropfall=True)
# ---- act 4: the drop — "I / don't / wish / you / well" — one cut per syllable, then into the mirror (loop)
shot("blood_face", "p8", th(152), HK[0], 103.00, 104.06, z=[(0, 1.10), (1, 1.18)], tin="bloom")
shot("knife", "p1", HK[0], HK[1], 158.05, 158.30, z=[(0, 1.00), (1, 1.04)], tin="slam")
shot("table", "p8", HK[1], HK[2], 100.90, 101.20, z=[(0, 1.00), (1, 1.05)], tin="slam")
shot("walk", "p1", HK[2], HK[3], 186.40, 186.62, z=[(0, 1.00), (1, 1.04)], tin="slam")
shot("smirk", "p8", HK[3], HK[4], 346.60, 346.84, z=[(0, 1.00), (1, 1.05)], tin="slam")
shot("well", "p8", HK[4], th(164), 313.40, 313.97, z=[(0, 1.00), (1, 1.04)], tin="slam", tout="mirror_out", rain=True)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text: each moment has its own design. styles: behind (big word set behind Dexter's cutout, tracked to his head),
#      lyric (two-line eased lockup: wide-tracked sans + serif italic emphasis), script (serif-italic write-on with a
#      pen nib), hook (word-by-word build that survives the climax cuts)
TEXT = [
    dict(style="behind", words=[(w, s2e(t), 0) for w, t in W_PICK], end=th(97) - 0.03, emph=["UP"], band=(560, 1300)),
    dict(style="lyric", words=[(w, s2e(t), 0 if i < 4 else 1) for i, (w, t) in enumerate(W_NEED)], end=s2e(22.42) + 0.26, emph=["NEED"], quick_out=True),
    dict(style="lyric", words=[(w, s2e(t), 0) for w, t in W_WANT[:4]], end=th(111) - 0.08, emph=[], quick_out=True),
    dict(style="behind", words=[("WANT", s2e(23.76), 0)], end=th(111) - 0.03, emph=["WANT"], band=(560, 1300)),
    dict(style="lyric", words=[(w, s2e(t), 0 if i < 1 else 1) for i, (w, t) in enumerate(W_GOD)], end=th(118) - 0.06, emph=["GOD,"]),
    dict(style="script", words=[("Tonight's the night.", VO[0][2] + 0.0, 0)], end=th(136) - 0.10, emph=[], band=(1300, 1560)),
    dict(style="script", words=[("Darling,", DARLING_T, 0)], end=th(144) + 0.55, emph=["Darling,"], band=(1280, 1580)),
    dict(style="hook", words=[(w, s2e(t), 0 if i < 4 else 1) for i, (w, t) in enumerate(W_HOOK)], end=th(164) - 0.30, emph=["WELL"]),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CLOSE_T = None

# ---- engine knobs
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
DROP_TITLE = None
MONTAGE = (88, 128)
VANISH_T0 = None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:11s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {s['tmap'][0][1]:7.2f}-{s['tmap'][-1][1]:7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "VO", [round(v[2], 2) for v in VO], "darling", round(DARLING_T, 2), "hook", [round(x, 2) for x in HK])
    for t_ in TEXT: print(f"  {t_['style']:7s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
