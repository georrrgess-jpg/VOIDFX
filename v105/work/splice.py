"""splice fx105.py (the v105 look/transitions/frame) into render105.py just before main() is invoked (above the pipeline v2 WP2 section)."""
import os
d = os.path.dirname(os.path.abspath(__file__)); R = f"{d}/render105.py"; src = open(R).read()
A, B = "# >>> v105 section (generated from fx105.py by splice.py)\n", "# <<< v105 section\n"
if A in src: src = src[:src.index(A)].rstrip("\n") + "\n\n" + src[src.index(B) + len(B):].lstrip("\n")
tail = 'if __name__ == "__main__":\n    main()'
WP2 = "# >>> pipeline v2 · WP2"                                   # the shared speed section stays last: the edit goes above it
i = src.rindex(WP2) if WP2 in src else src.rindex(tail)
src = src[:i].rstrip("\n") + "\n\n" + A + open(f"{d}/fx105.py").read() + "\n" + B + "\n" + src[i:]
open(R, "w").write(src); print("spliced", len(src.splitlines()), "lines")
