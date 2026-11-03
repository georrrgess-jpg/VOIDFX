"""SURPRISE — Doakes × Need It (voidfx v3, 9:16). Single source of truth for the edit.

Edit structure (seconds):
  0.00 - 6.50  COLD OPEN  Doakes catches Dexter (scene audio, word-timed captions, tracked name tags)
  6.50 - 11.06 BUILD      song "I said I need it ... then I bleed it" — standoff, lyric type, reticle
 11.06         DROP       muzzle flash -> cracked glass -> shatter (bass re-entry, song hb41)
 11.06 - 22.31 MONTAGE    one cut per beat (74 BPM), bursts, designed transitions
 22.31 - 24.75 OUTRO      music stops on "caught up"; Doakes: "I always knew there was something with you."
 24.75 - 26.40 LOGO
"""
import os
ROOT = "/home/user/VOIDFX"
FPS, W, H = 60, 1080, 1920

SRC = {"dk": (f"{ROOT}/src/doakes.mp4", 60.0, 1280, 720), "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720),
       "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720), "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720),
       "p2": (f"{ROOT}/src/scenepack2_60fps.mp4", 60.0, 1280, 720), "p3": (f"{ROOT}/src/scenepack3_24fps.mp4", 24000 / 1001, 1280, 720)}

# ---------------------------------------------------------------- music
HB = 0.40540                      # half-beat (74 BPM)
HB_OFF = 0.388                    # song time of half-beat 0 (bass-onset corrected)
SONG_IN = 12.45                   # song second played at edit T_SONG
T_SONG = 6.50
def st(h): return HB_OFF + h * HB                  # song time of half-beat h
def te(h): return T_SONG + st(h) - SONG_IN          # edit time of half-beat h
def fe(t): return int(round(t * FPS))
def fh(h): return fe(te(h))
SONG_OUT_HB = 68.75               # music stops here (after "caught up")
DROP_HB = 41
T_STOP = te(SONG_OUT_HB)
T_LOGO = 24.75
DUR = 26.40
DUR_F = fe(DUR)

# ---------------------------------------------------------------- dialogue (doakes.mp4 seconds -> edit seconds)
DIALOGUE = [  # (src_in, src_out, edit_at)
    (16.20, 18.88, 0.00),          # DOAKES: "Jesus fucking Christ, you're the Bay Harbor butcher."
    (19.00, 20.50, 2.76),          # DEXTER: "I really hate that name."
    (26.98, 28.97, 4.49),          # DEXTER: "What can I say? You were right about me."
    (23.20, 25.12, 22.62),         # DOAKES: "I always knew there was something with you."
]
# captions: word, src start (whisper large-v3, verified on the waveform), speaker
CAPTIONS = [
    [("Jesus", 16.28), ("fucking", 16.76), ("Christ,", 17.22), ("you're", 17.66), ("the", 17.88), ("Bay", 18.02), ("Harbor", 18.22), ("Butcher.", 18.46)],
    [("I", 19.06), ("really", 19.48), ("hate", 19.68), ("that", 19.96), ("name.", 20.12)],
    [("What", 27.06), ("can", 27.54), ("I", 27.66), ("say?", 27.78), ("You", 28.02), ("were", 28.12), ("right", 28.24), ("about", 28.40), ("me.", 28.62)],
    [("I", 23.28), ("always", 23.70), ("knew", 23.98), ("there", 24.12), ("was", 24.22), ("something", 24.38), ("with", 24.56), ("you.", 24.82)],
]
CAP_SPEAKER = ["DOAKES", "DEXTER", "DEXTER", "DOAKES"]
CAP_END = [18.88, 20.48, 28.95, 25.10]

def d2e(i, s):  # dialogue i: source second -> edit second
    a, b, at = DIALOGUE[i]
    return at + (s - a)

# lyric typography (song word times from whisper large-v3)
LYRICS = [("I NEED IT", 13.36, 14.06), ("UNDEFEATED", 14.72, 15.60), ("BLEED IT", 16.78, 16.99),
          ("BULLETS", 18.42, 18.90), ("I CAN'T SEE IT", 19.68, 20.46), ("CAN'T GET CAUGHT", 27.40, 28.24)]
