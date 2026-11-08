"""WONDERWALL - The Flash x Oasis "Wonderwall" (voidfx v106, 9:16). Single source of truth: the renderer, audio builder and
QC read only this file. Scaffolded from the v11 BOP standard (made in the Dexter studio's range as a one-off Flash edit).

Concept: "Maybe you're gonna be the one that saves me." In the S3 finale Barry walks into the Speed Force to pay for
Flashpoint, and Iris watches him go; in the S4 premiere she is the one who brings him back ("Run, Barry, run"). So the
edit opens INSIDE the Speed Force (Barry in the blue mist looking back over his shoulder) on "I said maybe"; on "you're
gonna be the one" a lightning rod strikes and splits the frame onto Iris in tears; on "saves me" he tears out in gold.
The instrumental bar is the run (velocity ramps, the beat camera). On "and after all" THE WONDERWALL rises behind him:
a wall of glowing tiles, each a moment of the edit, with gold light in the mortar; it cracks on "you're my", and on
"WONDERWALL" the frame itself becomes the wall and bursts toward the camera as he strides out through it, the title
forged from its light. Relief (the smile); then he turns and walks back into the Speed Force, the mist rolls over the
lens and clears on frame 0: the loop is the story starting again ("I said maybe").
Look: WONDER - golden-hour amber light against Speed Force cobalt, milky lifted blacks, halation on the highlights.
Song: src/wonderwall.mp3 (Oasis, 4:19), 87.02 BPM (drum-stem fit; the auto map locked to 4/3 of it), half-beat
P = 0.34475 s, offset 0.2889. Window h456 -> h520 (bars 57-65, 157.50 -> 179.56 s, 8 bars, 22.06 s): the second
chorus, "I said maybe / you're gonna be the one that saves me / and after all / you're my wonderwall". Bar 65 is where
chorus 3 starts the same way in the song, so the loop is musically exact.
Lyrics (large-v3 on the Demucs vocal stem, checked on the stem's envelope: silent 154.75-158.45, "I said" 158.57):
  I 1.07  SAID 1.14  MAYBE 1.36 | YOU'RE 4.44  GONNA 5.54  BE 5.82  THE 6.26  ONE 6.42  THAT 6.72  SAVES 6.98  ME 7.52
  AND 11.04  AFTER 11.36  ALL 11.76 | YOU'RE 14.42  MY 16.40  WONDERWALL 16.64 (held to ~20.8)
Edit half-beat e = song half-beat - H0. Even e are beats.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v106", "wonderwall_flash"          # folder + output name: v106/out/wonderwall_flash_voidfx_9x16.mp4
SONG = f"{ROOT}/src/wonderwall.mp3"             # decoded to v106/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/wonderwall"   # Demucs stems of the song (vocals.wav / no_vocals.wav)
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height); fps from ffprobe. 24p content in a 60 fps container is de-duplicated;
# run `nohup python3 tools/sr_prep.py 106 &` after prep so every frame is restored and 2x upscaled.
SRC = {"fh": (f"{ROOT}/src/flash_all_hq.mp4", 60.0, 1280, 720),    # all seasons, 2.20 Mb/s (the sharpest Flash pack)
       "f3": (f"{ROOT}/src/flash_s3_30.mp4", 30.0, 1280, 720),     # S3 (the Speed Force, Iris)
       "f5": (f"{ROOT}/src/flash_s5_24.mp4", 23.976023976023978, 1280, 720),   # S5 (24p)
       "fz": (f"{ROOT}/src/flash_blitz.mp4", 60.0, 1280, 720)}     # Blitzkrieg pack

HB, HB_OFF = 0.34475, 0.2889               # half-beat period + offset (drum-stem fit around the window)
H0, H1 = 456, 520                          # bars 57 -> 65
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 24; DROP_HB = HDROP; T_STOP = DUR  # the run after 'saves me' (the velocity montage); the focal is E_WALL
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0   # optional sections (v10: freeze / run / loop); = end when unused
STUT_GAPS, STUT_HITS = [], []              # optional: half-beats where time freezes / jolts forward
E_BEAT, E_DIP = 6, 23                      # the beat camera starts after the cold open
E_WALL0, E_WALL = 32, 48                   # THE WONDERWALL: rises on 'and after all', bursts on 'WONDERWALL'
E_LOOP = 58                                # the loop: he walks back into the Speed Force (the beat camera rests)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []                                    # dialogue: (stem, src_in, src_out, edit_at); [] = music-only
SET_PIECES = [("lightning rod", th(13), th(15)), ("her tear", th(15), th(18)), ("saves me", th(20), th(22)), ("the wall rises", th(32), th(36)),
              ("WONDERWALL burst", th(47), th(51)), ("the loop", th(58), th(64))]
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

WD = dict(look="wonder")
# ---- "I said maybe": inside the Speed Force (frame 0 is the loop's landing)
shot("sf", "f3", 0, 6, 133.00, 134.20, z=[(0, 1.00), (1, 1.05)], interp="flow", seg=True, mist=1.0, **WD)
shot("eyes", "fh", 6, 10, 116.70, 118.20, z=[(0, 1.02), (1, 1.08)], tin="mist_swirl", seg=True, rays=0.5, interp="flow", **WD)
shot("run1", "f5", 10, 13, 113.00, 116.00, z=[(0, 1.00), (1, 1.06)], tin="strobe_echo", seg=True, face=None, cx=(700, 640),
     tmap=vel(10, 13, 113.00, 116.00), lin=True, interp="flow", **WD)
# ---- "you're gonna be the one": the lightning rod strikes onto Iris; on "GONNA" her tear falls toward the lens and holds
#      Barry's goodbye (the S3 farewell, the reverse shot); we fall through it onto him on "BE" (rev 3: slower, 1 s);
#      the clash into "saves me" moved one half-beat later, onto the sung "SAVES"
shot("iris", "f3", 13, 17, 130.90, 131.90, z=[(0, 1.00), (1, 1.04)], tin="lightning_rod", seg=True, interp="flow", dust=0.35, **WD)
shot("goodbye", "f3", 17, 20, 127.30, 128.35, z=[(0, 1.00), (1, 1.04)], tin="tear_lens", interp="flow", dust=0.3, **WD)
# ---- "that saves me": he tears out in gold
shot("saves", "fh", 20, 22, 127.70, 128.50, z=[(0, 1.04), (1, 1.00)], tin="clash106", seg=True, rays=0.6, interp="flow", **WD)
shot("runat2", "f5", 22, 24, 119.30, 121.30, z=[(0, 1.00), (1, 1.05)], tin="lightstreak", face=None, cx=(800, 760),
     tmap=vel(22, 24, 119.30, 121.30), lin=True, interp="flow", **WD)
# ---- the run (instrumental bar): velocity on every beat
shot("fly", "fh", 24, 27, 119.60, 122.80, z=[(0, 1.00), (1, 1.06)], tin="phase", face=None, cx=(560, 700), speed=0.6,
     tmap=vel(24, 27, 119.60, 122.80), lin=True, interp="flow", **WD)
shot("pov", "fz", 27, 29, 61.00, 63.45, z=[(0, 1.00), (1, 1.04)], tin="speedforce_in", face=None, cx=(640, 640),
     tmap=vel(27, 29, 61.00, 63.45, lo=0.5, hi=2.4), lin=True, interp="flow", **WD)
shot("runred", "f5", 29, 32, 108.50, 110.80, z=[(0, 1.00), (1, 1.06)], tin="bolt_trace", seg=True, face=None, cx=(470, 560),
     tmap=vel(29, 32, 108.50, 110.80), lin=True, interp="flow", **WD)
# ---- "and after all": THE WONDERWALL rises behind him
shot("lookup", "fh", 32, 35, 89.85, 90.95, z=[(0, 1.00), (1, 1.06)], tin="whirlwind", seg=True, wall=1, **WD)
shot("emblem", "fh", 35, 37, 129.40, 130.30, z=[(0, 1.04), (1, 1.00)], tin="emblem_flash", face=None, cx=(640, 640), interp="flow", **WD)
shot("city", "fz", 37, 39, 71.72, 72.28, z=[(0, 1.00), (1, 1.06)], interp="flow", tin="dolly", face=None, cx=(700, 760), **WD)
shot("wallrun", "fz", 39, 42, 74.40, 77.60, z=[(0, 1.00), (1, 1.05)], tin="lichtenberg", face=None, cx=(560, 700), speed=0.5,
     tmap=vel(39, 42, 74.40, 77.60), lin=True, interp="flow", **WD)
# ---- "you're my": arms open, the wall glows and cracks; the charge-up
shot("arms", "f5", 42, 45, 12.80, 14.20, z=[(0, 1.00), (1, 1.06)], tin="whip", seg=True, wall=2, interp="flow", **WD)
shot("eyes2", "f5", 45, 46, 106.80, 107.40, z=[(0, 1.02), (1, 1.06)], tin="strobe", seg=True, wall=2, **WD)
shot("charge", "fz", 46, 48, 47.90, 49.00, z=[(0, 1.00), (1, 1.05)], tin="perimeter", seg=True, wall=3, charge=1.0, **WD)
# ---- "WONDERWALL": the frame becomes the wall and bursts; he strides out through it
shot("through", "fh", 48, 54, 49.40, 51.20, z=[(0, 1.06), (1, 1.00)], tin="wonderwall", seg=True, rays=0.7, dust=0.5, interp="flow", **WD)
shot("smile", "fh", 54, 58, 6.80, 8.60, z=[(0, 1.00), (1, 1.05)], tin="light_leak", seg=True, dust=0.4, interp="flow", **WD)
# ---- the loop: he turns and walks back into the Speed Force; the mist rolls over the lens and clears on frame 0
#      (rev 2: from 134.50, after the source's pink lightning flicker at 134.37-134.47 that jumped twice)
shot("home", "f3", 58, 64, 134.50, 135.40, z=[(0, 1.00), (1, 1.04)], tin="mist_swirl", interp="flow", seg=True, mist=1.0, face=None,
     cx=(560, 520), tout="loop_mist", **WD)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
def sw(t): return s2e(t)
TEXT = [
    dict(style="cap", words=[("I", sw(158.57), 0), ("SAID", sw(158.64), 0), ("MAYBE", sw(158.86), 0)], end=th(6) - 0.06, emph=["MAYBE"]),
    dict(style="cap", words=[("YOU'RE", sw(161.94), 0), ("GONNA", sw(163.04), 0), ("BE", sw(163.32), 0), ("THE", sw(163.76), 1),
                             ("ONE", sw(163.92), 1), ("THAT", sw(164.22), 1), ("SAVES", sw(164.48), 1), ("ME", sw(165.02), 1)],
         end=sw(165.36) + 0.35, emph=["ONE", "SAVES"]),
    dict(style="cap", words=[("AND", sw(168.54), 0), ("AFTER", sw(168.86), 0), ("ALL", sw(169.26), 0)], end=sw(170.44) + 0.30, emph=["ALL"]),
    dict(style="cap", words=[("YOU'RE", sw(171.92), 0)], end=th(45) - 0.22, emph=[]),                  # paused over the eyes2 close-up
    dict(style="cap", words=[("YOU'RE", sw(171.92), 0), ("MY", sw(173.90), 0)], end=th(E_WALL) - 0.04, emph=[], **{"from": th(46)}),
    dict(style="wonder", words=[("WONDERWALL", sw(174.14), 0)], end=th(54) - 0.05, emph=["WONDERWALL"], band=(1450, 1615)),
]
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, E_LOOP)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3))
