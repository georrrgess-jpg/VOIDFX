# SURPRISE v4 — Doakes × Need It (voidfx, 9:16)

This revision of the v3 edit is built from your notes. It is 25.0 s at 1080×1920, 60 fps, and it loops.

## What changed and why

| Your note | What v4 does |
|---|---|
| Beginning is sloppy; BAY HARBOR BUTCHER sat under the captions | The cold open is rebuilt. The title is now set **behind Dexter's head** using person matting (MODNet): BUTCHER is red and behind his neck, BAY HARBOR is small and above him. Each word lands on Doakes's syllable, and the captions sit low and clear of it. |
| Don't label Doakes and Dexter | Name tags, speaker chips and the stamp are removed. |
| Dexter's lines are choppy, "stuck together with glue" | The first 4.3 s is **one continuous take** of the scene's audio. The shots change underneath it: Doakes, Dexter listening, then Dexter answering. "What can I say?" comes in as a J-cut under a Doakes reaction shot. The 24p night footage is optical-flow smoothed to 60 fps, the cuts are dissolves, and every audio join has a 40 ms equal-power fade. |
| Text animation not appealing | Every word now eases in: fade, a 22 px rise and blur-to-sharp over 9 frames. Lines re-centre smoothly as words arrive and fade upward on exit. Each lyric moment has its own smooth move: mask-rise, tracking-resolve, light-sweep reveal, fly-in from the camera. Nothing just pops on. |
| TARGET ACQUIRED / I NEED IT felt shoved together | It is now one continuous move. The camera pushes into Doakes's barrel, flies through into black, and comes out in a **rifle-scope view of Dexter**. The scope sways, tightens and drains to grey through the bass gap with accelerating lock-on beeps, then cuts to the real gunshot. |
| More pronounced transitions | Every montage cut now has a stronger, designed move (listed below), each with its own sound. |
| The loop didn't work because of the outro | The outro logo is removed. The edit ends by **flying into Dexter's pupil to black** and starts by **irising out of black onto Doakes**, so the wrap lands black-to-black. The audio at the seam is matched: an inhale at the start, a suck at the end, both about −44 dBFS at the join. |
| No constant watermark | The watermark is gone. The voidfx logo appears **once**, as a transition: it slams in over the fight shot, a sheen runs across the metal, and the camera **flies through the "o"** into the next shot. |
| Feel like you're going *through* something | There are fly-through transitions throughout: into the gun barrel, into the scope, through shattered glass, into his shadow, into his eye, through the voidfx "o", into a photo on the kill-room wall, and finally into his pupil. |

## Timeline

| Time | Section |
|---|---|
| 0.00–6.60 | Iris opens on Doakes. One continuous exchange: *"Jesus fucking Christ, you're the Bay Harbor Butcher."* → *"I really hate that name."* → Doakes reaction → *"What can I say? You were right about me."* Then a white flash. |
| 6.60–11.06 | *"I said I need it…"*: Doakes's gun, then push into the barrel, then scope view of Dexter (*"undefeated"*), then drain and lock-on, then the barrel of the real gun. |
| 11.06 | Drop: muzzle flash, cracked glass, shatter. |
| 11.06–22.31 | Montage, one transition per beat: shatter → dark pass → eye portal → 3D roll → flash cuts → **voidfx "o" fly-through** → cube → **through the photo** → polaroid flick → face-lock burst → zoom-through with echo → datamosh → split slam |
| 22.31 | Freeze on *"…can't get caught up"*, then tape-stop. |
| 22.62–25.00 | Doakes: *"I always knew there was something with you."* Then into the pupil, then black, then the loop. |

## Review passes (on the encoded upload file)

| Pass | Result |
|---|---|
| Format | 1080×1920, 60 fps CFR, 1,500 frames, 25.000 s; full decode with no errors |
| Loudness | −13.2 LUFS, true peak −2.8 dBTP |
| Face centering | all 25 shots pass. The 5 flagged frames are deliberate (the pan to the photo wall, the split slam) or a false detection on Doakes's gun hand. |
| Text over faces | 1 frame, a false detection on Doakes's hand during the iris |
| Cuts | 18 of 25 re-detected; the 7 hidden ones are inside the dissolves and fly-through transitions on purpose |
| Frozen / black | no frozen runs; black only at the loop seam (iris start, pupil end) and inside the barrel fly-through |
| Audio | no clicks at any dialogue join, the song entry, the stop or the loop seam |
| Loop seam | last frame vs first frame differ by 1.8 luma levels (both black); audio is −45.4 / −44.9 dBFS on either side |


## Revision 5

- **BLEED IT:** the old version was 14 frames over a dark shot and couldn't be read. It now builds across the end of the scope shot:
  - a white outline draws in on *"then I"*;
  - on *"bleed"* the letters fill with glossy blood from the top, with a wavy liquid front;
  - drips run down from the letter bottoms, over a dark vignette;
  - the finished title is baked into the muzzle-flash frame, so it **cracks and shatters with the glass** on the drop;
  - sound: a wet fill and three drips.
- **"What can I say" cut:** the hard cut to a Doakes reaction is replaced by a **matched-angle morph**. Both shots are the same camera angle on Dexter, so optical flow warps one into the other under a light bloom and a soft reversed swell. Dialogue stays lip-synced.
- **BAY HARBOR BUTCHER:** the text no longer sits around Dexter. It is now **footage-in-letters knockout type**:
  - the frame darkens and the three words slam in on Doakes's syllables, stacked full-width;
  - Dexter is seen *through* the letterforms, with BUTCHER tinted blood red;
  - on exit the letters fly apart toward the camera and the picture fills back in;
  - each word has a deep thud.
- **New transition, knife slash:** a blade glint sweeps diagonally across the frame with a metallic "shing". The frame splits along the cut, and the two halves slide apart with red-lit edges to reveal the next shot. It replaces the cube turn.
- **Loop audio is now continuous:**
  - the scene's own room tone fades in under the last 0.58 s, matching what plays at 0:00;
  - the drone runs at the same level on both sides;
  - the timeline is built circularly: the last 2,048 samples crossfade into the actual lead-in of the first frame;
  - the AAC encoder pre-roll is the loop's own tail;
  - the mix is mastered (limiter and resampler) on a circularly padded copy and then trimmed, so neither end starts "cold";
  - result on the final MP4: the level stays about −25 to −30 dBFS across the wrap, the sample step at the wrap is in the normal range (no click), and audio and video are both exactly 25.000 s and sample-aligned.

## Files

- `out/surprise_v4_voidfx_9x16.mp4`: upload version.
- `out/surprise_v4_voidfx_9x16_master.mov`: master.
- `work/edl4.py`: every decision.
- `work/render4.py`: picture (face tracking and person matting).
- `work/audio4.py`: sound.
- `work/qc4.py`: automated review passes.

### Re-render

```bash
python3 v4/work/render4.py prep
python3 v4/work/audio4.py
python3 v4/work/render4.py video v4/out
python3 v4/work/qc4.py v4/out/surprise_v4_voidfx_9x16.mp4
```

The MODNet portrait-matting model (`v3/models/modnet/onnx/model.onnx`) and the YuNet face detector are downloaded from Hugging Face. The models are not committed.

## Limitations

- **I can't watch or listen.** Everything was checked frame by frame and by measurement. Watch once at normal speed with sound.
- **Sources are 720p**, so the 9:16 crops are upscaled.
- **The datamosh is meant to look messy.** It smears pixels on purpose.
- **Explicit language.** The lyrics and dialogue are explicit.
