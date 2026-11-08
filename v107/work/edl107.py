"""ALL CAPS - Dexter x Madvillain "All Caps" (voidfx v107, 9:16). Single source of truth: the renderer, audio builder and QC
read only this file. Scaffolded from the v12 BLOOM engine (v11 BOP + v12): the Dexter base (v105) has no restored-source
sampler, so this Dexter edit runs on the engine that does; it carries every v4-v9 Dexter transition (plastic rip, zipper,
redact, slidebox, m99 ...).

Concept: ALL CAPS. "Just remember ALL CAPS when you spell the man name." The press only knows him as the BAY HARBOR
BUTCHER; the song spells his name. The verse is his work (the kill table, the blood lab, the plastic, the con on Doakes,
Doakes in the cage); the newspaper spins in on "took a few minutes to convince" with his own photo under the BUTCHER
headline; on "ALL CAPS" a strip of newsprint slaps across the frame and the six words "when you spell the man name" stamp
D-E-X-T-E-R onto it in letterpress type, one sorts per word. The strip flies up into the sky and becomes the real banner
the plane tows over Miami: WE <3 DEXTER (the S1 finale fantasy). The beat break is the parade: he has got the masses.
The confetti thickens over the lens and clears on frame 0: "and he won't stop till he got the masses". Look: TABLOID
(newsprint cream highlights, ink blacks, slate blues, one spot red, a misregistered red plate, paper grain, a fine screen).
Song: src/all_caps.mp3 (Madvillain, 2:14), 87.50 BPM (drum-stem fit over 8 bars; the auto map read 175.6 and the drum
autocorrelation 117.4, the dotted pattern), kick on every beat from 22.5166 s. Window h176 -> h240 (8 bars, 60.92 ->
82.86 s, 21.94 s): the end of verse 1 and the beat break after it. The bass drops out in the last bar and comes back on
bar 1, so the loop lands like a drop.
Lyrics: Whisper large-v3 on the Demucs vocal stem, onsets snapped to the stem where strong (v107/work/onsets.json);
"bugaboo" is the published word (Whisper heard "boogaloo" twice).
Edit half-beat e = song half-beat - H0. Even e are beats; every line starts on the "and" before a bar line (e 8k - 0.5).
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v107", "all_caps_dexter"          # folder + output name: v107/out/all_caps_dexter_voidfx_9x16.mp4
SONG = f"{ROOT}/src/all_caps.mp3"             # decoded to v107/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/all_caps"   # Demucs stems of the song (vocals.wav / no_vocals.wav)
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height); fps from ffprobe. 24p content in a 60 fps container is de-duplicated;
# run `nohup python3 tools/sr_prep.py 107 &` after prep so every frame is restored and 2x upscaled.
SRC = {"ds2b": (f"{ROOT}/src/dexter_s2_b.mp4", 60.0, 1280, 720),   # S2 (2.07 Mb/s): the kill table, the lab, the shh, the night stare
       "ds2a": (f"{ROOT}/src/dexter_s2_a.mp4", 60.0, 1280, 720),   # S2 (1.98 Mb/s): Doakes in the cage
       "dmx": (f"{ROOT}/src/dexter_mix_b.mp4", 60.0, 1280, 720)}   # S1-S3 mix (1.72 Mb/s): the hazmat, the plastic, Doakes, the parade

HB, HB_OFF = 0.342857, 0.57375            # 87.50 BPM; the kick downbeat at 22.5166 s = h64
H0, H1 = 176, 240                          # 8 bars: 'and he won't stop' -> the end of the beat break
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 42; DROP_HB = HDROP; T_STOP = DUR  # 'ALL CAPS' (the focal set piece)
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0   # optional sections (v10: freeze / run / loop); = end when unused
STUT_GAPS, STUT_HITS = [], []              # optional: half-beats where time freezes / jolts forward
E_BEAT, E_DIP = 2, 40                      # the beat camera from the first beat after frame 0 (frame 0 stays clean)
E_LOOP = 58                                # the loop: the crowd's confetti spells his name, bursts, clears on frame 0
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []                                    # dialogue: (stem, src_in, src_out, edit_at); [] = music-only
SET_PIECES = [("hot molasses", th(13), th(15)), ("headspin", th(19), th(22)), ("the front page", th(24), th(29)),
              ("ALL CAPS", th(42), th(48)), ("the banner", th(48), th(50)), ("the masses spell his name", th(58), th(64))]
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

def robo(e0, e1, a, b, steps_per_half=2, snap=0.035):
    """the robot: the source moves in snaps on every sixteenth (a hold, then a 35 ms snap to the next pose)."""
    T = th(e1) - th(e0); n = int(round((e1 - e0) * steps_per_half)); dt = T / n; ks = [(0.0, a)]
    for i in range(n):
        u0 = (i * dt + dt - snap) / T; u1 = (i + 1) * dt / T
        ks.append((u0, a + (b - a) * i / n)); ks.append((u1, a + (b - a) * (i + 1) / n))
    return ks

TB = dict(look="tabloid")
# ---- "AND HE WON'T STOP TILL HE GOT THE MASSES" (frame 0 is the loop's landing)
shot("stare", "ds2b", 0, 4, 322.30, 323.20, z=[(0, 1.00), (1, 1.05)], interp="flow", seg=True, redthr=0.30, **TB)
shot("table", "ds2b", 4, 8, 156.40, 157.80, z=[(0, 1.02), (1, 1.07)], tin="plastic_rip", face=None, cx=(640, 640), interp="flow", **TB)
# ---- "AND SHOW 'EM WHAT THEY KNOW NOT THROUGH FLOWS OF HOT MOLASSES"
shot("shh", "ds2b", 8, 11, 346.40, 347.50, z=[(0, 1.02), (1, 1.07)], interp="flow", **TB)   # rev 4: a clean cut on the downbeat
shot("lab", "ds2b", 11, 14, 178.30, 179.40, z=[(0, 1.00), (1, 1.05)], tin="page_turn107", interp="flow", **TB)   # rev 4: the page turns (was the redaction boxes)
shot("hazmat", "dmx", 14, 17, 94.95, 95.95, z=[(0, 1.04), (1, 1.00)], tin="molasses", interp="flow", **TB)
# ---- "DO IT LIKE THE ROBOT TO HEADSPIN TO BOOGALOO"
shot("robot", "dmx", 17, 20, 191.50, 194.30, z=[(0, 1.00), (1, 1.06)], tin="impact", face=None, cx=(560, 620), robot=True,
     tmap=robo(17, 20, 191.50, 194.30), lin=True, interp="flow", **TB)
shot("pillow", "ds2a", 20, 22, 19.00, 19.80, z=[(0, 1.00), (1, 1.04)], tin="headspin", interp="flow", **TB)
shot("grin", "dmx", 22, 28, 75.50, 76.80, z=[(0, 1.00), (1, 1.00)], tin="whip", interp="flow", **TB)
# ---- "TOOK A FEW MINUTES TO CONVINCE THE AVERAGE BUGABOO": the front page spins in; we dive into his photo under the headline
shot("con", "ds2b", 28, 30, 244.00, 244.80, z=[(0, 1.00), (1, 1.04)], tin="frontpage", interp="flow", **TB)
shot("doakes", "dmx", 30, 32, 11.00, 11.80, z=[(0, 1.02), (1, 1.06)], tin="whip", interp="flow", **TB)
# ---- "IT'S UGLY LIKE LOOK AT YOU, IT'S A DAMN SHAME": Doakes in the cage
shot("cage", "ds2a", 32, 35, 226.60, 228.00, z=[(0, 1.00), (1, 1.05)], tin="slam", interp="flow", **TB)
shot("lookat", "ds2a", 35, 37, 224.20, 224.90, z=[(0, 1.02), (1, 1.06)], tin="whip", interp="flow", **TB)
shot("shame", "ds2b", 37, 40, 161.50, 162.60, z=[(0, 1.00), (1, 1.04)], tin="zipper", interp="flow", **TB)
# ---- "JUST REMEMBER ALL CAPS WHEN YOU SPELL THE MAN NAME": the strip of newsprint, D-E-X-T-E-R stamped one letter a word
shot("remember", "ds2b", 40, 42, 296.00, 296.80, z=[(0, 1.00), (1, 1.05)], tin="impact", interp="flow", **TB)
shot("parade", "dmx", 42, 48, 327.30, 328.90, z=[(0, 1.00), (1, 1.04)], tin="slam", face=None, cx=(640, 600), interp="flow", stamp=True, redthr=0.30, **TB)
# ---- the beat break: the strip flies up and becomes the banner the plane tows; the parade; he has got the masses
shot("banner", "dmx", 48, 51, 326.05, 326.68, tin="banner_match", face=None, banner=True, interp="flow", **TB)
shot("laugh", "dmx", 51, 54, 343.10, 344.70, z=[(0, 1.00), (1, 1.04)], tin="confetti_pop", interp="flow", seg=True, pop=True, redthr=0.30, **TB)
shot("crowd", "dmx", 54, 56, 337.60, 338.40, z=[(0, 1.00), (1, 1.04)], tin="dolly", face=None, cx=(620, 620), interp="flow", **TB)
shot("walk", "dmx", 56, 64, 331.90, 334.10, z=[(0, 1.00), (1, 1.06)], tin="smear", interp="flow", redthr=0.30, tout="name_loop", **TB)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
TEXT = [
    dict(style="cap", words=[("AND", 0.06, 0), ("HE", 0.64, 0), ("WON'T", 0.79, 0), ("STOP", 1.15, 0), ("TILL", 1.28, 1), ("HE", 1.55, 1),
                             ("GOT", 1.76, 1), ("THE", 1.94, 1), ("MASSES", 2.11, 1)], end=2.55, emph=["MASSES"]),
    dict(style="cap", words=[("AND", 2.62, 0), ("SHOW", 2.99, 0), ("'EM", 3.17, 0), ("WHAT", 3.32, 1), ("THEY", 3.48, 1), ("KNOW", 3.62, 1),
                             ("NOT", 3.74, 1)], end=3.92, emph=["NOT"]),
    dict(style="cap", words=[("THROUGH", 3.95, 0), ("FLOWS", 4.18, 0), ("OF", 4.39, 1), ("HOT", 4.61, 1), ("MOLASSES", 4.73, 1)], end=5.36, emph=["MOLASSES"]),
    dict(style="cap", words=[("DO", 5.41, 0), ("IT", 5.76, 0), ("LIKE", 6.02, 0), ("THE", 6.14, 0), ("ROBOT", 6.25, 0), ("TO", 6.63, 1),
                             ("HEADSPIN", 6.88, 1), ("TO", 7.32, 1), ("BOOGALOO", 7.55, 1)], end=th(24) - 0.06, emph=["ROBOT", "HEADSPIN"]),
    dict(style="cap", words=[("TOOK", 8.05, 0), ("A", 8.47, 0), ("FEW", 8.64, 0), ("MINUTES", 8.87, 0), ("TO", 9.23, 1), ("CONVINCE", 9.44, 1)],
         end=9.78, emph=["CONVINCE"], **{"from": th(28)}),
    dict(style="cap", words=[("THE", 9.81, 0), ("AVERAGE", 10.01, 0), ("BUGABOO", 10.30, 1)], end=10.84, emph=["BUGABOO"]),
    dict(style="cap", words=[("IT'S", 10.87, 0), ("UGLY", 11.43, 0), ("LIKE", 11.81, 1), ("LOOK", 12.15, 1), ("AT", 12.32, 1), ("YOU", 12.40, 1)],
         end=12.64, emph=["UGLY"]),
    dict(style="cap", words=[("IT'S", 12.67, 0), ("A", 12.92, 0), ("DAMN", 12.96, 1), ("SHAME", 13.09, 1)], end=13.46, emph=["SHAME"]),
    dict(style="cap", words=[("JUST", 13.49, 0), ("REMEMBER", 14.01, 0), ("ALL", 14.36, 1), ("CAPS", 14.76, 1)], end=15.00, emph=["ALL", "CAPS"],
         ys=(1452, 1568), band=(1382, 1638)),                                            # lower: his face fills "remember"
    dict(style="cap", words=[("WHEN", 15.03, 0), ("YOU", 15.36, 0), ("SPELL", 15.60, 0), ("THE", 15.86, 1), ("MAN", 16.08, 1), ("NAME", 16.27, 1)],
         end=th(48) - 0.05, emph=["NAME"]),
    dict(style="stamp", words=[(c, th(44 + 0.5 * i), 0) for i, c in enumerate("DEXTER")],   # rev 3: an even 16th grid (e44-46.5), each letter lands on its hit
         sung=["WHEN", "YOU", "SPELL", "THE", "MAN", "NAME"], end=th(48) + 0.02, band=(745, 1000)),
]
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (2, E_LOOP)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3))
