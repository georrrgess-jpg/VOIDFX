"""THE DARK PASSENGER (voidfx v2) — edit decision list. Single source of truth.

Music: MATRIX FUNK (slowed) — played back slowed again by R = 1.12644 with pitch drop (vinyl-style),
matching the reference TikTok (measured 102.83 BPM vs the file's 115.82 BPM). Edit time 0 = the song's
half-beat 34 (orig 9.039 s). Timeline unit: 'e' = one half-beat of the slowed song = 0.291771 s.
"""
import os

ROOT = "/home/user/VOIDFX"
R = 1.12644                      # slow-down factor (duration multiplier)
HB_ORIG = 0.25902                # half-beat in the original file (s)
OFF_ORIG = 0.2325                # original-file time of half-beat 0 (grid + measured 13 ms onset bias)
HB0 = 34                         # first half-beat used
E = HB_ORIG * R                  # 0.291771 s per half-beat in the edit
FPS = 60
ORIENT = os.environ.get("ORIENT", "h")          # "h" = 1920x1080, "v" = 1080x1920
W, H = (1920, 1080) if ORIENT == "h" else (1080, 1920)

def te(e):            # edit seconds of half-beat e
    return e * E

def fe(e):            # output frame of half-beat e
    return int(round(e * E * FPS))

def orig_t(e):        # original song time at edit half-beat e
    return OFF_ORIG + (HB0 + e) * HB_ORIG

DROP_E, BANG_E, END_E = 32, 80, 88
DUR_F = fe(END_E)
GAP_E = (14, 16)

PACKS = {
    "p1": dict(path=f"{ROOT}/src/scenepack.mp4", fps=60.0, w=1200, h=720),
    "p2": dict(path=f"{ROOT}/src/scenepack2_60fps.mp4", fps=60.0, w=1280, h=720),
    "p3": dict(path=f"{ROOT}/src/scenepack3_24fps.mp4", fps=24000 / 1001, w=1280, h=720),
}

