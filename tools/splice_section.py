"""Put an edit's own section into its renderer ABOVE the pipeline v2 speed section (v11-based edits).

  python3 tools/splice_section.py N SECTION.py        # inserts SECTION.py's text just above `# >>> pipeline v2: speed`
  python3 tools/splice_section.py N --check           # warn about overrides placed below the section
  python3 tools/splice_section.py N SECTION.py --replace   # re-splice an edited section: replaces the block from its first
                                                           # line up to the speed section with the file's current text

The speed section wraps whatever `grade`, `render_shot` and hot effects exist above it (fast grade, still cache,
channel-wise effects). A `grade` or `render_shot` defined below it replaces the fast path: the picture is still right,
only slower (toolkit pitfall 1). Idempotent: a section whose first line is already in the file isn't inserted twice.
Without the marker (an older engine), it falls back to inserting just before `def main():`.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START, END = "# >>> pipeline v2: speed", "# <<< pipeline v2: speed"
WRAPPED = ("grade", "render_shot", "light_rgb", "light_from", "anamorphic", "finish11", "motes11")

def below_section(src):
    """names in WRAPPED defined at top level after the end of the speed section (before main)."""
    if END not in src: return []
    tail = src.split(END, 1)[1].split("\ndef main():", 1)[0]
    return [m for m in re.findall(r"^def (\w+)\(", tail, re.M) if m in WRAPPED]

def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    n, arg = sys.argv[1], sys.argv[2]
    p = f"{ROOT}/v{n}/work/render{n}.py"; src = open(p).read()
    if arg == "--check":
        bad = below_section(src)
        print("ok: no overrides below the speed section" if not bad else
              f"WARNING render{n}.py: {', '.join(bad)} defined below the pipeline v2 speed section (they bypass it: correct but slower); "
              f"move that section above '{START}' (tools/splice_section.py)")
        sys.exit(0)
    sec = open(arg).read().rstrip("\n") + "\n\n"
    first = next((l for l in sec.splitlines() if l.strip()), "")
    if first and first in src and "--replace" in sys.argv and START in src:
        a, b = src.index(first), src.index(START)
        if a < b:
            open(p, "w").write(src[:a] + sec + src[b:]); print(f"replaced {arg} in render{n}.py ({len(sec.splitlines())} lines)"); return
    if first and first in src: print(f"already in render{n}.py: {first[:70]} (use --replace to update it)"); return
    if START in src: src = src.replace(START, sec + START, 1); where = "above the speed section"
    else: src = src.replace("\ndef main():", "\n" + sec + "def main():", 1); where = "before main() (no speed section)"
    open(p, "w").write(src); print(f"inserted {arg} into render{n}.py {where}")

if __name__ == "__main__":
    main()
