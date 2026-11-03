"""Word-timed transcript of a song or a scene pack (faster-whisper large-v3, CPU int8).

Usage:  python3 tools/transcribe.py vN NAME MEDIA [--vad] [--start S --dur D]
Writes: vN/work/tr_NAME.json  [{t0, t1, text, words: [(word, start, end, prob)]}]  (times in MEDIA seconds)
Tip: for dialogue under a score, transcribe the Demucs vocal stem; "--vad" for packs, not for songs.
"""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel

ver, name, media = sys.argv[1], sys.argv[2], sys.argv[3]
st = float(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 0.0
du = ["-t", sys.argv[sys.argv.index("--dur") + 1]] if "--dur" in sys.argv else []
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(st), "-i", media, *du, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.float32).copy()
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs, _ = m.transcribe(a, word_timestamps=True, vad_filter="--vad" in sys.argv, beam_size=5, language="en", condition_on_previous_text=False)
out = []
for s in segs:
    w = [(x.word.strip(), round(st + x.start, 2), round(st + x.end, 2), round(x.probability, 2)) for x in s.words]
    out.append(dict(t0=round(st + s.start, 2), t1=round(st + s.end, 2), text=s.text.strip(), words=w))
    print(f"[{st + s.start:7.2f}-{st + s.end:7.2f}] {s.text.strip()}\n   " + " ".join(f"{x[0]}@{x[1]:.2f}" for x in w), flush=True)
json.dump(out, open(f"/home/user/VOIDFX/{ver}/work/tr_{name}.json", "w"), indent=1)