# ---------------------------------------------------------------------------------------------- clips
# e0,e1  : timeline in half-beats
# src    : pack; tmap: [(u, source seconds)] eased piecewise-linear time map (u = 0..1 over the clip)
# cam    : centre (cx, cy) source px at u=0 and u=1; zoom keys [(u, z)]; rot keys optional
# look   : 'mono' (intro photographic B&W) | 'ink' (comic ink) ; ink params override defaults
# interp : 'hold' (native cadence) | 'blend' | 'flow' (optical-flow slow motion)
# bounce : zoom-punch amplitude on the cut;  fx: extra per-clip effects
CLIPS = [
    # ===== INTRO: the public world (B&W, letterboxed, music filtered) =====
    dict(name="tunnel_walk", e0=0, e1=8, src="p2", tmap=[(0, 62.07), (1, 64.40)], interp="hold",
         cam=dict(c0=(760, 380), c1=(740, 350), zoom=[(0, 1.00), (1, 1.08)]), look="mono", bounce=0),
    dict(name="hall_axe", e0=8, e1=14, src="p3", tmap=[(0, 14.02), (1, 15.72)], interp="hold",
         cam=dict(c0=(640, 300), c1=(660, 280), zoom=[(0, 1.10), (1, 1.30)]), look="mono", bounce=0.03),
    dict(name="hall_flicker", e0=14, e1=16, src="p3", tmap=[(0, 15.72), (1, 15.76)], interp="hold",
         cam=dict(c0=(660, 280), c1=(660, 280), zoom=[(0, 1.30), (1, 1.31)]), look="mono", bounce=0,
         fx=["flicker_out"]),
    dict(name="gloves_light", e0=16, e1=22, src="p2", tmap=[(0, 31.40), (1, 33.15)], interp="hold",
         cam=dict(c0=(690, 330), c1=(700, 300), zoom=[(0, 1.10), (1, 1.20)]), look="mono", bounce=0,
         fx=["light_on"]),
    dict(name="pool_gloves", e0=22, e1=24, src="p2", tmap=[(0, 26.05), (1, 26.62)], interp="hold",
         cam=dict(c0=(500, 260), c1=(500, 255), zoom=[(0, 1.30), (1, 1.36)]), look="mono", bounce=0.04),
    dict(name="eyes_up", e0=24, e1=32, src="p3", tmap=[(0, 22.06), (0.5, 22.62), (0.75, 22.85), (1, 22.94)],
         interp="flow", cam=dict(c0=(505, 285), c1=(585, 270), zoom=[(0, 1.75), (1, 1.90)]), look="mono",
         bounce=0, fx=["predrop_dark"]),
    # ===== DROP: the Dark Passenger's world (ink comic, red only for blood) =====
    dict(name="hood_up", e0=32, e1=34, src="p3", tmap=[(0, 23.30), (0.45, 24.45), (1, 24.82)], interp="hold",
         cam=dict(c0=(640, 300), c1=(650, 290), zoom=[(0, 1.05), (1, 1.10)]), look="ink", bounce=0.16,
         ink=dict(t1=0.28, t2=0.62, gain=1.35, flat=14, flat_c=0.25, lines=0.55, soft=2.0), fx=["drop_hit"]),
    dict(name="jungle_charge", e0=34, e1=36, src="p3", tmap=[(0, 25.86), (0.55, 26.52), (1, 26.80)], interp="hold",
         cam=dict(c0=(640, 330), c1=(700, 320), zoom=[(0, 1.05), (1, 1.15)]), look="ink", bounce=0.10,
         ink=dict(t1=0.24, t2=0.62, flat=12, lines=0.6, soft=1.8), fx=["speed_lines"]),
    dict(name="fence_stare", e0=36, e1=38, src="p1", tmap=[(0, 171.10), (1, 171.76)], interp="hold",
         cam=dict(c0=(470, 230), c1=(500, 250), zoom=[(0, 1.30), (1, 1.40)]), look="ink", bounce=0.08,
         ink=dict(t1=0.22, t2=0.55, gain=1.15), fx=["whip_out"]),
    dict(name="garage_run", e0=38, e1=40, src="p3", tmap=[(0, 5.95), (1, 6.72)], interp="hold",
         cam=dict(c0=(560, 330), c1=(600, 330), zoom=[(0, 1.10), (1, 1.20)]), look="ink", bounce=0.0,
         ink=dict(t1=0.26, t2=0.62), fx=["whip_in", "speed_lines"]),
    dict(name="stick_charge", e0=40, e1=42, src="p3", tmap=[(0, 3.50), (0.5, 4.40), (1, 4.72)], interp="hold",
         cam=dict(c0=(620, 300), c1=(640, 280), zoom=[(0, 1.05), (1, 1.18)]), look="ink", bounce=0.12,
         ink=dict(t1=0.25, t2=0.60), fx=["invert_hit", "speed_lines"]),
    dict(name="drill_flare", e0=42, e1=44, src="p2", tmap=[(0, 42.22), (1, 43.12)], interp="hold",
         cam=dict(c0=(600, 300), c1=(620, 300), zoom=[(0, 1.10), (1, 1.18)]), look="ink", bounce=0.08,
         ink=dict(t1=0.20, t2=0.55)),
    dict(name="blood_slide", e0=44, e1=46, src="p1", tmap=[(0, 109.80), (1, 110.47)], interp="hold",
         cam=dict(c0=(520, 260), c1=(540, 270), zoom=[(0, 1.25), (1, 1.35)]), look="ink", bounce=0.10,
         ink=dict(t1=0.18, t2=0.50, gain=1.2, red_rg=2.0)),
    dict(name="crime_tape", e0=46, e1=47, src="p2", tmap=[(0, 23.42), (1, 23.75)], interp="hold",
         cam=dict(c0=(600, 250), c1=(610, 250), zoom=[(0, 1.12), (1, 1.18)]), look="ink", bounce=0.10,
         ink=dict(t1=0.22, t2=0.58, flat=8, flat_c=0.18)),
    dict(name="kill_room_knife", e0=47, e1=48, src="p2", tmap=[(0, 12.10), (1, 12.42)], interp="hold",
         cam=dict(c0=(700, 300), c1=(720, 290), zoom=[(0, 1.15), (1, 1.25)]), look="ink", bounce=0.08,
         ink=dict(t1=0.22, t2=0.55, gain=1.25, tex=0.22), fx=["slab_out"]),
    dict(name="over_victim", e0=48, e1=52, src="p2", tmap=[(0, 52.00), (1, 53.17)], interp="hold",
         cam=dict(c0=(560, 320), c1=(560, 330), zoom=[(0, 1.05), (1, 1.15)]), look="ink", bounce=0.0,
         ink=dict(t1=0.20, t2=0.50, gain=1.2, tex=0.25, red=False), fx=["slab_in", "words"]),
    dict(name="knife_hands", e0=52, e1=53, src="p1", tmap=[(0, 158.30), (1, 158.60)], interp="hold",
         cam=dict(c0=(540, 320), c1=(540, 320), zoom=[(0, 1.20), (1, 1.24)]), look="ink", bounce=0.10,
         ink=dict(t1=0.20, t2=0.52, gain=1.2)),
    dict(name="bandana", e0=53, e1=54, src="p1", tmap=[(0, 95.00), (1, 95.30)], interp="hold",
         cam=dict(c0=(560, 230), c1=(560, 230), zoom=[(0, 1.25), (1, 1.30)]), look="ink", bounce=0.10,
         ink=dict(t1=0.18, t2=0.45, gain=1.5), fx=["glitch_in"]),
    dict(name="blue_room", e0=54, e1=56, src="p2", tmap=[(0, 44.40), (1, 45.00)], interp="hold",
         cam=dict(c0=(700, 310), c1=(700, 300), zoom=[(0, 1.30), (1, 1.40)]), look="ink", bounce=0.10,
         ink=dict(t1=0.20, t2=0.50, gain=1.3)),
    dict(name="axe_stare", e0=56, e1=57, src="p3", tmap=[(0, 12.20), (1, 12.46)], interp="hold",
         cam=dict(c0=(600, 260), c1=(600, 260), zoom=[(0, 1.70), (1, 1.78)]), look="ink", bounce=0.12,
         ink=dict(t1=0.26, t2=0.62, gain=1.3, flat=14, flat_c=0.25, lines=0.55, soft=2.0)),
    dict(name="hand_on_face", e0=57, e1=58, src="p1", tmap=[(0, 76.45), (1, 76.75)], interp="hold",
         cam=dict(c0=(580, 300), c1=(600, 300), zoom=[(0, 1.10), (1, 1.18)]), look="ink", bounce=0.08,
         ink=dict(t1=0.20, t2=0.52, gain=1.25)),
    dict(name="face_shield", e0=58, e1=59, src="p1", tmap=[(0, 58.75), (1, 59.05)], interp="hold",
         cam=dict(c0=(480, 260), c1=(500, 260), zoom=[(0, 1.15), (1, 1.25)]), look="ink", bounce=0.10,
         ink=dict(t1=0.30, t2=0.70), fx=["invert_hit"]),
    dict(name="gloves_walk", e0=59, e1=60, src="p3", tmap=[(0, 27.00), (1, 27.30)], interp="hold",
         cam=dict(c0=(650, 330), c1=(650, 330), zoom=[(0, 1.35), (1, 1.42)]), look="ink", bounce=0.12,
         ink=dict(t1=0.26, t2=0.62, gain=1.25, flat=12, flat_c=0.22, lines=0.6, soft=1.8)),
    dict(name="shh", e0=60, e1=62, src="p1", tmap=[(0, 96.42), (1, 97.10)], interp="hold",
         cam=dict(c0=(540, 280), c1=(540, 290), zoom=[(0, 1.20), (1, 1.30)]), look="mono", bounce=0.10),
    dict(name="peek", e0=62, e1=64, src="p3", tmap=[(0, 8.34), (1, 8.92)], interp="hold",
         cam=dict(c0=(880, 260), c1=(890, 250), zoom=[(0, 1.55), (1, 1.70)]), look="ink", bounce=0.10,
         ink=dict(t1=0.28, t2=0.62, gain=1.35, flat=14, flat_c=0.25, lines=0.5, soft=2.0)),
    # ===== COMIC PAGE (4 panels slam in on the beats) =====
    dict(name="page", e0=64, e1=72, kind="page", fx=["glitch_out_end"]),
    # ===== FINAL: the friendly mask, the finger gun, BANG =====
    dict(name="finger_gun", e0=72, e1=80, src="p1", tmap=[(0, 63.80), (0.85, 64.88), (1, 65.02)], interp="blend",
         cam=dict(c0=(560, 260), c1=(560, 250), zoom=[(0, 1.10), (1, 1.42)]), look="ink", bounce=0.10,
         ink=dict(t1=0.22, t2=0.58, gain=1.05, red_rg=4.6), fx=["glitch_in", "strobe_end"]),
    dict(name="logo", e0=80, e1=88, kind="logo"),
]

