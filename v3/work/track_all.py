import json, sys, cv2, numpy as np
sys.path.insert(0, "v3/work"); import facetrack as FT
S = {"dk": "src/doakes.mp4", "p4": "src/pack4_aesthetic.mp4", "p5": "src/pack5_mixtape120.mp4", "p1": "src/scenepack.mp4",
     "p2": "src/scenepack2_60fps.mp4", "p3": "src/scenepack3_24fps.mp4"}
C = [("dk6","dk",16.40,19.00,"largest"),("dk7","dk",19.10,20.65,"largest"),("dk11","dk",27.25,29.40,"largest"),
     ("dk13","dk",32.17,34.30,"largest"),("dk15","dk",45.82,48.10,"largest"),("dk21","dk",66.70,68.00,"largest"),
     ("dk14","dk",34.35,45.75,"largest"),("dk33","dk",95.80,96.33,"largest"),
     ("p4_1","p4",12.17,14.75,"largest"),("p4_2","p4",14.83,16.27,"largest"),("p4_3","p4",16.35,18.14,"largest"),
     ("p4_7","p4",24.46,25.63,"largest"),("p4_13","p4",30.33,32.60,"largest"),("p4_16","p4",38.92,45.34,"largest"),
     ("p4_18","p4",48.10,50.44,"largest"),("p4_21","p4",56.49,58.14,"largest"),("p4_22","p4",58.22,59.07,"largest"),
     ("p4_23","p4",59.15,60.80,"largest"),("p4_27","p4",65.71,67.22,"left"),("p4_30","p4",70.61,73.47,"largest"),
     ("p5_5","p5",16.12,19.23,"largest"),("p5_7","p5",24.82,26.63,"largest"),("p5_10","p5",30.95,34.66,"largest"),
     ("p5_12","p5",35.89,39.66,"largest"),("p5_15","p5",41.12,42.66,"largest"),("p5_18","p5",49.05,51.16,"largest"),
     ("p5_20","p5",51.60,54.56,"largest"),("p5_22","p5",56.67,61.36,"largest"),
     ("p1_gun","p1",63.80,65.60,"largest"),("p3_hood","p3",23.00,25.70,"largest"),("p3_jungle","p3",25.80,26.85,"largest")]
out = {}
for name, pk, a, b, pick in C:
    r = FT.track(S[pk], a, b, pick, step=2)
    out[name] = dict(src=pk, t0=a, t1=b, det=r)
    print(f"{name:10s} {len(r):4d} det  cx~{np.median([x['cx'] for x in r]) if r else -1:.0f} w~{np.median([x['w'] for x in r]) if r else -1:.0f}", flush=True)
json.dump(out, open("v3/work/tracks.json", "w"))
# sheet: 9:16 crop (h=720, w=405) centred on smoothed face cx at u=0.1,0.5,0.9
cells = []
for name, pk, a, b, pick in C:
    d = out[name]; ts, cx, cy, fw, cov = FT.smooth_track(d["det"], a, b, fallback=(640, 300, 200))
    cap = cv2.VideoCapture(S[pk]); fps = cap.get(5); W0 = int(cap.get(3)); H0 = int(cap.get(4))
    for u in (0.1, 0.5, 0.9):
        t = a + (b - a) * u; cap.set(1, int(t * fps)); ok, f = cap.read()
        x = float(np.interp(t, ts, cx)); cw = H0 * 9 / 16; x0 = int(min(max(x - cw / 2, 0), W0 - cw))
        cr = cv2.resize(f[:, x0:x0 + int(cw)], (135, 240))
        for r in d["det"]:
            if abs(r["t"] - t) < 0.05:
                X = (r["cx"] - x0) * 135 / cw; Y = r["cy"] * 240 / H0; R = r["w"] * 135 / cw / 2
                cv2.rectangle(cr, (int(X - R), int(Y - R)), (int(X + R), int(Y + R)), (0, 255, 0), 1); break
        cv2.putText(cr, name, (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        cells.append(cr)
while len(cells) % 15: cells.append(np.zeros_like(cells[0]))
cv2.imwrite("v3/frames/track_sheet.jpg", np.vstack([np.hstack(cells[i:i + 15]) for i in range(0, len(cells), 15)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
