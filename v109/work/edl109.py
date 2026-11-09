"""PHANTOM - Dexter x EsDeeKid & Rico Ace "Phantom" (voidfx v109, 9:16). Scaffolded from v108 DOOMSDAY (--base v108).

Concept: PHANTOM. "Rocked out like a phantom": the Bay Harbor Butcher is a ghost the city hunts and never sees. He walks
out of the dark (frame 0), a flashlight finds him, and on the drop he materialises out of mist in the red kill room. The
hook is his ghost work: after-images, his double in a reflection, the phone glitching on "tantrum", vanishing between
frames, the crime-scene tape, the night hunt ("the only one that I'm hunting"). Rev 1 (owner notes): we pass through
him instead of the headspin; the Doakes shots are gone (the mangroves, the burning photo); the ending is a chain of
graphics that become the transitions (his fingerprint, the photo's fire, the heart monitor's flatline); the loop: he
blows away as glowing dust and the same gust carries the dust into frame 0, where he walks out of the dark again.
Look: SPECTRAL (silver-blue night, inky blacks, cold cyan highlights with a faint ghost bloom; only blood red survives).
Text: one designed title, PHANTOM, on the sung word (the lyrics are explicit: titles, not captions, v11 rule).
Song: src/phantom.mp3 (1:50), 70.0 BPM on the drum stem (the auto map read 93.3 = 4/3), window h24->h80 (10.478 ->
34.478 s, 24.0 s): one bar before the drop (13.05 s = e6) through "you've never got no motion, as you've never got no
action". Lines start just after each bar (e8.8, 15.8, 23.9, 31.8, 39.3, 47.3); "phantom" e10.4, "tantrum" e14.6,
"hunting" e38.8, "action" e54.5. Edit half-beat e = song half-beat - H0; even e are beats, bars every 8 e.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v109", "phantom_dexter"
SONG = f"{ROOT}/src/phantom.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 0.0
FPS, W, H = 60, 1080, 1920
SRC = {"s1": (f"{ROOT}/src/dexter_s1_hq.mp4", 60.0, 1280, 720), "s4": (f"{ROOT}/src/dexter_s4_hq.mp4", 60.0, 1280, 720),
       "p7": (f"{ROOT}/src/pack7_4k.mp4", 60.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720), "dmx": (f"{ROOT}/src/dexter_mix_b.mp4", 60.0, 1280, 720),
       "ds2a": (f"{ROOT}/src/dexter_s2_a.mp4", 60.0, 1280, 720), "ds2b": (f"{ROOT}/src/dexter_s2_b.mp4", 60.0, 1280, 720)}
HB, HB_OFF = 0.428563, 0.1929             # 70.0 BPM (drum stem; the auto map read 4/3 of it)
H0, H1 = 24, 80
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 6; DROP_HB = HDROP; T_STOP = DUR   # the beat drops (13.05 s): the phantom materialises
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 6, 4                       # the beat camera from the drop
E_LOOP = 53                                # the loop: he blows away as glowing dust; the gust carries it into frame 0
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)
VO = []
SET_PIECES = [("the flashlight", th(2), th(4)), ("THE PHANTOM'S TRAIL", th(34.2), th(36.4)), ("MATERIALISE", th(5), th(8)), ("PHANTOM", th(10), th(13.5)),
              ("the surveillance", th(27), th(31)), ("THE GUST (loop)", th(53), th(56))]
SIGNATURE = ["materialize109"]
HERO = ["mist_veil"]                        # the phantom mist: the drop, the vanish, the loop
HERO_TINS = ["materialize109", "vanish109"]
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

SP = dict(look="spectral109")
shot("open", "p1", 0, 3, 186.40, 187.60, z=[(0, 1.00), (1, 1.05)], interp="flow", ev=0.6, seg=True, **SP)                 # he walks out of the dark (frame 0)
shot("flash", "s4", 3, 6, 184.70, 185.90, z=[(0, 1.00), (1, 1.04)], tin="flashlight109", interp="flow", **SP)
shot("drop", "p7", 6, 9, 0.05, 1.10, z=[(0, 1.06), (1, 1.00)], tin="materialize109", seg=True, interp="flow", ev=0.6, **SP)   # the red kill room
shot("hood", "s1", 9, 11, 302.20, 303.10, z=[(0, 1.00), (1, 1.04)], tin="afterimage109", interp="blend", **SP)
shot("double", "s4", 11, 13, 157.10, 158.00, z=[(0, 1.00), (1, 1.03)], tin="mirror109", interp="flow", **SP)   # PHANTOM: his double
shot("chain", "p1", 13, 15, 171.10, 171.75, z=[(0, 1.00), (1, 1.04)], tin="time_particles", interp="flow", **SP)   # the chain-link stare
shot("walk", "s1", 15, 17, 230.75, 231.65, z=[(0, 1.00), (1, 1.04)], tin="tantrum109", interp="flow", ev=0.6, **SP)   # "tantrum": the phone glitch
shot("night", "p5", 17, 19, 31.45, 32.35, z=[(0, 1.00), (1, 1.04)], tin="flicker109", seg=True, interp="flow", **SP)   # he walks at us...   # the night walk
shot("anthem", "s4", 19, 21, 41.00, 41.95, z=[(0, 1.00), (1, 1.04)], tin="phantom_pass109", interp="flow", **SP)   # ...and we pass through him
shot("hazmat", "dmx", 21, 24, 94.95, 95.85, z=[(0, 1.04), (1, 1.00)], tin="slices", interp="blend", **SP)
shot("table", "s4", 24, 26, 102.95, 103.85, z=[(0, 1.00), (1, 1.04)], tin="surface", interp="flow", **SP)   # the plastic-wrapped table
shot("gloves", "p1", 26, 28, 102.20, 102.80, z=[(0, 1.00), (1, 1.04)], tin="polaroid", interp="flow", ev=0.7, **SP)
shot("tape", "p7", 28, 30, 22.55, 23.65, z=[(0, 1.00), (1, 1.04)], tin="cctv109", seg=True, interp="blend", hflip=True, **SP)   # the pack mirrored it (DO NOT CROSS read backwards)
shot("hall", "s1", 30, 32, 349.40, 350.30, z=[(0, 1.00), (1, 1.04)], tin="vanish109", seg=True, interp="flow", **SP)
shot("police", "s4", 32, 34, 48.40, 49.30, z=[(0, 1.00), (1, 1.03)], tin="page_turn107", interp="flow", redthr=0.30, **SP)   # "the only one that I'm hunting": the predator's look
shot("dock", "s4", 34, 36, 73.80, 74.80, z=[(0, 1.00), (1, 1.04)], tin="whip", seg=True, interp="flow", **SP)   # the phantom's trail circles him
shot("hunt", "s1", 36, 39, 355.40, 356.40, z=[(0, 1.00), (1, 1.04)], tin="trail109", interp="flow", **SP)   # ...and dives at the lens
shot("mangrove", "s1", 39, 41, 176.00, 176.90, z=[(0, 1.00), (1, 1.03)], tin="print109", interp="flow", **SP)   # through his print: the mangroves
shot("lighter", "s1", 41, 43, 222.30, 223.20, z=[(0, 1.00), (1, 1.03)], tin="smear", interp="flow", **SP)   # he burns the photo
shot("hammer", "s4", 43, 46, 222.30, 223.30, z=[(0, 1.00), (1, 1.04)], tin="burn109", interp="flow", **SP)   # the photo's fire burns the frame away
shot("container", "s1", 46, 48, 371.70, 372.60, z=[(0, 1.00), (1, 1.03)], tin="whip", interp="flow", redthr=0.30, **SP)   # the rusted container
shot("drive", "s4", 48, 50, 0.50, 1.40, z=[(0, 1.00), (1, 1.03)], tin="redwash109", interp="flow", ev=0.4, **SP)   # red-lit, driving
shot("syringe", "s4", 50, 52, 177.40, 178.30, z=[(0, 1.00), (1, 1.04)], tin="streetlight109", interp="flow", **SP)   # "no motion": the M99 takes him
shot("stare", "ds2b", 52, 56, 322.28, 323.32, z=[(0, 1.00), (1, 1.04)], seg=True, interp="flow", tout="dust_loop109", **SP)   # rev 2: no monitor; a clean cut on the downbeat
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
