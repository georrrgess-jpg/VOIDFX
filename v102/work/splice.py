"""splice fx102.py (the v102 look/transitions/frame) into render102.py just before main() is invoked."""
import os
d = os.path.dirname(os.path.abspath(__file__)); R = f"{d}/render102.py"; src = open(R).read()
A, B = "# >>> v102 section (generated from fx102.py by splice.py)\n", "# <<< v102 section\n"
if A in src: src = src[:src.index(A)] + src[src.index(B) + len(B):]
tail = 'if __name__ == "__main__":\n    main()'
i = src.rindex(tail)
src = src[:i] + A + open(f"{d}/fx102.py").read() + "\n" + B + "\n" + src[i:]
open(R, "w").write(src); print("spliced", len(src.splitlines()), "lines")
