"""DRACULA — Dexter × Tame Impala "Dracula" (voidfx v105, 9:16). Single source of truth.

Concept SUNDOWN: by day he wears the mask (sunny Miami, the smile, the ice cream); the song's final chorus is "run from the sun
like Dracula", so the sun sets in one bar on the song's drop-out and night slams in on the biggest change in the song
(162.90 s, +29.8 dB). Night is the hunt. At the end the sun comes up again and burns the frame white: the loop opens in that
same white light.
Looks: DAY "postcard" (bleached warm Miami, a sun with light rays) -> DUSK -> NIGHT "crimson" (deep black, cold moonlit skin,
crimson kept and pushed).
Set pieces: SUNDOWN (k24-32), THE BAT BURST + DRACULA (drop, k32), THE BLOOD MOON (k48, the 2nd "Dracula"), THE COFFIN (k64, the
3rd), DAYBREAK (loop, k84-88).
Song window: half-beats h592 -> h680 of dracula.mp3 (114.99 BPM; k = edit half-beat = 0.26090 s), 154.55 -> 177.51 s.
Lyrics checked on the Demucs vocal (plain Whisper in tight windows, no hint): "Saw this moment coming from afar" 155.16-157.6;
"(So) run from the sun like Dracula" 161.02-163.6; "Dracula" again at 167.2 and 171.4. Not captioned (not clear on the
vocal): "Now here we are", the other words of the later repeats, "this love is spectacular".
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v105", "dracula_dexter"           # v105/out/dracula_dexter_voidfx_9x16.mp4
SONG = f"{ROOT}/src/dracula.mp3"
FPS, W, H = 60, 1080, 1920                           # 60 fps output; every source plays at its own 24p/30p cadence (interp="hold": no optical flow)
SRC = {"p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720),
       "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720), "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720),
       "p8": (f"{ROOT}/src/pack8_s1.mp4", 60.0, 1280, 720), "p9": (f"{ROOT}/src/pack9_s4_best.mp4", 60.0, 1280, 720),
       "p10": (f"{ROOT}/src/pack10_s4_24p.mp4", 24.0, 1280, 720),
       "p3": (f"{ROOT}/src/scenepack3_24fps.mp4", 24000 / 1001, 1280, 720), "p6": (f"{ROOT}/src/pack6_s5.mp4", 30.0, 1280, 720),
       "dk": (f"{ROOT}/src/doakes.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.26090, 0.0978                         # tools/song_map.py (v105/work/song_map.json)
H0, H1 = 592, 680
K_SPL = 88; K_END = 88; HDROP = 32                  # no splice
PHR = [0, 24, 32, 48, 64, 84]                         # verse, sundown, drop, blood moon, coffin, daybreak
def st(h): return HB_OFF + h * HB
def th(k): return k * HB
def song_at(e): return st(H0) + e
def s2e(sng): return sng - st(H0)
def sw(sng): return s2e(sng)
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
BASS = list(range(0, 88, 2))                          # the kick: every beat
SUN_K = (24, 31.5)                                     # the sun sets across the drop-out bar
DAWN_K = (84, 88)                                      # it rises again at the end (the loop)

# ---- no dialogue: the song's own voice carries the text
VO = []; VO_STEMS = {}
def vo_e(seg, src_t): return 0.0
VO_STEM = None; VO_STEM_T0 = 0.0
SONG_VOX = None; SONG_VOX_T0 = 0.0; VOX_MUTE = None

S = []
def shot(n, src, k0, k1, a, b=None, **kw):
    if b is None: b = a + (k1 - k0) * HB             # 1:1 by default
    d = dict(n=n, src=src, t0=th(k0), t1=th(k1), k0=k0, k1=k1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "night"),
             z=kw.pop("z", [(0, 1.00), (1, 1.06)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- DAY (k0-24): the mask. "Saw this moment coming from afar."
shot("boat", "p6", 0, 3, 17.20, tin=None, look="day", sun=(0.78, 0.13), z=[(0, 1.06), (1, 1.00)], con=0.7, seg=True, motes=1.0)
shot("hood", "p3", 3, 6, 24.30, 25.08, tin="sun_flare", look="day", sun=(0.85, 0.10), seg=True, motes=0.8)
shot("icecream", "p1", 6, 9, 69.25, 70.20, tmap=[(0, 69.25), (0.55, 69.80), (1, 70.20)], tin="whip", look="day")
shot("badge", "p7", 9, 12, 14.60, tin="burn", look="day", sun=(0.15, 0.08), seg=True, motes=0.8)
shot("pinkwall", "p5", 12, 15, 6.60, tin="slam", look="day", sun=(0.88, 0.12), seg=True, motes=0.8)
shot("lollipop", "p8", 15, 18, 117.70, tin="tilt", look="day")
shot("boatgrin", "p1", 18, 21, 70.90, tin="quarter_roll", look="day", sun=(0.12, 0.10), seg=True, motes=0.8)
shot("palms", "p10", 21, 24, 130.60, tin="smear", look="day", sun=(0.80, 0.10), seg=True, motes=1.0)
# ---- SUNDOWN (k24-32): the drop-out bar. "Run from the sun like ..."
shot("sunset", "p8", 24, 27, 405.95, 406.62, tin="light_sweep", look="dusk", sun=(0.70, 0.12), z=[(0, 1.00), (1, 1.03)], seg=True, motes=0.6, face_x=0.62)   # ends before he leans out of the crop
shot("looksup", "p9", 27, 32, 230.60, 231.90, tin="whip_up", look="dusk", z=[(0, 1.00), (1, 1.10)], seg=True)
# ---- NIGHT (k32-84): DRACULA. The bats burst on the drop.
shot("scope", "dk", 32, 38, 46.20, 47.80, tin="bat_burst", z=[(0, 1.12), (1, 1.02)], fog=0.8)
shot("redrive", "p9", 38, 41, 0.40, 1.20, tin="strobe", redthr=0.05)
shot("blinds", "p9", 41, 44, 101.30, 102.10, tin="impact", ev=0.6)
shot("lighttable", "p9", 44, 46, 145.95, 146.45, tin="torch_blind", face=None, cx=(640, 360))
shot("gloving", "p1", 46, 48, 102.20, 102.72, tin="cape")                                 # a Dracula cape sweeps across the lens
# THE BLOOD MOON (the 2nd "Dracula", k48.5): his cut-out against a rising crimson moon, bats across it
shot("moon", "p1", 48, 54, 186.50, 187.70, tin="moon_iris", seg=True, bloodmoon=dict(k0=48, k1=54), z=[(0, 1.00), (1, 1.06)])
shot("lamp", "p10", 54, 57, 181.10, tin="lamp_on", flare=0.7, ev=0.55)
shot("garage", "p9", 57, 60, 203.30, 204.40, tmap=[(0, 203.30), (0.35, 203.95), (1, 204.40)], tin="logo_orig", ghost=0.25)
shot("flip", "p9", 60, 64, 125.00, tin="roll", spin=(0.0, -4.0), redthr=0.45)            # he hangs upside down like a bat
# THE COFFIN (the 3rd "Dracula", k64.6): a lid slams shut over him and opens on the next
shot("container", "p4", 64, 66, 65.80, 66.45, tmap=[(0, 65.80), (0.40, 66.20), (1, 66.45)], tin="coffin", ghost=0.4)
shot("knife", "p9", 66, 68, 178.30, tin="mist")                                     # he rises out of the coffin as mist and re-forms with the knife
shot("attack", "p9", 68, 71, 164.80, 165.75, tmap=[(0, 164.80), (0.30, 165.40), (1, 165.75)], tin="bat_swarm", ghost=0.45)
shot("syringe", "p8", 71, 74, 146.30, tin="pupil_dive", face=None, cx=(980, 980))
shot("profile", "p6", 74, 77, 68.60, tin="facematch", cx=(560, 560))
shot("stare", "p9", 77, 80, 117.80, tin="shutter")
shot("low", "p9", 80, 82, 222.60, tin="zipper")
shot("torch", "p9", 82, 84, 185.40, tin="bat_pass", flare=0.8)                       # one great bat flies through the lens; his torch flares into the dawn
# ---- DAYBREAK (k84-88): the sun comes up and burns the frame white (the loop opens in this light)
shot("dawn", "p9", 84, 88, 75.00, tin="sun_flare", look="dusk", daybreak=True, z=[(0, 1.20), (1, 1.30)], seg=True)   # he walks into the sunrise and burns
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
# AAC pads the audio to 1024-sample blocks: trim the loop by up to 3 frames so the padding stays under ~12 ms (< 1 frame)
for _d in range(4):
    if (1024 - round((fh(K_END) - _d) / FPS * 48000) % 1024) % 1024 <= 576: break
DUR_F = fh(K_END) - _d; DUR = DUR_F / FPS; T_STOP = DUR
SHOTS[-1]["f1"] = DUR_F; SHOTS[-1]["t1"] = DUR

# ---- text: only the clearly sung words (checked on the vocal stem), each on its sung time
TEXT = [
    dict(style="cap", words=[("SAW", sw(155.16), 0), ("THIS", sw(155.62), 0), ("MOMENT", sw(155.90), 0), ("COMING", sw(156.34), 1), ("FROM", sw(156.86), 1),
                             ("AFAR", sw(157.22), 1)], end=sw(158.45), emph=["AFAR"], band=(1330, 1545)),
    dict(style="cap", words=[("RUN", sw(161.02), 0), ("FROM", sw(161.42), 0), ("THE", sw(161.88), 0), ("SUN", sw(162.28), 0), ("LIKE", sw(162.52), 1)],
         end=sw(162.98), emph=["SUN"], band=(1330, 1545)),
    dict(style="hero", lines=["DRACULA"], words=[("DRACULA", sw(163.14), 0)], end=th(36.2), exit="bats", band=(1080, 1300)),
    dict(style="cap", words=[("DRACULA", sw(167.20), 0)], end=sw(167.20) + 0.62, emph=["DRACULA"], big=True, band=(1330, 1545)),
    dict(style="cap", words=[("DRACULA", sw(171.42), 0)], end=sw(171.42) + 0.62, emph=["DRACULA"], big=True, band=(1570, 1785)),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAP_Y = (1380, 1496)

# ---- animation layers
BEAT_PUNCH = [(k, 0.35) for k in BASS if k < 24] + [(k, 0.0) for k in BASS if 24 <= k < 32] + [(k, 1.0 if k % 8 == 0 else 0.55) for k in BASS if k >= 32]
PULSE_K = []
T_SURFACE = 0.0; T_SPLASH = DUR + 1

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
