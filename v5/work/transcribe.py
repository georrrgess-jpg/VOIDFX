import json, sys, numpy as np, scipy.io.wavfile as wf
from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
for name, path, vad in (("song", "v5/audio/song16.wav", False), ("pack_b", "v5/audio/pack_b.wav", True), ("pack_a", "v5/audio/pack_a.wav", True)):
    sr, a = wf.read(path); a = a.astype(np.float32) / 32768
    if name == "song": a = a[: sr * 120]
    segs, _ = m.transcribe(a, word_timestamps=True, vad_filter=vad, beam_size=5, language="en", condition_on_previous_text=False)
    out = []
    for s in segs:
        w = [(x.word.strip(), round(x.start, 2), round(x.end, 2), round(x.probability, 2)) for x in s.words]
        out.append(dict(t0=round(s.start, 2), t1=round(s.end, 2), text=s.text.strip(), words=w))
        print(f"{name} [{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
    json.dump(out, open(f"v5/work/tr_{name}.json", "w"), indent=1)
