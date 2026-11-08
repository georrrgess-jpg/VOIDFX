"""Scaffold a new voidfx edit from the newest standard engine (v12 BLOOM rev 3 on v11 BOP: every v4-v12 transition and graphic, the
restored-source sampler, velocity + optical flow, the beat camera, the v9 text system, the v11 rival/emblem/rift pieces).

Usage:  python3 tools/new_edit.py N SLUG "TITLE — Show × Song"
        e.g. python3 tools/new_edit.py 7 night_drive_dexter "NIGHT DRIVE — Dexter × Song"
Creates vN/{work,frames,audio,out}; copies the engine (render, audio, qc, facetrack, analyze) wired to vN/work/edlN.py;
writes edlN.py from tools/edl_template.py; adds the media folders to .gitignore. The engine reads every path and the
output file name from the EDL (VER, SLUG), so nothing else needs renaming.
"""
import os, sys, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "v12"                                                    # the standard engine (superset of v4-v12; v12 BLOOM rev 3)
n, slug, title = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
V = f"v{n}"; D = f"{ROOT}/{V}"
if os.path.exists(f"{D}/work/edl{n}.py"): sys.exit(f"{V} already exists — refusing to overwrite")
for sub in ("work", "frames", "audio", "out"): os.makedirs(f"{D}/{sub}", exist_ok=True)

BN = BASE[1:]
def port(src, dst, extra=()):
    s = open(f"{ROOT}/{BASE}/work/{src}").read()
    s = s.replace(f"import edl{BN} as E", f"import edl{n} as E")
    for a, b, *c in extra: s = s.replace(a, b, *c)
    open(f"{D}/work/{dst}", "w").write(s)

port(f"render{BN}.py", f"render{n}.py")
port(f"audio{BN}.py", f"audio{n}.py", [('"""', f'"""[{title} (voidfx {V}) — ported from the {BASE} engine; rewrite the sound design below]\nPrevious edit: ', 1)])
port(f"qc{BN}.py", f"qc{n}.py")
shutil.copy(f"{ROOT}/{BASE}/work/facetrack.py", f"{D}/work/facetrack.py")
port("analyze.py", "analyze.py", [(f'f"{BASE}/work/', f'f"{V}/work/'), (f'f"{BASE}/frames/', f'f"{V}/frames/'), ('f"v6/work/', f'f"{V}/work/'), ('f"v6/frames/', f'f"{V}/frames/')])

t = open(f"{ROOT}/tools/edl_template.py").read()
t = t.replace("{{TITLE}}", title).replace("{{VER}}", V).replace("{{SLUG}}", slug).replace("{{N}}", n)
open(f"{D}/work/edl{n}.py", "w").write(t)

gi = f"{ROOT}/.gitignore"; g = open(gi).read() if os.path.exists(gi) else ""
add = [f"{V}/work/*.log", f"{V}/audio/", f"{V}/frames/", f"{V}/out/", f"{V}/work/*.npz", f"{V}/work/*.npy"]
new = [a for a in add if a not in g.split("\n")]
if new: open(gi, "a").write(("\n" if g and not g.endswith("\n") else "") + "\n".join(new) + "\n")

print(f"""scaffolded {V}: {title}
next:
  bash tools/build.sh {n} song:src/SONG.mp3[:H0:H1]                # map, stems, drum-stem grid, vocal-stem words, loop wrap -> EDL lines
  python3 {V}/work/analyze.py src/PACK.mp4 TAG                     # shot list + contact sheets per NEW pack (known packs: copy shots_*.json)
  python3 tools/transcribe.py {V} NAME src/PACK.mp4 --vad          # dialogue word times (if using dialogue)
  edit {V}/work/edl{n}.py  (shots, transitions, HERO, SET_PIECES, knobs) and audio{n}.py
  bash tools/build.sh {n} audio plan                               # sound, then preflight: the plan against every owner rule
  bash tools/build.sh {n} prep auto                                # tracks/mattes, preflight, restoration in the background, sheets of every cut
  bash tools/build.sh {n} clip:A:B preview                         # motion checks
  bash tools/build.sh {n} video qc                                 # final render + ship checkpoint + review pack (vN/frames/review_*.jpg)
  revision rounds: bash tools/build.sh {n} plan rev                # preflight, then audio + only the changed frames + QC""")
