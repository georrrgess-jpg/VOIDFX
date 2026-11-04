"""splice fx101.py (the v101 look/transitions/frame) into render101.py just before main() is invoked."""
import os
d = os.path.dirname(os.path.abspath(__file__)); R = f"{d}/render101.py"; src = open(R).read()
A, B = "# >>> v101 section (generated from fx101.py by splice.py)\n", "# <<< v101 section\n"
if A in src: src = src[:src.index(A)] + src[src.index(B) + len(B):]
tail = 'if __name__ == "__main__":\n    main()'
i = src.rindex(tail)
src = src[:i] + A + open(f"{d}/fx101.py").read() + "\n" + B + "\n" + src[i:]
open(R, "w").write(src); print("spliced", len(src.splitlines()), "lines")
