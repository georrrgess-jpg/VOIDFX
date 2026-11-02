"""Transcribe each non-silent burst separately (no VAD) with word timings."""
import sys, json, numpy as np, scipy.io.wavfile as wf
from faster_whisper import WhisperModel
model_name = sys.argv[1] if len(sys.argv) > 1 else "medium.en"
sr, a = wf.read("audio/pack_mono16k.wav"); a = a.astype(np.float32) / 32768
hop = sr // 20
rms = np.array([np.sqrt(np.mean(a[i:i+hop]**2) + 1e-12) for i in range(0, len(a) - hop, hop)])
on = 20 * np.log10(rms) > -55
segs = []; k = 0
while k < len(on):
    if on[k]:
        j = k
        while j < len(on) and (on[j] or (j + 6 < len(on) and on[j:j+6].any())): j += 1
        segs.append((k * hop / sr, j * hop / sr)); k = j
    else: k += 1
print("bursts:", [(round(x, 2), round(y, 2)) for x, y in segs])
m = WhisperModel(model_name, device="cpu", compute_type="int8")
out = []
for t0, t1 in segs:
    s0 = max(0, int((t0 - 0.3) * sr)); s1 = min(len(a), int((t1 + 0.3) * sr))
    res, _ = m.transcribe(a[s0:s1], word_timestamps=True, vad_filter=False, beam_size=5, language="en",
                          condition_on_previous_text=False)
    for s in res:
        words = [dict(w=w.word, t0=round(w.start + s0 / sr, 3), t1=round(w.end + s0 / sr, 3), p=round(w.probability, 2)) for w in s.words]
        out.append(dict(burst=[round(t0, 2), round(t1, 2)], text=s.text.strip(), nsp=round(s.no_speech_prob, 2), words=words))
        print(f"burst {t0:6.2f}-{t1:6.2f} | nsp {s.no_speech_prob:.2f} | {s.text.strip()}")
        print("    " + " ".join(f"{w['w'].strip()}@{w['t0']:.2f}({w['p']})" for w in words))
json.dump(out, open(f"work/transcript_segs_{model_name}.json", "w"), indent=1)
