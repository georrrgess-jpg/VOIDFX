"""DOOMSDAY - Dexter x MF DOOM "Doomsday" (feat. Pebbles the Invisible Girl) (voidfx v108, 9:16). Single source of truth:
the renderer, audio builder and QC read only this file. Scaffolded from v107 ALL CAPS (the v12 engine + the v107 toolkit).

Concept: UNDER THE SURFACE / BORN IN BLOOD. The hook is DOOM's: "On Doomsday, ever since the womb, till I'm back where my
brother went, that's what my tomb say". In Dexter's history it is literal: he was born in blood in a shipping container
(the womb), and the S1 finale takes him back to his brother Brian's table, wrapped in plastic. The first bar is the mask
(warm Miami, the smile); on "stay in the zone" kill-room plastic stretches over the calm picture and peels away to the
darker Dexter underneath (SURFACE, the owner's concept); the beat drops out under "turn H2O to cognac" while he holds a
blood slide to the light, and on "DOOMSDAY" the slide crosses his face, magnifies his eye, and the next shot appears inside
the glass before it fills the screen (SPECIMEN, the owner's concept, the signature). The hook: the container ("ever since
the womb"), frost creeps over the lens for the Ice Truck Killer and thaws on him strapped to Brian's table ("back where my
brother went"), the tomb, the bags at sea ("unmarked or engraved"), the body-bag zipper on "go get bagged". The loop: one
blood drop falls toward the lens as he looks up; frame 0's smile is inside it, and it fills the frame (the slide's drop
is the hero object: a motif twice, SPECIMEN and the loop). No text anywhere (the owner's brief for this edit).
Look: two grades split by the peel. SURFACE (shots 1-3): warm, bleached pastel Miami. UNDER (from the peel): cold steel
and teal, deep blacks, only blood red survives.
Song: src/doomsday.mp3 (MF DOOM, 4:58), 95.39 BPM (drum-stem fit agrees with the map), window h208 -> h280 (9 bars,
65.643 -> 88.286 s, 22.64 s; loop wrap 0.956 on the music stem). The drums drop out under "turn H2O to cognac"
(e18-e22) and slam back on "DOOMSDAY" (e22).
Lyrics (Whisper large-v3 on the vocal stem, edit half-beats): watch@3.6 ... alone@9.8 black@11.1 | stay@11.8 zone@14.1
turn H2O to cognac@15.3-18.7 | on@20.4 DOOMSDAY@22.1 ever since the womb@24.6-26.9 | till I'm back where my brother
went@27.8-31.4 | that's what my tomb say@32.2-35.3 | right above my government@37.9-40.8 Dumile name@42.5-43.3 | either
unmarked@44.2 or engraved@47.6 hey who's to say@49.3-51.0 | I wrote this one in@52.3 B-C-D-C-O section@55.2-58.1 | if you
don't believe me@59.2-63.0 go get bagged@63.9-65.2 and checked in@66.5-67.4 | cell number@68.3.
Edit half-beat e = song half-beat - H0. Even e are beats; bars every 8 e.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v108", "doomsday"          # folder + output name: v108/out/doomsday_voidfx_9x16.mp4
SONG = f"{ROOT}/src/doomsday.mp3"             # decoded to v108/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 57.634   # Demucs htdemucs (drums / bass / other / vocals) of 57.63-96.28 s
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height). 24p content in a 60 fps container is de-duplicated; sr_prep restores every frame.
SRC = {"s1": (f"{ROOT}/src/dexter_s1_hq.mp4", 60.0, 1280, 720),    # S1 (2.00 Mb/s, the sharpest Dexter pack; pack8_s1 timing)
       "s4": (f"{ROOT}/src/dexter_s4_hq.mp4", 60.0, 1280, 720),    # S4 (1.80 Mb/s; pack9_s4_best timing)
       "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720),        # 2.10 Mb/s: Miami Metro, the badge
       "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720)}  # 1.7 Mb/s: the boat with the trash bags

HB, HB_OFF = 0.314488, 0.2291             # 95.39 BPM (the drum-stem fit agrees with the map)
H0, H1 = 208, 280                          # 9 bars: "...save me the trouble, yo" -> "...checked in / cell number"
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 22; DROP_HB = HDROP; T_STOP = DUR  # "DOOMSDAY": the beat slams back; SPECIMEN
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0   # optional sections (v10: freeze / run / loop); = end when unused
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 2, 18                      # the beat camera from the first beat after frame 0; the drums drop out e18-e22
E_LOOP = 68                                # the loop: the last drop falls toward the lens with frame 0 inside it
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []                                    # music only
SET_PIECES = [("SURFACE", th(10.5), th(14)), ("SPECIMEN", th(21), th(23.5)), ("the ice truck", th(26.5), th(29.5)),
              ("the last drop", th(68.5), th(72))]
SIGNATURE = ["specimen"]                    # the owner's concept: the slide crosses his face, the next shot inside the glass
HERO = ["blood_drop108"]                    # the drop of blood: the loop (SPECIMEN now uses the real slide)
HERO_TINS = []
PLAN_ACCEPT = {"sig_time:specimen": "the owner specified SPECIMEN at 0.3-0.5 s; the real slide is on screen in his hands for 1.26 s before it"}
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

SU = dict(look="surface108")                # the mask: warm, bleached pastel Miami
UN = dict(look="under108")                  # under the surface: cold steel and teal, only blood red survives
def V(e0, e1, a, b): return dict(tmap=vel(e0, e1, a, b, lo=0.55, hi=1.9), lin=True, interp="flow")
# ---- "...SAVE ME THE TROUBLE, YO / WATCH YOUR OWN BACK, CAME IN AND GO OUT ALONE, BLACK": the mask (frame 0 is the loop's landing)
shot("mask", "s1", 0, 3, 406.00, 407.10, z=[(0, 1.00), (1, 1.04)], interp="flow", **SU)   # the sunset smile
shot("palms", "s1", 3, 6, 65.00, 66.10, z=[(0, 1.02), (1, 1.06)], tin="light_sweep108", interp="flow", **SU)
shot("day2", "s1", 6, 9, 168.00, 169.00, z=[(0, 1.00), (1, 1.04)], tin="fronds108", interp="flow", **SU)     # rev 2: palm fronds sweep across the lens (was the heat haze)
shot("tension", "s4", 9, 12, 7.70, 8.70, z=[(0, 1.00), (1, 1.05)], tin="dolly", interp="flow", **SU)   # rev 1b: a calm day shot from another scene
# ---- "STAY IN THE ZONE": SURFACE, the plastic stretches over the calm picture and peels away to the darker Dexter
shot("release", "s4", 12, 16, 117.50, 118.90, z=[(0, 1.06), (1, 1.00)], tin="surface", interp="flow", **UN)
# ---- "TURN H2O TO COGNAC": the drums drop out; the water turns (diffusion); the M99 (double vision); the slide to the light
shot("syringe", "s1", 16, 18, 142.40, 143.20, z=[(0, 1.00), (1, 1.04)], tin="diffusion108", interp="flow", **UN)   # the M99
shot("enter", "s1", 18, 22, 262.40, 263.80, z=[(0, 1.00), (1, 1.06)], tin="double108", interp="flow", **UN)
# ---- "ON DOOMSDAY": SPECIMEN, the real slide lifts from his hands, crosses his eye, the next shot inside it, fills the lens
shot("reveal", "s1", 22, 25, 152.20, 153.20, z=[(0, 1.04), (1, 1.00)], tin="specimen", interp="flow", **UN)
# ---- "EVER SINCE THE WOMB": the shipping container he was born in
shot("womb", "s1", 25, 28, 371.60, 372.70, z=[(0, 1.06), (1, 1.10)], tin="molasses108", interp="flow", **UN)
# ---- "TILL I'M BACK WHERE MY BROTHER WENT": frost creeps over the lens (the Ice Truck Killer), thaws on Brian's table
shot("brother", "s1", 28, 32, 390.45, 391.95, z=[(0, 1.00), (1, 1.04)], tin="frost108", interp="flow", **UN)
# ---- "THAT'S WHAT MY TOMB SAY": lying face up
shot("tomb", "s4", 32, 36, 124.50, 125.90, z=[(0, 1.00), (1, 1.05)], tin="roll", interp="flow", **UN)
# ---- "RIGHT ABOVE MY GOVERNMENT, DUMILE NAME": Miami Metro, the badge; luminol onto the grin; the car
shot("badge", "p7", 36, 40, 14.60, 16.10, z=[(0, 1.00), (1, 1.04)], tin="polaroid", interp="flow", **UN)
shot("name", "s4", 40, 42, 46.95, 47.65, z=[(0, 1.00), (1, 1.04)], tin="luminol108", interp="flow", redthr=0.20, **UN)
shot("car", "s4", 42, 44, 88.20, 88.90, z=[(0, 1.00), (1, 1.04)], tin="whip", interp="flow", redthr=0.20, **UN)
# ---- "EITHER UNMARKED OR ENGRAVED": into the woods with the axe
shot("unmarked", "s4", 44, 48, 136.80, 138.20, z=[(0, 1.00), (1, 1.05)], tin="dolly", interp="flow", **UN)   # rev 2: a smooth push (no rain on the lens); the woods with the axe (the Trinity hike): an unmarked grave
# ---- "HEY, WHO'S TO SAY?": his face becomes the smirk at the lens
shot("whos", "s1", 48, 52, 283.32, 284.45, z=[(0, 1.00), (1, 1.03)], tin="facematch108", interp="flow", **UN)
# ---- "I WROTE THIS ONE IN B-C-D-C-O SECTION": the darkroom develops the red desk; the slide; the light table
shot("wrote", "s1", 52, 55, 78.20, 79.30, z=[(0, 1.00), (1, 1.05)], tin="developer108", interp="flow", **UN)
shot("slides2", "s1", 55, 57, 45.60, 46.30, z=[(0, 1.00), (1, 1.04)], tin="whip", interp="flow", **UN)
shot("section", "s4", 57, 59, 145.82, 146.50, z=[(0, 1.00), (1, 1.04)], tin="slam", face=None, cx=(640, 640), interp="blend", **UN)
# ---- "IF YOU DON'T BELIEVE ME, GO GET BAGGED AND CHECKED IN": the night drive; the wiper onto the bags; under the surface
shot("believe", "s1", 59, 64, 316.00, 317.70, z=[(0, 1.00), (1, 1.05)], tin="smear", interp="flow", redthr=0.30, **UN)
shot("bagged", "p5", 64, 68, 51.75, 53.30, z=[(0, 1.00), (1, 1.04)], tin="wiper108", interp="flow", **UN)
# ---- the loop: under the surface; he looks up; the last drop falls toward the lens with frame 0 inside it
shot("lookup", "s4", 68, 72, 230.75, 232.15, z=[(0, 1.00), (1, 1.03)], tin="sink108", interp="flow", tout="last_drop", **UN)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
TEXT = []                                   # no text anywhere (the owner's brief for this edit)
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
