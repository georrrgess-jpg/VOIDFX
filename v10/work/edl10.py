"""LET IT HAPPEN — The Flash × Tame Impala "Let It Happen" (voidfx v10, 9:16). Single source of truth: the renderer,
audio builder and QC read only this file.

Concept: "Let it happen." Barry Allen stops holding on. In the quiet before the storm he stands calm in the dark lab,
smiles, his eyes catch lightning, the Speed Force crawls over his suit; on the drop the camera dives through the bolt of
his emblem and he is gone. The hunt of light (throw, run, scream), then LET IT / HAPPEN struck letter by letter by
lightning. A bolt hits him, and on the song's own gated stutter TIME STOPS: the world freezes between beats while he
moves through it. "All this running around": he runs so fast he leaves afterimages, becomes a streak of light and
outruns time itself; the whole edit rewinds and he is back in the dark lab where it began (the loop).
Look: PRISM SPEED (new): graphite-slate shadows, rich suit crimson, white-gold lightning with bloom, a prismatic
time-slice (RGB channels split across time) on the fastest moments; the frozen world drains to steel with gold sparks.
Type: the approved v9 text system (bold keyline captions, per-letter hero title), recoloured: lightning-gold emphasis.

Song: src/let_it_happen.mp3 (radio edit, 4:16), 125.0 BPM, half-beat P = 0.24003 s, offset 0.1920 (grid verified
across the window). Window h392 -> h496 (94.32 -> 119.28 s, 13 bars, 24.96 s):
  94.32  the bass-less "whirlwind" breakdown, "It's gonna carry off all that isn't bound"   (cold open, build)
 100.26  "And when..."   101.94 DROP (bass returns, +26.5 dB): "...it happens, when it happens"
 107.68  "So let it happen, let it happen"                                                 (hero title)
 112.04  the gated stutter (the music cuts out every 4th half-beat)                         (time freeze)
 115.41  second impact (+15 dB): "All this running around"                                  (afterimage run)
 119.28  bar line before "I can't fight it..."                                             (rewind -> loop)
Edit half-beat e = song half-beat - 392.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "v10", "let_it_happen_flash"
SONG = f"{ROOT}/src/let_it_happen.mp3"
SONG_STEMS = f"{ROOT}/{VER}/audio/sep/htdemucs/let_it_happen"
FPS, W, H = 60, 1080, 1920
SRC = {"fb": (f"{ROOT}/src/flash_b.mp4", 60.0, 1280, 720)}          # 24p content in a 60 fps container (hold cadence)

HB, HB_OFF = 0.24002757, 0.19202206
H0, H1 = 392, 496
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(e): return e * HB
def fe(t): return int(round(t * FPS))
def fh(e): return fe(th(e))
def te(e): return th(e)
def s2e(s): return s - SONG_IN
DUR = th(H1 - H0); DUR_F = fh(H1 - H0)
HDROP = 32; DROP_HB = HDROP; T_STOP = DUR
E_STUT, E_RUN, E_REW = 74, 88, 100            # the gated stutter, the second impact, the rewind
STUT_GAPS = [75, 79, 83, 87]                  # half-beats where the music drops out (freeze), song h467/471/475/479
STUT_HITS = [76, 80, 84]                      # half-beats where it kicks back in (time jolts forward)
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

VO = []                                       # the packs carry no usable dialogue; music-driven
VO_STEM = None; VO_STEM_T0 = 0.0

# ---- lyric word times (Demucs vocal stem + Whisper, re-checked in short windows; song seconds). Only unambiguous
#      words go on screen ("isn't bound/found" and "won't/will be holding on" are left off).
W_AND = [("AND", 100.26), ("WHEN", 101.56)]
W_HAP1 = [("IT", 102.48), ("HAPPENS", 102.82)]
W_HAP2 = [("WHEN", 103.92), ("IT", 104.42), ("HAPPENS", 104.70)]
W_LET = [("LET", 108.02), ("IT", 108.38), ("HAPPEN", 108.54)]
W_LET2 = [("LET", 109.34), ("IT", 110.26), ("HAPPEN", 110.44)]
W_RUN = [("ALL", 115.24), ("THIS", 116.12), ("RUNNING", 117.00), ("AROUND", 117.58)]

S = []
def shot(n, src, e0, e1, a, b, **kw):
    """n name, src pack key, e0/e1 edit half-beats, a/b source seconds. tin = transition INTO this shot."""
    d = dict(n=n, src=src, t0=th(e0), t1=th(e1), e0=e0, e1=e1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "prism"),
             z=kw.pop("z", [(0, 1.00), (1, 1.07)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "hold"))
    d.update(kw); S.append(d)

# ---- cold open: the calm before the whirlwind (bass-less build)
shot("lab", "fb", 0, 8, 38.62, 40.54, z=[(0, 1.12), (1, 1.22)], tin="rewind_in", seg=True, arcs=0.35)
shot("smile", "fb", 8, 16, 34.40, 36.32, z=[(0, 1.00), (1, 1.08)], tin="arc_link", seg=True, arcs=0.5)
shot("eyes", "fb", 16, 24, 116.62, 118.54, z=[(0, 1.00), (1, 1.10)], tin="ignite", seg=True, arcs=0.7)
shot("charge", "fb", 24, 32, 83.85, 85.05, z=[(0, 1.02), (1, 1.16)], tin="arc_link", interp="blend", seg=True, arcs=1.0,
     emblem=[(83.95, 731, 462), (84.45, 744, 581), (84.95, 744, 625), (85.05, 745, 632)], emblem_r=42)
# ---- the drop: through the bolt of his emblem; the hunt of light
shot("takeoff", "fb", 32, 38, 4.62, 6.12, z=[(0, 1.14), (1, 1.04)], tin="emblem_gate", seg=True, trails=0.8)
shot("throw", "fb", 38, 40, 124.40, 124.77, z=[(0, 1.00), (1, 1.06)], tin="ramp")
shot("garage", "fb", 40, 46, 113.55, 114.99, z=[(0, 1.04), (1, 1.12)], tin="bolt_link", seg=True, trails=0.7)
shot("scream", "fb", 46, 50, 127.70, 128.66, z=[(0, 1.00), (1, 1.08)], tin="shock")
shot("grin", "fb", 50, 54, 56.30, 57.26, z=[(0, 1.00), (1, 1.05)], tin="prism_cut")
shot("turn", "fb", 54, 56, 102.86, 103.34, z=[(0, 1.00), (1, 1.06)], tin="ramp")
shot("hero", "fb", 56, 68, 109.76, 112.42, z=[(0, 1.00), (1, 1.10)], tin="logo_orig", seg=True, arcs=0.45)
shot("strike", "fb", 68, 74, 10.36, 11.80, z=[(0, 1.00), (1, 1.08)], tin="bolt_strike")
# ---- the gated stutter: time stops between the beats (source time only advances on the hits)
#      (the music: e74 low, e75 gap, e76-77 hit, e78 low, e79 gap, e80-81 hit, e82 low, e83 gap, e84-85 hit, e86 low, e87 gap)
shot("freeze_a", "fb", 74, 82, 0, 0, tmap=[(0, 13.00), (2 / 8, 13.00), (4 / 8, 14.60), (6 / 8, 14.60), (1, 16.20)],
     lin=True, z=[(0, 1.00), (1, 1.16)], tin="freeze_in", seg=True, frozen=True, face=None, cx=(870, 880))
shot("freeze_b", "fb", 82, 88, 0, 0, tmap=[(0, 28.10), (2 / 6, 28.10), (4 / 6, 29.40), (1, 29.40)],
     lin=True, z=[(0, 1.06), (1, 1.20)], tin="jolt", seg=True, frozen=True, face=None, cx=(1000, 960))
# ---- "All this running around": afterimages, then he outruns time
shot("run", "fb", 88, 100, 0, 0, tmap=[(0, 80.86), (8 / 12, 81.95), (1, 82.24)], z=[(0, 1.00), (1, 1.10)], tin="restart", face=None, cx=(560, 520),
     interp="blend", seg=True, trails=1.0, arcs=0.6, streak_e=98)
shot("rewind", "fb", 100, 104, 82.10, 82.24, tin="streak", graphic="rewind", face=None, cx=(640, 640))
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

# ---- text: the approved v9 system. cap = keyline captions, slam = one hard-hitting word pair, echo = speed-echo
#      caption, hero = per-letter title struck by lightning, speed = words that arrive with afterimage streaks
TEXT = [
    dict(style="cap", words=[(w, s2e(t), 0) for w, t in W_AND], end=th(32) - 0.02, emph=["WHEN"], rides=True),
    dict(style="slam", words=[(w, s2e(t), 0 if i == 0 else 1) for i, (w, t) in enumerate(W_HAP1)], end=th(38) - 0.06, emph=["HAPPENS"]),
    dict(style="echo", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_HAP2)], end=th(46) - 0.07, emph=["HAPPENS"]),
    dict(style="hero", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_LET)], end=th(68) - 0.05, emph=["HAPPEN"],
         pulses=[s2e(t) for _, t in W_LET2]),
    dict(style="speed", words=[(w, s2e(t), 0 if i < 2 else 1) for i, (w, t) in enumerate(W_RUN)], end=th(99) + 0.02, emph=["RUNNING", "AROUND"], rides=True),
]
for _t in TEXT:
    assert _t["end"] > _t["words"][-1][1] + 0.25, (_t["words"], _t["end"])
CAPS = []; CAP_Y = (1385, 1490); END_CAP = []
CLOSE_T = None; DROP_TITLE = None; VANISH_T0 = None
MONTAGE = (HDROP, E_STUT)
SONG_VOX, SONG_VOX_T0, VOX_MUTE = None, 0.0, None

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        ts = [k[1] for k in s["tmap"]]; sp = (max(ts) - min(ts)) / (s["t1"] - s["t0"])
        print(f"{s['n']:9s} e{s['e0']:3d}-e{s['e1']:3d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {min(ts):7.2f}-{max(ts):7.2f} x{sp:.2f} {s['interp']:5s} in={s.get('tin','')}")
    assert prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3), "stutter", round(th(E_STUT), 3), "run", round(th(E_RUN), 3), "rewind", round(th(E_REW), 3))
    for t_ in TEXT: print(f"  {t_['style']:5s} {t_['words'][0][1]:6.2f}-{t_['end']:6.2f} " + " ".join(f"{w}@{t:.2f}" for w, t, _ in t_["words"]))
