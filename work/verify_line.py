"""Cross-check the candidate dialogue bursts with a larger local model."""
import json, numpy as np, scipy.io.wavfile as wf
from faster_whisper import WhisperModel
sr, a = wf.read("audio/pack_mono16k.wav"); a = a.astype(np.float32) / 32768
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
out = []
for t0, t1 in [(43.2, 46.0), (49.8, 51.7), (56.8, 58.9), (20.4, 24.0), (25.5, 28.3), (5.2, 8.9), (137.9, 139.3)]:
    seg = a[int(t0 * sr):int(t1 * sr)]
    res, _ = m.transcribe(seg, word_timestamps=True, vad_filter=False, beam_size=5, language="en", condition_on_previous_text=False)
    for s in res:
        w = [(x.word.strip(), round(x.start + t0, 2), round(x.end + t0, 2), round(x.probability, 2)) for x in s.words]
        out.append(dict(win=[t0, t1], text=s.text.strip(), nsp=round(s.no_speech_prob, 2), words=w))
        print(f"{t0:6.2f}-{t1:6.2f} | nsp {s.no_speech_prob:.2f} | {s.text.strip()} | {w}", flush=True)
json.dump(out, open("work/transcript_large_v3.json", "w"), indent=1)
