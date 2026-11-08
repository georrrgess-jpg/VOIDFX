"""Lyric recognition (the v103 standard): every sung word in a song window, with its time, ready for word-timed captions.

Usage:  python3 tools/lyrics.py vN SONG START END ["published lyrics, one line per | or newline"] [--model large-v3]
        e.g. python3 tools/lyrics.py v103 src/everlong.mp3 209.5 219.0 "And I wonder | If everything could ever feel this real forever"

1. Demucs (htdemucs) separates the song once -> vN/audio/sep/htdemucs/<song>/vocals.wav (cached; about 2 min on CPU).
2. faster-whisper transcribes the vocal stem inside the window, with word timestamps.
3. If the published lyrics are given (always give them: Whisper mishears sung words, e.g. "you'd ever feel is real" for
   "could ever feel this real"), they are aligned onto Whisper's words. Matched words take Whisper's times, mishears are
   replaced by the published word at the same time, and words Whisper missed are placed between their neighbours and
   marked CHECK.
4. Each word's loudness on the vocal stem is measured. Words more than 18 dB under the window's loudest are marked QUIET:
   don't caption them (v103 rev 2: text only on clearly sung words; whispers don't count).

Writes vN/work/lyrics.json and prints a TEXT block for the EDL. Times are SONG seconds; the EDL converts them with
sw(t) = s2e(t), so the captions stay right across splices.
"""
import sys, os, re, json, difflib, subprocess, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
ver, song, t0, t1 = args[0], args[1], float(args[2]), float(args[3])
lyr = args[4] if len(args) > 4 else ""
model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "large-v3"
song = song if os.path.isabs(song) else f"{ROOT}/{song}"
name = os.path.splitext(os.path.basename(song))[0]
sep = f"{ROOT}/{ver}/audio/sep"; stem = f"{sep}/htdemucs/{name}/vocals.wav"
os.makedirs(f"{ROOT}/{ver}/work", exist_ok=True)