def s2e(s): return T_SONG + s - SONG_IN

# ---------------------------------------------------------------- shots
# t0,t1  : edit seconds; tmap: [(u, src s)] piecewise (pchip if >2 keys); z: zoom keys (1 = full source height)
# face   : "largest"/"left"/"right"/(x,y) hint for the tracker; fx=None -> manual centre (cx, cy)
# look   : "night" (cold open) | "cine" (montage)
# tin    : transition INTO this shot (name), tout handled by the next shot's tin
SHOTS = [
    # ===== COLD OPEN =====
    dict(n="doakes_aim", src="dk", t0=0.00, t1=1.40, tmap=[(0, 16.38), (1, 17.78)], z=[(0, 1.10), (1, 1.22)],
         face="largest", look="night", tag="SGT. JAMES DOAKES"),
    dict(n="dex_close", src="dk", t0=1.40, t1=2.76, tmap=[(0, 32.30), (1, 33.66)], z=[(0, 1.00), (1, 1.12)],
         face="largest", look="night", tag="DEXTER MORGAN", stamp=True, tin="flash_soft"),
    dict(n="dex_hate", src="dk", t0=2.76, t1=4.42, tmap=[(0, 19.08), (1, 20.64)], z=[(0, 1.35), (1, 1.50)],
         face="largest", look="night"),
    dict(n="dex_right", src="dk", t0=4.42, t1=te(30), tmap=[(0, 27.27), (0.12, 27.27), (1, 28.98)], z=[(0, 1.40), (1, 1.75)],
         face="largest", look="night"),
    # ===== BUILD (song hb30 -> hb41) =====
    dict(n="doakes_gun", src="dk", t0=te(30), t1=te(33), tmap=[(0, 66.72), (1, 67.98)], z=[(0, 1.00), (1, 1.10)],
         face="largest", look="night", tin="glitch_in"),
    dict(n="dex_stare", src="dk", t0=te(33), t1=te(35), tmap=[(0, 32.60), (1, 33.40)], z=[(0, 1.05), (1, 1.12)],
         face="largest", look="night", reticle=True),
    dict(n="massacre", src="p4", t0=te(35), t1=te(37), tmap=[(0, 74.95), (1, 75.95)], z=[(0, 1.0), (1, 1.12)],
         face=None, cx=(640, 640), look="cine", tin="whip", fit=True),
    dict(n="dex_still", src="dk", t0=te(37), t1=te(40.5), tmap=[(0, 46.05), (1, 47.90)], z=[(0, 1.0), (1, 1.35)],
         face="largest", look="night", reticle=True, drain=True),
    dict(n="barrel", src="dk", t0=te(40.5), t1=te(41), tmap=[(0, 95.49), (1, 95.60)], z=[(0, 1.0), (1, 1.08)],
         face=None, cx=(520, 520), look="night", interp="flow"),
    # ===== MONTAGE (hb41 -> hb68.75) =====
    dict(n="night_walk", src="p5", t0=te(41), t1=te(45), tmap=[(0, 31.40), (0.55, 31.85), (1, 33.10)], z=[(0, 1.00), (1, 1.12)],
         face="largest", look="cine", tin="shatter", interp="blend"),
    dict(n="turn", src="p5", t0=te(45), t1=te(47), tmap=[(0, 16.30), (1, 17.10)], z=[(0, 1.05), (1, 1.12)],
         face="largest", look="cine", tin="split"),
    dict(n="hood", src="p3", t0=te(47), t1=te(49), tmap=[(0, 24.30), (1, 25.10)], z=[(0, 1.05), (1, 1.12)],
         face="largest", look="cine", tin="eye"),
    dict(n="choke", src="p4", t0=te(49), t1=te(51), tmap=[(0, 65.90), (1, 66.90)], z=[(0, 1.00), (1, 1.06)],
         face="left", look="cine", tin="cube"),
    dict(n="attack", src="p4", t0=te(51), t1=te(52), tmap=[(0, 16.55), (1, 17.05)], z=[(0, 1.00), (1, 1.05)],
         face="largest", look="cine", tin="flash"),
    dict(n="fight", src="dk", t0=te(52), t1=te(53), tmap=[(0, 95.82), (1, 96.30)], z=[(0, 1.00), (1, 1.05)],
         face="largest", look="cine", tin="flash"),
    dict(n="boat", src="p5", t0=te(53), t1=te(55), tmap=[(0, 52.55), (1, 53.75)], z=[(0, 1.00), (1, 1.05)],
         face="largest", look="cine", tin="datamosh"),
    dict(n="photos", src="p5", t0=te(55), t1=te(57), tmap=[(0, 36.20), (1, 37.10)], z=[(0, 1.00), (1, 1.08)],
         face="largest", look="cine", tin="whip"),
    dict(n="lamp", src="p5", t0=te(57), t1=te(59), tmap=[(0, 41.30), (1, 42.20)], z=[(0, 1.00), (1, 1.06)],
         face="largest", look="cine", tin="leak", polaroid_out=True),
    # face-lock burst: four faces at the same screen spot and size, one per half-beat
    dict(n="lock1", src="dk", t0=te(59), t1=te(60), tmap=[(0, 46.40), (1, 46.80)], lock=True, face="largest", look="cine", tin="polaroid"),
    dict(n="lock2", src="p3", t0=te(60), t1=te(61), tmap=[(0, 12.20), (1, 12.60)], lock=True, face="largest", look="cine", tin="cut_rgb"),
    dict(n="lock3", src="p5", t0=te(61), t1=te(62), tmap=[(0, 59.20), (1, 59.60)], lock=True, face="largest", look="cine", tin="cut_rgb"),
    dict(n="lock4", src="p5", t0=te(62), t1=te(63), tmap=[(0, 24.95), (1, 25.35)], lock=True, face="largest", look="cine", tin="cut_rgb"),
    dict(n="tackle", src="p4", t0=te(63), t1=te(65), tmap=[(0, 56.60), (1, 57.55)], z=[(0, 1.00), (1, 1.06)],
         face="largest", look="cine", tin="zoomblur", echo=True),
    dict(n="icecream", src="p4", t0=te(65), t1=te(67), tmap=[(0, 72.86), (1, 73.46)], z=[(0, 1.05), (1, 1.12)],
         face=(820, 250), interp="blend", look="cine", tin="slide"),
    dict(n="fingergun", src="p1", t0=te(67), t1=T_STOP, tmap=[(0, 64.20), (1, 64.92)], z=[(0, 1.00), (1, 1.10)],
         face="largest", look="cine", tin="flash"),
    # ===== OUTRO =====
    dict(n="freeze", src="p1", t0=T_STOP, t1=22.62, tmap=[(0, 64.92), (1, 64.92)], z=[(0, 1.10), (1, 1.16)],
         face="largest", look="cine", freeze=True),
    dict(n="dex_end", src="dk", t0=22.62, t1=T_LOGO, tmap=[(0, 32.20), (1, 34.25)], z=[(0, 1.00), (1, 1.18)],
         face="largest", look="night", tin="glitch_in"),
    dict(n="logo", kind="logo", t0=T_LOGO, t1=DUR),
]
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

LOCK_FACE = dict(x=540, y=760, w=680)      # screen position/size for the face-lock burst
WATERMARK = dict(width=190, opacity=0.45, y=226)
SAFE = dict(top=200, bottom=1560, left=70, right=930)

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev)
        prev = s["f1"]
        print(f"{s['n']:12s} {s['t0']:6.2f}-{s['t1']:6.2f} ({s['t1'] - s['t0']:.2f}s) {s.get('src', '')} {s.get('tin', '')}")
    print("total", DUR, "frames", DUR_F, "drop at", round(te(DROP_HB), 3), "stop at", round(T_STOP, 3))
    assert prev == DUR_F
