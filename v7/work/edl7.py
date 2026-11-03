"""HIM ALL ALONG — Dexter × Gunna "Him All Along" (voidfx v7 rev 2, 9:16). Single source of truth.

Concept: the friendly blood-spatter analyst investigates — and the evidence points back at him. Forensic noir.
Act 1 (song's vocal breakdown): his eye through a magnifying glass; "on the way to reaching my goals … open … close" —
his rosewood blood-slide box slams shut on "close", reopens, and the camera dives into a blood drop on a slide; crime
scene (evidence markers), the red desk; Dexter on the kill-room floor: "Could it be him?" (lip-synced) — Gunna answers
"HIM ALL ALONG" in luminol on kill-room plastic, which stretches toward the camera and BURSTS on the drop (2:13, +17 dB).
Act 2: kill-room montage. Ending: he smirks at the camera (CASE CLOSED), the magnifying glass sweeps in on his eye, the
camera dives into his pupil -> black -> loops into the glass opening on the same eye.
Song window: half-beats 528 -> 640 (14 bars, 130 BPM), drop at hb576.
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

# ---- dialogue (pack8 seconds; Whisper word times); voice from the Demucs stem
VO = [  # (src_in, src_out, edit_at)
    (336.86, 337.92, th(556) + 0.02),     # "Could it be him?"  (the only line — answered by Gunna's "HIM ALL ALONG")
]
VO_STEM = f"{ROOT}/{VER}/audio/sep/htdemucs/p8_dialogue/vocals.wav"   # stem of pack8 318-338 s (offset VO_STEM_T0)
VO_STEM_T0 = 318.0
SONG_VOX = f"{ROOT}/{VER}/audio/sep/htdemucs/song_110_150"            # song stems (vocals / no_vocals) from 110 s
SONG_VOX_T0 = 110.0
VOX_MUTE = (VO[0][2] - 0.10 + SONG_IN, VO[0][2] + 1.20 + SONG_IN)     # (song s) Gunna's vocal steps aside under Dexter's line
VOX_MUTE = (s2e(VOX_MUTE[0]), s2e(VOX_MUTE[1]))

S = []
def shot(n, src, t0, t1, a, b, **kw):
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "noir"),
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- act 1: the investigation (song's vocal breakdown)
shot("magnifier", "p8", th(528), th(536), 121.20, 123.05, z=[(0, 1.00), (1, 1.08)], tin="lens_open", face=None, cx=(650, 730), lensframe=True)
shot("slide_up", "p8", th(536), th(544), 262.20, 264.05, z=[(0, 1.05), (1, 1.14)], tin="microscope")
shot("tape", "p7", th(544), th(550), 22.55, 23.70, z=[(0, 1.00), (1, 1.06)], tin="slidebox_close", markers=True)
shot("red_desk", "p8", th(550), th(556), 78.20, 79.58, z=[(0, 1.05), (1, 1.12)], tin="uv_sweep")
shot("floor", "p8", th(556), th(568), 392.40, 395.17, z=[(0, 1.00), (1, 1.16)], tin="tape_snap")
shot("smirk", "p8", th(568), th(576), 346.50, 348.35, z=[(0, 1.00), (1, 1.12)], tin="blood_lens", plastic=True)
# ---- act 2: the drop — the plastic bursts into the kill-room montage
shot("red_room", "p7", th(576), th(580), 0.00, 0.92, z=[(0, 1.05), (1, 1.12)], tin="burst")
shot("kill_table", "p8", th(580), th(584), 389.00, 389.92, z=[(0, 1.00), (1, 1.06)], tin="slash")
shot("plastic_room", "p8", th(584), th(588), 257.20, 258.12, z=[(0, 1.10), (1, 1.16)], tin="board")
shot("overhead", "p8", th(588), th(592), 31.70, 32.62, z=[(0, 1.00), (1, 1.08)], tin="zipper", face=None, cx=(640, 640))
shot("drive", "p8", th(592), th(600), 316.00, 317.85, z=[(0, 1.00), (1, 1.10)], tin="lightstreak")
shot("street", "p8", th(600), th(604), 2.30, 3.22, z=[(0, 1.00), (1, 1.06)], tin="logo_orig", face=None, cx=(600, 700))
shot("sweat", "p8", th(604), th(612), 143.80, 145.65, z=[(0, 1.00), (1, 1.08)], tin="polaroid")
shot("green", "p8", th(612), th(616), 152.20, 153.12, z=[(0, 1.00), (1, 1.06)], tin="m99")
shot("look_up", "p8", th(616), th(624), 355.60, 356.96, z=[(0, 1.00), (1, 1.08)], tin="strobe")
# ---- ending: he smirks at the camera (CASE CLOSED) -> the magnifying glass sweeps in -> into his pupil (loops)
shot("smirk_cam", "p8", th(624), th(632), 283.40, 284.46, z=[(0, 1.00), (1, 1.10)], tin="scan")
shot("end_eye", "p8", th(632), th(640), 111.20, 113.05, z=[(0, 1.05), (1, 1.16)], tin="mag_sweep", tout="pupil_end", lensframe=True)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])
def vo_e(vi, src_t): a, b, at = VO[vi]; return at + (src_t - a)

# ---- text: every word on its sung / spoken time. styles: case (forensic case-note lockup), doors (OPEN typed; CLOSE is
#      engraved on the slide-box lid), luminol (HIM ALL / ALONG on the plastic), casestamp (rubber stamp, ending)
TEXT = [
    dict(style="case", words=[("ON", s2e(122.56), 0), ("THE", s2e(122.86), 0), ("WAY", s2e(122.98), 0), ("TO", s2e(123.12), 0),
                             ("REACHING", s2e(123.18), 1), ("MY", s2e(123.44), 1), ("GOALS", s2e(123.56), 1)], end=s2e(124.30), emph=["GOALS"]),
    dict(style="doors", words=[("OPEN", s2e(124.54), 0), ("CLOSE", s2e(124.98), 1)], end=th(544) - 0.14, emph=[]),
    dict(style="case", words=[("COULD", vo_e(0, 336.90), 0), ("IT", vo_e(0, 337.38), 0), ("BE", vo_e(0, 337.48), 0), ("HIM?", vo_e(0, 337.58), 1)],
         end=th(568) - 0.30, emph=["HIM?"]),
    dict(style="luminol", words=[("HIM", s2e(131.92), 0), ("ALL", s2e(132.06), 0), ("ALONG", s2e(132.30), 1)], end=th(576), emph=[]),
    dict(style="casestamp", words=[("CASE CLOSED", th(628), 0)], end=th(632) - 0.05, emph=[]),
]
for _t in TEXT:   # every window must be non-empty and start on its word
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CLOSE_T = s2e(124.98)                      # the slide-box lid slams on "close"

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
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "VO at", [round(v[2], 2) for v in VO], "mute", [round(x, 2) for x in VOX_MUTE])
    for t_ in TEXT: print(f"  {t_['style']:9s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(w for w, _, _ in t_["words"]))