if not os.path.exists(stem):                                                            # 1. separate once
    print(f"demucs: separating {name} (cached afterwards) ...", flush=True)
    subprocess.run([sys.executable, "-m", "demucs", "-n", "htdemucs", "-o", sep, song], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

pad = 0.6                                                                                 # 2. transcribe the vocal stem in the window
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(max(0, t0 - pad)), "-i", stem, "-t", str(t1 - t0 + 2 * pad),
                      "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.float32).copy(); base = max(0, t0 - pad)
from faster_whisper import WhisperModel
m = WhisperModel(model_name, device="cpu", compute_type="int8")
segs, _ = m.transcribe(a, word_timestamps=True, vad_filter=False, beam_size=5, language="en", condition_on_previous_text=False,
                       initial_prompt=(lyr.replace("|", " ") if lyr else None))
heard = []
for s in segs:
    for w in s.words:
        tw = re.sub(r"[^\w']", "", w.word).strip()
        if tw and t0 - 0.2 <= base + w.start <= t1: heard.append(dict(w=tw, s=round(base + w.start, 3), e=round(base + w.end, 3), p=round(w.probability, 2)))

sr = 16000; hop = 160                                                                     # 10 ms loudness envelope of the vocal stem
env = 20 * np.log10(np.sqrt(np.convolve(a ** 2, np.ones(400) / 400, "same")[::hop]) + 1e-9)
def env_at(t): return env[min(len(env) - 1, max(0, int((t - base) * sr / hop)))]
for h in heard:                                                                           # snap each start to the real onset
    i0, i1 = int((h["s"] - base) * sr / hop), max(int((h["e"] - base) * sr / hop), int((h["s"] - base) * sr / hop) + 2)
    seg = env[max(0, i0):min(len(env), i1)]
    if len(seg) > 2:
        k = int(np.argmax(seg > seg.max() - 10)); on = round(base + (max(0, i0) + k) * hop / sr, 3)
        if on > h["s"] + 0.03: h["s"] = min(on, round(h["e"] - 0.05, 3))

def norm(x): return re.sub(r"[^a-z0-9]", "", x.lower())
words = []                                                                                # 3. align the published lyrics
if lyr:
    lines = [l.strip() for l in re.split(r"\||\n", lyr) if l.strip()]
    pub = [(re.sub(r"[^\w'?!.,-]", "", w), li) for li, l in enumerate(lines) for w in l.split()]
    sm = difflib.SequenceMatcher(a=[norm(h["w"]) for h in heard], b=[norm(w) for w, _ in pub], autojunk=False)
    got = {}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(j2 - j1): got[j1 + k] = (heard[i1 + k], "")
        elif op == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(j2 - j1): got[j1 + k] = (heard[i1 + k], f"heard '{heard[i1 + k]['w']}'")
        elif op == "replace":                                                             # uneven: spread the heard span over the words
            hs, he = heard[i1]["s"], heard[i2 - 1]["e"]
            for k in range(j2 - j1):
                q0 = hs + (he - hs) * k / (j2 - j1); got[j1 + k] = (dict(w="", s=round(q0, 3), e=round(q0 + (he - hs) / (j2 - j1), 3), p=0.0), "CHECK (respaced)")
    for j, (w, li) in enumerate(pub):
        if j in got: h, note = got[j]; words.append(dict(word=w.upper(), line=li, s=h["s"], e=h["e"], p=h["p"], note=note)); continue
        words.append(dict(word=w.upper(), line=li, s=None, e=None, p=0.0, note="CHECK (not heard)"))
    j = 0
    while j < len(words):                                                                 # spread each run of unheard words across its gap
        if words[j]["s"] is not None: j += 1; continue
        k = j
        while k < len(words) and words[k]["s"] is None: k += 1
        prv = words[j - 1] if j > 0 else None; nxt = words[k] if k < len(words) else None
        lo = prv["e"] if prv else (nxt["s"] - 0.3 * (k - j) if nxt else t0); hi = nxt["s"] if nxt else lo + 0.3 * (k - j)
        step = (hi - lo) / (k - j)
        for q in range(j, k): words[q]["s"], words[q]["e"] = round(lo + step * (q - j), 3), round(lo + step * (q - j + 0.9), 3)
        j = k
else:
    words = [dict(word=h["w"].upper(), line=0, s=h["s"], e=h["e"], p=h["p"], note="no lyrics given: CHECK against the published lyrics") for h in heard]

def db_at(s, e):
    i, j = int((s - base) * sr), max(int((e - base) * sr), int((s - base) * sr) + 160)
    seg = a[max(0, i):min(len(a), j)]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else -120.0
for w in words: w["db"] = round(float(db_at(w["s"], w["e"])), 1)
top = max([w["db"] for w in words] or [0])
for w in words:
    if w["db"] < top - 18: w["note"] = (w["note"] + "; " if w["note"] else "") + "QUIET: don't caption"

print(f"\n{name} {t0:.2f}-{t1:.2f} s, vocal stem {stem}\n  {'word':14s} {'song s':>8s} {'end':>7s} {'prob':>5s} {'dB':>6s}  note")
for w in words: print(f"  {w['word']:14s} {w['s']:8.2f} {w['e']:7.2f} {w['p']:5.2f} {w['db']:6.1f}  {w['note']}")
if lyr:
    print("\nEDL TEXT block (word times in song seconds through sw(); pick the emphasis words, set 'end' and the band):")
    for li in sorted(set(w["line"] for w in words)):
        ws = [w for w in words if w["line"] == li and "QUIET" not in w["note"] and "not heard" not in w["note"]]
        out_ = [w["word"] for w in words if w["line"] == li and ("QUIET" in w["note"] or "not heard" in w["note"])]
        if out_: print(f'    # left out (not clearly sung on the vocal stem; verify by ear before captioning): {" ".join(out_)}')
        if not ws: continue
        cut = len(ws)
        if len(ws) > 3:
            tot = sum(len(w["word"]) for w in ws); acc = 0
            for q, w in enumerate(ws):
                acc += len(w["word"])
                if acc >= tot * 0.55: cut = q + 1; break
        body = ", ".join(f'("{w["word"]}", sw({w["s"]:.2f}), {0 if q < cut else 1})' for q, w in enumerate(ws))
        print(f'    dict(style="cap", words=[{body}], end=sw({ws[-1]["e"]:.2f}) + 0.30, emph=[], band=(1330, 1545)),')
json.dump(dict(song=song, start=t0, end=t1, stem=stem, words=words, heard=heard), open(f"{ROOT}/{ver}/work/lyrics.json", "w"), indent=1)
print(f"\nwrote {ver}/work/lyrics.json")
