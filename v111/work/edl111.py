"""MONSTER - Dexter x Kanye West "Monster" (voidfx v111, 9:16). Scaffolded from v110 SLEEPWALKER (--base v110).

Concept: I SHOOT THE LIGHTS OUT. The thing that lives in the dark. A flow of light: on Bon Iver's "I shoot the lights out"
the lights of the city behind him go out, a wave from the edges in, and he is left in the dark; he hides till it's
bright out (the sun comes up at the edge of the frame, the day burns white); the sun goes down and the garden lamps come on ("just another lonely
night"); we look up and a full moon is rising behind him, and the moon becomes the lamp over the kill table ("Are you
willing to sacrifice your life?"). THE PASSENGER (the drop): crouched against the wall in the light from below, his shadow
climbs the wall and grows into something else while the song builds; on "...I'm a monster" the shadow lunges over the lens
and inside it is the blood-soaked suit walking out into the daylight. "No-good bloodsucker": the slides. "Now look who's
in trouble": the crime-scene tape in the red and blue of a light bar. "As you run through my jungles": the woods, the
mangroves, the bamboo; "all you hear is rumbles": he raises the pistol at us and fires; the flash lands on frame 0 and
the lights are back on, for now (the loop).
Look: NIGHTSHADE (teal-navy shadows, warm practicals, the day golden; after the drop harder, the reds full).
Text: none (the owner's rule: start without).
Song: src/monster_pad.wav (src/monster.mp3 with 1.0 s of silence in front, so the edit can start 0.17 s before "I").
93.7 BPM: the drum stem, the snare and the full mix agree on a 0.640 s beat (the first map's 125 BPM was a 3:4 alias of
the kick pattern). Window h2->h90 (0.93 -> 29.10 s, 28.18 s): "I shoot the lights out" e0-e11, "Hide till it's bright
out" e13-e26, "Oh, just another lonely night" e29.5-e40, "Are you willing to sacrifice your life?" e45-e58, the build
e58-e65, the drop e65 (the bass, "...I'm a monster"), "no good bloodsucker" e68-e71, "Fat motherfucker" e71.6-e74,
"now look who's in trouble" e76-e79, "As you run through my jungles" e79.4-e83.5, "all you hear is rumbles" e84.4-e88.
Edit half-beat e = song half-beat - H0; bars every 8 e from e1 (the window starts half a beat before the bar).
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v111", "monster_dexter"
SONG = f"{ROOT}/src/monster_pad.wav"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 0.000
FPS, W, H = 60, 1080, 1920
SRC = {"s1": (f"{ROOT}/src/dexter_s1_hq.mp4", 60.0, 1280, 720), "s4": (f"{ROOT}/src/dexter_s4_hq.mp4", 60.0, 1280, 720),
       "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "dmx": (f"{ROOT}/src/dexter_mix_b.mp4", 60.0, 1280, 720),
       "ds2a": (f"{ROOT}/src/dexter_s2_a.mp4", 60.0, 1280, 720), "ds2b": (f"{ROOT}/src/dexter_s2_b.mp4", 60.0, 1280, 720)}
HB, HB_OFF = 0.320171, 0.2882             # 93.7 BPM (the drum stem agrees with the map)
H0, H1 = 2, 90
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 65; DROP_HB = HDROP; T_STOP = DUR   # the bass and "...I'm a monster" (song 21.74 s): THE PASSENGER
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 65, 4                      # the beat camera from the drop
E_LOOP = 85                                # the loop: he raises the pistol and fires; the flash lands on frame 0
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
VO = []
SET_PIECES = [("LIGHTS OUT", th(0), th(12)), ("DAYBREAK", th(22.5), th(29.5)), ("NIGHTFALL", th(32), th(37)),
              ("THE MOON", th(37), th(46.5)), ("THE PASSENGER", th(57), th(66.5)), ("THE SIREN", th(76.3), th(78.5)),
              ("THE SHOT (loop)", th(85), th(88))]
SIGNATURE = ["passenger111"]
HERO = ["moon_draw111"]                   # the light: the moon (it becomes the lamp that throws the shadow)
HERO_TINS = ["moon111", "passenger111"]         # the moon becomes the lamp; the lamp throws the shadow; the shot (the loop)
PLAN_ACCEPT = {}
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

SP = dict(look="night111")
# ---- LIGHTS OUT (e0-e11): "I shoot the lights out": the city's lights behind him go out, a wave from the edges in
shot("lights", "p1", 0, 11, 123.30, 124.40, z=[(0, 1.00), (1, 1.15)], interp="flow", seg=True, face=None, cx=(705, 725), **SP)   # frame 0: the marina at night, slowed (the shot's flash lands here)
# ---- HIDE (e11-e23): "Hide till it's bright out": in the dark, behind the door, behind the fence, waiting for the light
shot("dark", "ds2b", 11, 14, 323.40, 324.65, z=[(0, 1.00), (1, 1.04)], tin="emerge111", interp="flow", **SP)     # the light comes back first, from below
shot("door", "s4", 14, 17, 157.95, 158.95, z=[(0, 1.00), (1, 1.04)], tin="doorslide111", interp="flow", **SP)    # his face and its reflection (we pan past the door's edge)
shot("fence", "p1", 17, 20, 170.97, 171.78, z=[(0, 1.00), (1, 1.04)], tin="dolly", interp="flow", **SP)
shot("truck", "ds2a", 20, 23, 188.00, 189.00, z=[(0, 1.00), (1, 1.04)], tin="fence111", interp="flow", **SP)     # we push through the fence
# ---- DAYBREAK (e23-e29): "bright out": the sun comes up at the edge of the frame; the day burns white
shot("sunrise", "p1", 23, 26, 29.05, 30.15, z=[(0, 1.00), (1, 1.04)], tin="daybreak111", interp="flow", **SP)
shot("bright", "s1", 26, 29, 376.70, 377.66, z=[(0, 1.00), (1, 1.04)], tin="brightout111", interp="flow", **SP)
# ---- NIGHTFALL (e29-e45): "Oh, just another lonely night": the sun goes down, the garden lamps come on, the moon
shot("lake", "p1", 29, 33, 169.80, 170.90, z=[(0, 1.00), (1, 1.04)], tin="tear110", interp="flow", **SP)
shot("garden", "s4", 33, 37, 81.40, 82.70, z=[(0, 1.00), (1, 1.04)], tin="nightfall111", interp="flow", face=None, cx=(660, 670), ev=-0.9, **SP)   # night: the lamp behind him is the light   # the lights come on as the night comes down
shot("moon", "s4", 37, 45, 222.40, 224.95, z=[(0, 1.00), (1, 1.06)], tin="lookup111", interp="flow", seg=True, face=None, cx=(690, 790), **SP)   # we look up: THE MOON rises behind him
# ---- "Are you willing to sacrifice your life?" (e45-e57): the moon becomes the lamp over the kill table
shot("lamp", "p1", 45, 48, 133.98, 135.10, z=[(0, 1.06), (1, 1.00)], tin="moon111", interp="flow", **SP)
shot("table", "p1", 48, 51, 133.04, 133.90, z=[(0, 1.00), (1, 1.04)], tin="light_sweep108", interp="flow", **SP)
shot("gloves", "p1", 51, 54, 164.00, 165.00, z=[(0, 1.00), (1, 1.04)], tin="plasticroll110", interp="flow", **SP)
shot("scalpel", "p1", 54, 57, 180.00, 180.96, z=[(0, 1.00), (1, 1.04)], tin="underlight111", interp="flow", **SP)
# ---- THE PASSENGER (e57-e65): the build; his shadow climbs the wall and grows into something else
shot("passenger", "p1", 57, 65, 165.05, 166.55, z=[(0, 1.00), (1, 1.08)], tin="lightmatch111", interp="flow", seg=True, **SP)
# ---- MONSTER (e65-e88): the drop
shot("suit", "dmx", 65, 67, 94.90, 95.95, tmap=vel(65, 67, 94.90, 95.95), lin=True, interp="flow", tin="passenger111", **SP)   # "...I'm a monster"
shot("suitclose", "dmx", 67, 69, 96.80, 97.80, tmap=vel(67, 69, 96.80, 97.80), lin=True, interp="flow", tin="dolly", **SP)
shot("slides", "s1", 69, 71, 263.10, 263.95, tmap=vel(69, 71, 263.10, 263.95), lin=True, interp="flow", tin="slide111", **SP)   # "blood sucker": the slides
shot("goggles", "dmx", 71, 73, 106.10, 107.40, tmap=vel(71, 73, 106.10, 107.40), lin=True, interp="flow", tin="bleed111", **SP)   # the blood on the slide soaks out into the blood room
shot("grin", "s1", 73, 75, 346.60, 347.70, tmap=vel(73, 75, 346.60, 347.70), lin=True, interp="flow", **SP)   # a clean cut on the downbeat (the beat camera's punch)
shot("redface", "s1", 75, 77, 79.40, 80.60, tmap=vel(75, 77, 79.40, 80.60), lin=True, interp="flow", tin="flicker109", **SP)
shot("tape", "p7", 77, 79, 22.95, 23.70, tmap=vel(77, 79, 22.95, 23.70), lin=True, interp="hold", tin="siren111", hflip=True, **SP)   # "look who's in trouble" (the pack is mirrored: the tape reads backwards)
shot("axe", "s4", 79, 81, 136.60, 137.80, tmap=vel(79, 81, 136.60, 137.80), lin=True, interp="flow", tin="whip", **SP)
shot("mangrove", "s1", 81, 83, 174.70, 175.90, tmap=vel(81, 83, 174.70, 175.90), lin=True, interp="flow", tin="fronds108", **SP)
shot("bamboo", "ds2b", 83, 85, 370.20, 371.20, tmap=vel(83, 85, 370.20, 371.20), lin=True, interp="flow", tin="bokeh110", **SP)   # the sunlit leaves fall out of focus; his face comes into focus out of them
shot("aim", "ds2b", 85, 88, 372.45, 373.45, z=[(0, 1.00), (1, 1.05)], interp="flow", tin="dolly", tout="shot111", **SP)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
TEXT = []                                   # no text (the owner: start without)
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
