"""Which frames did each piece of renderer code draw?  (pipeline v2, change tracking for partial re-renders)

A full render records, for every frame, the renderer functions that ran while drawing it (sys.monitoring PY_START, one
event per function per frame, then disabled until the next frame: near-zero overhead). Each function is keyed by its
qualified name plus a hash of its own source text, so moving code up or down the file changes nothing, and editing a
function changes only its key.

At the next `video`, the renderer is imported again and every function that can still run is collected (module
globals, class bodies, containers such as the TR2 registry, closures, nested code). A frame is dirty when:
  * it ran a function whose key no longer exists (edited, deleted or shadowed by a later layer of the file), or
  * it ran a function that reads a module-level value or EDL global that changed (by name: co_names and string
    constants, so getattr(E, "X") counts), or
  * it ran a function that caches results across frames (it uses `global` or a module-level dict/list/set) and calls
    an edited function by name, because frames that hit that cache never called the edited function themselves.
Everything else is known to be unaffected. vrender re-renders only the dirty frames and still verifies frames outside
them bit-exact against the cache before splicing (a mismatch falls back to a full render).
"""
import sys, types, hashlib, functools
import numpy as np

TOOL = 4                                     # sys.monitoring tool id (0-5; 0 debugger, 1 coverage, 2 profiler, 5 optimizer)
_SEEN = set()
_KEYC = {}
_LINES = {}
_ON = [False]

def _lines(fn):
    if fn not in _LINES:
        try: _LINES[fn] = open(fn).read().split("\n")
        except Exception: _LINES[fn] = []
    return _LINES[fn]

def code_key(co):
    """qualname + hash of the code's own source lines (position-independent)."""
    k = _KEYC.get(co)
    if k is None:
        L = _lines(co.co_filename); a = co.co_firstlineno
        b = max([p[1] for p in co.co_positions() if p[1]] or [a])
        k = f"{co.co_qualname}:{hashlib.sha1(chr(10).join(L[a - 1:b]).encode()).hexdigest()[:12]}"
        _KEYC[co] = k
    return k

def names_of(co):
    """global names and identifier-like string constants used by this code and its nested code."""
    out = set(co.co_names)
    for c in co.co_consts:
        if isinstance(c, types.CodeType): out |= names_of(c)
        elif isinstance(c, str) and c.isidentifier(): out.add(c)
    return out

def holds_cache(co, R):
    """does this code keep state across frames (`global x`, or a module-level dict/list/set)?"""
    import dis
    for ins in dis.get_instructions(co):
        if ins.opname in ("STORE_GLOBAL", "DELETE_GLOBAL"): return True
    for n in co.co_names:
        v = getattr(R, n, None)
        if isinstance(v, (dict, list, set)) and not isinstance(v, type): return True
    return any(holds_cache(c, R) for c in co.co_consts if isinstance(c, types.CodeType))

# ---- worker side: trace one frame ------------------------------------------------------------------------------
def _on_start(code, off):
    _SEEN.add(code)
    return sys.monitoring.DISABLE

def start():
    M = sys.monitoring
    if _ON[0]: return
    try: M.use_tool_id(TOOL, "vrender-codetrack")
    except ValueError: pass
    M.register_callback(TOOL, M.events.PY_START, _on_start)
    M.set_events(TOOL, M.events.PY_START); _ON[0] = True

def traced(fn, f, rfile):
    """run fn(f) and return (result, sorted keys of the renderer code that ran)."""
    start(); _SEEN.clear(); sys.monitoring.restart_events()
    out = fn(f)
    seen = [c for c in list(_SEEN) if c.co_filename == rfile]
    keys = sorted({code_key(c) for c in seen})
    return out, keys

# ---- main side: what can run now, what changed ------------------------------------------------------------------
def live(R):
    """{key: code} for every renderer function that can still run."""
    rfile = R.__file__; codes = {}; seen = set()
    def add(co):
        if co.co_filename != rfile: return
        k = code_key(co)
        if k in codes: return
        codes[k] = co
        for c in co.co_consts:
            if isinstance(c, types.CodeType): add(c)
    def visit(v, d=0):
        if d > 5 or id(v) in seen: return
        seen.add(id(v))
        if isinstance(v, types.FunctionType):
            add(v.__code__)
            for c in v.__closure__ or ():
                try: visit(c.cell_contents, d + 1)
                except ValueError: pass
            for x in (v.__defaults__ or ()): visit(x, d + 1)
            for x in (v.__kwdefaults__ or {}).values(): visit(x, d + 1)
            if hasattr(v, "__wrapped__"): visit(v.__wrapped__, d + 1)
        elif isinstance(v, types.MethodType): visit(v.__func__, d + 1)
        elif isinstance(v, functools.partial): visit(v.func, d + 1); [visit(x, d + 1) for x in v.args]
        elif isinstance(v, type):
            if getattr(v, "__module__", None) == R.__name__:
                for x in vars(v).values(): visit(x, d + 1)
        elif isinstance(v, dict):
            if len(v) <= 4096:
                for x in v.values(): visit(x, d + 1)
        elif isinstance(v, (list, tuple, set, frozenset)):
            if len(v) <= 4096:
                for x in v: visit(x, d + 1)
        elif isinstance(v, (staticmethod, classmethod)): visit(v.__func__, d + 1)
    for v in list(vars(R).values()): visit(v)
    return codes

