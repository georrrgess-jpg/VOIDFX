"""SURPRISE v4 — Doakes × Need It (voidfx, 9:16). Single source of truth.

Loops: the edit ends by flying into Dexter's pupil (black) and opens by irising out of black.
  0.00 - 6.50  COLD OPEN  continuous Doakes/Dexter exchange (flow-smoothed), BAY HARBOR BUTCHER behind his head
  6.50 - 11.06 BUILD      push into Doakes's barrel -> fly through -> scope view of Dexter -> bass gap
 11.06         DROP       muzzle flash -> cracked glass -> shatter
 11.06 - 22.31 MONTAGE    fly-through transitions (dark pass, eye, roll, voidfx 'o', cube, photo, polaroid, face-lock ...)
 22.31 - 25.00 OUTRO      freeze on "caught up"; Doakes: "I always knew there was something with you." -> into the pupil
"""
ROOT = "/home/user/VOIDFX"
FPS, W, H = 60, 1080, 1920
SRC = {"dk": (f"{ROOT}/src/doakes.mp4", 60.0, 1280, 720), "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720),
       "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720), "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720),
       "p3": (f"{ROOT}/src/scenepack3_24fps.mp4", 24000 / 1001, 1280, 720)}

HB, HB_OFF = 0.40540, 0.388
SONG_IN, T_SONG = 12.45, 6.50
def st(h): return HB_OFF + h * HB
def te(h): return T_SONG + st(h) - SONG_IN
def fe(t): return int(round(t * FPS))
def fh(h): return fe(te(h))
SONG_OUT_HB = 68.75
DROP_HB = 41
T_STOP = te(SONG_OUT_HB)
DUR = 25.00
DUR_F = fe(DUR)

# dialogue: (src_in, src_out, edit_at)  — A+B is ONE continuous take from the scene
DIALOGUE = [(16.20, 20.50, 0.00),        # DOAKES "Jesus fucking Christ, you're the Bay Harbor Butcher."  DEXTER "I really hate that name."
            (26.86, 28.97, 4.30),        # DEXTER "What can I say? You were right about me." (J-cut under the reaction)
            (23.20, 25.12, 22.70)]       # DOAKES "I always knew there was something with you."
def d2e(i, s): a, b, at = DIALOGUE[i]; return at + (s - a)
CAPTIONS = [  # (dialogue index, [(word, src start)], src end, emphasis words)
    (0, [("Jesus", 16.28), ("fucking", 16.76), ("Christ,", 17.22)], 17.60, []),
    (0, [("you're", 17.66), ("the", 17.88)], 18.00, []),
    (0, [("I", 19.06), ("really", 19.48), ("hate", 19.68), ("that", 19.96), ("name.", 20.12)], 20.45, []),
    (1, [("What", 27.06), ("can", 27.54), ("I", 27.66), ("say?", 27.78)], 28.00, []),
    (1, [("You", 28.02), ("were", 28.12), ("right", 28.24), ("about", 28.40), ("me.", 28.62)], 28.95, ["me."]),
    (2, [("I", 23.28), ("always", 23.70), ("knew", 23.98), ("there", 24.12)], 24.20, []),
    (2, [("was", 24.22), ("something", 24.38), ("with", 24.56), ("you.", 24.82)], 25.10, ["you."]),
]
BHB = [("BAY", 18.02), ("HARBOR", 18.22), ("BUTCHER", 18.46)]      # title behind Dexter's head

def s2e(s): return T_SONG + s - SONG_IN
LYRICS = [("I NEED IT", 13.36, 14.06), ("UNDEFEATED", 14.72, 15.60), ("BLEED IT", 16.78, 16.99),
          ("BULLETS", 18.42, 18.95), ("I CAN'T SEE IT", 19.68, 20.46), ("CAN'T GET CAUGHT", 27.40, 28.24)]
LYRIC_WORDS = {"I NEED IT": [("I", 13.36), ("NEED", 13.56), ("IT", 13.80)],
               "CAN'T GET CAUGHT": [("CAN'T", 27.40), ("GET", 27.66), ("CAUGHT", 27.74)]}

