"""Detail strips: N evenly spaced frames per shot, labelled with source time.

Usage: python3 work/strips.py OUTNAME N shot_id [shot_id ...]
"""
import cv2, json, sys, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
info = json.load(open("work/shots.json")); shots = {s["id"]: s for s in info["shots"]}; fps = info["fps"]
out, N, ids = sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:]]
cap = cv2.VideoCapture("src/scenepack.mp4")
TW, TH = 240, 144
rows = []
for i in ids:
    s = shots[i]; thumbs = []
    for j in range(N):
        k = int(round(s["start"] + 1 + j * (s["end"] - s["start"] - 2) / (N - 1)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
        t = cv2.resize(f, (TW, TH), interpolation=cv2.INTER_AREA)
        cv2.putText(t, f"{k / fps:.2f}", (3, TH - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
        if j == 0:
            cv2.putText(t, f"#{i}", (3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        thumbs.append(t)
    rows.append(np.hstack(thumbs))
cv2.imwrite(f"frames/{out}.jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
