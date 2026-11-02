"""Transcribe the non-silent parts of the scene pack audio with word timings (local model)."""
import sys, json
from faster_whisper import WhisperModel
model_name = sys.argv[1] if len(sys.argv) > 1 else "small.en"
import numpy as np, scipy.io.wavfile as wf
sr, a = wf.read("audio/pack_mono16k.wav"); a = a.astype(np.float32) / 32768
m = WhisperModel(model_name, device="cpu", compute_type="int8")
segs, info = m.transcribe(a, word_timestamps=True, vad_filter=True, beam_size=5,
                          condition_on_previous_text=False)
out = []
for s in segs:
    words = [dict(w=w.word, t0=round(w.start, 3), t1=round(w.end, 3), p=round(w.probability, 2)) for w in s.words]
    out.append(dict(t0=round(s.start, 3), t1=round(s.end, 3), text=s.text.strip(), nsp=round(s.no_speech_prob, 2), words=words))
    print(f"[{s.start:7.2f}-{s.end:7.2f}] (nsp {s.no_speech_prob:.2f}) {s.text.strip()}")
json.dump(out, open(f"work/transcript_{model_name}.json", "w"), indent=1)
