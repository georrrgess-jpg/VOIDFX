"""SLEEPWALKER - Dexter x "Sleepwalker (Slowed)" (voidfx v110, 9:16). Scaffolded from v109 PHANTOM (--base v109).

Concept: SLEEPWALKER. His waking life is a sleepwalk, and the nightmare that made him loops forever. He lies awake (frame
0), walks through the night half asleep, looks up into a failing light on "I'm losing power" while the song loses its bass,
falls asleep in the fog; on the drop the power surges back and we dive through the spinning fan into the kill room (the
Dark Passenger awake). The hunt. On the child's "Mommy?" he is in the blood room (the S1 hotel room drenched in blood,
the memory of his mother's murder); the loop falls from there straight down into frame 0: he wakes in bed.
Look: 3 A.M. (sodium amber highlights, navy shadows, a dream bloom and soft edges; blood stays red).
Text: one designed title on the sung words, I'M LOSING POWER, flickering like a failing tube.
Song: src/sleepwalker_slowed.mp3, 98.6 BPM (the drum stem agrees), window h162->h241 (49.39 -> 73.43 s, 24.04 s) from the
owner's "roughly the 49-second mark": "I'm losing power" e10.2-e16.3, the bass drops out e~15-e29, the drop e30 (58.5 s),
"Mommy?" e72.3 and e77.4. Edit half-beat e = song half-beat - H0; even e are beats, bars every 8 e.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v110", "sleepwalker_dexter"
SONG = f"{ROOT}/src/sleepwalker_slowed.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 41.384
FPS, W, H = 60, 1080, 1920
SRC = {"s1": (f"{ROOT}/src/dexter_s1_hq.mp4", 60.0, 1280, 720), "s4": (f"{ROOT}/src/dexter_s4_hq.mp4", 60.0, 1280, 720),
       "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "dmx": (f"{ROOT}/src/dexter_mix_b.mp4", 60.0, 1280, 720),
       "ds2a": (f"{ROOT}/src/dexter_s2_a.mp4", 60.0, 1280, 720), "ds2b": (f"{ROOT}/src/dexter_s2_b.mp4", 60.0, 1280, 720)}
HB, HB_OFF = 0.304274, 0.0988            # 98.6 BPM (the drum stem agrees with the map)
H0, H1 = 162, 241
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 30; DROP_HB = HDROP; T_STOP = DUR   # the bass returns (58.5 s): the power surges back, through the fan
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 30, 4                      # the beat camera from the drop
E_LOOP = 75                                # the loop: from the blood room we fall into bed (frame 0)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
VO = []
SET_PIECES = [("POWER FAILURE", th(10), th(21)), ("THROUGH THE FAN", th(24), th(31)), ("THE BARREL", th(43.5), th(47)),
              ("THE SWINGING LIGHT", th(65), th(70)), ("THE DRIP (loop)", th(74.6), th(79))]
SIGNATURE = ["fan110"]
HERO = ["power_light110"]                  # the failing / surging light: the title, the brownout, the fan
HERO_TINS = ["lightson110", "brownout110", "fan110"]
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

SP = dict(look="sleep110")
# ---- the sleepwalk (e0-e10): he lies awake; he walks through the night half asleep
shot("bed", "ds2a", 0, 3, 20.40, 21.30, z=[(0, 1.00), (1, 1.03)], interp="flow", seg=True, **SP)             # frame 0: awake, staring up
shot("yard", "dmx", 3, 6, 254.20, 255.20, z=[(0, 1.00), (1, 1.03)], tin="dolly", interp="flow", **SP)
shot("marina", "p1", 6, 8, 123.20, 124.00, z=[(0, 1.00), (1, 1.03)], tin="whip", interp="flow", **SP)
shot("doorway", "ds2b", 8, 10, 393.10, 393.80, z=[(0, 1.00), (1, 1.03)], tin="bokeh110", interp="flow", **SP)
# ---- POWER FAILURE (e10-e21): "I'm losing power"; the light above him fails, the bass goes
shot("light", "p1", 10, 17, 147.00, 148.20, z=[(0, 1.00), (1, 1.04)], tin="lightson110", interp="flow", **SP)   # the tube blinks on with "I'm"; the title
shot("fog", "ds2b", 17, 21, 140.30, 141.70, z=[(0, 1.02), (1, 1.00)], tin="brownout110", interp="flow", **SP)
shot("asleep", "s4", 21, 24, 143.60, 144.90, z=[(0, 1.00), (1, 1.04)], tin="fogwipe110", interp="flow", **SP)  # his eyes close
shot("fan", "ds2b", 24, 30, 260.75, 261.70, z=[(0, 1.00), (1, 1.06)], tin="nodoff110", seg=True, interp="blend", **SP)   # the fan flickers: no flow (v15); the earlier frames are ghosted in the pack
# ---- the hunt (e30-e68): the drop dives through the fan into the kill room
shot("killroom", "ds2a", 30, 33, 223.90, 225.10, z=[(0, 1.04), (1, 1.00)], tin="fan110", interp="flow", **SP)
shot("victim", "s1", 33, 35, 390.50, 391.40, z=[(0, 1.00), (1, 1.03)], tin="facematch108", interp="flow", **SP)
shot("plastic", "ds2b", 35, 37, 159.30, 160.30, z=[(0, 1.00), (1, 1.03)], tin="double108", interp="flow", **SP)   # drugged: double vision
shot("green", "s1", 37, 39, 152.20, 153.00, z=[(0, 1.00), (1, 1.03)], tin="light_sweep108", interp="flow", **SP)
shot("drive", "s1", 39, 41, 316.00, 316.90, z=[(0, 1.00), (1, 1.03)], tin="wiper108", interp="flow", **SP)   # the car: the wiper
shot("dark", "s4", 41, 43, 117.50, 118.40, z=[(0, 1.00), (1, 1.03)], tin="tear110", interp="flow", **SP)
shot("aim", "ds2b", 43, 46, 369.40, 370.12, z=[(0, 1.00), (1, 1.03)], tin="fronds108", interp="flow", **SP)   # he aims through the bamboo: THE BARREL
shot("warm", "dmx", 46, 48, 159.30, 160.20, z=[(0, 1.00), (1, 1.03)], tin="barrel110", interp="flow", **SP)
shot("neon", "ds2b", 48, 50, 203.80, 204.50, z=[(0, 1.00), (1, 1.03)], tin="flicker109", interp="flow", **SP)   # the power fails again: red neon
shot("lamp", "ds2b", 50, 53, 290.90, 291.90, z=[(0, 1.00), (1, 1.03)], tin="whip", interp="flow", **SP)
shot("night", "ds2a", 53, 56, 188.00, 189.30, z=[(0, 1.00), (1, 1.03)], tin="curtain110", interp="flow", **SP)   # the curtain blows across
shot("killwide", "p1", 56, 58, 135.30, 136.10, z=[(0, 1.00), (1, 1.03)], tin="plasticroll110", face=None, cx=(560, 640), interp="flow", **SP)   # the kill room: its plastic unrolls
shot("cabin", "p1", 58, 60, 176.60, 177.50, z=[(0, 1.00), (1, 1.03)], tin="brush110", interp="flow", **SP)
shot("closeup", "s4", 60, 62, 161.10, 161.90, z=[(0, 1.00), (1, 1.03)], tin="streetlight109", interp="flow", **SP)
shot("anguish", "p1", 62, 68, 164.00, 164.90, z=[(0, 1.00), (1, 1.04)], tin="dolly", interp="flow", **SP)      # THE SPATTER
# ---- "Mommy?" (e68-e79): the blood room; the loop falls into bed
shot("bloodwall", "dmx", 68, 72, 111.80, 112.90, z=[(0, 1.00), (1, 1.05)], tin="swinglight110", interp="flow", **SP)   # the blood-spattered wall, in the bulb's light
shot("bloodroom2", "dmx", 72, 74, 110.05, 110.75, z=[(0, 1.00), (1, 1.03)], tin="tilt110", interp="flow", **SP)   # "Mommy?": he looks up at the blood
shot("lookup", "dmx", 74, 79, 122.90, 124.30, z=[(0, 1.00), (1, 1.04)], tin="glide110", interp="flow", tout="driploop110", **SP)
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text (the approved v9 construction): style = cap | carry | bound | charge | slam | echo | hero | speed | <your own>
#      words=[(WORD, edit t, line 0|1)] on the sung onsets, end=t, emph=[...]; rides=True draws it before the transition
TEXT = []                                   # no text (rev 3: the owner removed I'M LOSING POWER)
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