def _vh(v, h, d=0):
    """stable content hash of a module-level value (functions by name only: their code is tracked by key)."""
    if d > 6: h.update(b"deep"); return
    if isinstance(v, (bool, int, float, complex, str, bytes, type(None))): h.update(repr(v).encode())
    elif isinstance(v, np.ndarray):
        h.update(f"nd{v.shape}{v.dtype}".encode())
        b = np.ascontiguousarray(v).view(np.uint8).ravel()
        h.update((b if b.size <= 1 << 22 else b[::max(1, b.size // (1 << 20))]).tobytes())
    elif isinstance(v, np.generic): h.update(repr(v.item()).encode())
    elif isinstance(v, (list, tuple)):
        h.update(f"{type(v).__name__}{len(v)}".encode())
        if len(v) <= 4096:
            for x in v: _vh(x, h, d + 1)
    elif isinstance(v, (set, frozenset)): h.update(repr(sorted(map(repr, v))).encode())
    elif isinstance(v, dict):
        h.update(f"dict{len(v)}".encode())
        if len(v) <= 256:
            for k in sorted(v, key=repr): h.update(repr(k).encode()); _vh(v[k], h, d + 1)
        else: h.update(repr(sorted(map(repr, v))[:4096]).encode())
    elif isinstance(v, (types.FunctionType, types.BuiltinFunctionType, type, functools.partial)):
        h.update(getattr(v, "__qualname__", type(v).__name__).encode())
    else: h.update(type(v).__name__.encode())

SKIP = {"FR", "UNIQ", "SEG", "RAW_TRK", "TRK", "_EDIT_ENV_READY",   # inputs: covered by the EDL shots and inputs_sig
        "SHOTS", "S", "STARTS"}                                   # shots: covered by the per-shot diff (changed_shots)

def data_sig(R):
    """{name: hash} of the renderer's module-level data (runtime caches, inputs and code excluded)."""
    out = {}
    for n, v in vars(R).items():
        if n.startswith("__") or n in SKIP or isinstance(v, (types.ModuleType, types.FunctionType, type, types.BuiltinFunctionType)): continue
        if n.startswith("_") and isinstance(v, (dict, list, set)): continue          # per-process caches
        h = hashlib.sha1(); _vh(v, h); out[n] = h.hexdigest()[:12]
    return out

def info(R, keys):
    """per executed key: the names it reads and whether it caches across frames (stored with the cache)."""
    L = live(R); out = {}
    for k in keys:
        co = L.get(k)
        if co is not None: out[k] = {"names": sorted(names_of(co)), "holder": holds_cache(co, R), "name": co.co_name}
    return out

# ---- frame sets as ranges ----------------------------------------------------------------------------------------
def to_ranges(fs):
    out = []
    for f in sorted(fs):
        if out and f == out[-1][1] + 1: out[-1][1] = f
        else: out.append([f, f])
    return out

def from_ranges(rs): return {f for a, b in rs for f in range(a, b + 1)}

def dirty(meta_ct, R, changed_names):
    """frames to re-render, and why. meta_ct = {"frames": {key: ranges}, "info": {key: {...}}, "data": {...}}."""
    L = live(R); fr = meta_ct["frames"]; inf = meta_ct["info"]
    missing = {k for k in fr if k not in L}
    dnew = data_sig(R); dold = meta_ct.get("data", {})
    changed = set(changed_names) | {n for n in set(dnew) | set(dold) if dnew.get(n) != dold.get(n)}
    hit = set(missing); why = {k: "edited or removed" for k in missing}
    for k, i in inf.items():
        if k in hit: continue
        r = changed.intersection(i["names"])
        if r: hit.add(k); why[k] = "reads " + ", ".join(sorted(r)[:4])
    edited = {inf[k]["name"] for k in missing if k in inf} | {k.split(":")[0].split(".")[-1] for k in missing}
    for k, i in inf.items():
        if k in hit or not i["holder"]: continue
        r = edited.intersection(i["names"])
        if r: hit.add(k); why[k] = "caches across frames and calls " + ", ".join(sorted(r)[:4])
    frames = set()
    for k in hit: frames |= from_ranges(fr.get(k, []))
    return frames, {k: why[k] for k in hit}, sorted(changed)
