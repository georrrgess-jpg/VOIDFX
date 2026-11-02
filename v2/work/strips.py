"""Frame strips: python3 v2/work/strips.py OUT N pack:shot [pack:shot ...]   (pack = p1|p2|p3)"""
import cv2, json, sys, os, numpy as np
ROOT = "/home/user/VOIDFX"; os.chdir(ROOT)
SRC = {"p1": ("src/scenepack.mp4", "work/shots.json"), "p2": ("src/scenepack2_60fps.mp4", "v2/work/shots_p2.json"),
       "p3": ("src/scenepack3_24fps.mp4", "v2/work/shots_p3.json")}
out, N = sys.argv[1], int(sys.argv[2]); rows = []
for item in sys.argv[3:]:
    p, i = item.split(":"); i = int(i)
    info = json.load(open(SRC[p][1])); s = info["shots"][i]; fps = info["fps"]
    cap = cv2.VideoCapture(SRC[p][0]); th = []
    for j in range(N):
        k = int(round(s["start"] + 1 + j * (s["end"] - s["start"] - 2) / (N - 1)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
        t = cv2.resize(f, (224, 126), interpolation=cv2.INTER_AREA)
        cv2.putText(t, f"{k / fps:.2f}", (3, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
        if j == 0: cv2.putText(t, item, (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        th.append(t)
    rows.append(np.hstack(th))
cv2.imwrite(f"v2/frames/{out}.jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
