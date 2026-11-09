# v14 — KEEPSAKES (The Flash × C418 "Mice on Venus"), 9:16

**The brief (the owner):** a nostalgic Flash edit on the attached song, using its best and most popular part to carry the
feeling; transitions; few, quiet sound effects so the song isn't overshadowed; a cool overlay that isn't overbearing, so
the clips stay clear; high quality, with custom graphics, animations and transitions.

**The first edit made start to finish on the efficiency update's loop** (`song:` → EDL → `plan` → `prep` → stills on
the render server → `rev`/`ship` → the fresh-eyes critique). Rounds and renders are logged in `work/metrics.json`.

## Concept: KEEPSAKES
Nostalgia as a box of instant photos. Barry, now (S5, golden window light), looks back, and the years develop in front of
him like instant prints: waking from the coma, the CSI lab, the first suit in the sun, laughing in S.T.A.R. Labs, Iris
by the water, the loft, the sea run at sunset, then the family ballgame, laughing in the S5 suit, the tux, and today.
- **The hero object is the print** (cream card, thick bottom border, paper grain, gloss, a soft shadow). It is a motif in
  three places: the signature, THE ALBUM, and the loop (v13 rule 1).
- **Real phenomenon:** instant-film development. The image rises out of the milky reagent, cool and flat first, then warm
  and full.

## The song
- **Window:** song 196.56 → 222.48 s (h728 → h824, 25.92 s). It has three parts:
  - the build;
  - the quiet pause (single piano notes on e30, e34, e38 and e42);
  - the full theme returning at e46 (song 208.97 s), the part people remember.
- **Grid:** no drums in this stretch, so it was fitted on the music stem. P = 0.26997 s, offset 0.0100 s, checked against the piano onsets.
- **Loop wrap:** music spectral correlation 0.906, the best of the candidate windows.

## Structure (edit half-beat e = 0.27 s)
| e | Shot | In |
|---|---|---|
| 0–10 | NOW: S5 Barry in golden window light; **the signature print** rises beside him, develops, and we fall into it | the loop |
| 10–14 | wake (S1: waking from the coma) | PRINT DIVE |
| 14–20 | lab (S1 CSI lab) | DOUBLE EXPOSURE |
| 20–26 | hood (the first suit, gold backlight) | SUN FLARE (the lab window's light) |
| 26–30 | laugh (S1 suit, laughing) | FILM BURN |
| 30–46 | **THE ALBUM** (focal set piece; see below) | SHUTTER FREEZE |
| 46–52 | the sea run at sunset (S1) | ALBUM OUT (out of the last print, as the theme returns) |
| 52–58 | shore: the Flash walks out of the water | RIPPLE |
| 58–62 | the S1 emblem | FOCUS RACK |
| 62–68 | S3 Barry smiling | **EMBLEM GLINT** (the emblem transition) |
| 68–74 | the ballgame (S5) | SPEED WHIP |
| 74–80 | laughing in the S5 suit | LIGHT LEAK |
| 80–86 | the tux | dolly |
| 86–96 | today; **the loop**: the frame becomes a print and slides away over frame 0 | MEMORY ECHO |

**THE ALBUM**, in the song's pause:
1. On the first note, a soft shutter flash: the laugh freezes and shrinks into a print. The room behind goes to warm bokeh.
2. On each of the next three notes a print lands, with a little bounce, and develops: Iris and Barry by the water (S1), the loft (S3), and the sea at sunset.
3. On the pickup (e44) the camera falls into the last print, and the theme returns full-frame on the sea run.

The freeze starts exactly on the laugh's last frame, and the dive ends exactly on the sea run's first frame.

**EMBLEM GLINT:** the camera finds the S1 emblem. A glint runs down its own gold bolt (the bolt's pixels, found in the
frame) and the bolt lights up. The emblem's light blooms, and the next memory grows out of the emblem (v13 rule 2).

## Look: SUNFADE under a SUPER 8 HAZE
- **The grade:** golden hour on faded film:
  - lifted warm blacks, cream-gold highlights, a warm cast through the mids;
  - lowered saturation, with blues fading most (the S1 to S5 footage sits in one look);
  - skin protected.
- **The overlay, kept low:**
  - fine grain;
  - a sub-pixel gate weave (whole sine cycles over the edit, so the wrap has no step);
  - halation round the highlights;
  - two slow warm light leaks at the frame edges, away from faces;
  - a faint exposure flicker;
  - a few dust specks and the occasional hair, kept off the face.
- **Designed beats:** the light breathes on the piano's strong notes after the return, and the camera breathes 0.6 % with it. There is no sound on any of them.
- **Text:** none.

## Sound
The song, straight and circular: the pre-roll crossfades into the end, it is mastered on a wrapped copy, and it is
measured after AAC. **Four quiet effects in all**, each 12–15 dB under the music:
- a paper slide into the signature print;
- a soft shutter click when the memory freezes;
- an air rise into the theme's return;
- a paper slide as the loop's print leaves.

There is no sound on beats or small transitions.

## Measured (rev 1, the first delivery, on the encoded MP4)
- **QC:** ship checkpoint 11/11 PASS.
- **Loudness:** −13.9 LUFS, true peak −4.6 dBTP after AAC.
- **Loop seam:** blurred difference 0.18 (gate ≤ 1); audio seam step 0.040; picture wrap step 0.61 against a local median of 2.62.
- **Motion audit:** no dead spans, no judder, 1 pop (a cut), no unexplained pops. 0 flashes, 0 white-outs.
- **Faces vs effects:** 21 flags in 5 runs, all designed. 4 are in THE ALBUM, where the prints land over the blurred face behind them; 1 is the loop's print forming (1512–1516).
- **Sharpness:** SOFT flags on two shots.
  - **album:** its background is defocused by design; the prints themselves are sharp.
  - **emblem:** 0.90× the median. It is the S1 pack at 1.1 Mb/s, pushed in 1.3× for the glint.
  - Every source frame was restored (`sr_prep`, 498 frames).
- **Plan check:** 0 FAIL, 1 WARN (the album is the laugh shot frozen; by design).
- **Sound:** 4 placed effects, 12–15 dB under the music.

## How it was made (the efficiency pilot)
- **Song to delivery:** about 1 h 30 min. This includes:
  - song prep (2 min);
  - restoring 498 source frames (about 25 min, in the background);
  - 14 still sheets on the render server (3 min in all).
- **Renders before delivery:** 2 full and 1 partial (the change-tracked partial: 22 frames re-rendered and 30 verified bit-exact, 174 s against about 350 s for a full render). QC ran 3 times, 10 min in all.
- **Caught before delivery:**
  - **The studio's own sign-off review:** the film burn's rim and ragged edge on his face, the sun flare's 3-frame crossfade (a pop at 326), the memory echo's double faces.
  - **The fresh-eyes critique** (`studio/CRITIQUE_PROMPT.md`):
    - the overlay was invisible at phone size; it is now coarser grain, readable dust, stronger edge leaks and a Super 8 gate;
    - the theme's return was blurry, unframed water; the sea run and shore are now reframed on him;
    - the loop repeated the freeze; it is now a print that drops away;
    - the emblem's disc read as a dark hole, close to the rejected emblem_horizon; it now fills with gold and opens on his lit face;
    - the album prints were small and stayed milky too long;
    - the two laughing-in-suit shots looked alike; the S5 laugh became the S3 sunglasses shot;
    - the whip had a scan-line streak and mirrored edges;
    - the signature print had a faint grey rectangle as it arrived.
