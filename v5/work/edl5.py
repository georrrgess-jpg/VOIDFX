"""FASTEST — The Flash × bôa "Duvet" (voidfx v5, 9:16). Single source of truth.

Song window: Duvet half-beats h208 -> h288 (exactly 10 bars, 93 BPM), "and you don't even think a thing ...
I am falling, I am fading, I am drowning, tell me to breathe, I am hurting, I have lost it all, I am losing,
tell me to breathe." The window is a whole number of bars, so the loop jumps bar 36 -> bar 26 in tempo.
Loop picture: the last shot flies into Barry's eye -> speed-force streaks collapse to black; the edit opens from
black with a lightning strike that tears the first shot open.
"""
import numpy as np
ROOT = "/home/user/VOIDFX"
FPS, W, H = 60, 1080, 1920
SRC = {"fb": (f"{ROOT}/src/flash_b.mp4", 60.0, 1280, 720), "fa": (f"{ROOT}/src/flash_a.mp4", 25.421, 1280, 720)}

HB, HB_OFF = 0.32211, 0.2085            # half-beat grid of the song (fitted, 529 onsets)
H0, H1 = 208, 288
def st(h): return HB_OFF + h * HB        # song time of half-beat h
SONG_IN = st(H0)
def th(h): return st(h) - SONG_IN        # edit time of half-beat h
def fe(t): return int(round(t * FPS))
def fh(h): return fe(th(h))
def s2e(s): return s - SONG_IN           # song seconds -> edit seconds
DUR = th(H1)
DUR_F = fh(H1)
# compat names used by the shared engine
def te(h): return th(h)
T_STOP = DUR
DROP_HB = 224
LOGO_W = 900
LOCK_FACE = dict(x=540, y=760, w=680)

