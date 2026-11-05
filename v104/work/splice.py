"""splice fx104.py (the v104 look/transitions/frame) into render104.py just before main() is invoked."""
import os
d = os.path.dirname(os.path.abspath(__file__)); R = f"{d}/render104.py"; src = open(R).read()
A, B = "# >>> v104 section (generated from fx104.py by splice.py)\n", "# <<< v104 section\n"
if A in src: src = src[:src.index(A)] + src[src.index(B) + len(B):]
tail = 'if __name__ == "__main__":\n    main()'
i = src.rindex(tail)
src = src[:i] + A + open(f"{d}/fx104.py").read() + "\n" + B + "\n" + src[i:]
open(R, "w").write(src); print("spliced", len(src.splitlines()), "lines")
