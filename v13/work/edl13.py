"""EVENT HORIZON — The Flash × Brent Faiyaz "Wish You Well" (voidfx v13, 9:16). Single source of truth: the renderer, audio
builder and QC read only this file. Scaffolded from the v12 BLOOM standard engine.

Concept: SINGULARITY. In the S1 finale a singularity tears open over Central City and pulls everything toward it; Barry
runs into it to close it. The song is the singularity's voice, a love that pulls everything in ("Pick me up, don't know if
it's what I need, but it's what I want, God, look out for me … Darling, I don't wish you well, when you ain't with me, I
want you crying"). The hero asset is a procedural black hole (shadow, photon ring, gravitational lensing of the footage, an
accretion disk of lightning) that runs through the edit:
  - frame 0: it sits at the core of the S1 vortex over the city; "Pick me up": the pull lifts the debris;
  - "God, look out for me": he looks up at it; his pupil becomes it (EYE HORIZON); the take-off;
  - "Darling,": the EVENT HORIZON (focal set piece): time dilates and stops, the light redshifts, the photon ring shows his
    images orbiting; in the song's deepest rest it collapses, and on the music's return a gravitational wave breaks out;
  - "I don't wish you well": the breakout and the montage; EMBLEM HORIZON on the real tracked emblem; Iris left in his wind
    on "I want you crying";
  - the loop: he looks up into it, we fall in (tidal stretch), and frame 0 comes out of its Einstein ring.
Transitions built on the real physics: gravitational lensing (Einstein ring), frame dragging, spaghettification (tidal
stretch), gravitational redshift and time dilation, gravitational waves (quadrupole strain), the photon ring.
Look REDSHIFT: a desaturated silver-steel world; only the suit's crimson, skin, and the singularity's light keep colour
(white-hot core, amber-red receding side, cool white approaching side). No text. Sound: few, big, gravitational.

Song window: song half-beats 92 -> 188 (20.05 -> 40.92 s), 96 half-beats = 6 phrases of 16 (3.48 s each). The section has
no real drums: an ambient phrase with an 808 hit at e = 8 (mod 16) and a rest at e = 12-14 (mod 16). Bar 23 mirrors bar 11
(music spectral correlation 0.9996 across the wrap), so the window loops exactly.
Grid fitted on the Demucs drum stem: P = 0.217398 s (137.99 BPM half-beats; the feel is 69 BPM), offset 0.0539 s.
Lyrics on the vocal stem (Whisper large-v3): "Pick" e2.7, "God" e23, "Darling," e49.6, vocal silent e52-e66,
"I don't wish you well" e67-e73, "When you ain't with me, I want you crying" e75-e87.
Edit half-beat e = song half-beat - H0.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v13", "horizon"          # folder + output name: v13/out/horizon_voidfx_9x16.mp4
SONG = f"{ROOT}/src/wish_you_well_full.mp3"            # decoded to v13/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/win"; STEMS_T0 = 10.0   # Demucs stems of song 10-50 s (vocals / no_vocals)
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height). flash_b_hq is 24p content in a 60 fps container (give held shots interp="flow").
SRC = {"fs1": (f"{ROOT}/src/flash_s1.mp4", 30.0, 1280, 720), "fbh": (f"{ROOT}/src/flash_b_hq.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.217398, 0.0539              # drum-stem fit (song_map: 0.21739 / 0.0435)
H0, H1 = 92, 188                           # phrases: song 20.05 -> 40.92 s
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB                   # edit time of edit half-beat e
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN             # song seconds -> edit seconds
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 64; DROP_HB = HDROP; T_STOP = DUR  # the breakout (the music returns after the deepest rest)
E_DARLING = 48                             # the event horizon set piece starts (Darling at e49.6)
E_STUT, E_RUN, E_REW = H1 - H0, H1 - H0, H1 - H0
STUT_GAPS, STUT_HITS = [], []
E_BEAT, E_DIP = 4, HDROP - 16
E_LOOP = H1 - H0 - 8                       # the loop set piece (the beat camera rests from here)
BAR = 8 * HB; BEAT = 2 * HB
PHRASE = 16                                # half-beats per phrase; the 808 hit at e % 16 == 8, the rest at 12-14
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []
VO_STEM = None; VO_STEM_T0 = 0.0

def vel(e0, e1, a, b, lo=0.42, hi=2.4, tau=0.09, n=96, every=4):
    """velocity ramp for a slow song: a burst on every beat of the 69 BPM feel (every 4 half-beats), smooth slow motion
    between; the same source range a..b. Use with lin=True, interp="flow"."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); sp = _np.full_like(ts, lo)
    for e in range(e0, e1):
        if e % every == 0:
            tb = th(e) - th(e0); sp = sp + (hi - lo) * _np.exp(-_np.clip(ts - tb, 0, None) / tau) * (ts >= tb)
    src = _np.concatenate([[0.0], _np.cumsum((sp[1:] + sp[:-1]) / 2 * _np.diff(ts))]); src /= src[-1]
    return [(float(u), float(a + (b - a) * _np.interp(u * T, ts, src))) for u in _np.linspace(0, 1, n)]

