"""Load edit N's renderer as a library, set up exactly as its `main()` does before rendering.

    import edit_env; R = edit_env.load_edit(11); frame = R.render(600)

Used by golden.py (regression frames), rsrv.py (render server) and the partial re-render.
"""
import os, sys, json, importlib
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def work_dir(n): return f"{ROOT}/v{n}/work"

def load_edit(n, setup=True):
    """import vN/work/renderN.py and run its pre-render set-up (sources, hits, tracks, mattes)."""
    wd = work_dir(n)
    if wd not in sys.path: sys.path.insert(0, wd)
    R = importlib.import_module(f"render{n}")
    if setup and not getattr(R, "_EDIT_ENV_READY", False):
        R.load(); R.init_hits()
        R.RAW_TRK.update(json.load(open(f"{wd}/tracks{n}.json")))
        z = np.load(f"{wd}/seg{n}.npz"); R.SEG.update({k: z[k] for k in z.files})
        R._EDIT_ENV_READY = True
    return R

def edl(n):
    wd = work_dir(n)
    if wd not in sys.path: sys.path.insert(0, wd)
    return importlib.import_module(f"edl{n}")
