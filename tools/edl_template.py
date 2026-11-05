"""{{TITLE}} (voidfx {{VER}}, 9:16). Single source of truth: the renderer, audio builder and QC read only this file.

STARTING POINT = the v104 THE PASSENGER standard (approved: "I really like this edit and would like for it to be a standard").
Everything below is THE PASSENGER's real EDL, kept as a worked example so the scaffold renders on day one (FOREVER, v103, is
the other standard; its toolkit is in fxN.py too). Replace it section by section: song + window (tools/song_map.py), the grid
(k = one sixteenth here: fit it to the song's own hits), shots, dialogue, captions (tools/lyrics.py for sung words), set pieces.
Keep the bar: a designed cut or animation beat in EVERY span (no headspace: nothing longer than about a second without a cut,
a transition or a designed beat), BEAT_PUNCH through every music section, graphics in every hold (handbook §0).

Concept: <one sentence from the character's world>. Set pieces on the phrase starts: <...>.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "{{VER}}", "{{SLUG}}"           # v104/out/the_passenger_dexter_voidfx_9x16.mp4
SONG = f"{ROOT}/src/still_love_you_rec.wav"
FPS, W, H = 60, 1080, 1920                           # 60 fps output; every source plays at its own 24p/30p cadence (interp="hold": no optical flow)
SRC = {"p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720),
       "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720), "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720),
       "p8": (f"{ROOT}/src/pack8_s1.mp4", 60.0, 1280, 720), "p9": (f"{ROOT}/src/pack9_s4_best.mp4", 60.0, 1280, 720),
       "p10": (f"{ROOT}/src/pack10_s4_24p.mp4", 24.0, 1280, 720)}

HB, HB_OFF = 0.13370, 0.042                          # k = one sixteenth (the bass grid), song time of k0
H0, H1 = 0, 172
K_SPL = 172; K_END = 172; HDROP = 12                 # no splice; the bass entry is the drop
PHR = [12, 44, 76, 108, 140]                         # phrase starts (two bars each)
def st(h): return HB_OFF + h * HB
def th(k): return k * HB
def song_at(e): return st(H0) + e
def s2e(sng): return sng - st(H0)
def fe(t): return int(round(t * FPS))
def fh(k): return fe(th(k))
DUR = th(K_END); DUR_F = fh(K_END)
H1_EDIT = K_END
def te(k): return th(k)
T_STOP = DUR; DROP_HB = HDROP
BAR = 16 * HB; BEAT = 4 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
T_DROP = th(HDROP); T_SPLICE = th(K_SPL)
# the sub-bass hits (k), measured on the Demucs bass stem; the last phrase repeats the first one's pattern
BASS = [12, 16, 20, 23, 26, 29, 32, 35, 38, 41, 44, 48, 52, 55, 58, 60, 63, 66, 69, 72, 76, 80, 84, 87, 90, 93, 96, 99, 102, 105,
        108, 112, 116, 119, 122, 124, 127, 130, 133, 136, 140, 144, 148, 151, 154, 157, 160, 163, 166, 169]

# ---- dialogue: two short lines of his narration (S1, pack 8), played as voice-over (his lips aren't shown saying them).
#      Stems: Demucs of p8 222-234 s and 293-302 s. Word onsets measured on the stem envelope.
VO_STEMS = {"a": (f"{ROOT}/{VER}/audio/sep/htdemucs/p8_222/vocals.wav", 222.0), "b": (f"{ROOT}/{VER}/audio/sep/htdemucs/p8_293/vocals.wav", 293.0)}
# (stem, stem in, stem out, edit at): "I like to pretend I'm ALONE" -> ALONE on the bass entry; "completely ALONE." -> on the k29 hit;
# "I have a DARK side, too." -> DARK on the k112 hit as the shadow rises
VO = [("a", 4.30, 5.92, th(12) - (5.10 - 4.30)), ("a", 7.02, 8.30, th(29) - (7.62 - 7.02)), ("b", 5.55, 6.92, th(112) - (6.22 - 5.55))]
def vo_e(seg, src_t):
    st_, a, b, at = VO[seg]; return at + (src_t - a)
VO_STEM = None; VO_STEM_T0 = 0.0
SONG_VOX = None; SONG_VOX_T0 = 0.0; VOX_MUTE = None

S = []
def shot(n, src, k0, k1, a, b=None, **kw):
    if b is None: b = a + (k1 - k0) * HB             # 1:1 by default
    d = dict(n=n, src=src, t0=th(k0), t1=th(k1), k0=k0, k1=k1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "sumi"),
             z=kw.pop("z", [(0, 1.00), (1, 1.06)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- pickup (k0-12): paper; one drop of ink falls; "I like to pretend I'm..."
shot("ink", "p9", 0, 12, 73.80, 73.80, tin=None, graphic="ink_open", face=None, cx=(640, 640))
# ---- P1 (k12-44): alone. The drop lands on the bass entry and blooms into him.
shot("dock", "p9", 12, 20, 73.80, 74.95, tmap=[(0, 73.80), (0.35, 74.55), (1, 74.95)], tin="ink_bloom", z=[(0, 1.10), (1, 1.02)], motes=1.0)
shot("stare", "p9", 20, 26, 118.00, tin="page_turn", z=[(0, 1.00), (1, 1.08)], motes=1.0)                     # rev 3
shot("floor", "p8", 26, 35, 392.40, tin="brush", z=[(0, 1.02), (1, 1.10)], brush=dict(ang=-28, seed=3, white=True), motes=0.8,
     swash=dict(k0=29, k1=43, y=1478))
shot("chain", "p1", 35, 41, 171.10, 171.74, tin="whip", z=[(0, 1.04), (1, 1.10)], motes=0.6)
shot("shh", "p1", 41, 44, 96.45, 96.85, tin="smear", z=[(0, 1.00), (1, 1.06)], redthr=0.45)                            # rev 3
# ---- P2 (k44-76): the ritual. Gloves, the slide, the mirror, the shield goes down.
shot("gloving", "p1", 44, 49, 102.15, tin="impact", z=[(0, 1.00), (1, 1.08)])
shot("gloves", "p7", 49, 55, 33.30, tin="slam", z=[(0, 1.00), (1, 1.06)], flare=0.6)
shot("slide", "p1", 55, 60, 109.80, tin="light_sweep", z=[(0, 1.00), (1, 1.06)])
shot("mirror", "p9", 60, 66, 158.40, tin="brush", z=[(0, 1.02), (1, 1.08)], brush=dict(ang=62, seed=7, red=True), redthr=0.45)
shot("flip", "p9", 66, 72, 125.00, tin="roll", z=[(0, 1.00), (1, 1.06)], redthr=0.45, spin=(0.0, -4.0))   # rev 2: longer, and it keeps turning
shot("visor", "p9", 72, 76, 180.62, 181.42, tin="tilt", z=[(0, 1.00), (1, 1.08)])
# ---- P3 (k76-108): THE SPATTER, then the violence.
shot("shield", "p1", 76, 84, 58.60, 59.12, tin="spatter", z=[(0, 1.12), (1, 1.04)], spat=dict(k=76, x=0.80, y=0.70))
shot("attack", "p9", 84, 90, 164.70, 165.85, tmap=[(0, 164.70), (0.30, 165.45), (1, 165.85)], tin="whip_up", z=[(0, 1.02), (1, 1.10)], ghost=0.55)
shot("container", "p4", 90, 96, 65.75, 66.70, tmap=[(0, 65.75), (0.30, 66.35), (1, 66.70)], tin="strobe", z=[(0, 1.00), (1, 1.06)], ghost=0.5)
shot("gun", "p9", 96, 102, 94.30, tin="facematch", z=[(0, 1.00), (1, 1.08)])
shot("redroom", "p7", 102, 108, 0.10, tin="burn", z=[(0, 1.00), (1, 1.08)])
# ---- P4 (k108-140): THE PASSENGER. "I have a dark side, too."
shot("table", "p8", 108, 120, 389.00, 390.30, tmap=[(0, 389.00), (0.45, 389.75), (1, 389.90)], tin="ink_bleed", z=[(0, 1.00), (1, 1.04)], target=0.43,
     seg=True, passenger=dict(k_rise=112, k_lunge=117, cut_y=0.80))
shot("redsmirk", "p8", 120, 126, 346.90, tin="passenger", z=[(0, 1.10), (1, 1.02)])
shot("turn", "p5", 126, 131, 16.30, 17.00, tmap=[(0, 16.30), (0.40, 16.80), (1, 17.00)], tin="quarter_roll", z=[(0, 1.00), (1, 1.06)], redthr=0.45, ghost=0.45)
shot("police", "p9", 131, 136, 47.30, 48.10, tmap=[(0, 47.30), (0.35, 47.90), (1, 48.10)], tin="logo_orig", z=[(0, 1.00), (1, 1.06)], redthr=0.45)
shot("eyesup", "p1", 136, 140, 46.60, tin="shutter", z=[(0, 1.02), (1, 1.08)])
# ---- P5 (k140-172): THE SILHOUETTE, the fastest run, then back into the drop.
shot("walkout", "p1", 140, 148, 186.60, tin="lamp_on", z=[(0, 1.00), (1, 1.08)], seg=True, window=dict(src="p10", a=165.95, k_in=140, k_out=147))
shot("torch", "p10", 148, 152, 161.20, tin="wrap", z=[(0, 1.00), (1, 1.06)], flare=1.0)
shot("darkside", "p8", 152, 156, 297.60, tin="torch_blind", z=[(0, 1.02), (1, 1.08)])
shot("grin", "p9", 156, 162, 41.00, tin="pupil_dive", z=[(0, 1.00), (1, 1.08)])
shot("low", "p9", 162, 172, 222.60, tin="zipper", z=[(0, 1.00), (1, 1.10)], ink_out=dict(k0=166), target=0.46)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
# AAC pads the audio to 1024-sample blocks: trim the loop by up to 3 frames so the padding stays under ~12 ms (< 1 frame)
for _d in range(4):
    if (1024 - round((fh(K_END) - _d) / FPS * 48000) % 1024) % 1024 <= 576: break
DUR_F = fh(K_END) - _d; DUR = DUR_F / FPS; T_STOP = DUR
SHOTS[-1]["f1"] = DUR_F; SHOTS[-1]["t1"] = DUR

# ---- text: only spoken words (no clear lyric in this sound: Whisper and the published-lyrics search both came up empty)
TEXT = [
    dict(style="cap", words=[("I", vo_e(0, 4.38), 0), ("LIKE", vo_e(0, 4.46), 0), ("TO", vo_e(0, 4.62), 0), ("PRETEND", vo_e(0, 4.72), 0),
                             ("I'M", vo_e(0, 4.98), 1), ("ALONE,", vo_e(0, 5.10), 1)], end=vo_e(1, 7.02) - 0.02, emph=["ALONE,"], band=(1330, 1545)),
    dict(style="hero", lines=["COMPLETELY", "ALONE."], words=[("COMPLETELY", vo_e(1, 7.10), 0), ("ALONE.", vo_e(1, 7.62), 1)],
         end=th(43), exit="blood", band=(1180, 1600)),
    dict(style="hero", lines=["I HAVE A", "DARK SIDE, TOO."], words=[("I HAVE A", vo_e(2, 5.64), 0), ("DARK SIDE, TOO.", vo_e(2, 6.22), 1)],
         end=th(126) - 0.05, exit="blood", band=(1180, 1600)),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAP_Y = (1380, 1496)

# ---- animation layers
BEAT_PUNCH = [(k, 0.6 if k in PHR else 0.38) for k in BASS if k < 44] + [(k, 1.0 if k in PHR or (k - 12) % 16 == 0 else 0.5) for k in BASS if k >= 44]
PULSE_K = []
T_SURFACE = 0.0; T_SPLASH = DUR + 1                  # (FOREVER's water loop is off in this edit)

# ---- engine knobs (older-engine compatibility)
CAPS = []; END_CAP = []; DROP_TITLE = None; VANISH_T0 = None; CLOSE_T = None
MONTAGE = (HDROP, K_END)
ACCENTS = [th(k) for k in BASS]
CHOPS = []

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]
        print(f"{s['n']:10s} k{s['k0']:3d}-{s['k1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']:4s} {ts[0]:7.2f}-{ts[-1]:7.2f} x{(ts[-1] - ts[0]) / (s['t1'] - s['t0']):.2f} in={s.get('tin','')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "shots", len(SHOTS), "cuts", len(SHOTS) - 1)
    for t_ in TEXT: print(f"  {t_['style']:5s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
    print("VO at", [(round(v[3], 2), round(v[3] + v[2] - v[1], 2)) for v in VO])