PANELS = [  # polygon on the 1920x1080 page, appear half-beat, clip
    dict(poly=[(70, 60), (1010, 60), (960, 515), (70, 515)], e=64, caption="THE DARK PASSENGER",
         clip=dict(name="p_hands", src="p2", tmap=[(0, 13.60), (1, 15.90)], interp="hold",
                   cam=dict(c0=(720, 330), c1=(740, 330), zoom=[(0, 1.25), (1, 1.32)]),
                   ink=dict(t1=0.20, t2=0.50, gain=1.4))),
    dict(poly=[(1035, 60), (1850, 60), (1850, 515), (985, 515)], e=66,
         clip=dict(name="p_car", src="p2", tmap=[(0, 56.40), (1, 58.15)], interp="hold",
                   cam=dict(c0=(660, 280), c1=(660, 270), zoom=[(0, 1.55), (1, 1.62)]),
                   ink=dict(t1=0.10, t2=0.30, gain=1.9))),
    dict(poly=[(70, 540), (700, 540), (650, 1020), (70, 1020)], e=68,
         clip=dict(name="p_crouch", src="p2", tmap=[(0, 46.60), (1, 47.75)], interp="hold",
                   cam=dict(c0=(500, 330), c1=(500, 330), zoom=[(0, 1.45), (1, 1.50)]),
                   ink=dict(t1=0.20, t2=0.50, gain=1.3))),
    dict(poly=[(725, 540), (1850, 540), (1850, 1020), (675, 1020)], e=70,
         clip=dict(name="p_rapture", src="p1", tmap=[(0, 134.00), (1, 134.58)], interp="hold",
                   cam=dict(c0=(610, 230), c1=(610, 230), zoom=[(0, 1.20), (1, 1.26)]),
                   ink=dict(t1=0.22, t2=0.55, gain=1.1))),
]