def dilate(e0, e1, a, b, e_slow, e_stop, n=96):
    """time dilation at the horizon: normal speed until e_slow, then the clock slows exponentially and stops at e_stop
    (frozen after it)."""
    import numpy as _np
    T = th(e1) - th(e0); ts = _np.linspace(0, T, 800); t1, t2 = th(e_slow) - th(e0), th(e_stop) - th(e0)
    sp = _np.where(ts < t1, 1.0, _np.clip(1 - (ts - t1) / (t2 - t1), 0, 1) ** 2.2)
    src = _np.concatenate([[0.0], _np.cumsum((sp[1:] + sp[:-1]) / 2 * _np.diff(ts))]); src /= src[-1]
    return [(float(u), float(a + (b - a) * _np.interp(u * T, ts, src))) for u in _np.linspace(0, 1, n)]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot.
    v13: lens_drop frame_drag redshift photon_ring eye_horizon accretion_whip event_horizon grav_wave spaghettify
    emblem_horizon; the loop (loop_in13 + the dive in render()). Library moves are restyled through the v13 palette."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "redshift"),
             z=kw.pop("z", [(0, 1.00), (1, 1.06)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- PHRASE 1-2: THE PULL ("Pick me up, don't know if it's what I need / But it's what I want, God, look out for me")
shot("sky", "fs1", 0, 8, 290.22, 291.40, tin="loop_in13", face=None, cx=(480, 480), z=[(0, 1.00), (1, 1.04)], flowmax=40)
shot("pull", "fs1", 8, 14, 277.47, 278.90, tin="edge_current", seg=True, z=[(0, 1.00), (1, 1.05)], flowmax=40)
shot("mask", "fs1", 14, 19, 228.10, 229.20, tin="focus_rack", seg=True)
shot("blood", "fs1", 19, 24, 286.95, 288.20, tin="speed_whip", seg=True)
shot("god", "fs1", 24, 30, 268.30, 269.80, tin="ribbon", seg=True)
# ---- PHRASE 3: "look out for me" — the eye, the take-off
shot("eye", "fs1", 30, 34, 291.50, 292.80, tin="dolly", face=None, cx=(320, 320), z=[(0, 1.00), (1, 1.08)])
shot("takeoff", "fs1", 34, 40, 195.00, 196.80, tin="eye_iris", face=None, cx=(640, 640), seg=True,
     tmap=vel(34, 40, 195.00, 196.80), lin=True, ev=0.35, flowmax=40)
# ---- PHRASE 4: the run, Iris and Joe watching, "Darling,"
shot("run", "fbh", 40, 44, 80.90, 82.20, tin="time_slice", face=None, cx=(560, 520), tmap=vel(40, 44, 80.90, 82.20), lin=True, satk=0.6)
shot("watch", "fs1", 44, 48, 285.55, 286.65, tin="afterimage", seg=True)
# ---- THE EVENT HORIZON (focal set piece): Darling (e49.6), time dilates and stops, the photon ring, the collapse
shot("darling", "fs1", 48, 56, 221.72, 222.95, tin="light_leak13", seg=True, tmap=dilate(48, 56, 221.72, 222.95, 50, 55.5))
shot("horizon", "fs1", 56, 64, 207.55, 207.95, tin="event_horizon", seg=True, z=[(0, 1.00), (1, 1.06)],
     tmap=dilate(56, 64, 207.55, 207.95, 56, 60))                       # the airfield: the hole looms in the sky behind him
# ---- PHRASE 5: the breakout ("I don't wish you well"), the emblem, he leaves her ("When you ain't with me, I want you crying")
shot("breakout", "fbh", 64, 72, 52.92, 54.28, tin="grav_wave", seg=True, ev=0.30, flowmax=14, flowfall="blend")
shot("emblem", "fbh", 72, 78, 83.85, 85.05, tin="panel_run", seg=True, satk=0.75, flowmax=30)
shot("leave", "fs1", 78, 82, 236.30, 237.60, tin="emblem_split", seg=True)
shot("iris", "fs1", 82, 88, 237.80, 238.75, tin="slipstream", seg=True)
# ---- PHRASE 6: the loop: he looks up into it, the fall, frame 0 out of the Einstein ring
shot("last", "fs1", 88, 96, 279.55, 281.10, tin="whip_up13", seg=True, z=[(0, 1.00), (1, 1.03)], flowmax=40)
SET_PIECES = [("ribbon", th(20), th(26)), ("event_horizon", th(48), th(64)), ("grav_wave", th(62), th(68)), ("emblem_split", th(76), th(80)), ("ribbon_loop", th(92), th(96))]
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

TEXT = []
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, H1 - H0 - 8)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert not SHOTS or prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "breakout", round(th(HDROP), 3), "song in", round(SONG_IN, 3))
