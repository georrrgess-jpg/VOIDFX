"""THE MASK SLIPS — edit decision list (the single source of truth for the edit).

All timeline positions are on the song's pulse grid (P = one eighth-note pulse,
6 pulses per bar). Edit t=0 is bar 31 of the Blood Theme instrumental.
Change values here and re-render; render.py reads nothing else.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_g = json.load(open(os.path.join(ROOT, "work", "grid.json")))
P = _g["P"]                      # pulse length (s) ~0.33336 (180 pulses/min, 6/8 bars of 2.0 s)
OFF = _g["off"]                  # song time of pulse 0 (bias-corrected)
FPS = 60
W, H = 1080, 1920                # vertical master
SRC = os.path.join(ROOT, "src", "scenepack.mp4")
SONG = os.path.join(ROOT, "src", "blood_theme.mp3")
PACK_AUDIO = os.path.join(ROOT, "audio", "pack_orig.wav")

def bar_t(bar, pulse=0):
    """Song time of a bar/pulse."""
    return OFF + (bar * 6 + pulse) * P

def tp(p):
    """Edit time (s) of pulse index p (pulse 0 = edit start)."""
    return p * P

def fp(p):
    """Output frame of pulse index p."""
    return int(round(tp(p) * FPS))

# ---------------------------------------------------------------- music edit
# A: bars 31-39 (build, drop at bar 35); B: bar 56 onward (final hits, the hard stop, outro tail)
MUSIC = dict(
    a_in=bar_t(31), a_out=bar_t(40),          # 18.0015 s
    b_in=bar_t(56),                           # continues to the end of the edit
    splice_xfade=0.010,
    tail_fade=(21.35, 22.0),                  # fade the outro bed out before the loop point
)
STOP_SONG_T = 113.047                         # measured: broadband falls >10 dB here
STOP_T = (MUSIC["a_out"] - MUSIC["a_in"]) + (STOP_SONG_T - MUSIC["b_in"])   # edit time of the hard stop
LOOP_PULSES = 66
DUR_FRAMES = 1320                             # 22.000 s  (66 pulses = 22.002 s)
DROP_P = 24                                   # bar 35 downbeat
STOP_F = int(round(STOP_T * FPS))

# ---------------------------------------------------------------- dialogue
# "Check in. Establish an alibi." — scene-pack audio 43.10-45.50 s (verified by 3 local ASR models;
# word times refined from the waveform in build_audio.py).
VO = dict(src_in=43.65, src_out=45.70,            # the pack keeps sound only for this shot
          words=[("Check", 43.75), ("in.", 43.97), ("Establish", 44.43), ("an", 44.90), ("alibi.", 45.00)],
          word_end=45.62,
          edit_at_check=tp(59))                      # "Check" on pulse 59: two silent pulses after the stop
VO_SHIFT = VO["edit_at_check"] - VO["words"][0][1]   # edit time = pack time + VO_SHIFT

# ---------------------------------------------------------------- shots
# a,b    : source seconds (scene pack) mapped linearly (or via 'ease') onto [t0,t1)
# t0,t1  : pulse indices (int) or ("f", frame) for frame-exact edges
# crop   : keyframes (u, cx, cy, h) in source px; h = crop height (width = h*9/16); eased between keys
# zoom   : keyframes (u, scale) applied around the crop centre (push-ins / punches)
# face   : (cx, cy, r) source px for exposure metering (approx centre of the face mid-shot)
# look   : 'day' | 'night' | 'room'  -> exposure target + creative look family
# role   : why the shot is there
SHOTS = [
    # ---------------- HOOK / SETUP (bars 31-34): the public face, then the first crack
    dict(name="finger_gun", pack=36, a=64.50, b=65.68, t0=0, t1=4,
         crop=[(0, 560, 360, 720), (1, 560, 360, 720)], zoom=[(0, 1.04), (1, 1.08)],
         face=(545, 130, 40), look="day",
         role="HOOK: grins and points a finger-gun at the viewer — charm with a gun in it"),
    dict(name="boat_grin", pack=40, a=70.55, b=71.88, t0=4, t1=8,
         crop=[(0, 470, 360, 720), (1, 610, 360, 720)], zoom=[(0, 1.0), (1, 1.03)],
         face=(490, 300, 50), look="day",
         role="public face: the easy laugh"),
    dict(name="icecream_stare", pack=39, a=69.00, b=70.333, t0=8, t1=12,
         crop=[(0, 560, 360, 720), (1, 700, 360, 720)], zoom=[(0, 1.0), (1, 1.04)],
         face=(615, 250, 42), look="day",
         role="first crack (lands on the big sub hit): eating ice cream, eyes go cold"),
    dict(name="gloves_day", pack=22, a=45.65, b=47.58, t0=12, t1=18,
         crop=[(0, 690, 360, 720), (1, 730, 360, 720)], zoom=[(0, 1.0), (1, 1.05)],
         face=(780, 165, 40), look="day",
         role="preparation in daylight: black gloves on, eyes up to the lens"),
    dict(name="from_dark", pack=130, a=186.35, b=188.40, t0=18, t1=24,
         crop=[(0, 470, 360, 720), (1, 540, 360, 720)], zoom=[(0, 1.0), (0.7, 1.04), (1, 1.10)],
         face=(480, 160, 40), look="night",
         role="the build: walks out of darkness toward us; push-in accelerates into the drop",
         fx=["predrop_blink"]),
    # ---------------- DROP + MONTAGE (bars 35-39): the mask slips
    dict(name="unmask", pack=32, a=58.567, b=59.15, t0=24, t1=26,
         crop=[(0, 520, 360, 720), (1, 540, 360, 720)], zoom=[(0, 1.10), (1, 1.0)],
         face=(470, 190, 38), look="day",
         role="DROP: the face shield comes down over a blood-spattered suit — the other mask goes on",
         fx=["drop_flash", "drop_slices"]),
    dict(name="slide_face", pack=75, a=109.80, b=110.467, t0=26, t1=30,
         tmap=[(0.0, 109.80), (0.5, 110.467), (1.0, 110.467)],   # runs 1x, then freezes on pulse 28
         crop=[(0, 470, 360, 720), (1, 505, 360, 720)], zoom=[(0, 1.0), (1, 1.04)],
         face=(520, 240, 45), look="room",
         role="signature: the blood slide raised to his eye; frame freezes as evidence on pulse 28",
         fx=["slide_annotation", "glass_tink", "evidence_freeze"]),
    dict(name="container_walk", pack=10, a=23.70, b=24.37, t0=30, t1=32,
         crop=[(0, 455, 360, 720), (1, 420, 360, 720)], zoom=[(0, 1.0), (1, 1.02)],
         face=(500, 150, 20), look="day",
         role="the hunt: gloved, low angle, walking in"),
    dict(name="fence_stare", pack=119, a=171.098, b=171.765, t0=32, t1=34,
         crop=[(0, 450, 360, 720), (1, 525, 360, 720)], zoom=[(0, 1.0), (1, 1.03)],
         face=(480, 170, 28), look="night",
         role="the hunt: through the chain-link, eyes on the target"),
    dict(name="gloves_night", pack=67, a=102.15, b=102.82, t0=34, t1=36,
         crop=[(0, 610, 360, 720), (1, 610, 360, 720)], zoom=[(0, 1.0), (1, 1.04)],
         face=(580, 165, 30), look="night",
         role="ritual: gloving up at night"),
    dict(name="photo_wall", pack=59, a=92.70, b=93.70, t0=36, t1=39,
         crop=[(0, 560, 360, 720), (1, 600, 360, 720)], zoom=[(0, 1.0), (1, 1.03)],
         face=(610, 130, 26), look="room",
         role="the kill room: plastic and the victims' photos"),
    dict(name="victim_pov_slide", pack=88, a=128.30, b=128.95, t0=39, t1=41,
         crop=[(0, 480, 360, 720), (1, 480, 360, 720)], zoom=[(0, 1.08), (0.4, 1.0), (1, 1.0)],
         face=(520, 300, 50), look="room",
         role="the victim's view: the slide, upside down", fx=["punch"]),
    dict(name="knife", pack=110, a=158.30, b=158.63, t0=41, t1=42,
         crop=[(0, 520, 360, 720), (1, 520, 360, 720)], zoom=[(0, 1.0), (1, 1.0)],
         face=(540, 165, 28), look="room",
         role="escalation (half-unit): yellow gloves, the blade"),
    dict(name="masked", pack=60, a=95.00, b=95.33, t0=42, t1=43,
         crop=[(0, 525, 360, 720), (1, 525, 360, 720)], zoom=[(0, 1.0), (1, 1.0)],
         face=(600, 110, 25), look="night",
         role="escalation (half-unit): the other mask"),
    dict(name="hand_on_face", pack=46, a=76.30, b=76.97, t0=43, t1=45,
         crop=[(0, 560, 360, 720), (1, 600, 360, 720)], zoom=[(0, 1.0), (1, 1.03)],
         face=(580, 165, 28), look="room",
         role="the act: hand over the victim's face"),
    dict(name="gloved_hands", pack=47, a=78.00, b=79.00, t0=45, t1=48,
         crop=[(0, 430, 360, 720), (1, 470, 360, 720)], zoom=[(0, 1.0), (1, 1.04)],
         face=(480, 125, 26), look="room",
         role="the ritual: gloved hands over the plastic-wrapped table"),
    dict(name="rapture", pack=93, a=134.00, b=135.00, t0=48, t1=51,
         crop=[(0, 560, 360, 720), (1, 560, 345, 690)], zoom=[(0, 1.0), (1, 1.05)],
         face=(610, 185, 36), look="room",
         role="release: he looks up — the face of the hidden self"),
    dict(name="smile_reveal", pack=96, a=138.217, b=139.117, t0=51, t1=54,
         crop=[(0, 360, 360, 720), (1, 520, 360, 720)], zoom=[(0, 1.0), (1, 1.06)],
         face=(520, 200, 45), look="night",
         role="the slip completes: head lifts into the private smile", gamma=0.68, contrast=1.32),
    dict(name="shh", pack=62, a=96.42, b=97.10, t0=54, t1=("f", None),   # t1 = STOP_F
         crop=[(0, 505, 360, 720), (1, 500, 360, 720)], zoom=[(0, 1.0), (1, 1.06)],
         face=(540, 220, 35), look="day",
         role="'shh' — finger to lips on the last hit; the music obeys a beat later"),
    # ---------------- AFTER THE STOP: the mask goes back on (loops into the hook)
    dict(name="alibi_walk", pack=21, a=43.65, b=45.583, t0=("f", None), t1=("f", 1260),  # t0 = STOP_F
         crop=[(0, 480, 360, 720), (1, 540, 360, 720)], zoom=[(0, 1.0), (1, 1.06)],
         face=(522, 162, 20), look="room",
         role="'Check in…' — walks back into public life, checks his watch"),
    dict(name="alibi_smile", pack=36, a=63.767, b=64.50, t0=("f", 1260), t1=("f", DUR_FRAMES),
         crop=[(0, 560, 360, 720), (1, 560, 360, 720)], zoom=[(0, 1.0), (1, 1.04)],
         face=(545, 130, 40), look="day",
         role="'…establish an alibi.' — the public smile; flows straight into the hook on loop"),
]

# ---------------------------------------------------------------- variants
# EDIT_VARIANT=alt_open swaps the hook for a darker, forensic cold open (comparison cut).
VARIANT = os.environ.get("EDIT_VARIANT", "main")
if VARIANT == "alt_open":
    SHOTS[0] = dict(name="slide_coldopen", pack=126, a=179.98, b=180.95, t0=0, t1=4,
                    crop=[(0, 560, 360, 720), (1, 560, 360, 720)], zoom=[(0, 1.06), (1, 1.12)],
                    face=(560, 200, 40), look="room",
                    role="ALT HOOK: his eyes over a fresh blood slide — forensic cold open")

# fill frame-exact edges that depend on the measured stop
for s in SHOTS:
    if s["t1"] == ("f", None):
        s["t1"] = ("f", STOP_F)
    if s["t0"] == ("f", None):
        s["t0"] = ("f", STOP_F)

def frame_of(edge):
    return edge[1] if isinstance(edge, tuple) else fp(edge)

def timeline():
    out = []
    for s in SHOTS:
        out.append((frame_of(s["t0"]), frame_of(s["t1"]), s))
    return out

# ---------------------------------------------------------------- text & graphics
# subtitle lines: words appear on their spoken onsets; the accent word is set heavier
SUBS = [
    dict(words=["Check", "in."], t_out=tp(59) + 0.62, accent=[]),
    dict(words=["Establish", "an", "alibi."], t_out=DUR_FRAMES / FPS, accent=["alibi."]),
]
SUB_Y = 1180          # baseline-ish centre line (px) — above TikTok caption zone, below faces
SIGNATURE = dict(enabled=True, text="voidfx", t_in=tp(30) + 0.05, t_out=tp(34) - 0.02)
FREEZE_P = 28

if __name__ == "__main__":
    print(f"P={P:.5f}s  bar={6 * P:.4f}s  drop at {tp(DROP_P):.3f}s (frame {fp(DROP_P)})  stop at {STOP_T:.3f}s (frame {STOP_F})")
    prev = 0
    for f0, f1, s in timeline():
        assert f0 == prev, f"gap/overlap before {s['name']}: {prev} vs {f0}"
        speed = (s["b"] - s["a"]) / ((f1 - f0) / FPS)
        print(f"{s['name']:18s} #{s['pack']:3d} frames {f0:5d}-{f1:5d} ({(f1 - f0) / FPS:5.2f}s)  src {s['a']:.2f}-{s['b']:.2f}  speed {speed:.2f}x")
        prev = f1
    assert prev == DUR_FRAMES, prev
