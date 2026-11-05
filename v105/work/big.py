"""big stills for review: python3 big.py NAME COLS f1 f2 ... (each frame at 432x768, parallel)."""
import sys, json, cv2, numpy as np
from multiprocessing import Pool
name, cols, frames = sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:]]
sys.argv = [sys.argv[0], "stills"]
import render105 as R
R.load(); R.init_hits()
R.RAW_TRK.update(json.load(open(f"{R.ROOT}/{R.E.VER}/work/tracks{R.E.VER[1:]}.json")))
z = np.load(f"{R.ROOT}/{R.E.VER}/work/seg{R.E.VER[1:]}.npz"); R.SEG.update({k: z[k] for k in z.files})
if __name__ == "__main__":
    with Pool(4) as p: rend = p.map(R.render, frames, chunksize=1)
    ims = []
    for f, r in zip(frames, rend):
        im = cv2.resize(r, (432, 768), interpolation=cv2.INTER_AREA)
        cv2.putText(im, str(f), (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA); ims.append(im)
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(f"{R.ROOT}/{R.E.VER}/frames/{name}.jpg", np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 86])
    print("wrote", name)
