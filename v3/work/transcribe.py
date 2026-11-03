import json, numpy as np, scipy.io.wavfile as wf
from faster_whisper import WhisperModel
sr, a = wf.read("v3/audio/doakes16k.wav"); a = a.astype(np.float32) / 32768
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs, _ = m.transcribe(a, word_timestamps=True, vad_filter=True, beam_size=5, language="en", condition_on_previous_text=False)
out = []
for s in segs:
    w = [(x.word.strip(), round(x.start, 2), round(x.end, 2), round(x.probability, 2)) for x in s.words]
    out.append(dict(t0=round(s.start, 2), t1=round(s.end, 2), text=s.text.strip(), words=w))
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
json.dump(out, open("v3/work/doakes_transcript.json", "w"), indent=1)
