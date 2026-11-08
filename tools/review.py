"""review.py: folded into tools/signoff.py on 2026-11-08 (one review tool for both studios: transitions and cuts, set pieces,
the loop wrap, titles, unexplained pops, with faceqc/motionqc flags boxed red). Kept so old commands still work."""
import os, sys
os.execv(sys.executable, [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "signoff.py")] + [a for a in sys.argv[1:] if not a.startswith("--per")])