T_OUT_A = 4.30          # end of the continuous take
SHOTS = [
    # ===== COLD OPEN (flow-smoothed) =====
    dict(n="open_doakes", src="dk", t0=0.00, t1=1.40, tmap=[(0, 16.37), (0.13, 16.38), (1, 17.60)], z=[(0, 1.22), (1, 1.34)],
         face="largest", look="night", interp="flow", tin="iris"),
    dict(n="bhb_close", src="dk", t0=1.40, t1=2.87, tmap=[(0, 14.60), (1, 16.07)], z=[(0, 1.30), (1, 1.38)],
         face="largest", look="night", interp="flow", knockout=True),
    dict(n="dex_hate", src="dk", t0=2.87, t1=T_OUT_A, tmap=[(0, 19.07), (1, 20.50)], z=[(0, 1.38), (1, 1.50)],
         face="largest", look="night", interp="flow", tin="dissolve"),
    dict(n="bridge", src="dk", t0=T_OUT_A, t1=4.69, tmap=[(0, 20.50), (1, 20.62)], z=[(0, 1.50), (1, 1.62)],
         face="largest", look="night", interp="flow", morph_to="dex_right"),
    dict(n="dex_right", src="dk", t0=4.69, t1=te(30), tmap=[(0, 27.25), (1, 29.16)], z=[(0, 1.70), (1, 2.15)],
         face="largest", look="night", interp="flow", tout="whiteflash"),
    # ===== BUILD =====
    dict(n="doakes_gun", src="dk", t0=te(30), t1=te(33), tmap=[(0, 66.72), (1, 67.98)], z=[(0, 1.00), (1, 1.18)],
         face="largest", look="night", interp="flow", barrel=(524, 547), tout="barrel"),
    dict(n="scope", src="dk", t0=te(33), t1=te(40.5), tmap=[(0, 46.05), (1, 48.06)], z=[(0, 1.05), (0.62, 1.20), (1, 1.62)],
         face="largest", look="night", interp="flow", scope=True, drain=(0.62, 1.0), tin="scope_in"),
    dict(n="barrel", src="dk", t0=te(40.5), t1=te(41), tmap=[(0, 95.49), (1, 95.60)], z=[(0, 1.0), (1, 1.10)],
         face=None, cx=(520, 520), look="night"),
    # ===== MONTAGE =====
    dict(n="night_walk", src="p5", t0=te(41), t1=te(45), tmap=[(0, 31.40), (0.55, 31.85), (1, 33.10)], z=[(0, 1.00), (1, 1.18)],
         face="largest", look="cine", tin="shatter", interp="blend", tout="darkpass"),
    dict(n="turn", src="p5", t0=te(45), t1=te(47), tmap=[(0, 16.30), (1, 17.10)], z=[(0, 1.05), (1, 1.12)],
         face="largest", look="cine", tin="darkpass", tout="eye"),
    dict(n="hood", src="p3", t0=te(47), t1=te(49), tmap=[(0, 24.30), (1, 25.10)], z=[(0, 1.05), (1, 1.12)],
         face="largest", look="cine", tin="eye", tout="roll"),
    dict(n="choke", src="p4", t0=te(49), t1=te(51), tmap=[(0, 65.90), (1, 66.90)], z=[(0, 1.00), (1, 1.06)],
         face="left", look="cine", tin="roll"),
    dict(n="attack", src="p4", t0=te(51), t1=te(52), tmap=[(0, 16.55), (1, 17.05)], z=[(0, 1.00), (1, 1.05)],
         face="largest", look="cine", tin="flash"),
    dict(n="fight", src="dk", t0=te(52), t1=te(53), tmap=[(0, 95.82), (1, 96.30)], z=[(0, 1.00), (1, 1.05)],
         face="largest", look="cine", tin="flash", tout="logo"),
    dict(n="boat", src="p5", t0=te(53), t1=te(55), tmap=[(0, 52.55), (1, 53.75)], z=[(0, 1.00), (1, 1.05)],
         face="largest", look="cine", tin="logo", tout="slash"),
    dict(n="photos", src="p5", t0=te(55), t1=te(57), tmap=[(0, 36.20), (1, 37.00)], z=[(0, 1.00), (1, 1.04)],
         face="largest", look="cine", tin="slash", pan_to=(0.45, 640, 360), photo=((540, 30), (727, 30), (727, 262), (540, 262)),
         tout="photo"),
    dict(n="lamp", src="p5", t0=te(57), t1=te(59), tmap=[(0, 41.30), (1, 42.20)], z=[(0, 1.00), (1, 1.06)],
         face="largest", look="cine", tin="photo", tout="polaroid"),
    dict(n="lock1", src="dk", t0=te(59), t1=te(60), tmap=[(0, 46.40), (1, 46.80)], lock=True, face="largest", look="cine", tin="polaroid", interp="flow"),
    dict(n="lock2", src="p3", t0=te(60), t1=te(61), tmap=[(0, 12.20), (1, 12.60)], lock=True, face="largest", look="cine", tin="cut_rgb"),
    dict(n="lock3", src="p5", t0=te(61), t1=te(62), tmap=[(0, 59.20), (1, 59.60)], lock=True, face="largest", look="cine", tin="cut_rgb"),
    dict(n="lock4", src="p5", t0=te(62), t1=te(63), tmap=[(0, 24.95), (1, 25.35)], lock=True, face="largest", look="cine", tin="cut_rgb", tout="zoomblur"),
    dict(n="tackle", src="p4", t0=te(63), t1=te(65), tmap=[(0, 56.60), (1, 57.55)], z=[(0, 1.00), (1, 1.06)],
         face="largest", look="cine", tin="zoomblur", echo=True),
    dict(n="icecream", src="p4", t0=te(65), t1=te(67), tmap=[(0, 72.86), (1, 73.46)], z=[(0, 1.05), (1, 1.12)],
         face=(820, 250), interp="blend", look="cine", tin="datamosh"),
    dict(n="fingergun", src="p1", t0=te(67), t1=T_STOP, tmap=[(0, 64.20), (1, 64.92)], z=[(0, 1.00), (1, 1.10)],
         face="largest", look="cine", tin="split", seg=True),
    # ===== OUTRO (loops into the start) =====
    dict(n="freeze", src="p1", t0=T_STOP, t1=22.62, tmap=[(0, 64.92), (1, 64.92)], z=[(0, 1.10), (1, 1.16)],
         face="largest", look="cine", freeze=True, seg=True),
    dict(n="dex_end", src="dk", t0=22.62, t1=DUR, tmap=[(0, 32.20), (1, 34.28)], z=[(0, 1.00), (0.78, 1.18), (1, 1.30)],
         face="largest", look="night", interp="flow", tin="dissolve", tout="pupil"),
]
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
LOCK_FACE = dict(x=540, y=760, w=680)
LOGO_W = 900                     # voidfx logo width when it slams in (the only watermark appearance)

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        print(f"{s['n']:12s} {s['t0']:6.2f}-{s['t1']:6.2f} ({s['t1'] - s['t0']:.2f}s) {s['src']} in={s.get('tin', '')} out={s.get('tout', '')}")
    assert prev == DUR_F
    print("frames", DUR_F, "drop", round(te(DROP_HB), 3), "stop", round(T_STOP, 3))
