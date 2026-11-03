"""WARMPOP — Dexter × George Clanton "Warmpop" (voidfx v6, 9:16). Single source of truth.

Concept: a VHS Miami daydream. Dexter's S5 voice-over ("I've disappeared so many people. My turn now to disappear
myself.") over the song's filtered build; on "disappear myself" he dissolves into pixels; the build shrinks into a CRT
floating over a neon grid + sunset and the camera flies through the screen into the drop (song's full mix returns,
2:29.5); a sunlit Miami montage; "It was me." over the red-shirt close-up; VHS rewind -> static -> loops to tape load.
Song window: half-beats 416 -> 496 (10 bars of 8 half-beats, 90 BPM), drop at hb448.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v6", "warmpop_dexter"          # folder + output file name (engine reads paths from these)
SONG = f"{ROOT}/src/warmpop.mp3"
FPS, W, H = 60, 1080, 1920
SRC = {"p6": (f"{ROOT}/src/pack6_s5.mp4", 30.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720), "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720),
       "p3": (f"{ROOT}/src/scenepack3_24fps.mp4", 24000 / 1001, 1280, 720)}

HB, HB_OFF = 0.33335, 0.1883
H0, H1, HDROP = 416, 496, 448
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

# dialogue (pack6 seconds, Whisper large-v3 word times); VO lines are isolated with Demucs in audio6.py
VO = [  # (src_in, src_out, edit_at)
    (17.30, 19.50, 0.95),        # "I've disappeared so many people"
    (20.52, 23.62, 3.62),        # "My turn now to disappear myself"
    (1.02, 3.55, None),          # "It... was me."  (lip-synced: placed with its shot below)
]
CAPS = [  # (vo index, [(word, src t, line)], src end, emphasis, style) — two-line lockups, every word on its spoken time
    (0, [("I've", 17.39, 0), ("disappeared", 17.95, 0), ("so", 18.39, 1), ("many", 18.77, 1), ("people.", 18.99, 1)], 19.45, ["disappeared"], "line"),
    (1, [("My", 20.61, 0), ("turn", 21.17, 0), ("now", 21.45, 0), ("to", 21.69, 0), ("disappear", 22.71, 1), ("myself.", 23.11, 1)], 23.60,
     ["disappear", "myself."], "vanish"),
]
CAP_Y = (1370, 1472)       # line centres (inside the 1280-1640 text band, clear of faces and TikTok UI)

S = []
def shot(n, src, t0, t1, a, b, **kw):
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "vapor"),
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

B = BAR; b = BEAT
# ---- cold open (filtered build) — voice-over
shot("boat_vo", "p6", 0.0, th(424), 16.50, 19.17, z=[(0, 1.00), (1, 1.12)], tin="tape_in")
shot("blue_vanish", "p6", th(424), th(436), 68.30, 72.30, z=[(0, 1.05), (1, 1.16)], seg=True, vanish=True, tin="eye_dive")
shot("red_scene", "p6", th(436), th(440), 5.30, 6.63, z=[(0, 1.05), (1, 1.15)], tin="assemble")
shot("interrog", "p6", th(440), th(442), 81.40, 82.06, z=[(0, 1.12), (1, 1.20)], tin="polaroid")
shot("blood_face", "p6", th(442), th(444), 30.20, 30.86, z=[(0, 1.00), (1, 1.06)], tin="facematch", face="right")
shot("tape_walk", "p6", th(444), th(448), 13.30, 14.63, z=[(0, 1.00), (1, 1.06)], tin="tear", tout="crt")
# ---- drop: Miami daylight montage
shot("boat_bags", "p5", th(448), th(452), 51.65, 53.00, z=[(0, 1.00), (1, 1.10)], tin="crt", interp="blend", seg=True, vapor_bg=True, motes=True)
shot("pink_wall", "p5", th(452), th(456), 6.30, 7.62, z=[(0, 1.05), (1, 1.12)], tin="cube", palms=True, motes=True)
shot("run", "p4", th(456), th(458), 56.80, 57.45, z=[(0, 1.00), (1, 1.06)], tin="sun", interp="blend", echo=True, motes=True)
shot("boat_grin", "p1", th(458), th(460), 70.60, 71.26, z=[(0, 1.00), (1, 1.05)], tin="filmstrip", palms=True, motes=True)
shot("palms", "p4", th(460), th(464), 33.30, 34.60, z=[(0, 1.00), (1, 1.08)], tin="peel", interp="blend")
shot("grin_kill", "p4", th(464), th(468), 65.85, 67.15, z=[(0, 1.00), (1, 1.08)], tin="ink", interp="blend", face="left", pause=1000)
shot("club", "p4", th(468), th(472), 70.70, 71.80, z=[(0, 1.00), (1, 1.06)], tin="slash", echo=True)
shot("night_garden", "p5", th(472), th(476), 31.50, 32.83, z=[(0, 1.00), (1, 1.08)], tin="logo")
shot("cap_night", "p5", th(476), th(478), 39.85, 40.50, z=[(0, 1.00), (1, 1.05)], tin="burn", lens=(0.06, 0.19, 0.075))
shot("hood", "p3", th(478), th(480), 24.30, 24.95, z=[(0, 1.05), (1, 1.10)], tin="lens")
shot("finger_gun", "p1", th(480), th(484), 64.10, 65.00, z=[(0, 1.00), (1, 1.10)], tin="shadow", muzzle=(820, 785))
# ---- ending: "It was me." (lip-synced) -> VHS rewind -> static (loops into tape load)
shot("it_was_me", "p6", th(484), th(496), 0.85, 4.85, z=[(0, 1.00), (0.75, 1.12), (1, 1.18)], tin="tv_off", tout="rewind_end")
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
_iwm = [s for s in SHOTS if s["n"] == "it_was_me"][0]
VO[2] = (1.02, 3.55, _iwm["t0"] + (1.02 - 0.85))           # lip-sync to the shot's time map (1:1 speed)
# neon words light on their spoken times (vocal stem: "It" 1.13, "was" 2.70-2.92, "me" 3.08-3.38)
END_CAP = [("IT", _iwm["t0"] + (1.13 - 0.85)), ("WAS", _iwm["t0"] + (2.70 - 0.85)), ("ME.", _iwm["t0"] + (3.06 - 0.85))]

# ---- engine knobs (read by render/audio/qc; a new edit sets its own)
DROP_TITLE = "MIAMI"                     # chrome title word that sweeps in at the drop (None = no title)
MONTAGE = (HDROP, 484)                   # half-beat range with beat bounce, glints, light leaks and hits
VANISH_T0 = VO[1][2] + (22.71 - VO[1][0]) + 0.05   # pixel dissolve starts just after "disappear"
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/pack6_clip/vocals.wav"   # Demucs vocal stem the VO lines are cut from

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:12s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {s['tmap'][0][1]:.2f}-{s['tmap'][-1][1]:.2f} x{sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "VO", [round(v[2], 2) for v in VO])
