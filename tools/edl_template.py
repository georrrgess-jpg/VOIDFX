"""{{TITLE}} (voidfx {{VER}}, 9:16). Single source of truth: the renderer, audio builder and QC read only this file.

Concept: <one paragraph: story beat of the cold open, what the drop goes through, the montage, the ending, the loop>.
Song window: half-beats H0 -> H1 (whole bars), drop at HDROP — from `python3 tools/song_map.py SONG {{VER}}/work`.
"""
ROOT = "/home/user/VOIDFX"
VER, SLUG = "{{VER}}", "{{SLUG}}"          # folder + output name: {{VER}}/out/{{SLUG}}_voidfx_9x16.mp4
SONG = f"{ROOT}/src/SONG.mp3"             # decoded to {{VER}}/audio/song48.wav on the first audio build
FPS, W, H = 60, 1080, 1920
# pack key -> (path, fps, width, height); fps from ffprobe (24p/30p packs are de-duplicated and flow-interpolated)
SRC = {"p6": (f"{ROOT}/src/pack6_s5.mp4", 30.0, 1280, 720), "p5": (f"{ROOT}/src/pack5_mixtape120.mp4", 60.0, 1280, 720),
       "p4": (f"{ROOT}/src/pack4_aesthetic.mp4", 29000 / 1001, 1280, 720), "p1": (f"{ROOT}/src/scenepack.mp4", 60.0, 1200, 720),
       "p3": (f"{ROOT}/src/scenepack3_24fps.mp4", 24000 / 1001, 1280, 720)}

HB, HB_OFF = 0.5, 0.0                      # half-beat period + offset (song_map.json: P, off)
H0, H1, HDROP = 0, 80, 32                  # window start / end / drop in half-beats (song_map.json: windows)
def st(h): return HB_OFF + h * HB
SONG_IN = st(H0)
def th(h): return st(h) - SONG_IN          # edit time of half-beat h
def fe(t): return int(round(t * FPS))
def fh(h): return fe(th(h))
def s2e(s): return s - SONG_IN
DUR = th(H1); DUR_F = fh(H1)
def te(h): return th(h)
T_STOP = DUR; DROP_HB = HDROP
BAR = 8 * HB; BEAT = 2 * HB
LOGO_W = 860
LOCK_FACE = dict(x=540, y=760, w=680)

# ---- dialogue: (src_in, src_out, edit_at) from tools/transcribe.py word times; [] = music-only edit
VO = []
# ---- captions: (vo index, [(word, src t, line 0|1)], src end, [chrome words], "line"|"vanish"); every word on its spoken time
CAPS = []
CAP_Y = (1370, 1472)                       # caption line centres (text band 1280-1640, clear of faces + TikTok UI)
END_CAP = []                               # neon words [(WORD, edit t)] for the ending, [] = none

# ---- engine knobs
DROP_TITLE = None                          # chrome title word at the drop (e.g. "MIAMI"), None = none
MONTAGE = (HDROP, H1 - 12)                 # half-beats with beat bounce, glints, light leaks, hits
VANISH_T0 = None                           # edit time the pixel dissolve starts (shot flag vanish=True)
VO_STEM = None                             # Demucs vocal stem the VO lines are cut from (f"{ROOT}/{VER}/audio/sep/htdemucs/NAME/vocals.wav")

S = []
def shot(n, src, t0, t1, a, b, **kw):
    """n name, src pack key, t0/t1 edit seconds (use th(h)), a/b source seconds. Options (all optional):
    tin=   transition INTO this shot:  tape_in eye_dive assemble polaroid facematch tear crt cube sun filmstrip peel
           ink slash logo burn lens shadow tv_off   (+ older: kaleido rewind flash tiles neon_trace ripple pixel_sort vhs_roll)
    tout=  crt (with the next shot's tin="crt"), rewind_end (last shot -> static -> loop)
    z=[(u, zoom)...]  face="largest"|"left"|"right"|None (+cx=(x0,x1))  interp="flow"|"blend"|"hold"  look="vapor"
    seg=True (MODNet matte)  vanish=True  vapor_bg=True  echo=True  palms=True  motes=True  pause=FRAME
    lens=(dy, kx, ky) for tin="lens" on the NEXT shot (sunglasses shape)   muzzle=(x, y) for tin="tv_off" on the next shot"""
    d = dict(n=n, src=src, t0=t0, t1=t1, tmap=kw.pop("tmap", [(0, a), (1, b)]), look=kw.pop("look", "vapor"),
             z=kw.pop("z", [(0, 1.00), (1, 1.08)]), face=kw.pop("face", "largest"), interp=kw.pop("interp", "flow"))
    d.update(kw); S.append(d)

# ---- cold open (dialogue / build)
# shot("open", "p6", th(H0), th(H0 + 8), 16.50, 19.17, tin="tape_in")
# ---- drop
# shot("drop", "p5", th(HDROP), th(HDROP + 4), 51.65, 53.00, tin="crt", seg=True, vapor_bg=True)
# ---- ending (loops)
# shot("last", "p6", th(H1 - 12), th(H1), 0.85, 4.85, tout="rewind_end")
SHOTS = S
for s in SHOTS:
    s["f0"], s["f1"] = fe(s["t0"]), fe(s["t1"])

if __name__ == "__main__":
    prev = 0
    for s in SHOTS:
        assert s["f0"] == prev, (s["n"], s["f0"], prev); prev = s["f1"]
        sp = (s["tmap"][-1][1] - s["tmap"][0][1]) / (s["t1"] - s["t0"])
        print(f"{s['n']:12s} {s['t0']:6.2f}-{s['t1']:6.2f} {s['src']} {s['tmap'][0][1]:.2f}-{s['tmap'][-1][1]:.2f} x{sp:.2f} in={s.get('tin','')} out={s.get('tout','')}")
    assert prev == DUR_F, (prev, DUR_F)
    print("dur", round(DUR, 3), "frames", DUR_F, "drop", round(th(HDROP), 3))
