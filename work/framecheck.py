"""Large vertical previews of each EDL shot (first / middle / last frame of the crop),
two shots per row. Usage: python3 work/framecheck.py [names...] -> frames/framecheck_XX.jpg"""
import cv2, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl
from cropcheck import crop_rect
cap = cv2.VideoCapture(edl.SRC)
names = sys.argv[1:]
shots = [s for s in edl.SHOTS if not names or s["name"] in names]
cells = []
for s in shots:
    trip = []
    for u in (0.0, 0.5, 1.0):
        t = s["a"] + (s["b"] - s["a"]) * u
        k = int(round(t * 60)) - (1 if u == 1.0 else 0)
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
        cx, cy, w, h = crop_rect(s, u)
        M = np.float32([[w / 270, 0, cx - w / 2], [0, h / 480, cy - h / 2]])
        v = cv2.warpAffine(f, M, (270, 480), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
        cv2.rectangle(v, (0, 0), (269, 479), (60, 60, 60), 1)
        # TikTok UI danger zones (scaled): bottom 300/1920, right 160/1080
        cv2.line(v, (0, 480 - 75), (269, 480 - 75), (0, 0, 255), 1)
        cv2.line(v, (270 - 40, 0), (270 - 40, 479), (0, 0, 255), 1)
        cv2.putText(v, f"{t:.2f}", (4, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
        trip.append(v)
    c = np.hstack(trip)
    lab = np.zeros((24, c.shape[1], 3), np.uint8)
    cv2.putText(lab, f"{s['name']} #{s['pack']}", (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(np.vstack([lab, c]))
rows = []
for i in range(0, len(cells), 2):
    pair = cells[i:i + 2]
    if len(pair) == 1: pair.append(np.zeros_like(pair[0]))
    rows.append(np.hstack([pair[0], np.full((pair[0].shape[0], 12, 3), 30, np.uint8), pair[1]]))
for i in range(0, len(rows), 4):
    cv2.imwrite(f"frames/framecheck_{i // 4:02d}.jpg", np.vstack(rows[i:i + 4]), [cv2.IMWRITE_JPEG_QUALITY, 82])
print("sheets:", (len(rows) + 3) // 4)
