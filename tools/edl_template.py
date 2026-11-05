"""{{TITLE}} (voidfx {{VER}}, 9:16). Single source of truth: the renderer, audio builder and QC read only this file.
Scaffolded from the v11 BOP standard (rev 4; v10 LET IT HAPPEN structure). Keep the structure; replace the look, the
shots and the text. v11 reference: v11/work/edl11.py (a concept taken from the song's own words, a rival in a second
grade, two designed titles, a focal set piece, beat moments, a loop that lands exactly on frame 0).

Concept: <one paragraph rooted in the character's world: the cold open, what the drop goes through, the hook,
the set pieces, the ending, how the loop lands back on frame 0>.
Song window: half-beats H0 -> H1 (whole bars), drop at HDROP, from `python3 tools/song_map.py SONG {{VER}}/work`.
Lyrics: Whisper word times, then every word checked against its sung onset on the Demucs vocal stem (toolkit pitfall 14).
Edit half-beat e = song half-beat - H0. Even e are beats.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "{{VER}}", "{{SLUG}}"          # folder + output name: {{VER}}/out/{{SLUG}}_voidfx_9x16.mp4
SONG = f"{ROOT}/src/SONG.mp3"             # decoded to {{VER}}/audio/song48.wav on the first audio build
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/SONG"   # Demucs stems of the song (vocals.wav / no_vocals.wav)
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height); fps from ffprobe. 24p content in a 60 fps container is de-duplicated;
# run `nohup python3 tools/sr_prep.py {{N}} &` after prep so every frame is restored and 2x upscaled.
SRC = {"fb": (f"{ROOT}/src/flash_b.mp4", 60.0, 1280, 720), "p9": (f"{ROOT}/src/pack9_s4_best.mp4", 60.0, 1280, 720)}

HB, HB_OFF = 0.5, 0.0                      # half-beat period + offset (song_map.json: P, off)
H0, H1 = 0, 104                            # window start / end in song half-beats (whole bars)
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
E_BEAT, E_DIP = 8, HDROP - 8               # v11 engine: where the beat drops in, the dip before the drop
E_LOOP = H1 - H0 - 6                       # v11 engine: where the loop set piece starts (the beat camera rests from here)
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

# ---- cold open (the build)
# shot("open", "fb", 0, 8, 38.62, 40.54, tin="tunnel_in", seg=True, arcs=0.35, wind=0.55)
# ---- the drop (the biggest set piece)
# shot("drop", "fb", 32, 38, 4.62, 6.12, tin="emblem_gate", seg=True, wave=True, tmap=vel(32, 38, 4.62, 6.12), lin=True, interp="flow")
# ---- the loop (lands on frame 0)
# shot("tunnel", "fb", 100, 104, 82.10, 82.24, tin="portal", graphic="tunnel", face=None, cx=(640, 640))
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
