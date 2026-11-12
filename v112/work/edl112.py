"""FORGIVENESS - Dexter x Tame Impala "Posthumous Forgiveness" (voidfx v112, 9:16). Scaffolded from v111 MONSTER (--base v111).

Concept: WANNA TELL YOU 'BOUT THE TIME. The song is a son talking to his dead father; Dexter's is Harry, who gave him the
Code. Through the long held "Wanna tell you 'bout the time..." it is golden hour and memory: the port at sunset (frame 0),
his face in the sun, the funeral, the close dark of the kill room, and him at the grave by the lake, where the world
stretches away behind him in a slow dolly zoom (VERTIGO) as the song builds. On the drop the vertigo snaps forward and we
are in the life he would tell Harry about: sunlit Miami, the sunglasses going on (the glint), the grin, the mask that
fools everyone, the slides (all the times that he had), the kill room, the crime scenes. The loop is a camera move: an
orbit around him carries the last shot round into frame 0 at the port.
Look: GOLDEN HOUR (warm 70s film: amber highlights, lifted teal shadows, red halation, film grain, a soft chromatic edge;
night shots cooler). No text.
Song: src/posthumous.mp3 (6:06). Part two's groove: 83 BPM, half-beat 0.3615 s (the full mix and the snare agree; the drum
fit and the map disagreed with each other across the song's tempo change, so the grid was fitted on 309-329 s by hand).
Window h820->h888 (296.75 -> 321.33 s, 24.58 s): "Wanna tell you 'bout the time" from e1.7, held over the break (no bass),
the drop at e38 (310.5 s, the bass returns), "I was in Abbey Road" e44, "All the times that I had" e52, "...a fool" e60,
ending before "Thought of you". Edit half-beat e = song half-beat - H0.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v112", "posthumous_dexter"
SONG = f"{ROOT}/src/posthumous.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 287.786
FPS, W, H = 60, 1080, 1920
SRC = {"s1": (f"{ROOT}/src/dexter_s1_hq.mp4", 60.0, 1280, 720), "s4": (f"{ROOT}/src/dexter_s4_hq.mp4", 60.0, 1280, 720),
       "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "dmx": (f"{ROOT}/src/dexter_mix_b.mp4", 60.0, 1280, 720),
       "ds2a": (f"{ROOT}/src/dexter_s2_a.mp4", 60.0, 1280, 720), "ds2b": (f"{ROOT}/src/dexter_s2_b.mp4", 60.0, 1280, 720)}
HB, HB_OFF = 0.3615, 0.3190               # 83 BPM (part two's groove)
H0, H1 = 820, 888
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 38; DROP_HB = HDROP; T_STOP = DUR   # the bass returns (310.5 s): the vertigo snaps
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 38, 4
E_LOOP = 65                                # the loop: the orbit round him into frame 0
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
VO = []
SET_PIECES = [("SUN LEAK", th(3.5), th(6.5)), ("VERTIGO", th(30), th(40)), ("THE GLINT", th(44.2), th(46)), ("THE ORBIT (loop)", th(65), th(68))]
SIGNATURE = ["vertigo112"]
HERO = ["flare112"]                        # the golden light: the sun leak, the flares, the glint
HERO_TINS = ["leak112", "glint112"]
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

SP = dict(look="gold112")
# ---- "Wanna tell you 'bout the time" (e0-e38): golden hour and memory; the build to the drop
shot("port", "s1", 0, 5, 366.00, 367.75, z=[(0, 1.00), (1, 1.04)], interp="flow", seg=True, **SP)                  # frame 0: the port at sunset (the orbit lands here)
shot("profile", "s4", 5, 9, 196.80, 198.10, z=[(0, 1.00), (1, 1.04)], tin="leak112", interp="flow", **SP)           # his face in the sun
shot("funeral", "p1", 9, 13, 51.30, 52.45, z=[(0, 1.00), (1, 1.04)], tin="prism112", interp="flow", **SP)          # the casket
shot("redclose", "dmx", 13, 17, 394.00, 395.40, z=[(0, 1.00), (1, 1.03)], tin="emerge111", interp="flow", **SP)
shot("dusk", "s1", 17, 21, 379.95, 381.35, z=[(0, 1.00), (1, 1.04)], tin="lookup111", interp="flow", **SP)         # he looks up at the evening
shot("car", "dmx", 21, 25, 272.30, 273.70, z=[(0, 1.00), (1, 1.04)], tin="nightfall111", interp="flow", **SP)
shot("killroom", "ds2a", 25, 30, 233.90, 235.70, z=[(0, 1.00), (1, 1.04)], tin="plasticroll110", interp="flow", **SP)
shot("grave", "p1", 30, 38, 5.55, 8.40, interp="flow", tin="bokeh110", seg=True, **SP)                               # VERTIGO: the cemetery stretches away behind him
# ---- the drop (e38-e68): the life he would tell him about
shot("street", "s1", 38, 41, 209.40, 210.90, tmap=vel(38, 41, 209.40, 210.90), lin=True, interp="flow", tin="vertigo112", **SP)
shot("cap", "ds2b", 41, 43, 388.35, 389.55, tmap=vel(41, 43, 388.35, 389.55), lin=True, interp="flow", tin="whip", **SP)
shot("shades", "s1", 43, 46, 157.90, 159.80, z=[(0, 1.00), (1, 1.05)], interp="flow", tin="dolly", **SP)               # the sunglasses go on (the glint)
shot("grin", "dmx", 46, 48, 37.75, 39.00, tmap=vel(46, 48, 37.75, 39.00), lin=True, interp="flow", tin="glint112", **SP)
shot("smirk", "s4", 48, 50, 41.05, 41.95, tmap=vel(48, 50, 41.05, 41.95), lin=True, interp="flow", tin="whip", **SP)
shot("slides", "s1", 50, 52, 262.20, 263.00, tmap=vel(50, 52, 262.20, 263.00), lin=True, interp="flow", tin="slide111", **SP)   # "all the times that I had"
shot("kill", "p1", 52, 54, 135.40, 136.30, tmap=vel(52, 54, 135.40, 136.30), lin=True, interp="flow", tin="lightmatch111", **SP)
shot("warm", "s1", 54, 56, 307.30, 308.60, tmap=vel(54, 56, 307.30, 308.60), lin=True, interp="flow", tin="light_sweep108", **SP)
shot("crime", "s1", 56, 58, 58.00, 59.40, tmap=vel(56, 58, 58.00, 59.40), lin=True, interp="flow", tin="siren111", **SP)
shot("gloves", "s1", 58, 60, 64.97, 66.30, tmap=vel(58, 60, 64.97, 66.30), lin=True, interp="flow", tin="fronds108", **SP)   # "make everyone a fool"
shot("house", "s1", 60, 62, 169.00, 170.50, tmap=vel(60, 62, 169.00, 170.50), lin=True, interp="flow", tin="tear110", **SP)
shot("fire", "s1", 62, 65, 294.30, 295.90, z=[(0, 1.00), (1, 1.04)], interp="flow", tin="flicker109", **SP)
shot("last", "s4", 65, 68, 7.65, 9.20, z=[(0, 1.00), (1, 1.03)], interp="flow", tin="daybreak111", tout="orbit112", seg=True, **SP)   # the orbit carries him round into frame 0
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
TEXT = []                                   # no text
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