NAME_CARD = dict(e_in=2, e_out=13, line1="DEXTER MORGAN", line2="BLOOD SPATTER ANALYST  —  MIAMI METRO P.D.")
TITLE = dict(text="DEXTER", e_in=28, e_drop=DROP_E)
WORDS = [("TONIGHT'S", 48), ("THE", 49), ("NIGHT", 50)]
LETTERBOX = 138 if ORIENT == "h" else 250     # intro bars, snap open on the drop
WATERMARK = dict(width=250, opacity=0.62, margin=(46, 40)) if ORIENT == "h" else dict(width=230, opacity=0.62, margin=(150, 330))

# transitions applied around a cut (half-beat): radial zoom-through / spin with motion blur
TRANS = [("zoom", 36), ("zoom", 42), ("spin", 54), ("zoom", 60)]
TRANS2 = [("slices", 46), ("inkbleed", 62)]       # two-clip transitions
# blood-splatter bursts: (half-beat, centre x, y, size px, seed, lifetime in half-beats)
SPLATS = ([(32.6, 250, 250, 300, 1, 2.0), (32.6, 1690, 840, 340, 2, 2.0), (50, 560, 900, 230, 3, 2.0)] if ORIENT == "h" else
          [(32.6, 190, 520, 260, 1, 2.0), (32.6, 900, 1480, 300, 2, 2.0), (50, 250, 1330, 210, 3, 2.0)])
LAYOUT = dict(
    h=dict(title=(960, 742, 1.0), namecard=(150, 772, 852), logo=980,
           words={"TONIGHT'S": (760, 330, 215), "THE": (1270, 520, 190), "NIGHT": (1060, 770, 340)}, rush=(1290, 780)),
    v=dict(title=(540, 1240, 0.70), namecard=(80, 1330, 1405), logo=880,
           words={"TONIGHT'S": (540, 640, 150), "THE": (540, 850, 190), "NIGHT": (540, 1090, 235)}, rush=(540, 1620)),
)[ORIENT]
if ORIENT == "v":
    PANELS[0]["poly"] = [(50, 150), (1030, 150), (1030, 560), (50, 610)]
    PANELS[1]["poly"] = [(50, 635), (1030, 585), (1030, 1000), (50, 1000)]
    PANELS[2]["poly"] = [(50, 1025), (1030, 1025), (1030, 1390), (50, 1440)]
    PANELS[3]["poly"] = [(50, 1465), (1030, 1415), (1030, 1780), (50, 1780)]
# vertical reframing: subject x centre per clip (source px), gentler zoom; overrides below after checks
VX = {"tunnel_walk": (860, 830), "eyes_up": (700, 730), "gloves_light": (650, 660), "over_victim": (670, 670),
      "blue_room": (760, 760), "peek": (790, 800), "drill_flare": (600, 600)}
