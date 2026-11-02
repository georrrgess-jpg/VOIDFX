"""Vertical framing check: mid-frame of each clip with the 9:16 window drawn on the source (cx from VX or c0/c1)."""
import os, sys, cv2, numpy as np
os.environ["ORIENT"] = "v"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl2 as E
cells = []
for c in E.CLIPS:
    if "src" not in c: continue
    P = E.PACKS[c["src"]]; cap = cv2.VideoCapture(P["path"])
    for u in (0.1, 0.9):
        t = c["tmap"][0][1] + (c["tmap"][-1][1] - c["tmap"][0][1]) * u
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * P["fps"])); ok, f = cap.read()
        vx = E.VX.get(c["name"]); cam = c["cam"]
        cx = (vx[0] + (vx[1] - vx[0]) * u) if vx else cam["c0"][0] + (cam["c1"][0] - cam["c0"][0]) * u
        z = cam["zoom"][0][1] + (cam["zoom"][-1][1] - cam["zoom"][0][1]) * u; z = 1 + (z - 1) * 0.45
        s = max(1080 / P["w"], 1920 / P["h"]) * z; hw = 540 / s; hh = 960 / s
        cy = cam["c0"][1]; cx = min(max(cx, hw), P["w"] - hw); cy = min(max(cy, hh), P["h"] - hh)
        x0, y0 = int(cx - hw), int(cy - hh)
        crop = cv2.resize(f[y0:int(cy + hh), x0:int(cx + hw)], (135, 240))
        cv2.putText(crop, c["name"][:14], (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        cv2.putText(crop, f"cx{int(cx)}", (2, 234), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        cells.append(crop)
while len(cells) % 16: cells.append(np.zeros_like(cells[0]))
cv2.imwrite(f"{E.ROOT}/v2/frames/vframe.jpg", np.vstack([np.hstack(cells[i:i + 16]) for i in range(0, len(cells), 16)]))
