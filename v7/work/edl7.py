"""HIM ALL ALONG — Dexter × Gunna "Him All Along" (voidfx v7, 9:16). Single source of truth.

Concept: the friendly blood-spatter analyst investigates — and the evidence points back at him. A forensic-noir edit:
deep blacks, cold desaturated light, blood red as the only warm colour, UV-luminol cyan. Cold open on the song's vocal
breakdown: Gunna "on the way to reaching my goals … open … close", then Dexter (lip-synced, S1) "A jar of blood.
Dramatic. Cryptic. Playful. Could it be him?" — Gunna answers "stay strong … HIM ALL ALONG", written in glowing luminol
on kill-room plastic, and the plastic rips open on the song's biggest return (2:13, +17 dB) into the kill-room montage.
Ending: "I'm a serial killer." (lip-synced) -> the camera dives into his pupil -> black -> the edit re-opens through the
magnifying glass on his eye (loop). Song window: half-beats 528 -> 640 (14 bars, 130 BPM), drop at hb576.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v7", "him_all_along_dexter"          # folder + output name (engine reads paths from these)
SONG = f"{ROOT}/src/him_all_along.mp3"
FPS, W, H = 60, 1080, 1920
SRC = {"p8": (f"{ROOT}/src/pack8_s1.mp4", 60.0, 1280, 720), "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.2307482993197279, 0.08076190476190476      # tools/song_map.py
H0, H1, HDROP = 528, 640, 576
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

# ---- dialogue (pack8 seconds; Whisper word times on the pack audio); voice taken from the Demucs stem
VO = [  # (src_in, src_out, edit_at)
    (331.90, 333.10, th(544) + 0.10),     # "A jar of blood."          lip-synced on the jar shot
    (333.56, 334.14, th(550) + 0.00),     # "Dramatic."
    (334.34, 334.92, th(552) + 0.00),     # "Cryptic."
    (335.46, 336.04, th(554) + 0.00),     # "Playful."
    (336.86, 337.92, th(556) + 0.02),     # "Could it be him?"
    (325.19, 326.35, None),               # "I'm a serial killer."     lip-synced on the confession shot (set below)
]
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/p8_dialogue/vocals.wav"   # stem of pack8 318-338 s (offset VO_STEM_T0)
VO_STEM_T0 = 318.0
SONG_VOX = f"{ROOT}/{VER}/audio/sep/htdemucs/song_110_150"            # song stems (vocals / no_vocals) from 110 s
SONG_VOX_T0 = 110.0
VOX_MUTE = (s2e(125.32), s2e(130.52))      # Gunna's vocals drop out under Dexter's lines (instrumental stem)

S = []
def shot(n, src, t0, t1, a, b, **kw):
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "noir"),
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- act 1: the investigation (song's vocal breakdown)
shot("magnifier", "p8", th(528), th(536), 121.20, 123.05, z=[(0, 1.00), (1, 1.08)], tin="lens_open", face=None, cx=(650, 730), lensframe=True)
shot("slide_up", "p8", th(536), th(544), 262.20, 264.05, z=[(0, 1.05), (1, 1.14)], tin="microscope", tout="doors")
shot("jar", "p8", th(544), th(550), 331.80, 333.18, z=[(0, 1.25), (1, 1.35)], tin="doors")
shot("tape", "p7", th(550), th(552), 22.90, 23.36, z=[(0, 1.00), (1, 1.04)], tin="redact")
shot("red_desk", "p8", th(552), th(554), 80.00, 80.46, z=[(0, 1.05), (1, 1.10)], tin="uv_sweep")
shot("lolli", "p8", th(554), th(556), 117.90, 118.36, z=[(0, 1.10), (1, 1.14)], tin="fingerprint")
shot("floor", "p8", th(556), th(568), 392.40, 395.17, z=[(0, 1.00), (1, 1.16)], tin="tape_snap")
shot("smirk", "p8", th(568), th(576), 346.50, 348.35, z=[(0, 1.00), (1, 1.12)], tin="strings", plastic=True)
# ---- act 2: the drop — kill-room montage
shot("red_room", "p7", th(576), th(580), 0.00, 0.92, z=[(0, 1.05), (1, 1.12)], tin="plastic_rip")
shot("kill_table", "p8", th(580), th(584), 389.00, 389.92, z=[(0, 1.00), (1, 1.06)], tin="slash")
shot("plastic_room", "p8", th(584), th(588), 257.20, 258.12, z=[(0, 1.10), (1, 1.16)], tin="board")
shot("overhead", "p8", th(588), th(592), 31.70, 32.62, z=[(0, 1.00), (1, 1.08)], tin="shadow", face=None, cx=(640, 640))
shot("drive", "p8", th(592), th(600), 316.00, 317.85, z=[(0, 1.00), (1, 1.10)], tin="lightstreak")
shot("street", "p8", th(600), th(604), 2.30, 3.22, z=[(0, 1.00), (1, 1.06)], tin="logo_uv", face=None, cx=(600, 700))
shot("sweat", "p8", th(604), th(612), 143.80, 145.65, z=[(0, 1.00), (1, 1.08)], tin="polaroid")
shot("green", "p8", th(612), th(616), 152.20, 153.12, z=[(0, 1.00), (1, 1.06)], tin="scan")
shot("look_up", "p8", th(616), th(624), 355.60, 357.00, z=[(0, 1.00), (1, 1.08)], tin="strobe")
# ---- act 3: the confession -> into his pupil (loops to the magnifier)
shot("confess", "p8", th(624), th(640), 323.60, 327.29, z=[(0, 1.12), (0.6, 1.24), (1, 1.36)], tin="slidebox", tout="pupil_end")
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
_cf = [s for s in SHOTS if s["n"] == "confess"][0]
VO[5] = (325.19, 326.35, _cf["t0"] + (325.19 - 323.60))
def vo_e(vi, src_t): a, b, at = VO[vi]; return at + (src_t - a)

# ---- text: every word on its sung / spoken time. style: case (forensic case-note lockup), stamp (single word),
#      doors (OPEN / CLOSE on the doors), luminol (HIM ALL ALONG on the plastic), confess (end line)
TEXT = [
    dict(style="case", words=[("ON", s2e(122.56), 0), ("THE", s2e(122.86), 0), ("WAY", s2e(122.98), 0), ("TO", s2e(123.12), 0),
                             ("REACHING", s2e(123.18), 1), ("MY", s2e(123.44), 1), ("GOALS", s2e(123.56), 1)], end=s2e(124.30), emph=["GOALS"]),
    dict(style="doors", words=[("OPEN", s2e(124.54), 0), ("CLOSE", s2e(124.98), 1)], end=th(544) - 0.06, emph=[]),
    dict(style="case", words=[("A", vo_e(0, 331.94), 0), ("JAR", vo_e(0, 332.22), 0), ("OF", vo_e(0, 332.50), 0), ("BLOOD.", vo_e(0, 332.70), 0)],
         end=th(550) - 0.03, emph=["BLOOD."]),
    dict(style="stamp", words=[("DRAMATIC.", vo_e(1, 333.60), 0)], end=th(552) - 0.02, emph=[]),
    dict(style="stamp", words=[("CRYPTIC.", vo_e(2, 334.38), 0)], end=th(554) - 0.02, emph=[]),
    dict(style="stamp", words=[("PLAYFUL.", vo_e(3, 335.50), 0)], end=th(556) - 0.02, emph=[]),
    dict(style="case", words=[("COULD", vo_e(4, 336.90), 0), ("IT", vo_e(4, 337.38), 0), ("BE", vo_e(4, 337.48), 0), ("HIM?", vo_e(4, 337.58), 1)],
         end=s2e(130.45), emph=["HIM?"]),
    dict(style="case", words=[("STAY", s2e(130.74), 0), ("STRONG", s2e(130.90), 0)], end=th(568) + 0.35, emph=["STRONG"]),
    dict(style="luminol", words=[("HIM", s2e(131.92), 0), ("ALL", s2e(132.06), 0), ("ALONG", s2e(132.30), 1)], end=th(576), emph=[]),
    dict(style="confess", words=[("I'M", vo_e(5, 325.23), 0), ("A", vo_e(5, 325.51), 0), ("SERIAL", vo_e(5, 325.55), 1), ("KILLER.", vo_e(5, 325.89), 1)],
         end=th(640) - 0.42, emph=["KILLER."]),
]
for _t in TEXT:   # every window must be non-empty and start on its word
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])

# ---- engine knobs (v6 engine compatibility)
CAPS = []; CAP_Y = (1370, 1472); END_CAP = []
DROP_TITLE = None
MONTAGE = (HDROP, 624)
VANISH_T0 = None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:12s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {s['tmap'][0][1]:7.2f}-{s['tmap'][-1][1]:7.2f} x{sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "VO at", [round(v[2], 2) for v in VO])
    for t_ in TEXT: print(f"  {t_['style']:8s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
