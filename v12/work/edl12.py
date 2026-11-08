"""BLOOM (voidfx v12, 9:16). Single source of truth: the renderer, audio builder and QC read only this file.
Scaffolded from the v11 BOP standard (rev 4; v10 LET IT HAPPEN structure). Keep the structure; replace the look, the
shots and the text. v11 reference: v11/work/edl11.py (a concept taken from the song's own words, a rival in a second
grade, two designed titles, a focal set piece, beat moments, a loop that lands exactly on frame 0).

Concept: LIGHTNING BLOOM. "Night blooming" = the night Barry was struck by lightning: lightning leaves Lichtenberg
figures, "lightning flowers". The hero asset is a five-petal LIGHTNING JASMINE (petal edges and veins of live lightning,
a pale-yellow glowing heart) that runs bud -> bloom -> full bloom -> closing through the edit.
  Act 1, the night (instrumental, e0-e32): the storm sky (NIGHT grows out of lightning branches) -> the bolt strikes Barry
  (S1 lab) -> he wakes in S.T.A.R. Labs -> first sparks -> the suit in blue cortex light -> lightning fills his iris.
  THE BLOOM (e32, the vocal enters): the flower opens out of his iris, BLOOM blooms open; the speed montage (velocity
  ramps, beat camera, a beat animation on every shot). FULL BLOOM (e64, the claps enter; the focal set piece): a giant
  lightning jasmine unfolds behind him (matte, light wrap), its petals sweep past the camera. The loop: the flower closes
  into a bud at his emblem, the camera dives into it, and inside the bud is the storm sky of frame 0.
Song window: fakemink "Night Blooming Jasmine", bars 8-18 = song 18.71-42.05 s (10 bars, 23.35 s): bars 8-11 the
instrumental groove, bar 12 (28.05 s) the vocal enters and the hats fall away (the drop), bar 16 (37.39 s) the claps enter.
The last vocal line (starts 41.02 s) is muted on the stems so the instrumental runs into the loop on the bar grid.
Lyrics: Whisper word times, then every word checked against its sung onset on the Demucs vocal stem (toolkit pitfall 14).
Edit half-beat e = song half-beat - H0. Even e are beats.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v12", "bloom_flash"          # folder + output name: v12/out/bloom_flash_voidfx_9x16.mp4
SONG = f"{ROOT}/src/night_blooming_jasmine.mp3"             # decoded to v12/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 14.0   # stems of song 14-50 s   # Demucs stems of the song (vocals.wav / no_vocals.wav)
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height); fps from ffprobe. 24p content in a 60 fps container is de-duplicated;
# run `nohup python3 tools/sr_prep.py 12 &` after prep so every frame is restored and 2x upscaled.
SRC = {"fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720), "fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720),
       "fs2t": (f"{ROOT}/src/flash_s2_topaz.mp4", 30.0, 1280, 720), "fs3": (f"{ROOT}/src/flash_s3.mp4", 30.0, 1280, 720),
       "fs5": (f"{ROOT}/src/flash_s5.mp4", 24000 / 1001, 1280, 720), "fbk": (f"{ROOT}/src/flash_blitzkrieg.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.29184580498866214, 0.029184580498866214   # 102.79 BPM (v9/work/song_map.json: P, off)
H0, H1 = 64, 144                           # bars 8-18: song 18.71-42.05 s
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 32; DROP_HB = HDROP; T_STOP = DUR  # the drop (edit half-beat): the biggest set piece lands here
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0   # optional sections (v10: freeze / run / loop); = end when unused
STUT_GAPS, STUT_HITS = [], []              # optional: half-beats where time freezes / jolts forward
E_BEAT, E_DIP = 0, HDROP - 4               # v11 engine: where the beat drops in, the dip before the drop
E_LOOP = H1 - H0 - 5                       # v11 engine: where the loop set piece starts (the beat camera rests from here)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []                                    # dialogue: (stem, src_in, src_out, edit_at); [] = music-only
VO_STEM = None; VO_STEM_T0 = 0.0

def vel(e0, e1, a, b, lo=0.30, hi=3.2, tau=0.07, n=96):
    """the v10 rev 5 velocity: a speed burst on every beat of the shot (the cut included), smooth slow motion between
    beats; the same source range a..b, so the speeds scale to fit. Use with lin=True, interp="flow"."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); sp = _np.full_like(ts, lo)
    for e in range(e0, e1):
        if e % 2 == 0:
            tb = th(e) - th(e0); sp = sp + (hi - lo) * _np.exp(-_np.clip(ts - tb, 0, None) / tau) * (ts >= tb)
    src = _np.concatenate([[0.0], _np.cumsum((sp[1:] + sp[:-1]) / 2 * _np.diff(ts))]); src /= src[-1]
    return [(float(u), float(a + (b - a) * _np.interp(u * T, ts, src))) for u in _np.linspace(0, 1, n)]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot.
    v10 set pieces: emblem_gate (emblem=[(src t, x, y)...], emblem_r) phase whirlwind lichtenberg lens_shatter perimeter
      time_particles (pfocus=(x, y)) slices ignite shock ramp logo_orig bolt_strike freeze_in restart; the loop:
      the last shot graphic="tunnel" + the first shot tin="tunnel_in" (T_OPEN / TUN_PANELS in the renderer).
    Older (v4-v9): tape_in eye_dive assemble polaroid facematch tear crt cube sun filmstrip peel ink slash logo burn lens
      shadow tv_off slidebox plastic zipper mirror_in tilt foliage petals bloom strobe beam blinds roll smear shutter ...
    Motion (rev 5 standard): tmap=vel(e0, e1, a, b), lin=True, interp="flow" on every hook shot; the beat camera is
      automatic (beat_bounce / shake / beat_fx); frozen=True + a tmap with flat holds gets the bullet-time glide.
    v11 pieces: red_phase red_link red_streak red_slices red_eye_dive dolly bolt_split whip strobe_echo bolt_trace
      heat_haze clash rift speedforce_in emblem_flash; look="voltage"|"rival"; the REVERSE loop (reverse_loop + loop_in).
    Graphics: seg=True (MODNet matte) arcs= wind= orbit= sparks= trails= rays= wave=True streak_e= ember= fire= dust=
      speed= red_arcs= aura= remnants= charge= warp=
    Framing: z=[(u, zoom)...] face="largest"|None (+cx=(x0, x1)); look= your own grade."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "prism"),
             z=kw.pop("z", [(0, 1.00), (1, 1.07)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- ACT 1, THE NIGHT (instrumental groove, e0-e32)
shot("sky", "fs5", 0, 6, 105.12, 106.58, tin="loop_in", face=None, cx=(700, 700), z=[(0, 1.00), (1, 1.06)])
shot("strike", "fbh", 6, 12, 10.32, 12.06, tin="strike_link", seg=True, tame=1.0)
shot("wake", "fs1", 12, 15, 4.45, 4.98, tin="ecg_bolt", interp="flow", lin=True)
shot("spark", "fbk", 15, 20, 133.20, 134.20, tin="bolt_trace", seg=True, interp="flow", lin=True)
shot("cortex", "fs2t", 20, 27, 28.90, 31.30, tin="bud_iris", seg=True)
shot("eye", "fs1", 27, 32, 291.90, 292.85, tin="dolly", face=None, cx=(343, 343), z=[(0, 1.00), (1, 1.10)], interp="flow", lin=True)
# ---- THE BLOOM (e32, the vocal enters) and the speed montage (e32-e64): velocity ramps + a beat animation per shot
shot("bloomrun", "fbk", 32, 36, 60.70, 63.40, tin="bloom", face=None, cx=(640, 640), tmap=vel(32, 36, 60.70, 63.40), lin=True, interp="flow")
shot("blue", "fbk", 36, 40, 124.75, 126.20, tin="petal_whip", seg=True, pollen=1.0, tmap=vel(36, 40, 124.75, 126.20), lin=True, interp="flow")
shot("street", "fs5", 40, 44, 72.00, 74.60, tin="lichtenberg", seg=True, stars=1.0, tmap=vel(40, 44, 72.00, 74.60), lin=True, interp="flow")
shot("crouch", "fs5", 44, 48, 108.60, 110.90, tin="strobe_echo", seg=True, tmap=vel(44, 48, 108.60, 110.90), lin=True, interp="flow")
shot("hood", "fbk", 48, 52, 23.95, 25.78, tin="slices", seg=True, echo=1.0, tmap=vel(48, 52, 23.95, 25.78), lin=True, interp="flow")
shot("charge", "fs5", 52, 56, 180.00, 182.60, tin="clash", seg=True, bud=1.0, tmap=vel(52, 56, 180.00, 182.60), lin=True, interp="flow")
shot("s3night", "fs3", 56, 60, 59.10, 61.50, tin="heat_haze", seg=True, ring=1.0, tmap=vel(56, 60, 59.10, 61.50), lin=True, interp="flow")
shot("dash", "fbk", 60, 64, 20.00, 21.85, tin="whip", face=None, cx=(838, 838), tmap=vel(60, 64, 20.00, 21.85), lin=True, interp="flow")
# ---- FULL BLOOM (e64, the claps enter; the focal set piece) and the loop
shot("full", "fbk", 64, 70, 136.02, 138.20, tin="full_bloom", seg=True)
shot("s3mask", "fs3", 70, 74, 106.80, 108.45, tin="petal_pass", seg=True, tmap=vel(70, 74, 106.80, 108.45), lin=True, interp="flow")
shot("last", "fbh", 74, 80, 109.70, 112.40, tin="pollen_burst", seg=True)
SET_PIECES = [("bloom", th(31), th(36)), ("full_bloom", th(63), th(70)), ("close_dive", th(76), th(80))]
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
TEXT = []
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, H1 - H0 - 12)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3))
