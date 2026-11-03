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
shot("cowl", "fb", 216, 220, 69.00, 70.30, z=[(0, 1.00), (1, 1.10)], tin="phase")
shot("street_run", "fb", 220, 224, 65.10, 65.48, z=[(0, 1.00), (1, 1.15)], tout="slit", face=None, cx=(640, 650))
# ---- "I am falling, I am fading"
shot("falling", "fb", 224, 228, 119.45, 120.75, z=[(0, 1.00), (1, 1.10)], tin="slit", face=None, cx=(560, 640))
shot("lightning_face", "fb", 228, 232, 83.85, 85.05, z=[(0, 1.05), (1, 1.15)], tin="bolt_split")
shot("equations", "fb", 232, 236, 59.85, 61.05, z=[(0, 1.05), (1, 1.15)], tin="remnant")
shot("close_up", "fb", 236, 240, 37.15, 38.45, z=[(0, 1.10), (1, 1.20)], tout="phase")
# ---- "I am drowning, tell me to breathe"
shot("sparks", "fb", 240, 244, 52.85, 54.30, z=[(0, 1.00), (1, 1.10)], tin="phase", arcs=True)
shot("blue_chest", "fb", 244, 248, 44.00, 45.30, z=[(0, 1.00), (1, 1.10)], tin="whip", arcs=True)
shot("eyes", "fb", 248, 256, 116.60, 119.20, z=[(0, 1.00), (1, 1.25)], tin="flash", tout="logo")
# ---- "I am hurting, I have lost it all"
shot("hurting", "fb", 256, 260, 104.55, 105.65, z=[(0, 1.05), (1, 1.15)], tin="logo")
shot("lab_bolt", "fb", 260, 262, 28.00, 28.64, z=[(0, 1.00), (1, 1.05)], tin="flash", face="right")
shot("side_run", "fb", 262, 264, 80.90, 81.54, z=[(0, 1.00), (1, 1.05)], tin="whip", arcs=True)
shot("run_cam", "fb", 264, 266, 66.45, 67.02, z=[(0, 1.00), (1, 1.05)], tin="zoomblur", face=None, cx=(640, 640))
shot("run_close", "fb", 266, 268, 67.46, 68.10, z=[(0, 1.00), (1, 1.05)], tin="remnant")
shot("lightning_run", "fb", 268, 272, 4.35, 5.65, z=[(0, 1.00), (1, 1.08)], tin="roll", arcs=True)
# ---- "I am losing, tell me to breathe"
shot("scream", "fb", 272, 274, 127.70, 128.34, z=[(0, 1.00), (1, 1.06)], tin="shockwave", arcs=True)
shot("beam", "fb", 274, 276, 124.40, 124.76, z=[(0, 1.00), (1, 1.06)], tin="cut_rgb", face=None, cx=(560, 600))
shot("lab_storm", "fa", 276, 278, 86.70, 87.40, z=[(0, 1.00), (1, 1.06)], tin="flash", interp="blend", arcs=True)
shot("dark_hand", "fb", 278, 280, 63.00, 63.64, z=[(0, 1.05), (1, 1.10)], tin="twirl")
shot("white_suit", "fb", 280, 284, 89.75, 91.05, z=[(0, 1.00), (1, 1.10)], tin="bolt_split", arcs=True)
shot("final_eye", "fb", 284, 288, 85.20, 86.50, z=[(0, 1.05), (0.65, 1.12), (1, 1.20)], tin="flash", tout="slit_end")
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

TITLE = dict(text="THE FASTEST MAN ALIVE", t_in=th(209), t_out=th(219.5))
# lyric words (song time from whisper large-v3 word timings), styled per moment
LYR = [("FALLING", 74.16, 75.40, "fall"), ("FADING", 76.74, st(240) - 0.05, "fade"),
       ("DROWNING", 79.32, st(248) - 0.02, "drown"), ("tell me to", 80.70, st(256) - 0.02, "pre"), ("BREATHE", 81.94, st(256) - 0.02, "breathe"),
       ("HURTING", 84.32, 85.02, "glitch"), ("LOST IT ALL", 86.92, 88.68, "slam"),
       ("LOSING", 89.64, st(280) - 0.02, "streak"), ("tell me to", 91.00, st(288) - 0.30, "pre"), ("BREATHE", 92.32, st(288) - 0.30, "breathe")]

# sanity: every lyric window must be non-empty and start on its sung word
for _w, _s0, _s1, _st in LYR: assert _s1 > _s0 + 0.3, (_w, _s0, _s1)

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:15s} {s['t0']:6.2f}-{s['t1']:6.2f} src {s['src']} {s['tmap'][0][1]:.2f}-{s['tmap'][-1][1]:.2f} speed {sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    print("dur", round(DUR, 3), "frames", DUR_F)