S = []
def shot(n, src, h0, h1, t0s, t1s, **kw):
    d = dict(n=n, src=src, t0=th(h0), t1=th(h1), tmap=kw.pop("tmap", [(0, t0s), (1, t1s)]), look="speed",
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- intro: "and you don't even think a thing" (calm, title)
shot("open_mask", "fb", 208, 212, 54.45, 55.75, z=[(0, 1.00), (1, 1.04)], tin="emblem")
shot("barry_dark", "fb", 212, 216, 33.10, 34.40, z=[(0, 1.10), (1, 1.18)], tin="flare")
shot("cowl", "fb", 216, 220, 69.00, 70.30, z=[(0, 1.00), (1, 1.10)], tin="phase", tout="slit")
shot("smile", "fb", 220, 224, 56.05, 57.35, z=[(0, 1.05), (1, 1.15)], tin="slit")
# ---- "I am falling, I am fading"
shot("emblem_bolt", "fb", 224, 226, 129.25, 129.90, z=[(0, 1.00), (1, 1.10)], tin="ring", face=None, cx=(640, 640))
shot("green_arcs", "fb", 226, 228, 132.45, 133.10, z=[(0, 1.00), (1, 1.06)], tin="bolt_wipe")
shot("lightning_face", "fb", 228, 232, 83.85, 85.05, z=[(0, 1.05), (1, 1.15)], tin="bolt_split")
shot("equations", "fb", 232, 236, 59.85, 61.05, z=[(0, 1.05), (1, 1.15)], tin="remnant")
shot("close_up", "fb", 236, 240, 37.15, 38.45, z=[(0, 1.10), (1, 1.20)], tin="prism", tout="phase")
# ---- "I am drowning, tell me to breathe"
shot("sparks", "fb", 240, 244, 52.85, 54.30, z=[(0, 1.00), (1, 1.10)], tin="phase", arcs=True)
shot("blue_chest", "fb", 244, 248, 44.00, 45.30, z=[(0, 1.00), (1, 1.10)], tin="whip", arcs=True)
shot("eyes", "fb", 248, 256, 116.60, 119.20, z=[(0, 1.00), (1, 1.25)], tin="bolt_wipe", tout="logo")
# ---- "I am hurting, I have lost it all"
shot("hurting", "fb", 256, 260, 104.55, 105.65, z=[(0, 1.05), (1, 1.15)], tin="logo")
shot("lab_bolt", "fb", 260, 262, 28.00, 28.64, z=[(0, 1.00), (1, 1.05)], tin="smear", face="right")
shot("side_run", "fb", 262, 264, 80.90, 81.54, z=[(0, 1.00), (1, 1.05)], tin="whip", arcs=True, streaks=True)
shot("run_cam", "fb", 264, 266, 66.45, 67.02, z=[(0, 1.00), (1, 1.05)], tin="zoomblur", face=None, cx=(640, 640), streaks=True)
shot("run_close", "fb", 266, 268, 67.46, 68.10, z=[(0, 1.00), (1, 1.05)], tin="remnant", streaks=True)
shot("lightning_run", "fb", 268, 272, 4.35, 5.65, z=[(0, 1.00), (1, 1.08)], tin="roll", arcs=True)
# ---- "I am losing, tell me to breathe"
shot("scream", "fb", 272, 274, 127.70, 128.34, z=[(0, 1.00), (1, 1.06)], tin="shockwave", arcs=True)
shot("beam", "fb", 274, 276, 124.40, 124.76, z=[(0, 1.00), (1, 1.06)], tin="prism", face=None, cx=(560, 600))
shot("lab_storm", "fa", 276, 278, 86.70, 87.40, z=[(0, 1.00), (1, 1.06)], tin="bolt_wipe", interp="blend", arcs=True)
shot("dark_hand", "fb", 278, 280, 63.00, 63.64, z=[(0, 1.05), (1, 1.10)], tin="twirl")
shot("white_suit", "fb", 280, 284, 89.75, 91.05, z=[(0, 1.00), (1, 1.10)], tin="bolt_split", arcs=True)
shot("final_eye", "fb", 284, 288, 85.20, 86.50, z=[(0, 1.05), (0.65, 1.12), (1, 1.20)], tin="ring", tout="slit_end")
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

TITLE = dict(text="THE FASTEST MAN ALIVE", t_in=th(209), t_out=th(219.5))
# lyric lockups: small lead line + big keyword, every word on its sung time (whisper large-v3)
PHRASES = [
    ([("YOU", 67.84), ("DON'T", 68.56), ("EVEN", 69.12)], [("FEEL", 69.26), ("A", 69.96), ("THING", 70.12)], "think", st(220) - 0.03),
    ([("I", 72.46), ("AM", 73.36)], [("FALLING", 74.16)], "fall", 75.40),
    ([("I", 75.50), ("AM", 75.96)], [("FADING", 76.74)], "fade", st(240) - 0.05),
    ([("I", 78.00), ("AM", 78.76)], [("DROWNING", 79.32)], "drown", 80.60),
    ([("TELL", 80.70), ("ME", 81.30), ("TO", 81.68)], [("BREATHE", 81.94)], "breathe", st(256) - 0.02),
    ([("I", 82.90), ("AM", 83.78)], [("HURTING", 84.32)], "hurt", 85.70),
    ([("I", 85.84), ("HAVE", 86.46)], [("LOST", 86.92), ("IT", 87.68), ("ALL", 88.26)], "lost", 88.68),
    ([("I", 88.74), ("AM", 89.38)], [("LOSING", 89.64)], "losing", 90.90),
    ([("TELL", 91.00), ("ME", 91.58), ("TO", 92.00)], [("BREATHE", 92.32)], "breathe", st(288) - 0.30),
]
LYR = []
TITLE = dict(text="", t_in=-1, t_out=-1)

# sanity: every lyric window must be non-empty and start on its sung word
for _p, _k, _st, _e in PHRASES: assert _e > _k[-1][1] + 0.3, (_k, _e)

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:15s} {s['t0']:6.2f}-{s['t1']:6.2f} src {s['src']} {s['tmap'][0][1]:.2f}-{s['tmap'][-1][1]:.2f} speed {sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    print("dur", round(DUR, 3), "frames", DUR_F)
