"""Download scene packs from a list of share links into src/ (Google Drive file links; any direct-download URL works too).

  python3 tools/fetch_packs.py LINKS.txt          # one link per line; "link | name | note" is fine, extra text is ignored
  python3 tools/fetch_packs.py LINKS.txt --list   # only show each link's file name and size

Each file is downloaded into its own folder under src_incoming/, then identified by SHA-256 against
studio/src_manifest.json. A known file is moved to src/ under its library name; a file that's already in src/ is
skipped; an unknown file stays in src_incoming/ to be catalogued (probe it, name it, add it to the manifest and
studio/SCENE_PACKS.md). Large Drive files (> ~100 MB) go through Drive's virus-scan confirmation automatically.

**Never commit the link list: the repository is public, and the links open the owner's Drive files.** Keep it in
src/ (git-ignored) or re-send it to each new session.
"""
import os, re, sys, json, shutil, hashlib, subprocess, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN = f"{ROOT}/studio/src_manifest.json"; INC = f"{ROOT}/src_incoming"

def drive_id(url):
    m = re.search(r"/d/([A-Za-z0-9_-]{10,})", url) or re.search(r"[?&]id=([A-Za-z0-9_-]{10,})", url)
    return m.group(1) if m else None

def dl_url(url):
    i = drive_id(url)
    return f"https://drive.usercontent.google.com/download?id={i}&export=download" if i else url

def curl(args, **kw): return subprocess.run(["curl", "-sS", "-L", "--retry", "3", *args], **kw)

def head(url):
    """(file name, size in bytes or None, confirm-page html or None)."""
    r = curl(["-r", "0-0", "-D", "-", "-o", "/dev/null", url], capture_output=True, text=True)
    hd = r.stdout.replace("\r", "")
    cd = re.findall(r"(?im)^content-disposition:.*?filename\*?=\"?(?:UTF-8'')?([^\";\n]+)", hd)
    cr = re.findall(r"(?im)^content-range:.*/(\d+)", hd)
    if cd: return html.unescape(cd[-1]), int(cr[-1]) if cr else None, None
    page = curl([url], capture_output=True, text=True).stdout
    nm = re.search(r'class="uc-name-size"><a[^>]*>([^<]+)</a>\s*\(([^)]+)\)', page)
    return (html.unescape(nm.group(1)) if nm else "?"), (nm.group(2) if nm else None), page

def confirmed(url, page):
    if not page: return url
    q = {k: v for k, v in re.findall(r'name="(id|export|confirm|uuid)" value="([^"]*)"', page)}
    if "id" not in q: return url
    return "https://drive.usercontent.google.com/download?" + "&".join(f"{k}={v}" for k, v in q.items())

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    links = re.findall(r"https?://\S+", open(sys.argv[1]).read())
    man = json.load(open(MAN)); by_sha = {e["sha256"]: e["file"] for e in man["files"] if e.get("sha256")}
    have = {e["file"] for e in man["files"] if os.path.exists(f"{ROOT}/src/{e['file']}")}
    os.makedirs(f"{ROOT}/src", exist_ok=True); new = []
    for k, link in enumerate(links, 1):
        link = link.rstrip("|,;")
        url = dl_url(link); name, size, page = head(url)
        print(f"{k:2d}. {name}  ({size if size else '?'} bytes)", flush=True)
        if "--list" in sys.argv: continue
        d = f"{INC}/l{k:02d}"; os.makedirs(d, exist_ok=True); out = f"{d}/file.mp4"
        r = curl(["-o", out, confirmed(url, page)])
        if r.returncode or not os.path.exists(out) or os.path.getsize(out) < 100000:
            print("    download failed (is the link shared as 'Anyone with the link'?)"); continue
        h = sha256(out); lib = by_sha.get(h)
        if lib and lib in have: os.remove(out); os.rmdir(d); print(f"    already in src/ as {lib}"); continue
        if lib:
            shutil.move(out, f"{ROOT}/src/{lib}"); os.chmod(f"{ROOT}/src/{lib}", 0o444); os.rmdir(d); print(f"    -> src/{lib}"); continue
        print(f"    NEW (not in the manifest): left in {d}/ for cataloguing"); new.append((d, name))
    if new: print(f"\n{len(new)} new file(s) to catalogue: probe them (ffprobe), make contact sheets, name them, then add them "
                  f"to studio/src_manifest.json and studio/SCENE_PACKS.md")

if __name__ == "__main__":
    main()
