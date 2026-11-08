"""Is he actually saying the line on screen? A lip sheet to look at before calling a line "lip-synced".

Usage:  python3 tools/lipcheck.py SRC.mp4 SPEECH_T0 SPEECH_T1 OUT.jpg [--pad 0.5] [--vocals STEM.wav --stem-t0 S]
        SPEECH_T0/T1: the line's spoken interval in SRC seconds (Whisper word times, ideally on the Demucs vocal stem)
        --vocals: the vocal stem to draw the speech level from (default: the SRC audio); --stem-t0: the stem's start in SRC s
Writes OUT.jpg: the face (top row) and a magnified mouth crop (bottom row) every ~0.1 s across the line +-pad, with the
speech level drawn under each crop (the yellow bar) and the speech interval marked in red. If the mouth doesn't open
and close with the yellow bars, the line is VOICE-OVER (inner monologue): don't present it as spoken on screen.
Background: Dexter's lines are often narration. v101 put the narrated confession over a shot where he isn't speaking
and the owner rejected it. Automatic mouth-motion scores were tried and disagreed with known cases, so judge by eye.
"""
import sys, os, subprocess
import numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "v7", "work"))
import facetrack as FT

src, s0, s1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
pad = float(sys.argv[sys.argv.index("--pad") + 1]) if "--pad" in sys.argv else 0.5
voc = sys.argv[sys.argv.index("--vocals") + 1] if "--vocals" in sys.argv else src
vt0 = float(sys.argv[sys.argv.index("--stem-t0") + 1]) if "--stem-t0" in sys.argv else 0.0
a, b = s0 - pad, s1 + pad
SR = 16000
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(max(0, a - vt0)), "-t", str(b - a), "-i", voc, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True).stdout
x = np.frombuffer(raw, np.float32); env = np.sqrt(np.convolve(x ** 2, np.ones(800) / 800, "same")) if len(x) else np.zeros(1)
ref = np.percentile(env, 98) + 1e-6
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS)
ts = np.arange(a, b, 0.1); faces, mouths = [], []; last = None
for t in ts:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps))); ok, fr = cap.read()
    f = FT.choose(FT.detect(fr), "largest", last) if ok else None
    if f is not None: last = f
    f = f or last
    if f is None: faces.append(np.zeros((150, 120, 3), np.uint8)); mouths.append(np.zeros((90, 120, 3), np.uint8)); continue
    fw, cx, cy = f["w"], f["cx"], f["cy"]
    def crop(x0, y0, x1, y1, size):
        x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(fr.shape[1], int(x1)), min(fr.shape[0], int(y1))
        return cv2.resize(fr[y0:y1, x0:x1], size, interpolation=cv2.INTER_CUBIC) if x1 > x0 and y1 > y0 else np.zeros(size[::-1] + (3,), np.uint8)
    fc = crop(cx - 0.6 * fw, cy - 0.75 * fw, cx + 0.6 * fw, cy + 0.75 * fw, (120, 150))
    (ex1, ey1, ex2, ey2) = f["eyes"]; mx, my = (ex1 + ex2) / 2, (ey1 + ey2) / 2; iod = max(8.0, ((ex1 - ex2) ** 2 + (ey1 - ey2) ** 2) ** 0.5)
    mc = crop(mx - 0.75 * iod, my + 0.75 * iod, mx + 0.75 * iod, my + 1.55 * iod, (120, 90))   # the lips, from the eye landmarks
    i = int((t - a) * SR); lv = float(env[min(len(env) - 1, max(0, i))] / ref) if len(env) > 1 else 0.0
    cv2.rectangle(mc, (0, 84), (int(119 * min(1, lv)), 89), (0, 230, 255), -1)
    col = (0, 0, 255) if s0 <= t <= s1 else (90, 90, 90)
    cv2.rectangle(fc, (0, 0), (119, 149), col, 2); cv2.putText(fc, f"{t:.1f}", (3, 14), 0, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
    faces.append(fc); mouths.append(mc)
cols = 12; tiles = []
for i in range(0, len(faces), cols):
    rf, rm = faces[i:i + cols], mouths[i:i + cols]
    while len(rf) < cols: rf.append(np.zeros_like(faces[0])); rm.append(np.zeros_like(mouths[0]))
    tiles.append(np.vstack([np.hstack(rf), np.hstack(rm)]))
cv2.imwrite(out, np.vstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 85])
print("wrote", out, f"({len(ts)} samples; red frames = the spoken interval, yellow bar = speech level)")
