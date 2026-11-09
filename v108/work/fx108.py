# ============================================================================ v108 — DOOMSDAY: toolkit from the v107 standard (restyle it)
# The edit's own section (above the pipeline v2 speed section). Last definition wins.
#   LOOK      TABLOID: newsprint cream highlights, ink blacks, slate blues, one spot red; a misregistered red plate,
#             paper grain and a fine screen in the shadows (finish107).
#   PRINT     halftone(): the press screen. The press flash prints the next shot as a newspaper photo; the front page's
#             photo is the next shot, and the dive resolves its dots into the footage.
#   molasses  "flows of hot molasses": a viscous sheet of blood pours down the lens (fingering front, a bead on its
#             edge, refraction, absorption, a glossy highlight), the next shot is under it, it drains with streaks.
#   headspin  "to headspin": the frame spins two turns about its centre (motion-blurred) onto the upside-down shot.
#   frontpage "took a few minutes to convince": the front page spins in (BAY HARBOR / BUTCHER), lands, and we dive into
#             its photo of him (the next shot).
#   stamp     "when you spell the man name": a strip of newsprint slaps on; D-E-X-T-E-R is stamped one letter per sung
#             word; the strip flies into the sky onto the real banner the plane tows (WE <3 DEXTER).
#   confetti  procedural paper confetti (lit, fluttering, depth of field): the pop into the parade and the loop
#             (it thickens over the lens on the bass drop-out bar and clears on frame 0).
INK = np.array([0.045, 0.040, 0.040], np.float32)       # BGR ink black
PAPER = np.array([0.84, 0.92, 0.96], np.float32)        # BGR newsprint cream
SPOT = np.array([0.13, 0.12, 0.80], np.float32)         # BGR spot red
SLATE = np.array([0.50, 0.42, 0.34], np.float32)        # BGR slate blue
BLOODC = np.array([0.03, 0.02, 0.30], np.float32)       # BGR deep blood body
EMPH = np.array([0.16, 0.16, 0.92], np.float32)         # caption emphasis: the spot red (cap_word reads EMPH)

# ---- the grade: TABLOID -------------------------------------------------------------------------------------------
_LUTT = {}
def lutt():
    if "t" not in _LUTT:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTT["t"] = (x, PchipInterpolator([0, .05, .18, .50, .80, .94, 1], [0.030, 0.040, 0.135, 0.47, 0.80, 0.915, 0.94])(x).astype(np.float32))
    return _LUTT["t"]

_grade_pre107 = grade
def grade(img, s, f):
    if s.get("look") != "tabloid": return _grade_pre107(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = lutt()
    if in_unit(img):
        x = apply_lut3(img, tone_lut(("tab107", s["n"], ev, float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.interp(np.clip(np.clip(img * gains, 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - np.maximum(Gc, Bc) - s.get("redthr", 0.12)) * 3.2, 0, 1)          # strong reds survive as the spot colour
    skin = np.clip((Rc - Bc) * 2.2, 0, 1) * (1 - red)
    sat = 0.30 + 0.20 * skin + 0.85 * red
    hi = np.clip((L - 0.45) * 1.8, 0, 1)
    o = np.empty(x.shape, np.float32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v *= 1 + hi * (PAPER[ch] / 0.96 - 1) * 0.9                                         # paper cream in the light
        v += (1 - L) ** 3 * (0.012 if ch == 0 else 0.0)                                    # ink, a hair cool in the deepest black
        v += red * L * (SPOT[ch] / 0.80 - 1) * 0.25                                        # reds lean to the printing red
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

# ---- the print: halftone screen ------------------------------------------------------------------------------------
_HT = {}
def ht_grid(pitch, ang):
    key = (round(pitch, 2), ang)
    if key not in _HT:
        if len(_HT) > 10: _HT.clear()
        a = math.radians(ang); p = key[0]                                                 # from the rounded key: order-independent (partial renders verify)
        u = (_GX * math.cos(a) + _GY * math.sin(a)) / p; v = (-_GX * math.sin(a) + _GY * math.cos(a)) / p
        du, dv = u - np.round(u), v - np.round(v); _HT[key] = np.sqrt(du * du + dv * dv).astype(np.float32)
    return _HT[key]

def halftone(img, pitch=9.0, ang=45, red_plate=True):
    """the image as a newspaper print: ink dots on newsprint (size by darkness, sampled per cell), reds on their own
    screen at 75 degrees."""
    r = ht_grid(pitch, ang); sm = cv2.GaussianBlur(img, (0, 0), pitch * 0.45)
    Lb = lum(sm); d = np.clip((1 - Lb) * 1.08 - 0.04, 0, 1)
    R = np.sqrt(d / math.pi) * 1.02; aa = 1.2 / pitch
    dot = np.clip((R - r) / aa + 0.5, 0, 1)
    o = PAPER * (1 - dot[..., None]) + INK * dot[..., None]
    if red_plate:
        red = np.clip((sm[..., 2] - np.maximum(sm[..., 0], sm[..., 1]) - 0.05) * 2.5, 0, 1)
        r2 = ht_grid(pitch, 75); dr = np.clip((np.sqrt(red / math.pi) * 1.02 - r2) / aa + 0.5, 0, 1) * (1 - dot)
        o = o * (1 - dr[..., None]) + SPOT * dr[..., None]
    return o.astype(np.float32)

# ---- the finish: misregistered red plate, paper grain, a fine screen in the shadows, vignette ------------------------
_PAPERTEX = {}
def paper_tex():
    if "p" not in _PAPERTEX:
        rng = np.random.default_rng(1070)
        fib = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8)
        fib = fib + cv2.resize(cv2.GaussianBlur(rng.standard_normal((H // 6, W // 6)).astype(np.float32), (0, 0), 1.2), (W, H)) * 0.8
        fib = cv2.GaussianBlur(fib, (0, 0), sigmaX=2.2, sigmaY=0.6)                        # fibres run one way
        _PAPERTEX["p"] = (fib / (np.abs(fib).max() + 1e-6)).astype(np.float32)
    return _PAPERTEX["p"]

def finish107(out, f, s=None):
    Bc, Gc, Rc = out[..., 0], out[..., 1], out[..., 2]
    red = np.clip((Rc - np.maximum(Gc, Bc) - 0.06) * 2.0, 0, 1)
    ghost = np.roll(np.roll(red, 3, 1), 2, 0) * (1 - red) * 0.22                           # the red plate sits a few px off
    L = lum(out); scr = ht_grid(6.0, 45)
    dots = np.clip(1 - scr * 2.4, 0, 1) * np.clip((0.55 - L) * 1.6, 0, 1) * 0.07           # a fine screen in the shadows only
    pt = paper_tex(); g = grain(f, 0.011)[..., 0]; v = VIG[..., 0]
    o = np.empty(out.shape, np.float32)
    for ch in range(3):
        oc = o[..., ch]; np.copyto(oc, out[..., ch])
        oc += ghost * (SPOT[ch] - 0.55) * 0.6
        oc *= (1 - dots); oc *= (1 + pt * 0.022); oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: from e2 (frame 0 clean) to the loop; it rests through the spins, the front page and the match ---
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < E.E_LOOP - 1) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- smooth motion: where flow is refused (big frame-to-frame change), blend the two frames instead of holding one ----
def src_weights(s, f):
    """as the engine's, but a flow shot whose neighbours differ too much for clean flow blends them (motion-blur-like at
    60 fps) instead of holding one (24p judder). check_sources keeps every range inside one source shot."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > 14: return [(i0, 1 - a), (i1, a)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

# ---- base frame ---------------------------------------------------------------------------------------------------
def banner_geom(t):
    """the banner shot: the source cropped round the banner (tracked as it drifts left and up), scaled 1.2x so the whole
    banner fits the width; the sky is extended above and below."""
    x0 = 260.0 - 86.7 * (t - 326.05); y0 = -20.0 * (t - 326.05)
    return x0, y0, 1.2, 545.0

def banner_frame(s, f):
    t, u, _ = src_time(s, f); fr = sample(s["src"], t)
    img = fr.astype(np.float32) / 255 if fr.dtype != np.float32 else fr
    x0, y0, sc, yoff = banner_geom(t)
    M = np.float32([[sc, 0, -x0 * sc], [0, sc, yoff - y0 * sc]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    top, bot = img[4:60].reshape(-1, 3).mean(0), img[-60:-4].reshape(-1, 3).mean(0)          # extend the sky: its own top/bottom colour
    yy = (_GY[:, :1] - yoff) / (720 * sc)
    sky = np.where(yy < 0, top + (top - bot) * np.clip(-yy, 0, 1) * 0.15, bot - (top - bot) * np.clip(yy - 1, 0, 1) * 0.15).astype(np.float32)
    out_m = np.clip(np.maximum(-yy * 720 * sc, (yy - 1) * 720 * sc) / 40 + 0.5, 0, 1)        # 1 outside the source rows (soft edge)
    o = o * (1 - out_m[..., None]) + sky[:, None, :] * out_m[..., None]
    return np.clip(grade(np.clip(o, 0, 1), s, f), 0, 1)

def base107(s, f):
    if s.get("banner"): return banner_frame(s, f), None
    img, person = base12(s, f)
    if s.get("pop"): img = pop_behind(img, s, f, person)
    return img, person

_B107 = {}
def edge107(S_, which):
    key = (S_["n"], which)
    if key not in _B107:
        if len(_B107) > 6: _B107.clear()
        _B107[key] = base107(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B107[key]

# ---- PRESS FLASH: a press camera fires; the next shot is printed as a newspaper photo, then comes to life -------------
def press_flash(A, B, j, f, sa, sb, pre=4, post=18):
    if j < 0:
        u = (j + pre + 1) / pre
        return np.clip(A * (1 + 0.10 * u) + 0.03 * u, 0, 1)
    v = (j + 1) / post
    snap = edge107(sb, "first")
    pr = halftone(snap, 8.0)
    w = smooth((v - 0.30) / 0.55)                                                          # the print comes to life
    o = pr * (1 - w) + B * w
    if 0.15 < v < 0.85:                                                                    # dots shrink as it resolves
        o = o * 0.5 + (halftone(B, 8.0 - 5.0 * smooth((v - 0.15) / 0.7)) * (1 - w) + B * w) * 0.5
    fl = math.exp(-j / 1.8)                                                                # the flashbulb
    o = o + (PAPER * 0.9 + 0.08) * fl * 0.30
    return np.clip(o, 0, 1)
TR2["press_flash"] = (press_flash, 4, 18)

# ---- HOT MOLASSES: a viscous sheet of blood pours down the lens ---------------------------------------------------
_MOL = {}
def mol_fields():
    if "f" not in _MOL:
        rng = np.random.default_rng(1071); xs = np.arange(W // 4, dtype=np.float32)
        fing = np.zeros_like(xs)
        for _ in range(7):                                                                 # the fingers of the front
            c = rng.uniform(0, W // 4); w = rng.uniform(16, 40); a = rng.uniform(0.4, 1.0)
            fing += a * np.exp(-((xs - c) / w) ** 2)
        fing = fing / fing.max()
        wave = cv2.GaussianBlur(rng.standard_normal((H // 4 * 2, W // 4)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=16)
        _MOL["f"] = (fing, cv2.GaussianBlur(fing[None, :], (0, 0), 10)[0], wave / (np.abs(wave).max() + 1e-6))
    return _MOL["f"]

def mol_thickness(q, f):
    """quarter-res thickness of the sheet at progress q (0 -> 1 over pre + post); the cut is at MOL_QC."""
    fing, fsoft, wave = mol_fields(); h4, w4 = H // 4, W // 4
    yy = np.arange(h4, dtype=np.float32)[:, None]
    qp = clamp(q / MOL_QC, 0, 1); qd = clamp((q - MOL_QC) / (1 - MOL_QC), 0, 1)
    front = (-0.15 + 1.32 * ein(qp, 1.45)) * h4 + fing[None, :] * 85 * min(1.0, qp * 1.5) * (1 - 0.7 * qd)   # pours; fingers lead
    top = (-0.06 + 1.42 * ein(qd, 1.35)) * h4 + (1 - fsoft[None, :]) * 40 * qd                               # drains from the top
    body = np.clip((front - yy) / 26, 0, 1) * np.clip((yy - top) / 26, 0, 1)
    bead = np.exp(-((front - yy - 11) / 9.0) ** 2) * 0.45 * (qp < 1)                       # the rounded bead on the front
    bead2 = np.exp(-((yy - top - 10) / 9.0) ** 2) * 0.35 * (qd > 0) * np.clip((front - yy) / 26, 0, 1)   # the meniscus on the draining edge
    off = int(f * 3.0) % h4                                                                # undulations slide down the sheet
    und = 1 + 0.28 * wave[h4 - off:2 * h4 - off]
    th_ = (body * (0.72 + 0.28 * (1 - qd)) * und + bead + bead2).astype(np.float32)
    return np.clip(th_, 0, 1.5)

MOL_PRE, MOL_POST = 36, 24
MOL_QC = MOL_PRE / (MOL_PRE + MOL_POST)
def molasses(A, B, j, f, sa, sb, pre=MOL_PRE, post=MOL_POST):
    q = (j + pre + 0.5) / (pre + post)
    t4 = mol_thickness(q, f)
    if t4.max() < 0.003: return B if j >= 0 else A
    T = cv2.resize(t4, (W, H), interpolation=cv2.INTER_CUBIC)
    gy, gx = np.gradient(cv2.GaussianBlur(t4, (0, 0), 1.6))
    gx = cv2.resize(gx, (W, H)); gy = cv2.resize(gy, (W, H))
    plate = A if j < 0 else B
    ref = cv2.remap(plate, _GX + gx * 300, _GY + gy * 300, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)   # refraction
    sig = np.array([3.0, 2.8, 0.75], np.float32)
    Tr = np.exp(-sig * T[..., None] * 1.6)                                                 # absorption: crimson, deepest where thick
    col = ref * Tr * np.array([0.55, 0.55, 1.0], np.float32) ** np.clip(T[..., None] * 3, 0, 1) + BLOODC * (1 - Tr[..., 2:3]) * 0.9
    nx, ny = -gx * 26, -gy * 26; nz = np.ones_like(nx); nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    l = np.array([-0.45, -0.55, 0.70], np.float32); l /= np.linalg.norm(l); hv = l + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = (nx * hv[0] + ny * hv[1] + nz * hv[2]) / nn
    spec = np.clip(ndh, 0, 1) ** 46 * 1.10 * np.clip(T * 4, 0, 1)                         # the gloss
    sheen = np.clip((nx * l[0] + ny * l[1] + nz * l[2]) / nn, 0, 1) ** 8 * 0.10 * np.clip(T * 3, 0, 1)
    o = col + (spec + sheen)[..., None] * np.array([0.92, 0.95, 1.0], np.float32)
    return np.clip(o, 0, 1)
TR2["molasses"] = (molasses, MOL_PRE, MOL_POST)

# ---- HEADSPIN: two turns about the centre, motion-blurred, onto the upside-down shot --------------------------------
def spin_img(img, ang, z, n=1, spread=0.0):
    acc = None
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread if n > 1 else ang
        M = cv2.getRotationMatrix2D((W / 2, H / 2), a, z)
        r = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = r if acc is None else acc + r
    return acc / n

def headspin(A, B, j, f, sa, sb, pre=20, post=20):
    N = pre + post; q = (j + pre + 0.5) / N
    phi = 720 * q * q * (3 - 2 * q); dphi = 720 * 6 * q * (1 - q) / N                     # degrees, and per frame
    z = 1 + 0.30 * math.sin(math.pi * q)
    img = A if j < 0 else B; ang = -phi if j < 0 else -(phi - 720)
    n = int(clamp(dphi / 4, 1, 9))
    o = spin_img(img, ang, z, n, dphi)
    if dphi > 8: o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.0025 * dphi, 4)
    return np.clip(o, 0, 1)
TR2["headspin"] = (headspin, 20, 20)

def flip(A, B, j, f, sa, sb, pre=5, post=9):
    """the upside-down shot rolls the rest of the way over into the grin."""
    if j < 0:
        u = (j + pre + 1) / pre; ang = 90 * ein(u, 2); return np.clip(spin_img(A, ang, 1 + 0.15 * u, 5, 18 * u), 0, 1)
    v = (j + 1) / post; ang = -90 * (1 - eout(v, 2.2))
    return np.clip(spin_img(B, ang, 1 + 0.15 * (1 - v), 5 if v < 0.6 else 1, 18 * (1 - v)), 0, 1)
TR2["flip"] = (flip, 5, 9)

# ---- THE FRONT PAGE: BAY HARBOR BUTCHER; the photo under it is him (the next shot) --------------------------------
F_MAST = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_BODY = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
F_CAPT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
PHOTO = (56, 742, 456, 1453)                                                               # x0, y0, x1, y1 on the page (9:16)
def squeeze(m, sx): return cv2.resize(m, (max(1, int(m.shape[1] * sx)), m.shape[0]), interpolation=cv2.INTER_AREA)
def put_mask(canvas_a, m, x, y):
    h, w = m.shape; ys, xs = slice(max(0, y), min(H, y + h)), slice(max(0, x), min(W, x + w))
    canvas_a[ys, xs] = np.maximum(canvas_a[ys, xs], m[ys.start - y:ys.stop - y, xs.start - x:xs.stop - x])

_FP = {}
def page_layers():
    """(paper rgb, ink mask, red mask): the front page without its photo."""
    if "p" in _FP: return _FP["p"]
    rng = np.random.default_rng(1072)
    paper = np.empty((H, W, 3), np.float32); pt = paper_tex()
    for c in range(3): paper[..., c] = PAPER[c] * (1 + pt * 0.05)
    edge = np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 90, 0, 1)
    paper *= (0.90 + 0.10 * edge)[..., None]
    ink = np.zeros((H, W), np.float32); red = np.zeros((H, W), np.float32)
    m = text_mask("MIAMI GAZETTE", F_MAST, 104); m = squeeze(m, min(1.0, 980 / m.shape[1])); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 52)
    cv2.line(ink, (40, 40), (W - 40, 40), 1.0, 3); cv2.line(ink, (40, 196), (W - 40, 196), 1.0, 3); cv2.line(ink, (40, 238), (W - 40, 238), 1.0, 1)
    m = text_mask("SPECIAL EDITION   ·   MIAMI, FLORIDA   ·   FINAL", F_SB, 26, tracking=2); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 204)
    m = text_mask("BAY HARBOR", F_BLACK, 210, tracking=-4); m = squeeze(m, 990 / m.shape[1]); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 252)
    m = text_mask("BUTCHER", F_BLACK, 250, tracking=-4); m = squeeze(m, 990 / m.shape[1]); put_mask(red, m, int(W / 2 - m.shape[1] / 2), 452)
    m = text_mask("INVESTIGATION STILL ONGOING", F_XB, 46, tracking=1); m = squeeze(m, min(1.0, 990 / m.shape[1])); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 676)
    cv2.rectangle(ink, (PHOTO[0] - 3, PHOTO[1] - 3), (PHOTO[2] + 3, PHOTO[3] + 3), 1.0, 2)
    m = text_mask("Blood spatter analyst Dexter Morgan", F_CAPT, 21); put_mask(ink, m, PHOTO[0], PHOTO[3] + 12)
    m = text_mask("at the scene, Tuesday.", F_CAPT, 21); put_mask(ink, m, PHOTO[0], PHOTO[3] + 40)
    words = ("the police said investigators were searching the bay for more remains as federal agents joined the case and the "
             "department declined to comment on reports that a suspect had been identified among the bodies recovered from the "
             "water off the marina residents gathered at the docks overnight while divers worked in shifts the medical examiner "
             "confirmed that the victims had been killed elsewhere and the killer remains at large").split()
    cols = [(496, 742, 752), (776, 742, 1032)]
    for (x0, y0, x1) in cols:
        y = y0; wi = int(rng.integers(len(words)))
        while y < 1830:
            line = []; wsum = 0
            while True:
                w = words[wi % len(words)]; wi += 1; tw = len(w) * 11 + 9
                if wsum + tw > (x1 - x0): break
                line.append(w); wsum += tw
            m = text_mask(" ".join(line), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
            y += 29
            if rng.random() < 0.06: y += 22
        cv2.line(ink, (x1 + 12, 742), (x1 + 12, 1840), 0.8, 1)
    y = 1500
    while y < 1830:
        m = text_mask(" ".join(words[(y // 7) % 20:(y // 7) % 20 + 6]), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, 400 / m.shape[1])), PHOTO[0], y); y += 29
    _FP["p"] = (paper, ink, red); return _FP["p"]

def page_with_photo(photo):
    """the page, with photo (a full 1080x1920 frame) printed into the photo box as a halftone."""
    paper, ink, red = page_layers()
    pw, ph = PHOTO[2] - PHOTO[0], PHOTO[3] - PHOTO[1]
    small = cv2.resize(photo, (pw, ph), interpolation=cv2.INTER_AREA)
    pr = halftone(cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR), 9.0 * W / pw)  # screen at print scale
    pr = cv2.resize(pr, (pw, ph), interpolation=cv2.INTER_AREA)
    o = paper.copy(); o[PHOTO[1]:PHOTO[3], PHOTO[0]:PHOTO[2]] = pr * (0.97 + 0.03 * paper[PHOTO[1]:PHOTO[3], PHOTO[0]:PHOTO[2]] / PAPER)
    o = o * (1 - ink[..., None] * 0.94) + INK * ink[..., None] * 0.94
    o = o * (1 - red[..., None]) + SPOT * red[..., None]
    return o.astype(np.float32)

def frontpage(A, B, j, f, sa, sb, pre=82, post=28):
    PCX, PCY = (PHOTO[0] + PHOTO[2]) / 2, (PHOTO[1] + PHOTO[3]) / 2
    SDIVE = H / (PHOTO[3] - PHOTO[1])
    if j >= 0:                                                                             # the photo's dots resolve into him
        v = (j + 1) / post; pitch = 9.0 * SDIVE * (1 - eout(v, 1.6)) + 3.0
        w = smooth((v - 0.25) / 0.65)
        return np.clip(halftone(B, pitch) * (1 - w) + B * w, 0, 1)
    if "pg" not in _FP or _FP.get("pgk") != sb["n"]:
        _FP["pg"] = page_with_photo(edge107(sb, "first")); _FP["pgk"] = sb["n"]
    page = _FP["pg"]
    u = (j + pre + 1) / pre
    if u < 0.80:
        if u < 0.52:                                                                       # the classic spin-in
            w_ = eout(u / 0.52, 2.6); s_ = 0.04 + 0.86 * w_; rot = 3 * 360 * (1 - w_)
        else:                                                                              # it lands, settles, we push in
            w_ = (u - 0.52) / 0.28
            s_ = 0.90 + 0.05 * math.sin(math.pi * min(1, w_ * 2.2)) * math.exp(-w_ * 2) + 0.06 * w_; rot = 2.0 * math.exp(-w_ * 5) * math.cos(w_ * 12)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, s_)
    else:                                                                                  # the dive: his photo comes to fill the frame
        w_ = ein((u - 0.80) / 0.20, 2.2); s0 = 0.96; s_ = s0 * (SDIVE / s0) ** w_
        pcx0, pcy0 = W / 2 + (PCX - W / 2) * s0, H / 2 + (PCY - H / 2) * s0
        tcx, tcy = pcx0 + (W / 2 - pcx0) * w_, pcy0 + (H / 2 - pcy0) * w_
        M = np.float32([[s_, 0, tcx - PCX * s_], [0, s_, tcy - PCY * s_]])
    pa = cv2.warpAffine(np.dstack([page, np.ones((H, W), np.float32)]), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = pa[..., 3:4]
    bg = A * (1 - 0.45 * min(1.0, u * 2.5))
    if u < 0.80:                                                                           # its shadow on the scene
        sh = cv2.GaussianBlur(np.roll(np.roll(pa[..., 3], 18, 0), 12, 1), (0, 0), 16) * 0.55
        bg = bg * (1 - sh[..., None])
    return np.clip(bg * (1 - al) + pa[..., :3] * al, 0, 1)
TR2["frontpage"] = (frontpage, 82, 28)

# ---- confetti: lit paper pieces, fluttering, with depth ------------------------------------------------------------
CONF_COLS = np.array([[0.13, 0.12, 0.80], [0.84, 0.92, 0.96], [0.84, 0.92, 0.96], [0.06, 0.05, 0.05], [0.50, 0.42, 0.34], [0.20, 0.20, 0.86]], np.float32)
def conf_set(seed, n, t_a, t_b, mode):
    """n pieces. mode 'rain': spawned above the frame between t_a and t_b; 'pop': all at t_a from a burst point."""
    rng = np.random.default_rng(seed)
    d = dict(t=rng.uniform(t_a, t_b, n) if mode == "rain" else np.full(n, t_a, np.float32),
             x=rng.uniform(-80, W + 80, n), y=rng.uniform(-300, -40, n),
             depth=rng.uniform(0, 1, n) ** 1.6, col=rng.integers(0, len(CONF_COLS), n),
             a0=rng.uniform(0, 360, n), wa=rng.uniform(-420, 420, n), b0=rng.uniform(0, 6.28, n), wb=rng.uniform(5, 16, n),
             sway=rng.uniform(10, 60, n), ws=rng.uniform(1.5, 4.0, n), ar=rng.uniform(0.35, 0.75, n),
             vx=rng.normal(0, 1, n), vy=rng.normal(0, 1, n))
    return d

def draw_confetti(out, t, d, mode="rain", origin=(W / 2, H * 0.3), cover=1.0, guard=None):
    tau = t - d["t"]; alive = tau >= 0
    if not alive.any(): return out
    near = d["depth"]; size = 14 + 150 * near ** 2.2                                       # near pieces are big and soft
    if mode == "rain":
        vfall = (260 + 900 * near) if mode == "rain" and cover < 2 else 0
        vfall = vfall * (2.6 if cover >= 1.5 else 1.0)
        px = d["x"] + d["sway"] * np.sin(d["ws"] * tau + d["b0"]); py = d["y"] + vfall * tau
    else:
        sp = 900 + 1500 * near; ex = 1 - np.exp(-tau * 3.2)
        px = origin[0] + d["vx"] * sp * 1.4 * ex / 3.2 + d["sway"] * np.sin(d["ws"] * tau + d["b0"])
        py = origin[1] + (np.abs(d["vy"]) * 0.8 + 0.25) * sp * 0.75 * ex / 3.2 + (180 + 500 * near) * np.maximum(0, tau - 0.15) ** 1.4 * 1.6
    vis = alive & (py > -260) & (py < H + 260) & (px > -260) & (px < W + 260)
    if not vis.any(): return out
    lay_far = np.zeros((H, W, 3), np.uint8); a_far = np.zeros((H, W), np.uint8)
    lay_near = np.zeros((H, W, 3), np.uint8); a_near = np.zeros((H, W), np.uint8)
    order = np.argsort(near)
    for i in order:
        if not vis[i]: continue
        sz = size[i] * (1.25 if cover >= 1.5 else 1.0); ang = math.radians(d["a0"][i] + d["wa"][i] * tau[i]); fl = math.cos(d["b0"][i] + d["wb"][i] * tau[i])
        hw, hh = sz * 0.5, sz * 0.5 * d["ar"][i] * max(0.08, abs(fl))
        ca, sa_ = math.cos(ang), math.sin(ang)
        pts = np.array([[px[i] + ca * dx - sa_ * dy, py[i] + sa_ * dx + ca * dy] for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], np.float32)
        bright = 0.55 + 0.45 * abs(fl) + (0.55 if abs(fl) > 0.97 else 0.0)
        col = np.clip(CONF_COLS[d["col"][i]] * bright, 0, 1)
        far = near[i] < 0.55
        L_, A_ = (lay_far, a_far) if far else (lay_near, a_near)
        cv2.fillConvexPoly(L_, (pts * 4).astype(np.int32), tuple(int(c * 255) for c in col), cv2.LINE_AA, 2)
        cv2.fillConvexPoly(A_, (pts * 4).astype(np.int32), 255, cv2.LINE_AA, 2)
    o = out
    for L_, A_, blur in ((lay_far, a_far, 0.0), (lay_near, a_near, 2.4)):
        if not A_.any(): continue
        Lf = L_.astype(np.float32) / 255; Af = A_.astype(np.float32) / 255
        if blur: Lf = cv2.GaussianBlur(Lf, (0, 0), blur); Af = cv2.GaussianBlur(Af, (0, 0), blur)
        if guard is not None: Af = Af * guard
        o = o * (1 - Af[..., None]) + Lf * Af[..., None] * 1.0
    return o

def face_keep(s, f, grow=1.25):
    """1 everywhere except a feathered ellipse over the tracked face (particles never cross it)."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return None
    m = np.zeros((H // 4, W // 4), np.float32)
    cv2.ellipse(m, (int(fs[0] / 4), int(fs[1] / 4)), (int(fs[2] * 0.62 * grow / 4), int(fs[2] * 0.85 * grow / 4)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    return 1 - cv2.resize(cv2.GaussianBlur(m, (0, 0), 5), (W, H))

POP_PRE = 24
def pop_set():
    if "pop" not in _FP: _FP["pop"] = conf_set(1073, 190, 0.0, 0.0, "pop")
    return _FP["pop"]

def confetti_pop(A, B, j, f, sa, sb, pre=POP_PRE, post=2):
    """the confetti bursts in the sky over the banner; after the cut it carries on behind him (pop_behind)."""
    if j >= 0: return B
    return np.clip(draw_confetti(A, (j + pre + 1) / FPS, pop_set(), "pop", (W * 0.5, H * 0.02)), 0, 1)

def pop_behind(img, s, f, person):
    """a confetti burst from the top of the frame, between him and the crowd (his matte keeps it off him)."""
    k = f - s["f0"]
    if k >= 70 or person is None: return img
    c = draw_confetti(img, (k + POP_PRE + 1) / FPS, pop_set(), "pop", (W * 0.5, H * 0.02))
    pm = np.clip(person * 1.1, 0, 1)[..., None]
    return img * pm + c * (1 - pm)
TR2["confetti_pop"] = (confetti_pop, POP_PRE, 2)

# ---- THE LOOP: the confetti thickens over the lens on the bass drop-out bar and clears on frame 0 ---------------------
LOOP_F0 = None
def loop_w(f):
    f0 = fh(E.E_LOOP); u = (f - f0 + 1) / (E.DUR_F - f0)
    return smooth((u - 0.38) / 0.24) if f >= f0 else 0.0

_LV = {}
def frame0_plate():
    if "b" not in _LV: _LV["b"] = base107(SHOTS[0], SHOTS[0]["f0"])[0]
    return _LV["b"]

def confetti_loop(out, f, s):
    f0 = fh(E.E_LOOP)
    if f < f0: return out
    t = (f - f0) / FPS; T = (E.DUR_F - f0) / FPS
    if "rain" not in _FP: _FP["rain"] = conf_set(1074, 1100, -0.6, T - 0.95, "rain")
    w = loop_w(f)
    under = out if w <= 0 else (frame0_plate() if w >= 1 else out * (1 - w) + frame0_plate() * w)
    u = (f - f0 + 1) / (E.DUR_F - f0); thick = math.sin(math.pi * clamp(u / 0.95, 0, 1)) ** 0.8
    under = under * (1 - 0.10 * thick)
    o = draw_confetti(under, t, _FP["rain"], "rain", cover=1.6)
    fade = smooth((t - (T - 0.40)) / 0.36)                                                 # the stragglers fade as frame 0 arrives
    return np.clip(o * (1 - fade) + under * fade, 0, 1)

# ---- the STAMP: the newsprint strip and D-E-X-T-E-R, then the strip becomes the banner in the sky -------------------
STRIP_C, STRIP_W, STRIP_H, STRIP_ROT = (540, 870), 1010, 250, -3.0
_ST = {}
def strip_tex():
    if "s" in _ST: return _ST["s"]
    rng = np.random.default_rng(1075); h, w = STRIP_H + 60, STRIP_W + 60
    pt = paper_tex()[:h, :w]
    rgb = np.empty((h, w, 3), np.float32)
    for c in range(3): rgb[..., c] = PAPER[c] * (1 + pt * 0.06)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = cv2.resize(rng.standard_normal((h // 6, w // 6)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    torn = np.minimum(np.minimum(xx - 30 - n1 * 5, w - 30 - xx + n1 * 5), np.minimum(yy - 30 - n1 * 3, h - 30 - yy - n1 * 3))
    a = np.clip(torn / 1.5 + 0.5, 0, 1)
    rgb *= (0.93 + 0.07 * np.clip(torn / 40, 0, 1))[..., None]                             # the edges a touch darker
    _ST["s"] = np.dstack([rgb, a]).astype(np.float32)
    lets, xs = [], []
    for c in "DEXTER":
        m = text_mask(c, F_BLACK, 205, tracking=0); lets.append(m)
    tot = sum(m.shape[1] for m in lets) + 26 * 5; x = w / 2 - tot / 2
    for m in lets: xs.append(x + m.shape[1] / 2); x += m.shape[1] + 26
    rgi = np.random.default_rng(1076)
    inks = []
    for m in lets:                                                                         # letterpress ink: uneven, a little bite
        sp = cv2.resize(rgi.random((m.shape[0] // 3 + 1, m.shape[1] // 3 + 1)).astype(np.float32), (m.shape[1], m.shape[0]))
        inks.append(np.clip(m * (0.82 + 0.18 * sp) * (1 - (sp < 0.06) * 0.6), 0, 1))
    _ST["lets"] = (inks, xs); return _ST["s"]

def strip_canvas(t, stamps):
    """the strip (rgba, its own pixel space) with the letters stamped by time t."""
    base = strip_tex().copy(); inks, xs = _ST["lets"]; h, w = base.shape[:2]
    for (wd, tw), m, xc in zip(stamps, inks, xs):
        k = (t - tw) * FPS
        if k < 0: continue
        v = clamp(k / 4.0, 0, 1)
        if v < 1:                                                                          # the stamp coming down
            sc = 1.9 - 0.9 * ein(v, 2.2); mm = cv2.resize(m, None, fx=sc, fy=sc); mm = cv2.GaussianBlur(mm, (0, 0), 0.1 + 6 * (1 - v)) * v
        else: mm = m
        hh, ww = mm.shape; x0 = int(xc - ww / 2); y0 = int(h / 2 - hh / 2 + 6)
        ys, xs_ = slice(max(0, y0), min(h, y0 + hh)), slice(max(0, x0), min(w, x0 + ww))
        sub = mm[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        if v >= 1:                                                                         # the deboss: pressed into the paper
            dm = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sh = np.clip(np.roll(dm, 3, 0) - dm, 0, 1) * 0.35; hl = np.clip(np.roll(dm, -3, 0) - dm, 0, 1) * 0.10
            base[ys, xs_, :3] *= (1 - sh)[..., None]; base[ys, xs_, :3] += hl[..., None]
            spread = 1 + 0.10 * math.exp(-(k - 4) / 3)                                      # ink spreads at the hit, then settles
            sub = np.clip(sub * spread, 0, 1)
        base[ys, xs_, :3] = base[ys, xs_, :3] * (1 - sub[..., None]) + INK * sub[..., None]
    return base

def put_strip(out, rgba, cx, cy, sc, rot, a=1.0, shadow=0.45):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    pa = cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = pa[..., 3:4] * a
    if shadow > 0:
        sh = cv2.GaussianBlur(np.roll(np.roll(pa[..., 3], 16, 0), 10, 1), (0, 0), 14) * shadow * a
        out = out * (1 - sh[..., None])
    return out * (1 - al) + pa[..., :3] * al

def banner_target():
    """where the banner's DEXTER sits on screen in the banner shot (centre, scale vs the strip, rotation)."""
    return (785.0, 980.0), 0.53, -4.1

def text_stamp(out, f, tx):
    t = f / FPS; stamps = [(w, wt) for w, wt, _ in tx["words"]]
    t_in = next(wt for tx_ in E.TEXT if tx_["style"] == "cap" for w_, wt, _ in tx_["words"] if w_ == "CAPS") - 0.02   # it slaps on with "CAPS"
    t_cut = E.th(48); t_end = t_cut + 0.80
    if t < t_in or t > t_end: return out
    rgba = strip_canvas(min(t, t_cut + 0.2), stamps)
    k = (t - t_in) * FPS; v = clamp(k / 5.0, 0, 1)
    sc = 1.28 - 0.28 * eout(v, 3) + (0.02 * math.sin(k * 0.9) * math.exp(-k / 6) if v >= 1 else 0)
    cx, cy = STRIP_C; rot = STRIP_ROT; a = min(1.0, k / 3.0); shake = 0.0
    for _, tw in stamps:                                                                   # each stamp shakes the strip
        dk = (t - tw) * FPS - 4
        if 0 <= dk < 8: shake = max(shake, 5 * math.exp(-dk / 2.5))
    cy += shake * math.sin(f * 2.1)
    if t > t_cut - 0.02:                                                                   # it flies into the sky onto the banner
        w_ = smooth((t - t_cut + 0.02) / 0.45)
        (bx, by), bs, br = banner_target()
        cx, cy = cx + (bx - cx) * w_, cy + (by - cy) * w_; sc = sc + (bs - sc) * w_; rot = rot + (br - rot) * w_
        a = a * (1 - smooth((t - t_cut - 0.42) / 0.36))
    return put_strip(out, rgba, cx, cy, sc, rot, a, 0.45 * (1 - smooth((t - t_cut) / 0.3)))

def text_cap(out, f, tx, person=None):
    """the v9 caption (the approved construction), with an optional per-caption ys=(line0, line1)."""
    t = f / FPS; words = tx["words"]; t_in = max(words[0][1], tx.get("from", -1))
    if t < t_in - 0.02 or t > tx["end"] + 0.01: return out
    big = tx.get("big"); sizes = [92, 120] if big else [88, 114]
    ys = tx.get("ys") or ((1368, 1492) if big else (1380, 1496))
    emph = tx.get("emph", []); fr = tx.get("from", -1)
    a_out = 1 - smooth((t - (tx["end"] - 0.16)) / 0.16)
    out = out * cap_scrim(ys[0] - 70, ys[1] + 70, 0.34 * a_out * smooth((t - t_in + 0.05) / 0.25))
    for ln in (0, 1):
        ws = [(w, max(wt, fr)) for w, wt, l in words if l == ln]
        if not ws: continue
        sz = sizes[ln]
        for _ in range(6):                                                                 # auto-fit the line to 940 px
            ims = [cap_word(w, sz, w in emph) for w, _ in ws]
            gap = int(sz * 0.26); widths = [im.shape[1] - 72 for im in ims]
            tot = sum(widths) + gap * (len(ims) - 1)
            if tot <= 940: break
            sz = int(sz * 940 / tot) - 1
        x = W / 2 - tot / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = eout(clamp((t - wt) / 0.17, 0, 1), 2.4)
            o_im = im if a_out > 0.98 else cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - a_out))
            out = ease_word(out, o_im, x + wd / 2, ys[ln] - 14 * (1 - a_out), v, a_out, rise=30)
            x += wd + gap
    return out

def text107(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        if tx["style"] == "cap": out = text_cap(out, f, tx, None)
        elif tx["style"] == "stamp": out = text_stamp(out, f, tx)
    return out

# ---- the frame ----------------------------------------------------------------------------------------------------
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base107(s, f)
    out = text107(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge107(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge107(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "confetti_loop": out = confetti_loop(out, f, s)
    out = beat_fx(out, f)
    out = text107(out, f, s, False)
    out = flash_governor(out)
    return (np.clip(finish107(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 rev 2 (owner notes; overrides above)
# ---- the camera rests through the break (the ending is smooth) and during the TV ------------------------------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 54) and not (6.5 <= e < 9.7) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- SPECIAL REPORT: the shot is on a TV; the channel flips; we push back through the screen -------------------------
TV_W, TV_H = 860.0, 645.0                                                                  # the 4:3 screen at the TV's own scale
Z_FULL = W / TV_W                                                                          # the zoom where the screen fills the width
_TV = {}
def tv_assets():
    """(casing rgba at scale 1 around a screen centred on the frame, chyron rgba in screen pixels, scanlines)."""
    if "c" in _TV: return _TV["c"]
    bw, bh = 1000, 900; cx, cy = W / 2, H / 2 + 60                                          # the body: the screen sits high in it
    cas = np.zeros((H, W, 4), np.float32)
    body = np.zeros((H, W), np.float32)
    cv2.rectangle(body, (int(cx - bw / 2), int(cy - bh / 2 - 60)), (int(cx + bw / 2), int(cy + bh / 2 - 60)), 1.0, -1)
    body = cv2.GaussianBlur(body, (0, 0), 6); body = np.clip(body * 1.6 - 0.3, 0, 1)
    scr = np.zeros((H, W), np.float32)
    cv2.rectangle(scr, (int(W / 2 - TV_W / 2 + 22), int(H / 2 - TV_H / 2 + 22)), (int(W / 2 + TV_W / 2 - 22), int(H / 2 + TV_H / 2 - 22)), 1.0, -1)
    scr = np.clip(cv2.GaussianBlur(scr, (0, 0), 14) * 1.9 - 0.45, 0, 1)                    # rounded screen corners
    yy = (_GY - (cy - bh / 2 - 60)) / bh
    xx = (_GX - (cx - bw / 2)) / bw
    shade = 0.20 + 0.10 * (1 - np.clip(yy, 0, 1)) + 0.04 * np.sin(np.pi * np.clip(xx, 0, 1))   # lit from above and the front
    shade = shade + 0.16 * np.exp(-((_GY - (cy - bh / 2 - 54)) / 5) ** 2) + 0.06 * np.exp(-((_GX - (cx - bw / 2 + 6)) / 5) ** 2)   # edge highlights
    shade = shade - 0.06 * np.exp(-((_GY - (cy + bh / 2 - 66)) / 6) ** 2)                 # the bottom edge in shadow
    rim = np.exp(-((cv2.GaussianBlur(scr, (0, 0), 3) - 0.5) / 0.18) ** 2) * 0.16             # the bevel round the glass
    for c in range(3): cas[..., c] = shade * (0.95 + 0.05 * c) + rim
    led = np.exp(-(((_GX - (cx + bw / 2 - 90)) / 7) ** 2 + ((_GY - (cy + bh / 2 - 105)) / 7) ** 2))
    cas[..., :3] += led[..., None] * SPOT * 1.4
    for k in range(5): cv2.line(cas, (int(cx - bw / 2 + 70 + 34 * k), int(cy + bh / 2 - 112)), (int(cx - bw / 2 + 92 + 34 * k), int(cy + bh / 2 - 112)), (0.30, 0.30, 0.30, 1.0), 3, cv2.LINE_AA)
    cas[..., 3] = body * (1 - scr)
    cas[..., :3] *= cas[..., 3:4]
    sw, sh = int(TV_W), int(TV_H); ch = np.zeros((sh, sw, 4), np.float32)
    bar_y = int(sh * 0.74); cv2.rectangle(ch, (0, bar_y), (int(sw * 0.36), bar_y + 50), tuple(float(v) for v in SPOT) + (1.0,), -1)
    cv2.rectangle(ch, (int(sw * 0.36), bar_y), (sw, bar_y + 50), tuple(float(v) for v in PAPER) + (1.0,), -1)
    cv2.rectangle(ch, (0, bar_y + 50), (sw, bar_y + 92), tuple(float(v) for v in INK) + (0.92,), -1)
    def put_txt(word, font, size, col, x, y):
        m = text_mask(word, font, size, tracking=1); h_, w_ = m.shape; y0 = int(y - h_ / 2)
        sub = ch[y0:y0 + h_, x:x + w_]; mm = m[:sub.shape[0], :sub.shape[1]]
        sub[..., :3] = sub[..., :3] * (1 - mm[..., None]) + np.array(col, np.float32) * mm[..., None]; sub[..., 3] = np.maximum(sub[..., 3], mm)
    put_txt("SPECIAL REPORT", F_BLACK, 30, (0.97, 0.97, 0.97), 14, bar_y + 25)
    put_txt("BAY HARBOR BUTCHER STILL AT LARGE", F_BLACK, 28, tuple(float(v) for v in INK), int(sw * 0.36) + 14, bar_y + 25)
    put_txt("POLICE URGE RESIDENTS TO STAY ALERT · FBI JOINS INVESTIGATION", F_XB, 22, tuple(PAPER), 14, bar_y + 71)
    cv2.rectangle(ch, (22, 22), (110, 62), tuple(float(v) for v in SPOT) + (1.0,), -1); put_txt("LIVE", F_BLACK, 26, (0.97, 0.97, 0.97), 34, 42)
    scan = (1 - 0.10 * (np.arange(sh) % 3 == 0))[:, None].astype(np.float32)
    _TV["c"] = (cas, ch, scan, scr); return _TV["c"]

def tv_frame(content, Z, mask_h, chy, static, glow=1.0, f=0, scan_a=1.0, glass=1.0):
    """content (a full frame) on the TV: Z = zoom of the TV (Z_FULL: the screen is the frame's width); mask_h = the
    visible height of the screen window in output px (letterbox closing/opening); chy 0..1 chyron in; static 0..1."""
    cas, ch, scan, scr = tv_assets()
    k = Z / Z_FULL                                                                         # content scale: 1 at Z_FULL
    M = np.float32([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]])
    c = cv2.warpAffine(content, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    sw, sh = TV_W * Z, TV_H * Z                                                            # the screen window
    win_h = min(mask_h, sh) if Z >= Z_FULL - 1e-3 else sh
    sc = cv2.warpAffine(scr, np.float32([[Z, 0, W / 2 * (1 - Z)], [0, Z, H / 2 * (1 - Z)]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if Z >= Z_FULL - 1e-3 and mask_h > sh:                                                 # still opening: a plain letterbox
        sc = np.clip((mask_h / 2 - np.abs(_GY - H / 2)) / 3, 0, 1).astype(np.float32)
    # the screen: scanlines, phosphor, the chyron, static, the glass
    scr_img = c.copy()
    if scan_a > 0:
        sl = cv2.resize(np.repeat(scan, int(TV_W), 1), None, fx=Z, fy=Z, interpolation=cv2.INTER_LINEAR)
        y0 = int(H / 2 - sl.shape[0] / 2); x0 = int(W / 2 - sl.shape[1] / 2)
        full = np.ones((H, W), np.float32); ys, xs = slice(max(0, y0), min(H, y0 + sl.shape[0])), slice(max(0, x0), min(W, x0 + sl.shape[1]))
        full[ys, xs] = sl[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        scr_img = scr_img * (1 - scan_a + scan_a * full)[..., None]
    if chy > 0:
        Mc = np.float32([[Z, 0, W / 2 - TV_W * Z / 2 - (1 - eout(chy, 3)) * 400 * Z], [0, Z, H / 2 - TV_H * Z / 2]])
        cw = cv2.warpAffine(ch, Mc, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); a = cw[..., 3:4] * min(1.0, chy * 1.5)
        scr_img = scr_img * (1 - a) + cw[..., :3] * a
    if static > 0:
        rng = np.random.default_rng(f * 7 + 3); nz = cv2.resize(rng.random((H // 6, W // 6)).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST)
        roll = 0.5 + 0.5 * np.sin((_GY / H * 3 + f * 0.37) * 2 * math.pi)
        stc = (nz * 0.75 + 0.15) * (0.75 + 0.25 * roll)
        scr_img = scr_img * (1 - static) + stc[..., None] * PAPER * static
    vig = 1 - 0.35 * glass * np.clip(((_GX - W / 2) / (sw / 2 + 1)) ** 2 + ((_GY - H / 2) / (sh / 2 + 1)) ** 2, 0, 1) ** 1.5
    refl = np.exp(-(((_GX - W / 2) * 0.6 + (_GY - H / 2 + sh * 0.25)) / (sw * 0.18 + 1)) ** 2) * 0.06 * glass   # a soft glass reflection (fades with the letterbox)
    scr_img = scr_img * vig[..., None] + refl[..., None]
    # the room: dark, lit by the screen
    room = np.zeros((H, W, 3), np.float32) + INK * 0.6
    lum_s = float(cv2.resize(c, (8, 8), interpolation=cv2.INTER_AREA).mean())
    gl = np.exp(-(((_GX - W / 2) / (sw * 1.05 + 1)) ** 2 + ((_GY - H / 2) / (sh * 1.5 + 1)) ** 2)) * (0.16 + 0.35 * lum_s) * glow
    room = room + gl[..., None] * PAPER
    casz = cv2.warpAffine(cas, np.float32([[Z, 0, W / 2 * (1 - Z)], [0, Z, H / 2 * (1 - Z)]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    o = room * (1 - casz[..., 3:4]) + casz[..., :3]
    return np.clip(o * (1 - sc[..., None]) + scr_img * sc[..., None], 0, 1)

def broadcast(A, B, j, f, sa, sb, pre=36, post=36):
    Zmin = 0.92
    if j < 0:
        u = (j + pre + 1) / pre
        if u < 0.33:                                                                       # the picture closes into a TV image
            mh = H - (H - TV_H * Z_FULL) * smooth(u / 0.33)
            return tv_frame(A, Z_FULL, mh, 0.0, 0.0, f=f, scan_a=smooth(u / 0.33), glass=smooth(u / 0.33))
        w = smooth((u - 0.33) / 0.50); Z = Z_FULL + (Zmin - Z_FULL) * w                     # the TV pulls back into a dark room
        st = smooth((u - 0.86) / 0.14) * 0.85                                              # the channel starts to flip
        return tv_frame(A, Z, TV_H * Z, smooth((u - 0.30) / 0.30), st, f=f)
    v = (j + 1) / post
    st = 0.85 * (1 - smooth(v / 0.16))
    if v < 0.70:                                                                           # the new channel: him; we push in
        w = smooth((v - 0.14) / 0.56); Z = Zmin + (Z_FULL - Zmin) * w
        return tv_frame(B, Z, TV_H * Z, 1 - smooth((v - 0.20) / 0.30), st, f=f)
    w = smooth((v - 0.70) / 0.30); mh = TV_H * Z_FULL + (H - TV_H * Z_FULL) * w            # the screen opens to the frame
    return tv_frame(B, Z_FULL, mh, 0.0, 0.0, f=f, scan_a=1 - w, glass=1 - w)
TR2["broadcast"] = (broadcast, 36, 36)

# ---- HEADSPIN onto a centred shot: the turn decelerates about his face -------------------------------------------------
def spin_about(img, ang, z, cx, cy, n=1, spread=0.0):
    acc = None
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread if n > 1 else ang
        M = cv2.getRotationMatrix2D((cx, cy), a, z); M[0, 2] += W / 2 - cx; M[1, 2] += H / 2 - cy
        M[0, 2] += (cx - W / 2); M[1, 2] += (cy - H / 2)
        r = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = r if acc is None else acc + r
    return acc / n

def headspin(A, B, j, f, sa, sb, pre=20, post=24):
    N = pre + post; q = (j + pre + 0.5) / N
    phi = 720 * q * q * (3 - 2 * q); dphi = 720 * 6 * q * (1 - q) / N
    z = 1 + 0.28 * math.sin(math.pi * q)
    if j < 0: img, ang, cx, cy = A, -phi, W / 2, H / 2
    else:
        fs = face_scr(sb, f) if sb.get("face") is not None else None
        cx, cy = (fs[0], fs[1]) if fs else (W / 2, H / 2); img, ang = B, -(phi - 720)
    n = int(clamp(dphi / 4, 1, 9))
    o = spin_about(img, ang, z, cx, cy, n, dphi)
    if dphi > 8: o = radial_blur(o, cx, cy, 1.0, 1.0 + 0.0025 * dphi, 4)
    return np.clip(o, 0, 1)
TR2["headspin"] = (headspin, 20, 24)

# ---- THE MASSES SPELL HIS NAME (the loop): the parade's confetti gathers into DEXTER, holds, bursts into frame 0 -----
NL_G0, NL_G1, NL_B = 58.4, 60.4, 62.3                                                       # edit half-beats: gather, formed, burst
_NL = {}
def name_targets():
    if "t" in _NL: return _NL["t"]
    m = text_mask("DEXTER", F_BLACK, 300, tracking=10); m = squeeze(m, 1000 / m.shape[1])
    h, w = m.shape; cx, cy = W / 2, 1110
    ys, xs = np.nonzero(m > 0.6); rng = np.random.default_rng(1077); n = 1050
    pick = rng.choice(len(xs), n, replace=False)
    tx = (xs[pick] - w / 2 + cx).astype(np.float32); ty = (ys[pick] - h / 2 + cy).astype(np.float32)
    side = np.where(rng.random(n) < 0.5, -1.0, 1.0).astype(np.float32)
    d = dict(tx=tx, ty=ty, side=side, x0=(W / 2 + side * rng.uniform(W * 0.62, W * 1.05, n)).astype(np.float32),
             y0=rng.uniform(820, 1650, n).astype(np.float32), vf=rng.uniform(380, 900, n).astype(np.float32),
             delay=rng.uniform(0, 0.28, n).astype(np.float32),
             size=rng.uniform(18, 32, n).astype(np.float32), ar=rng.uniform(0.40, 0.70, n).astype(np.float32),
             a0=rng.uniform(0, 360, n).astype(np.float32), wa=rng.uniform(-240, 240, n).astype(np.float32),
             b0=rng.uniform(0, 6.28, n).astype(np.float32), wb=rng.uniform(5, 13, n).astype(np.float32),
             col=rng.choice([1, 1, 2, 2, 1, 0, 0, 5], n), sw=rng.uniform(-1, 1, n).astype(np.float32),
             bv=rng.uniform(0.8, 1.3, n).astype(np.float32))
    _NL["t"] = d; return d

def draw_pieces(out, px, py, size, ang, flut, cols, alpha=None, blur_big=True):
    """lit paper pieces (fluttering quads), far/near layers; size in px, ang in radians, flut = cos of the flutter."""
    lay = [np.zeros((H, W, 3), np.uint8), np.zeros((H, W, 3), np.uint8)]; al = [np.zeros((H, W), np.uint8), np.zeros((H, W), np.uint8)]
    for i in np.argsort(size):
        x, y, sz = px[i], py[i], size[i]
        if x < -sz or x > W + sz or y < -sz or y > H + sz or (alpha is not None and alpha[i] < 0.02): continue
        hw, hh = sz * 0.5, sz * 0.5 * 0.55 * max(0.10, abs(flut[i]))
        ca, sa_ = math.cos(ang[i]), math.sin(ang[i])
        pts = np.array([[x + ca * dx - sa_ * dy, y + sa_ * dx + ca * dy] for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], np.float32)
        bright = 0.60 + 0.40 * abs(flut[i]) + (0.45 if abs(flut[i]) > 0.97 else 0.0)
        col = np.clip(CONF_COLS[cols[i]] * bright, 0, 1); a8 = int(255 * (1.0 if alpha is None else alpha[i]))
        L = 1 if (blur_big and sz > 70) else 0
        cv2.fillConvexPoly(lay[L], (pts * 4).astype(np.int32), tuple(int(c * 255) for c in col), cv2.LINE_AA, 2)
        cv2.fillConvexPoly(al[L], (pts * 4).astype(np.int32), a8, cv2.LINE_AA, 2)
    o = out
    for L, bl in ((0, 0.0), (1, 3.0)):
        if not al[L].any(): continue
        Lf = lay[L].astype(np.float32) / 255; Af = al[L].astype(np.float32) / 255
        if bl: Lf = cv2.GaussianBlur(Lf, (0, 0), bl); Af = cv2.GaussianBlur(Af, (0, 0), bl)
        o = o * (1 - Af[..., None]) + Lf * Af[..., None]
    return o

def name_loop(out, f, s):
    t = f / FPS; e = t / E.HB
    if e < NL_G0 - 1.5: return out
    d = name_targets(); tg0, tg1, tb, T = E.th(NL_G0), E.th(NL_G1), E.th(NL_B), E.DUR
    # the pieces fall in from above the frame, then gather into the letters (staggered, with a curl)
    tf = t - (tg0 - 1.0)
    fx_ = d["x0"] - d["side"] * d["vf"] * 0.55 * tf; fy_ = d["y0"] + 60 * np.sin(1.7 * tf + d["b0"])     # drifting in from the sides
    w = np.clip((t - tg0 - d["delay"]) / (tg1 - tg0 - 0.28), 0, 1); we = w * w * (3 - 2 * w)
    curl = np.sin(np.pi * we) * 90 * d["sw"]
    px = fx_ + (d["tx"] - fx_) * we + curl; py = fy_ + (d["ty"] - fy_) * we
    ang = np.radians(d["a0"] + d["wa"] * t * (1 - 0.75 * we)); flut = np.cos(d["b0"] + d["wb"] * t)
    size = d["size"].copy(); alpha = None
    plate = out
    hold = smooth((t - tg0 - 0.3) / 0.5) * (1 - smooth((t - tb) / 0.25))
    if hold > 0:                                                                          # the parade steps back so the name reads
        soft = cv2.GaussianBlur(cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 2.5)
        plate = out * (1 - 0.45 * hold) + cv2.resize(soft, (W, H)) * (0.45 * hold)
        plate = plate * (1 - 0.30 * hold)
    if t >= tb:                                                                           # the burst: toward the lens and out
        b = clamp((t - tb) / (T - tb - 0.06), 0, 1); be = b ** 1.6
        dx, dy = d["tx"] - W / 2, d["ty"] - 1110
        px = d["tx"] + dx * 3.2 * be * d["bv"] + d["sw"] * 160 * be; py = d["ty"] + np.abs(dy) * 3.0 * be * d["bv"] + 260 * be
        size = d["size"] * (1 + 9 * be * d["bv"])
        alpha = np.clip(1 - (b - 0.55) / 0.40, 0, 1) * np.ones_like(size)
        wz = smooth((t - tb - 0.02) / 0.30)                                               # under it: frame 0
        if wz > 0: plate = plate * (1 - wz) + frame0_plate() * wz
    o = draw_pieces(plate, px, py, size, ang, flut, d["col"], alpha)
    if t > T - 0.08: o = o * 0 + frame0_plate() if t > T - 1.5 / FPS else o                 # the last frame is frame 0's picture
    return np.clip(o, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base107(s, f)
    out = text107(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge107(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge107(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "name_loop": out = name_loop(out, f, s)
    out = beat_fx(out, f)
    out = text107(out, f, s, False)
    out = flash_governor(out)
    return (np.clip(finish107(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 rev 3 (owner notes; overrides above)
# ---- DEXTER on the 16th grid: each letter lands ON its hit (the platen comes down in the 3 frames before) -------------
STAMP_DROP = 3
def strip_canvas(t, stamps):
    """the strip (rgba, its own pixel space) with the letters stamped by time t."""
    base = strip_tex().copy(); inks, xs = _ST["lets"]; h, w = base.shape[:2]
    for (wd, tw), m, xc in zip(stamps, inks, xs):
        k = (t - tw) * FPS + STAMP_DROP
        if k < 0: continue
        v = clamp(k / STAMP_DROP, 0, 1)
        if v < 1:                                                                          # the stamp coming down
            sc = 1.6 - 0.6 * ein(v, 2.0); mm = cv2.resize(m, None, fx=sc, fy=sc); mm = cv2.GaussianBlur(mm, (0, 0), 0.1 + 4 * (1 - v)) * (0.35 + 0.65 * v)
        else: mm = m
        hh, ww = mm.shape; x0 = int(xc - ww / 2); y0 = int(h / 2 - hh / 2 + 6)
        ys, xs_ = slice(max(0, y0), min(h, y0 + hh)), slice(max(0, x0), min(w, x0 + ww))
        sub = mm[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        if v >= 1:                                                                         # the deboss: pressed into the paper
            dm = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sh = np.clip(np.roll(dm, 3, 0) - dm, 0, 1) * 0.35; hl = np.clip(np.roll(dm, -3, 0) - dm, 0, 1) * 0.10
            base[ys, xs_, :3] *= (1 - sh)[..., None]; base[ys, xs_, :3] += hl[..., None]
            sub = np.clip(sub * (1 + 0.10 * math.exp(-(k - STAMP_DROP) / 3)), 0, 1)           # ink spreads at the hit, then settles
        base[ys, xs_, :3] = base[ys, xs_, :3] * (1 - sub[..., None]) + INK * sub[..., None]
    return base

def text_stamp(out, f, tx):
    t = f / FPS; stamps = [(w, wt) for w, wt, _ in tx["words"]]
    t_in = next(wt for tx_ in E.TEXT if tx_["style"] == "cap" for w_, wt, _ in tx_["words"] if w_ == "CAPS") - 0.02   # it slaps on with "CAPS"
    t_cut = E.th(48); t_end = t_cut + 0.80
    if t < t_in or t > t_end: return out
    rgba = strip_canvas(min(t, t_cut + 0.2), stamps)
    k = (t - t_in) * FPS; v = clamp(k / 5.0, 0, 1)
    sc = 1.28 - 0.28 * eout(v, 3) + (0.02 * math.sin(k * 0.9) * math.exp(-k / 6) if v >= 1 else 0)
    cx, cy = STRIP_C; rot = STRIP_ROT; a = min(1.0, k / 3.0); shake = 0.0
    for _, tw in stamps:                                                                   # each hit shakes the strip
        dk = (t - tw) * FPS
        if 0 <= dk < 8: shake = max(shake, 5 * math.exp(-dk / 2.5))
    cy += shake * math.sin(f * 2.1)
    if t > t_cut - 0.02:                                                                   # it flies into the sky onto the banner
        w_ = smooth((t - t_cut + 0.02) / 0.45)
        (bx, by), bs, br = banner_target()
        cx, cy = cx + (bx - cx) * w_, cy + (by - cy) * w_; sc = sc + (bs - sc) * w_; rot = rot + (br - rot) * w_
        a = a * (1 - smooth((t - t_cut - 0.42) / 0.36))
    return put_strip(out, rgba, cx, cy, sc, rot, a, 0.45 * (1 - smooth((t - t_cut) / 0.3)))

# ---- SPATTER ANALYSIS (new graphic, the kill table): blood spatters across the lens, strings run back from every
# ---- stain along its flight line and lock on the beat at the POINT OF ORIGIN, where his face is about to appear --------
SP_F0, SP_STR, SP_LOCK = 99, 106, 124                                                      # the spatter, the strings, the lock (e6)
BLOOD_HI = np.array([0.08, 0.06, 0.66], np.float32); BLOOD_LO = np.array([0.02, 0.01, 0.20], np.float32)
STRING_C = np.array([0.17, 0.16, 0.93], np.float32)
_SP = {}
def sp_origin():
    if "o" not in _SP:
        sb = [s_ for s_ in SHOTS if s_["n"] == "shh"][0]; fs = face_scr(sb, sb["f0"])
        _SP["o"] = (float(fs[0]), float(fs[1])) if fs else (W / 2, 640.0)
    return _SP["o"]

def sp_geom():
    if "g" in _SP: return _SP["g"]
    ox, oy = sp_origin(); rng = np.random.default_rng(1077)
    spec = [(-160, 430, 24, 28), (-125, 360, 18, 40), (-75, 440, 22, 24), (-35, 330, 26, 35), (-5, 420, 16, 20),
            (30, 360, 20, 46), (70, 310, 15, 38), (110, 330, 14, 50), (150, 300, 17, 33), (175, 380, 21, 22)]
    drops = []
    for i, (th_, r, w, al) in enumerate(spec):
        w = w * 1.7; a = math.radians(th_); ux, uy = math.cos(a), math.sin(a); L = w / math.sin(math.radians(al))
        sats = list(zip(rng.uniform(1.15, 2.0, 3) * L, rng.uniform(2.6, 6.0, 3), rng.uniform(-0.25, 0.25, 3)))
        drops.append(dict(x=ox + r * ux, y=oy + r * uy, ux=ux, uy=uy, w=w, L=L, al=al, sats=sats,
                          t=SP_F0 + int(rng.integers(0, 6)), s=SP_STR + 2 * i, lab=i in (0, 3, 5, 8)))
    ang = rng.uniform(-math.pi, math.pi, 70); rr = rng.uniform(170, 560, 70)
    mist = [(ox + q * math.cos(a), oy + q * math.sin(a), rad, SP_F0 + int(dt)) for a, q, rad, dt in
            zip(ang, rr, rng.uniform(1.8, 4.8, 70), rng.integers(0, 7, 70)) if oy + q * math.sin(a) < 1200]
    _SP["g"] = (drops, mist); return _SP["g"]

def sp_text(key, txt, size, col):
    if key not in _SP: _SP[key] = shadowed(text_mask(txt, F_MONO, size), col, blur=4, sa=0.8)
    return _SP[key]

def paste_rgba(out, rg, x, y, a=1.0):
    h, w = rg.shape[:2]; x0, y0 = int(round(x)), int(round(y))
    ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
    if ys.stop <= ys.start or xs.stop <= xs.start: return out
    sub = rg[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]; al = sub[..., 3:4] * a
    out[ys, xs] = out[ys, xs] * (1 - al) + sub[..., :3] * al
    return out

SS = 16                                                                                    # cv2 sub-pixel shift (4 bits)
def P_(x, y): return (int(round(x * SS)), int(round(y * SS)))

def spatter_fx(img, f):
    if f < SP_F0: return img
    drops, mist = sp_geom(); ox, oy = sp_origin(); out = img.copy()
    # the blood on the lens: elongated stains (round head, body along the flight line, a tapering tail), satellites, mist
    m = np.zeros((H, W), np.uint8)
    for d in drops:
        if f < d["t"]: continue
        g = eout(clamp((f - d["t"] + 1) / 3.0, 0, 1), 2)
        L = d["w"] + (d["L"] - d["w"]) * g; ang = math.degrees(math.atan2(d["uy"], d["ux"]))
        cx, cy = d["x"] + d["ux"] * (L / 2 - d["w"] / 2), d["y"] + d["uy"] * (L / 2 - d["w"] / 2)
        cv2.ellipse(m, P_(cx, cy), P_(L / 2, d["w"] / 2), ang, 0, 360, 255, -1, cv2.LINE_AA, 4)
        tx_, ty_ = d["x"] + d["ux"] * (L - d["w"] * 0.6), d["y"] + d["uy"] * (L - d["w"] * 0.6)
        ex, ey = tx_ + d["ux"] * 0.55 * L * g, ty_ + d["uy"] * 0.55 * L * g; px_, py_ = -d["uy"], d["ux"]; hw = d["w"] * 0.30
        tri = np.array([P_(tx_ + px_ * hw, ty_ + py_ * hw), P_(tx_ - px_ * hw, ty_ - py_ * hw), P_(ex, ey)], np.int32)
        cv2.fillConvexPoly(m, tri, 255, cv2.LINE_AA, 4)
        for dd, rad, side in d["sats"]:
            sx, sy = d["x"] + (d["ux"] + side * px_) * dd * g, d["y"] + (d["uy"] + side * py_) * dd * g
            cv2.circle(m, P_(sx, sy), int(rad * SS), 255, -1, cv2.LINE_AA, 4)
    for x, y, rad, t_ in mist:
        if f >= t_: cv2.circle(m, P_(x, y), int(rad * SS), 255, -1, cv2.LINE_AA, 4)
    M = m.astype(np.float32) / 255
    inner = cv2.GaussianBlur(M, (0, 0), 3.0)
    col = BLOOD_LO + (BLOOD_HI - BLOOD_LO) * np.clip(inner * 1.3, 0, 1)[..., None]
    hgt = cv2.GaussianBlur(M, (0, 0), 2.2); gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip((-gx * 0.55 - gy * 0.85) * 2.4, 0, 1) ** 2 * M * 0.75
    out = out * (1 - M[..., None]) + col * M[..., None] + spec[..., None] * PAPER
    # the strings: taut red string from each stain's head back along its flight line (a pin at the stain)
    sm = np.zeros((H, W), np.uint8); sh = np.zeros((H, W), np.uint8); pins = []
    for d in drops:
        if f < d["s"]: continue
        p = eout(clamp((f - d["s"]) / 9.0, 0, 1), 2.2)
        ex, ey = d["x"] + (ox - d["x"]) * p, d["y"] + (oy - d["y"]) * p
        cv2.line(sm, P_(d["x"], d["y"]), P_(ex, ey), 255, 5, cv2.LINE_AA, 4)
        cv2.line(sh, P_(d["x"] + 4, d["y"] + 5), P_(ex + 4, ey + 5), 255, 5, cv2.LINE_AA, 4)
        pins.append(d)
    if pins:
        S_ = cv2.GaussianBlur(sh.astype(np.float32) / 255, (0, 0), 1.6) * 0.45
        out = out * (1 - S_[..., None])
        Sm = sm.astype(np.float32) / 255
        out = out * (1 - Sm[..., None]) + STRING_C * Sm[..., None]
        for d in pins:
            cv2.circle(out, P_(d["x"], d["y"]), 10 * SS, tuple(float(v) for v in INK), -1, cv2.LINE_AA, 4)
            cv2.circle(out, P_(d["x"] - 3, d["y"] - 3), 3 * SS, tuple(float(v) for v in PAPER), -1, cv2.LINE_AA, 4)
            if d["lab"]:                                                                   # the impact angle, read off the stain
                rg = sp_text(f"al{d['al']}", f"{d['al']}\u00b0", 46, PAPER)
                px_, py_ = -d["uy"], d["ux"]; side = 1 if (d["x"] + px_ * 40) > ox else -1
                lx = d["x"] + side * px_ * (d["w"] + 46) - rg.shape[1] / 2; ly = d["y"] + side * py_ * (d["w"] + 46) - rg.shape[0] / 2
                out = paste_rgba(out, rg, lx, ly, smooth((f - d["s"] - 2) / 5.0))
    # the lock: a ring with a crosshair at the point of origin, a pulse, and the tag
    if f >= SP_LOCK:
        q = f - SP_LOCK; sc = eout(clamp(q / 6.0, 0, 1), 3); r = 48 * (1.6 - 0.6 * sc)
        lay = np.zeros((H, W), np.uint8)
        cv2.circle(lay, P_(ox, oy), int(r * SS), 255, 5, cv2.LINE_AA, 4)
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv2.line(lay, P_(ox + ddx * (r + 8), oy + ddy * (r + 8)), P_(ox + ddx * (r + 32), oy + ddy * (r + 32)), 255, 5, cv2.LINE_AA, 4)
        tgx, tgy = ox + 40, oy - 440
        cv2.line(lay, P_(ox + r * 0.72, oy - r * 0.72), P_(tgx + 30, tgy + 80), 255, 3, cv2.LINE_AA, 4)
        La = lay.astype(np.float32) / 255 * sc
        out = out * (1 - La[..., None]) + PAPER * La[..., None]
        cv2.circle(out, P_(ox, oy), 9 * SS, tuple(float(v) for v in STRING_C), -1, cv2.LINE_AA, 4)
        if q < 12:                                                                         # the pulse
            pr = np.zeros((H, W), np.uint8); cv2.circle(pr, P_(ox, oy), int((r + 70 * eout(q / 12, 2)) * SS), 255, 2, cv2.LINE_AA, 4)
            out = out + (pr.astype(np.float32) / 255 * 0.6 * (1 - q / 12))[..., None] * PAPER
        n = int(clamp((q - 2) * 2.2, 0, 15))
        if n > 0:                                                                          # POINT OF ORIGIN, typed on a paper tag
            txt = "POINT OF ORIGIN"[:n]
            if "tagm" not in _SP: _SP["tagm"] = text_mask("POINT OF ORIGIN", F_MONO, 48)
            rg = shadowed(text_mask(txt, F_MONO, 48), INK, blur=1, sa=0.0)            # padded by 7 px
            tw_, th2 = _SP["tagm"].shape[1] + 28, _SP["tagm"].shape[0] + 18
            x0, y0 = int(tgx), int(tgy)
            out[y0 + 6:y0 + th2 + 6, x0 + 5:x0 + tw_ + 5] *= 0.55                          # the tag's shadow
            out[y0:y0 + th2, x0:x0 + tw_] = PAPER * 0.97
            out[y0 + th2 - 4:y0 + th2, x0:x0 + tw_] = STRING_C                              # a red rule under the type
            out = paste_rgba(out, rg, x0 + 14 - 7, y0 + 9 - 7, 1.0)
    return np.clip(out, 0, 1)

_base107_r2 = base107
def base107(s, f):
    img, person = _base107_r2(s, f)
    if s["n"] == "table": img = spatter_fx(img, f)
    return img, person

# ---- RORSCHACH (the 3 s transition): from the point of origin a blood-ink blot blooms, mirrored about the fold like an
# ---- inkblot card; inside it his face appears mirrored (both of him), the blot floods the frame, the mirrored half of the
# ---- card swings open on the fold and the real shot is underneath. Full frame: no bars, no box. ---------------------------
RO_PRE, RO_POST = 21, 30
RO_BLOBS = [(0, 0, 95), (0, 110, 70), (0, -120, 60), (45, -190, 30), (150, -60, 95), (280, -120, 80), (400, -190, 62),
            (500, -230, 42), (560, -170, 30), (200, 70, 80), (330, 60, 62), (440, 20, 48), (520, -40, 36), (260, 160, 42),
            (390, 140, 34), (55, 210, 34), (70, 270, 20), (610, -110, 18), (150, 300, 14)]
INKB = np.array([0.03, 0.02, 0.24], np.float32)
_RO = {}
def ro_grids():
    if "g" not in _RO:
        ox, oy = sp_origin(); rng = np.random.default_rng(1078)
        X, Y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        AX = np.abs(X - ox); DY = Y - oy
        n1 = cv2.resize(rng.random((H // 40 + 2, W // 40 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.random((H // 10 + 2, W // 10 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        nz = 0.6 * n1 + 0.4 * n2
        xi = np.clip(ox + AX, 0, W - 1).astype(np.int32); nz = nz[np.arange(H)[:, None], xi]    # symmetric about the fold
        mx = np.where(X > ox, 2 * ox - X, X).astype(np.float32)                                  # the mirror map
        _RO["g"] = (AX, DY, nz, mx, Y)
    return _RO["g"]

def ro_mask(grow, flood=0.0):
    AX, DY, nz, _, _ = ro_grids(); F = np.zeros((H, W), np.float32)
    for bx, by, r in RO_BLOBS:
        bx, by, r = bx * 0.72, by * 1.25, r * 0.85                                          # a card: it fits the frame
        dist = math.hypot(bx, by); g = eout(clamp((grow - dist / 700 * 0.55) / 0.45, 0, 1), 2.5)
        rr = r * g * (1 + 2.2 * ein(clamp(flood / 0.5, 0, 1), 1.6))
        if rr > 0.5: F += rr * rr / ((AX - bx) ** 2 + (DY - by) ** 2 + 1.0)
    if flood > 0:
        rc = 1450 * eout(clamp(flood / 0.5, 0, 1), 1.8); F += rc * rc / (AX ** 2 + DY ** 2 + 1.0)
    F = F * (0.86 + 0.28 * nz)
    return cv2.GaussianBlur((F > 1.0).astype(np.float32), (0, 0), 1.1)

def mirror(img):
    _, _, _, mx, Y = ro_grids()
    return cv2.remap(img, mx, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def ink_comp(A, content, m, clear):
    inner = cv2.GaussianBlur(m, (0, 0), 14); rim = np.clip((m - inner) * 3.2, 0, 1)
    dens = np.maximum(rim, 1 - clear) * m
    ins = content * (1 - 0.92 * dens[..., None]) + INKB * 0.92 * dens[..., None]
    hgt = cv2.GaussianBlur(m, (0, 0), 5.0); gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip((-gx * 0.55 - gy * 0.85) * 5.0, 0, 1) ** 2 * m * 0.55
    halo = np.clip(cv2.GaussianBlur(m, (0, 0), 3.0) - m, 0, 1) * 0.7                       # the ink bleeds into the paper
    out = A * (1 - halo[..., None]) * (1 - m[..., None]) + ins * m[..., None] + spec[..., None] * PAPER
    return np.clip(out, 0, 1)

def unfold(Bm, B, phi):
    """the mirrored half of the card (right of the fold) swings away on the fold; the real shot is underneath."""
    ox, _ = sp_origin(); D = 1700.0; s = W - ox
    if phi >= math.pi / 2 - 1e-3: return B
    Z = s * math.sin(phi); k = D / (D + Z); xf = ox + s * math.cos(phi) * k
    src = np.float32([[ox, 0], [W, 0], [W, H], [ox, H]]); dst = np.float32([[ox, 0], [xf, H / 2 - H / 2 * k], [xf, H / 2 + H / 2 * k], [ox, H]])
    Mp = cv2.getPerspectiveTransform(src, dst)
    pg = cv2.warpPerspective(Bm, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    pm = np.zeros((H, W), np.float32); pm[:, int(ox):] = 1
    pm = cv2.warpPerspective(pm, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    shade = 1 - 0.55 * math.sin(phi); pm = pm * (1 - smooth((phi - math.radians(55)) / math.radians(30)))   # gone before it is edge-on
    shadow = np.clip(1 - np.abs(np.arange(W, dtype=np.float32) - xf) / 160, 0, 1) * 0.35 * math.sin(phi)   # the card's shadow
    base = B * (1 - shadow[None, :, None] * (np.arange(W) > ox)[None, :, None])
    return np.clip(base * (1 - pm[..., None]) + pg * shade * pm[..., None], 0, 1)

def rorschach(A, B, j, f, sa, sb, pre=RO_PRE, post=RO_POST):
    if j < 0:
        u = (j + pre + 1) / pre
        m = ro_mask(u); return ink_comp(A, mirror(B), m, smooth((u - 0.10) / 0.55))
    v = (j + 1) / post; Bm = mirror(B)
    if v < 0.5:
        m = ro_mask(1.0, v); return ink_comp(A, Bm, m, 1.0)
    return unfold(Bm, B, math.pi / 2 * smooth((v - 0.5) / 0.45))
TR2["rorschach"] = (rorschach, RO_PRE, RO_POST)

# ============================================================================ v107 rev 4 (owner notes; overrides above)
# ---- the POINT OF ORIGIN piece is gone: the kill table plays clean and cuts to "shh" on the downbeat ------------------
base107 = _base107_r2                                                                       # no spatter analysis
def beat_phase(f):                                                                          # the beat camera punches the e8 cut again
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 54) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- PAGE TURN ("shh" -> the lab, replaces the redaction boxes): the frame is a page of the paper. It lifts at the
# ---- bottom-right corner and rolls over a cylinder; its back is newsprint with the picture showing through; it lies
# ---- over itself as it turns, casts a shadow on the lab shot underneath, and clears off the top-left corner. ------------
PT_PRE, PT_POST = 14, 12
_PT = {}
def pt_back():
    """the back of the page: newsprint (three columns of body type, rules) on the paper."""
    if "b" in _PT: return _PT["b"]
    paper, _, _ = page_layers(); ink = np.zeros((H, W), np.float32); rng = np.random.default_rng(1079)
    words = ("residents were told to lock their doors as the task force widened the search along the bay and the "
             "department asked anyone who saw a boat leave the marina after dark to call the tip line divers recovered "
             "more bags from the water on monday and the medical examiner said the work was careful and practised").split()
    cols = [(60, 352), (394, 686), (728, 1020)]
    for ci, (x0, x1) in enumerate(cols):
        y = 90 + (60 if ci == 1 else 0); wi = int(rng.integers(len(words)))
        while y < H - 90:
            if rng.random() < 0.05:
                m = text_mask(" ".join(words[wi % len(words):wi % len(words) + 3]).upper(), F_XB, 34); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
                y += 58; wi += 3; continue
            line = []; wsum = 0
            while True:
                w = words[wi % len(words)]; wi += 1; tw = len(w) * 11 + 9
                if wsum + tw > (x1 - x0): break
                line.append(w); wsum += tw
            m = text_mask(" ".join(line), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
            y += 29
        if ci < 2: cv2.line(ink, (x1 + 21, 90), (x1 + 21, H - 90), 0.7, 1)
    cv2.line(ink, (60, 64), (W - 60, 64), 1.0, 2)
    _PT["b"] = (paper, ink); return _PT["b"]

def page_turn107(A, B, j, f, sa, sb, pre=PT_PRE, post=PT_POST):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1)
    d = np.array([-0.62, -0.785], np.float32); d /= np.linalg.norm(d)                       # from the bottom-right corner to the top-left
    s_ = (_GX - W) * d[0] + (_GY - H) * d[1]; smax = float(W * -d[0] + H * -d[1])
    R = 60 + 70 * u; c = (smax + 1.7 * R + 60) * (0.5 - 0.5 * math.cos(math.pi * u ** 1.15))  # the roll line, easing in and out
    def src(sig):                                                                            # screen point -> the page point at sigma
        return (_GX + (sig - s_) * d[0]).astype(np.float32), (_GY + (sig - s_) * d[1]).astype(np.float32)
    def inside(mx, my): return (mx >= 0) & (mx <= W - 1) & (my >= 0) & (my <= H - 1)
    paper, ink = pt_back()
    def back_at(mx, my, shade):
        pa = cv2.remap(paper, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ik = cv2.remap(ink, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)[..., None]
        thru = cv2.remap(A, (W - 1 - mx).astype(np.float32), my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)   # show-through, mirrored
        b = pa * (1 - 0.10 * (1 - lum(thru))[..., None]) * (1 - ik * 0.88) + INK * ik * 0.88
        return b * shade[..., None]
    o = B.copy()
    # 1. the flat page (front) beyond the roll line
    flat = s_ > c
    o = np.where(flat[..., None], A, o)
    # 2. the rising quarter of the roll (front side, seen foreshortened)
    cyl = (s_ <= c) & (s_ >= c - R)
    th1 = np.arcsin(np.clip((c - s_) / R, 0, 1)); mx, my = src(c - R * th1); ok1 = cyl & inside(mx, my)
    fr = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * (0.55 + 0.45 * np.cos(th1))[..., None]
    o = np.where(ok1[..., None], fr, o)
    # 3. the top half of the roll (its back, on top of the rising quarter)
    th2 = np.pi - th1; mx2, my2 = src(c - R * th2); ok2 = cyl & inside(mx2, my2)
    bk = back_at(mx2, my2, (0.80 + 0.22 * np.sin(th2)).astype(np.float32))
    o = np.where(ok2[..., None], bk, o)
    # 4. the turned-over part lying flat on top of the page (its back), beyond the roll line
    sig3 = 2 * c - np.pi * R - s_; mx3, my3 = src(sig3); ok3 = flat & (sig3 <= c - np.pi * R) & inside(mx3, my3)
    bk3 = back_at(mx3, my3, np.full((H, W), 0.93, np.float32))
    o = np.where(ok3[..., None], bk3, o)
    # shadows: the roll on the lab shot underneath, the flap's edge on the page
    uncov = s_ < c - R
    sh1 = np.exp(-np.clip((c - R) - s_, 0, None) / 46) * uncov * 0.55 * (c > 2)
    edge3 = ok3.astype(np.float32); sh2 = np.clip(cv2.GaussianBlur(edge3, (0, 0), 14) - edge3, 0, 1) * flat * (~ok3) * 0.9
    o = o * (1 - sh1[..., None]) * (1 - sh2[..., None])
    return np.clip(o, 0, 1)
TR2["page_turn107"] = (page_turn107, PT_PRE, PT_POST)

# ---- the colour split on the beat hits clamps at the frame edge (np.roll wrapped it: a cyan / magenta line on the edges)
def _shift_edge(ch, d, axis):
    if d == 0: return ch
    o = np.empty_like(ch); n = ch.shape[axis]; d = max(-n + 1, min(n - 1, d))
    src = [slice(None)] * ch.ndim; dst = [slice(None)] * ch.ndim; pad = [slice(None)] * ch.ndim; edge = [slice(None)] * ch.ndim
    if d > 0:
        dst[axis], src[axis], pad[axis], edge[axis] = slice(d, None), slice(0, n - d), slice(0, d), slice(0, 1)
    else:
        dst[axis], src[axis], pad[axis], edge[axis] = slice(0, n + d), slice(-d, None), slice(n + d, None), slice(n - 1, n)
    o[tuple(dst)] = ch[tuple(src)]; o[tuple(pad)] = ch[tuple(edge)]
    return o

def rgb_split(img, d, vertical=False):
    d = int(round(d))
    if d == 0: return img
    o = img.copy(); ax = 0 if vertical else 1
    o[..., 2] = _shift_edge(img[..., 2], d, ax); o[..., 0] = _shift_edge(img[..., 0], -d, ax)
    return o


# ============================================================================ v108 — DOOMSDAY (Dexter × MF DOOM "Doomsday")
# The edit's own pieces (last definition wins). UNDER THE SURFACE / BORN IN BLOOD; no text anywhere (the owner's brief).
#   LOOKS     surface108 (the mask: warm, bleached pastel Miami) | under108 (from the peel: cold steel and teal, deep
#             blacks, only blood red survives). finish108: fine grain, a soft vignette, a little halation in the light.
#   SURFACE   the owner's concept: clear kill-room plastic is pulled over the calm picture, stretches (its folds bend
#             the picture), and peels away diagonally (slow, then it snaps) to the darker Dexter underneath.
#   SPECIMEN  the owner's concept (the signature, on the drop): a glass slide with a drop of blood crosses his face and
#             magnifies his eye; the next shot appears inside the glass, then the slide comes to the lens and fills it.
#   FROST     "back where my brother went": frost grows over the lens from the edges (the Ice Truck Killer), the picture
#             cools under it, and it thaws from the centre onto him strapped to Brian's table.
#   LAST DROP the loop: he looks up; one drop of blood falls toward the lens; frame 0's smile is inside it; it fills the
#             frame on the last frame (the hero object: the slide's drop, twice).
_L108 = {}
def lut108(kind):
    if kind not in _L108:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        if kind == "surface108":
            ys = PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.060, 0.082, 0.215, 0.530, 0.820, 0.925, 0.950])(x)
        else:
            ys = PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.010, 0.020, 0.115, 0.425, 0.745, 0.875, 0.905])(x)
        _L108[kind] = (x, ys.astype(np.float32))
    return _L108[kind]

WARM108 = np.array([0.93, 0.99, 1.04], np.float32)          # BGR gains for the mask
PASTEL = np.array([0.86, 0.91, 0.98], np.float32)           # BGR: the cream-pink of the light by day
CRIMSON = np.array([0.10, 0.06, 0.78], np.float32)          # BGR: blood
TEAL = np.array([0.040, 0.026, -0.010], np.float32)         # BGR: added in the shadows under the surface
_grade_pre108 = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in ("surface108", "under108"): return _grade_pre108(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = lut108(lk)
    gains = tuple(float(a * b) for a, b in zip(gains, WARM108 if lk == "surface108" else (1.0, 1.0, 1.0)))
    if in_unit(img):
        x = apply_lut3(img, tone_lut((lk, s["n"], ev, float(g), gains), gains, g, ev, lx, ly))
    else:
        x = np.interp(np.clip(np.clip(img * np.array(gains, np.float32), 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    o = np.empty(x.shape, np.float32)
    if lk == "surface108":
        hi = np.clip((L - 0.50) * 1.6, 0, 1)
        for ch, P in enumerate((Bc, Gc, Rc)):
            v = L + (P - L) * 0.80
            v *= 1 + hi * (PASTEL[ch] / 0.98 - 1) * 0.8
            o[..., ch] = v
    else:
        red = np.clip((Rc - 1.85 * np.maximum(Gc, Bc) - s.get("redthr", 0.05)) * 3.0, 0, 1)          # blood, not skin
        skin = np.clip((Rc - Bc) * 1.8, 0, 1) * (1 - red)
        sat = 0.26 + 0.14 * skin + 0.95 * red
        sh = (1 - L) ** 2
        for ch, P in enumerate((Bc, Gc, Rc)):
            v = L + (P - L) * sat
            v += sh * TEAL[ch]
            v += red * L * (CRIMSON[ch] / 0.78 - 1) * 0.30
            o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

def finish108(out, f, s=None):
    L = lum(out)
    q = cv2.resize(np.clip(L - 0.80, 0, 1), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    hal = cv2.resize(cv2.GaussianBlur(q, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
    g = grain(f, 0.012)[..., 0]; v = VIG[..., 0]
    o = np.empty(out.shape, np.float32)
    for ch, k in enumerate((0.07, 0.08, 0.09)):                                                # a soft, near-neutral halation
        oc = o[..., ch]; np.copyto(oc, out[..., ch]); oc += hal * k; oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: from e2 to e64; it rests through SURFACE, the drop-out and SPECIMEN, the frost, and the ending ----
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 64) and not (10.5 <= e < 14.5) and not (18 <= e < 23.5) and not (26.5 <= e < 29.5)
    return ph, bi, hook, False

def base108(s, f):
    return base12(s, f)

_B108 = {}
def edge108(S_, which):
    key = (S_["n"], which)
    if key not in _B108:
        if len(_B108) > 6: _B108.clear()
        _B108[key] = base108(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B108[key]

def frame0_plate108():
    if "f0" not in _LV: _LV["f0"] = base108(SHOTS[0], SHOTS[0]["f0"])[0]
    return _LV["f0"]

def _blur(img, sig):
    return img if sig < 0.3 else cv2.GaussianBlur(img, (0, 0), sig)

def _remap(img, mx, my, border=cv2.BORDER_REFLECT):
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=border)

# ---- the drop of blood (the hero object): a lit, refracting dome or a falling bead ----------------------------------
R_FULL = 0.5 * math.hypot(W, H) + 40
def blood_drop108(out, cx, cy, r, behind=None, inside=None, inside_w=0.0, stretch=1.0, tint=1.0, light=(-0.55, -0.70), gloss=1.0):
    """draws a drop of blood of radius r (px) centred at (cx, cy) on out (in place, returns out).
    behind: the picture the drop refracts (default out); inside / inside_w: a picture seen *through* the drop (the
    lens image), blended in by inside_w; stretch > 1 elongates it vertically (a falling drop); tint 0..1 how much blood
    absorbs (1 = deep crimson)."""
    if r < 1.0: return out
    R = int(r * stretch * 1.25) + 4
    x0, x1 = max(0, int(cx - R)), min(W, int(cx + R) + 1); y0, y1 = max(0, int(cy - R * 1.0)), min(H, int(cy + R) + 1)
    if x1 <= x0 or y1 <= y0: return out
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xx - cx) / r; dy = (yy - cy) / (r * stretch)
    rho2 = dx * dx + dy * dy
    m = np.clip((1.0 - np.sqrt(rho2)) * r * 0.9 + 0.5, 0, 1)                                    # anti-aliased edge
    if m.max() <= 0: return out
    z = np.sqrt(np.clip(1 - rho2, 0, 1))
    src = behind if behind is not None else out
    k = 0.85                                                                                    # a lens: the scene behind, inverted and small
    sx = cx - dx * r * k * (0.35 + 0.65 * z); sy = cy - dy * r * k * (0.35 + 0.65 * z)
    ref = _remap(src, sx, sy)
    if inside is not None and inside_w > 0:
        # the lens image of `inside`: the whole picture, upright, squeezed into the drop (a fish-eye at the rim); it
        # relaxes to exactly 1:1 when the drop's radius reaches R_FULL (it then covers the frame)
        Sc = max(1.0, R_FULL / r)
        bulge = clamp(1 - (W * 0.5) / (r * Sc), 0, 0.62) * (1 - smooth((r - 0.80 * R_FULL) / (0.18 * R_FULL)))   # the rim maps inside frame 0
        ux = W / 2 + (xx - cx) * Sc * (1 - bulge * (1 - z)); uy = H / 2 + (yy - cy) * Sc * (1 - bulge * (1 - z))
        ins = _remap(inside, ux, uy, cv2.BORDER_REPLICATE)
        oob = np.clip(np.maximum(np.maximum(-ux, ux - (W - 1)), np.maximum(-uy, uy - (H - 1))) / 40.0, 0, 1)   # outside frame 0:
        soft = _remap(_blur_small(inside), ux, uy, cv2.BORDER_REPLICATE)                          # its blurred edge, carried out
        ins = ins * (1 - oob[..., None]) + soft * oob[..., None]
        ref = ref * (1 - inside_w) + ins * inside_w
    thick = z * (0.55 + 0.45 * z)
    sig = np.array([2.6, 2.4, 0.35], np.float32) * tint
    T = np.exp(-sig * thick[..., None] * 1.5)
    col = ref * T * (1 - 0.25 * tint) + CRIMSON * (1 - T[..., 2:3]) * 0.55 * tint
    nx, ny = dx, dy; nz = z + 1e-3; nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    lv = np.array([light[0], light[1], 0.62], np.float32); lv /= np.linalg.norm(lv)
    hv = lv + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = np.clip((nx * hv[0] + ny * hv[1] + nz * hv[2]) / nn, 0, 1)
    rs = clamp(110.0 / max(r, 1.0), 0.12, 1.0)                                                  # a big (near) drop keeps a small, sharp glint
    spec = ndh ** (140 / rs) * (0.45 + 0.5 * rs)
    fres = np.clip(1 - z, 0, 1) ** 3 * 0.22 * (0.4 + 0.6 * np.clip(-(dx * lv[0] + dy * lv[1]), 0, 1))
    caus = np.exp(-(((dx - 0.35) / 0.32) ** 2 + ((dy - 0.42) / 0.22) ** 2)) * 0.28 * tint   # light focused through the bead
    rim = np.exp(-((np.sqrt(rho2) - 0.97) / 0.035) ** 2) * 0.35                              # the dark meniscus at the edge
    col = col * (1 - rim[..., None] * 0.6 * gloss) + ((spec + fres) * gloss)[..., None] * np.array([0.96, 0.98, 1.0], np.float32)
    col = col + (caus * gloss)[..., None] * np.array([0.10, 0.18, 0.55], np.float32)
    reg = out[y0:y1, x0:x1]
    reg[:] = reg * (1 - m[..., None]) + col * m[..., None]
    return out

# ---- SURFACE: kill-room plastic over the calm picture, stretched, then peeled away diagonally ------------------------
SU_PRE, SU_POST = 26, 16
_SU = {}
def su_fields():
    """quarter-res height fields of the sheet: big curved folds, medium wrinkles, and the taut streaks it is pulled into."""
    if "f" not in _SU:
        h4, w4 = H // 4, W // 4; rng = np.random.default_rng(1081)
        def aniso(sx, sy, ang, seed, pad=160):
            n = np.random.default_rng(seed).standard_normal((h4 + 2 * pad, w4 + 2 * pad)).astype(np.float32)
            n = cv2.GaussianBlur(n, (0, 0), sigmaX=sx, sigmaY=sy)
            M = cv2.getRotationMatrix2D(((w4 + 2 * pad) / 2, (h4 + 2 * pad) / 2), ang, 1.0)
            n = cv2.warpAffine(n, M, (w4 + 2 * pad, h4 + 2 * pad), borderMode=cv2.BORDER_REFLECT)[pad:pad + h4, pad:pad + w4]
            return n / (np.abs(n).max() + 1e-6)
        yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
        folds = np.zeros((h4, w4), np.float32)
        for k in range(8):                                                                          # big curved creases
            a = rng.uniform(-1.25, -0.35); c = rng.uniform(-0.2, 1.4) * w4; wv = rng.uniform(7, 22)
            d = (xx * math.cos(a) + yy * math.sin(a)) - c + rng.uniform(8, 22) * np.sin(yy / rng.uniform(40, 90) + rng.uniform(0, 6))
            folds += rng.uniform(0.5, 1.0) * np.exp(-(d / wv) ** 2) * (1 if k % 2 else -0.7)
        wrink = aniso(20, 7.0, 25, 12) * 0.55 + aniso(26, 8.0, -30, 13) * 0.45                      # crumpled
        taut = aniso(80, 4.0, -42, 14) * 0.7 + aniso(55, 3.0, -38, 15) * 0.5                        # pulled along the diagonal
        lip = aniso(34, 34, 0, 16)                                                                   # the peel front wanders
        dg = ((xx / w4) + (yy / h4)) / 2                                                            # 0 top-left .. 1 bottom-right
        _SU["f"] = (folds, wrink, taut, lip, dg, xx, yy)
    return _SU["f"]

def surface(A, B, j, f, sa, sb, pre=SU_PRE, post=SU_POST):
    q = (j + pre + 0.5) / (pre + post)
    folds, wrink, taut, lip, dg, xx, yy = su_fields(); h4, w4 = folds.shape
    qa = eout(clamp(q / 0.24, 0, 1), 2.2)                                                        # the sheet is pulled over
    tens = smooth((q - 0.18) / 0.34)                                                             # it stretches
    pp = clamp((q - 0.46) / 0.52, 0, 1); peel = 0.16 * pp + 0.84 * pp ** 2.4                    # it peels: slow, then snaps
    # the stretch drags the sheet toward the lower right and pulls its folds long along the diagonal
    st = 1 + 0.22 * tens; dx_, dy_ = -26 * tens, -26 * tens
    ux, uy = (xx + yy) / 2, (xx - yy) / 2                                                        # diagonal axes
    sxp = (ux / st + uy) + dx_; syp = (ux / st - uy) + dy_
    fo = cv2.remap(folds, sxp.astype(np.float32), syp.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wr = cv2.remap(wrink, sxp.astype(np.float32), syp.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    front_arr = -0.12 + 1.32 * qa; front_peel = 1.12 - 1.32 * peel
    wob = cv2.GaussianBlur(lip, (0, 0), 6) * 0.03
    cov = np.clip((front_arr - dg + wob) * 60, 0, 1) * np.clip((front_peel - dg + wob) * 60, 0, 1)
    if cov.max() < 0.002 and q > 0.5: return B
    dfp = np.clip(front_peel - dg, 0, 1); curl_w = 0.03 + 0.05 * peel
    lift = np.exp(-(dfp / curl_w) ** 2) * (peel > 0)
    hgt = fo * (1.45 - 0.30 * tens) + wr * 0.40 * (1 - 0.6 * tens) + taut * 0.20 * tens
    gy, gx = np.gradient(cv2.GaussianBlur(hgt, (0, 0), 0.8))
    ly_, lx_ = np.gradient(cv2.GaussianBlur(lift, (0, 0), 1.5))
    k_ref = 26.0 + 16.0 * tens                                                                   # px of bend per unit slope (quarter res)
    gx = gx + lx_ * 0.5; gy = gy + ly_ * 0.5
    gxF = cv2.resize(gx, (W, H), interpolation=cv2.INTER_CUBIC); gyF = cv2.resize(gy, (W, H), interpolation=cv2.INTER_CUBIC)
    ef = np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 90.0, 0, 1)   # no bend at the frame edge
    gxF *= ef; gyF *= ef
    covF = cv2.resize(cov, (W, H), interpolation=cv2.INTER_LINEAR)
    plate = A
    under = _remap(plate, _GX + gxF * k_ref * 4, _GY + gyF * k_ref * 4)
    under[..., 2] = _remap(plate[..., 2], _GX + gxF * (k_ref + 1.5) * 4, _GY + gyF * (k_ref + 1.5) * 4)
    nx, ny = -gx * 18, -gy * 18; nn = np.sqrt(nx * nx + ny * ny + 1)
    lv = np.array([-0.45, -0.65, 0.62], np.float32); lv /= np.linalg.norm(lv)
    hv = lv + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = np.clip((nx * hv[0] + ny * hv[1] + hv[2]) / nn, 0, 1)
    spec = (ndh ** 60 * (0.70 + 0.40 * tens) + ndh ** 10 * 0.12) * (1 - np.clip(lift * 1.5, 0, 1))   # glints on the fold crests; none in the curl
    crease = np.clip(np.abs(cv2.Laplacian(hgt, cv2.CV_32F, ksize=3)) * 2.2 - 0.05, 0, 1) * 0.22   # stress-whitened creases
    curl_hi = np.exp(-((dfp - curl_w * 0.55) / (curl_w * 0.30)) ** 2) * (peel > 0) * 0.60         # the bright rolled edge
    edge_arr = np.exp(-((front_arr - dg) / 0.012) ** 2) * (qa < 1) * 0.40                         # the sheet's leading edge
    hl = cv2.resize((spec + crease + curl_hi + edge_arr).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    hl *= np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 60.0, 0, 1)        # no glints on the frame edge
    milk = 0.06 + 0.04 * tens
    sheet = under * (1 - milk) + milk * 0.90 + np.clip(hl, 0, 1.2)[..., None] * np.array([0.95, 0.97, 1.0], np.float32)
    base = B
    cast = cv2.resize(np.exp(-((dg - front_peel - 0.01) / 0.02) ** 2) * (dg > front_peel) * (peel > 0) * 0.30, (W, H))
    base = base * (1 - cast[..., None] * 0.5)
    if j < 0 and peel <= 0: base = A
    o = base * (1 - covF[..., None]) + sheet * covF[..., None]
    return np.clip(o, 0, 1)
TR2["surface"] = (surface, SU_PRE, SU_POST)

# ---- SPECIMEN: the slide crosses his face, magnifies his eye; the next shot inside the glass, then it fills the lens ----
SP_PRE, SP_POST = 16, 14
SP_U = np.array([0.848, -0.530], np.float32)                                                     # along the slide (up-right)
SP_N = np.array([0.530, 0.848], np.float32)                                                      # across it (down-right)
_SPX = {}
def sp_eye(sa):
    if sa["n"] not in _SPX:
        fs = face_scr(sa, sa["f1"] - 3)
        if fs is None: _SPX[sa["n"]] = (W * 0.5, H * 0.40, 300.0)
        else:
            e = min((fs[3], fs[4]), key=lambda q: abs(q[0] - W / 2)); _SPX[sa["n"]] = (float(e[0]), float(e[1]), float(fs[2]))
    return _SPX[sa["n"]]

def specimen(A, B, j, f, sa, sb, pre=SP_PRE, post=SP_POST):
    ex, ey, fw = sp_eye(sa)
    if j < 0:
        u = (j + pre + 0.5) / pre
        off = 1500 * (1 - eout(clamp(u / 0.55, 0, 1), 2.4)) - 50 * u                             # sweeps in from the lower right, settles on the eye
        hw = 230.0; M = 1.0 + 0.85 * smooth(u / 0.42)                                           # and magnifies it
        cin = smooth((u - 0.76) / 0.24)                                                          # then the next shot appears in the glass
    else:
        v = (j + 0.5) / post
        off = -50.0; hw = 230.0 + 2400 * ein(clamp(v / 0.85, 0, 1), 2.3)                          # the slide comes to the lens
        M = 1.85 - 0.85 * smooth(v / 0.90); cin = 1.0
    C = np.array([ex, ey], np.float32) + SP_N * off
    sc_ = hw / 230.0
    dn = (_GX - C[0]) * SP_N[0] + (_GY - C[1]) * SP_N[1]
    ds = (_GX - C[0]) * SP_U[0] + (_GY - C[1]) * SP_U[1]
    s0, s1 = -560 * sc_, 1400 * sc_                                                              # the slide's ends along its length
    rr = 26.0 * sc_                                                                              # rounded corners
    ad = np.abs(dn) - (hw - rr); sd_ = np.maximum(s0 + rr - ds, ds - (s1 - rr))
    dist = np.sqrt(np.maximum(ad, 0) ** 2 + np.maximum(sd_, 0) ** 2) + np.minimum(np.maximum(ad, sd_), 0) - rr
    inside = np.clip(0.5 - dist, 0, 1)                                                           # anti-aliased glass mask
    if inside.max() <= 0: return A if j < 0 else B
    bev = 24.0 * max(1.0, sc_ ** 0.5)
    edge = np.clip(1 + dist / bev, 0, 1) * (dist <= 0)                                            # 0 inside .. 1 at the edge
    pull = edge ** 2 * 46.0                                                                      # the bevel refracts outward
    nxb = np.where(ad > sd_, np.sign(dn), 0.0)                                               # which edge is nearest
    gx_ = nxb * SP_N[0] + (1 - np.abs(nxb)) * np.sign(ds - (s0 + s1) / 2) * SP_U[0]
    gy_ = nxb * SP_N[1] + (1 - np.abs(nxb)) * np.sign(ds - (s0 + s1) / 2) * SP_U[1]
    mx = C[0] + (_GX - C[0]) / M + gx_ * pull; my = C[1] + (_GY - C[1]) / M + gy_ * pull
    in_old = _remap(A, mx, my) if cin < 1 else None
    if cin > 0:                                                                                   # the next shot inside the glass: its own eye
        sa_n_for_b[sb["n"]] = sa["n"]; bx, by = sp_eye_b(sb); kk = smooth((j + 0.5) / post) if j >= 0 else 0.0                   # on the slide's line, whole face, then 1:1
        Mb = 1.0 + 0.0 * kk; ox = bx + (C[0] - bx) * kk; oy = by + (C[1] - by) * kk
        in_new = cv2.remap(B, (ox + (_GX - C[0]) / Mb + gx_ * pull).astype(np.float32), (oy + (_GY - C[1]) / Mb + gy_ * pull).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    else: in_new = None
    glass = in_new if in_old is None else (in_old if in_new is None else in_old * (1 - cin) + in_new * cin)
    glass[..., 2] = glass[..., 2] * (1 - edge * 0.35) + _remap((A if cin < 0.5 else B)[..., 2], mx + gx_ * 6 * edge, my + gy_ * 6 * edge) * edge * 0.35
    tintc = np.array([0.93, 0.98, 0.92], np.float32)                                            # the green of a glass edge
    glass = glass * (1 - edge[..., None] * 0.45) + glass * tintc * edge[..., None] * 0.45
    hi_top = np.exp(-((dist + bev * 0.30) / (bev * 0.18)) ** 2) * (dn < 0) * 0.55               # light on the upper edge
    hi_bot = np.exp(-((dist + bev * 0.55) / (bev * 0.25)) ** 2) * (dn > 0) * 0.18
    sheen = np.exp(-((ds - (s0 + 0.55 * (s1 - s0)) + 260 * (u if j < 0 else 1)) / (160 * sc_)) ** 2) * 0.05 * (1 - edge)
    glass = glass + (hi_top + hi_bot + sheen)[..., None] * np.array([0.96, 0.98, 1.0], np.float32)
    outside = A if j < 0 else A
    if j >= 0: outside = _blur(outside, 2.5 * min(1.0, (j + 1) / 6))
    o = outside * (1 - inside[..., None]) + glass * inside[..., None]
    # the drop of blood on the slide, near its lower-left end; it rides the slide out of frame
    dpx = C + SP_U * (-330 * sc_) + SP_N * (40 * sc_)
    o = blood_drop108(o, float(dpx[0]), float(dpx[1]), 64.0 * sc_ ** 0.75, tint=1.0)
    return np.clip(o, 0, 1)
TR2["specimen"] = (specimen, SP_PRE, SP_POST)

# ---- FROST: the Ice Truck Killer; frost grows over the lens from the edges, the picture cools, it thaws from the centre --
FR_PRE, FR_POST = 16, 22
_FR = {}
def fr_fields():
    """half-res fields: TF, the time each pixel of the frost ferns forms (they grow along their stems from the frame edges,
    branching at 60 degrees like ice); TH, when the frost haze reaches each pixel; spark, glints on the crystals."""
    if "f" not in _FR:
        h2, w2 = H // 2, W // 2; rng = np.random.default_rng(1082)
        segs = []                                                                                  # (time, x0, y0, x1, y1, width)
        def grow(x, y, ang, L, t0, depth, wdt):
            step = 5.0; n = int(L / step); t = t0
            for i in range(n):
                ang += rng.normal(0, 0.05)
                x1, y1 = x + math.cos(ang) * step, y + math.sin(ang) * step
                segs.append((t, x, y, x1, y1, wdt)); t += step / 620.0
                if depth < 2 and rng.random() < (0.30 if depth == 0 else 0.20) and i > 2:
                    side = 1 if rng.random() < 0.5 else -1
                    grow(x1, y1, ang + side * math.radians(60), L * rng.uniform(0.18, 0.40) * (1 - i / n * 0.5), t, depth + 1, max(1, wdt - 1))
                x, y = x1, y1
        cx_, cy_ = w2 / 2, h2 * 0.45
        for k in range(110):                                                                       # seeds along the edges
            side = k % 4; p_ = rng.uniform(0.02, 0.98)
            x, y = [(p_ * w2, 0), (w2 - 1, p_ * h2), (p_ * w2, h2 - 1), (0, p_ * h2)][side]
            ang = math.atan2(cy_ - y, cx_ - x) + rng.normal(0, 0.45)
            grow(x, y, ang, rng.uniform(50, 150), rng.uniform(0.0, 0.25), 0, 1)
        TF = np.full((h2, w2), 9.0, np.float32)
        for t, x0, y0, x1, y1, wd in sorted(segs, key=lambda q: -q[0]):                           # later times first, earlier overwrite
            cv2.line(TF, (int(x0), int(y0)), (int(x1), int(y1)), float(t), int(wd), cv2.LINE_AA)
        yy, xx = np.mgrid[0:h2, 0:w2].astype(np.float32)
        d_edge = np.minimum(np.minimum(xx, w2 - 1 - xx) / w2, np.minimum(yy, h2 - 1 - yy) / h2 * 1.15)
        n1 = cv2.GaussianBlur(rng.standard_normal((h2, w2)).astype(np.float32), (0, 0), 30); n1 /= np.abs(n1).max()
        TH = d_edge / d_edge.max() + n1 * 0.12; TH = (TH - TH.min()) / (TH.max() - TH.min())
        g1 = cv2.GaussianBlur(rng.standard_normal((h2, w2)).astype(np.float32), (0, 0), 0.8)
        g2 = cv2.GaussianBlur(rng.standard_normal((h2, w2)).astype(np.float32), (0, 0), 3.0)
        grain_ = g1 / np.abs(g1).max() * 0.6 + g2 / np.abs(g2).max() * 0.4                          # crystalline frosted-glass grain
        spark = (rng.random((h2, w2)) > 0.9975).astype(np.float32)
        _FR["f"] = (TF, TH, grain_, spark)
    return _FR["f"]

FROSTC = np.array([0.99, 0.95, 0.90], np.float32)
def frost108(A, B, j, f, sa, sb, pre=FR_PRE, post=FR_POST):
    TF, TH, grain_, spark = fr_fields(); gr_h = grain_
    if j < 0:
        u = (j + pre + 0.5) / pre; tau = 1.05 * eout(u, 1.3); hz = 0.95 * eout(u, 1.8); melt = 0.0; plate = A
    else:
        v = (j + 0.5) / post; tau = 1.05 + v; melt = clamp(eout(v / 0.70, 1.6), 0, 1); hz = 0.95 * (1 - melt * 1.15); plate = B
    fern = np.clip((tau - TF) / 0.025, 0, 1)                                                      # the ferns that have formed
    fern = cv2.GaussianBlur(fern, (0, 0), 0.7) * (1 - melt) * 0.0                                # rev: rime only, no line drawing
    haze = np.clip((hz - TH + gr_h * 0.03) / 0.08, 0, 1) * 0.80 if j < 0 else np.clip(((0.95 - melt * 1.15) - (1 - TH) * 0.0 - TH + 0.0) / 0.08, 0, 1) * 0.55
    if j >= 0: haze = np.clip(((1.0 - melt * 1.25) - TH + gr_h * 0.03) / 0.08, 0, 1) * 0.80 * (1 - melt * 0.5)  # the centre clears first
    glow = cv2.GaussianBlur(fern, (0, 0), 3.0)
    Fh = cv2.resize(np.clip(haze + glow * 0.25, 0, 1), (W, H)); Ff = cv2.resize(np.clip(fern, 0, 1), (W, H))
    gr = cv2.resize(grain_, (W, H)); sp = cv2.resize(spark * fern, (W, H))
    cold = clamp((hz if j < 0 else hz) * 1.1, 0, 1)
    L = lum(plate)[..., None]
    cooled = plate * (1 - 0.40 * cold) + (L * np.array([1.10, 1.0, 0.84], np.float32)) * 0.40 * cold
    diff = cv2.resize(_blur(cv2.resize(cooled, (W // 2, H // 2), interpolation=cv2.INTER_AREA), 6), (W, H))
    fogged = cooled * (1 - Fh[..., None]) + (diff * 0.72 + FROSTC * (0.24 + 0.10 * gr[..., None])) * Fh[..., None]
    tw = 0.6 + 0.4 * math.sin(f * 1.3)
    o = fogged * (1 - Ff[..., None] * 0.85) + FROSTC * Ff[..., None] * 0.85 + sp[..., None] * tw * 0.8
    return np.clip(o, 0, 1)
TR2["frost108"] = (frost108, FR_PRE, FR_POST)

# ---- THE LAST DROP (the loop) ----------------------------------------------------------------------------------------
LD_F0 = None
def last_drop(out, f, s):
    f0 = fh(68.6); f1 = E.DUR_F - 1
    if f < f0: return out
    t = (f - f0) / (f1 - f0)
    if f >= f1: return frame0_plate108().copy()
    fall = ein(clamp(t / 0.62, 0, 1), 1.6)                                                       # it falls down the dark beside his head
    cx = W * 0.84; cy = -70 + (H * 0.46 + 70) * fall
    r = 16 + 70 * fall
    grow = ein(clamp((t - 0.46) / 0.50, 0, 1), 2.4)                                               # then it falls toward the lens
    r = r + grow * (R_FULL - r)
    cx = cx + (W / 2 - cx) * grow ** 1.6; cy = cy + (H / 2 - cy) * grow ** 1.6                   # it stays on the right until it covers
    stretch = 1.0 + 0.45 * (1 - grow) * smooth(t / 0.15)                                         # a falling bead, longer while it falls
    iw = smooth((t - 0.30) / 0.45)                                                                # frame 0's smile inside it
    tint = 1.0 - smooth((t - 0.50) / 0.42); gloss = 1.0 - smooth((grow - 0.55) / 0.40)
    base = out
    if grow > 0: base = _blur(out, 6 * grow)
    o = blood_drop108(base.copy(), cx, cy, r, behind=base, inside=frame0_plate108(), inside_w=iw, stretch=stretch, tint=tint, gloss=gloss)
    return o

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "last_drop": out = last_drop(out, f, s)
    out = beat_fx(out, f)
    out = flash_governor(out)
    return (np.clip(finish108(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ---- "ever since the womb": born in blood. The v107 pour, quicker (0.8 s), centred on the cut (he was born in it)
MOL_QC = 0.5
def molasses108(A, B, j, f, sa, sb):
    return molasses(A, B, j, f, sa, sb, pre=24, post=24)
TR2["molasses108"] = (molasses108, 24, 24)

_BS = {}
def _blur_small(img):
    k = id(img)
    if k not in _BS:
        _BS.clear(); _BS[k] = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    return _BS[k]

_SPB = {}; sa_n_for_b = {}
def sp_eye_b(sb):
    if sb["n"] not in _SPB:
        fs = face_scr(sb, sb["f0"])
        if fs is None: _SPB[sb["n"]] = (W * 0.5, H * 0.40)
        else:
            ex_, ey_, _ = _SPX.get(sa_n_for_b.get(sb["n"], ""), (W / 2, H * 0.4, 0))
            e = min((fs[3], fs[4]), key=lambda q: (q[0] - ex_) ** 2 + (q[1] - ey_) ** 2); _SPB[sb["n"]] = (float(e[0]), float(e[1]))   # the eye nearest the slide
    return _SPB[sb["n"]]

# ---- rev (the fresh-eyes critique): the library whip without its gold streak (it crossed his mouth); a softer sun sweep
def whip108(A, B, j, f, sa, sb, pre=6, post=8):
    if j < 0:
        u = ein((j + pre + 1) / pre, 2.2); o = cv2.warpAffine(A, np.float32([[1, 0, -W * 0.55 * u], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 4 + 260 * u)
    else:
        v = 1 - eout((j + 1) / post, 2.6); o = cv2.warpAffine(B, np.float32([[1, 0, W * 0.55 * v], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 4 + 260 * v)
    return np.clip(o, 0, 1)
TR2["whip"] = (whip108, 6, 8)

def light_sweep108(A, B, j, f, sa, sb, n=9):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1); pos = -0.45 + 1.9 * smooth(u)
    xs = (_GX / W) * 0.55 + (_GY / H) * 0.85
    side = smooth((pos - xs) / 0.22 + 0.5)[..., None] if False else np.clip((pos - xs) / 0.22 + 0.5, 0, 1)[..., None]
    side = side * side * (3 - 2 * side)
    band = np.exp(-((xs - pos) / 0.16) ** 2)[..., None]
    o = A * (1 - side) + B * side
    return np.clip(o * (1 + 0.55 * band) + band * (SODIUM * 0.18 + WARMW * 0.10), 0, 1)
TR2["light_sweep108"] = (light_sweep108, 9, 9)

# ============================================================================ v108 rev 1 (owner notes, 2026-11-09)
# 1. SPECIMEN merged with the real slide: the slide in his hands (its own smear and frosted label, cut from the frame)
#    lifts toward the lens, swings up so its clear end lies over his eye and magnifies it; the next shot appears in the
#    clear glass; the slide comes to the lens and fills it. His face behind goes soft as the slide comes near.
# 2. No beat bounce in this edit (the owner: "remove that just for this edit"): no zoom punch, kick or hit-frame blur.
# 3. More custom transitions, smooth and creative (below).
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    return ph, bi, False, False

SP_PRE, SP_POST = 18, 14
SR_C = np.array([280.0, 995.0], np.float32)       # the real upper slide at f1 - SP_PRE (measured on the frame)
SR_L, SR_HH = 430.0, 150.0                         # half length (it runs off the left edge), half height
SR_SMEAR = (-13.0, 2.0, 135.0)                     # the blood smear: local centre and radius
SR_LABEL = (185.0, 417.0, -172.0, 133.0)           # the frosted label: local a0, a1, b0, b1
_SRT = {}
def sr_tex(sa):
    """the real slide's features (smear + label) as a local-coordinate texture with alpha, and the screen mask of them
    at their original place (for the fill once the slide has left)."""
    if sa["n"] not in _SRT:
        A0 = base108(sa, sa["f1"] - SP_PRE)[0]
        L, hh = int(SR_L), int(SR_HH) + 30
        bb, aa = np.mgrid[-hh:hh, -L:L].astype(np.float32)
        tex = _remap(A0, SR_C[0] + aa, SR_C[1] + bb, cv2.BORDER_REPLICATE)
        sm = np.clip((SR_SMEAR[2] - np.sqrt((aa - SR_SMEAR[0]) ** 2 + (bb - SR_SMEAR[1]) ** 2)) / 6.0, 0, 1)
        a0, a1, b0, b1 = SR_LABEL
        lb = np.clip(np.minimum.reduce([aa - a0, a1 - aa, bb - b0, b1 - bb]) / 5.0, 0, 1)
        alpha = np.maximum(sm, lb).astype(np.float32)
        body = np.clip(np.minimum(SR_L - np.abs(aa), SR_HH + 28 - np.abs(bb)) / 6.0, 0, 1)            # the whole glass leaves
        scr = np.zeros((H, W), np.float32)
        x0, y0 = int(SR_C[0]) - L, int(SR_C[1]) - hh
        ys, xs = slice(max(0, y0), min(H, y0 + 2 * hh)), slice(max(0, x0), min(W, x0 + 2 * L))
        scr[ys, xs] = np.maximum(alpha, body)[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        scr = cv2.GaussianBlur(cv2.dilate(scr, np.ones((31, 31), np.uint8)), (0, 0), 6)
        _SRT[sa["n"]] = (tex, alpha, scr)
    return _SRT[sa["n"]]

def sp_eye_r(sa):
    """the eye the slide's clear end lands on: the one on the right of the frame (the slide's far end runs off up-right)."""
    key = ("r", sa["n"])
    if key not in _SPX:
        fs = face_scr(sa, sa["f1"] - 3)
        _SPX[key] = (W * 0.70, H * 0.27) if fs is None else tuple(float(v) for v in max((fs[3], fs[4]), key=lambda q: q[0]))
    return _SPX[key]

SR_PIV = np.array([705.0, 995.0], np.float32)     # his fingers hold the slide's right end: it pivots there
def sp_eye_l(sa):
    key = ("l", sa["n"])
    if key not in _SPX:
        fs = face_scr(sa, sa["f1"] - 3)
        _SPX[key] = (W * 0.27, H * 0.27) if fs is None else tuple(float(v) for v in min((fs[3], fs[4]), key=lambda q: q[0]))
    return _SPX[key]

def specimen(A, B, j, f, sa, sb, pre=SP_PRE, post=SP_POST):
    """rev 1b: the real slide pivots up in his fingers (like tilting it to the light) until its clear end is over his
    left eye, magnifying it; the next shot appears in the glass; it fills the lens."""
    ex, ey = sp_eye_l(sa); tex, alpha, scr = sr_tex(sa)
    piv = SR_PIV; dvec = piv - np.array([ex, ey], np.float32); dlen = float(np.hypot(*dvec))
    ang_t = math.atan2(dvec[1], dvec[0])                                                    # the slide's axis toward the eye
    if j < 0:
        u = (j + pre + 0.5) / pre; k = smooth(u / 0.78)
        ang = ang_t * k; sc = 1.0 + 0.22 * k
        lens_a = SR_L - 5 - dlen / sc                                                         # the point of the slide over the eye
        cpos = piv - np.array([math.cos(ang), math.sin(ang)], np.float32) * (SR_L - 5) * sc
        lp = cpos + np.array([math.cos(ang), math.sin(ang)], np.float32) * lens_a * sc
        M = 1.0 + 0.85 * smooth((u - 0.45) / 0.40)
        cin = smooth((u - 0.80) / 0.20); dof = 5.0 * smooth(u / 0.7); gone = smooth(u / 0.25)
    else:
        v = (j + 0.5) / post; ang = ang_t
        sc0 = 1.22; sc = sc0 * (1 + 4.5 * ein(clamp(v / 0.85, 0, 1), 2.2))
        lp = np.array([ex, ey], np.float32); lens_a = SR_L - 5 - dlen / sc0
        M = 1.85 - 0.85 * smooth(v / 0.9); cin = 1.0; dof = 5.0; gone = 1.0
    ca, sn = math.cos(ang), math.sin(ang)
    uax = np.array([ca, sn], np.float32); nax = np.array([-sn, ca], np.float32)
    C = lp - uax * lens_a * sc                                                           # the slide's centre on screen
    dxp, dyp = _GX - C[0], _GY - C[1]
    la = (dxp * uax[0] + dyp * uax[1]) / sc; lb = (dxp * nax[0] + dyp * nax[1]) / sc       # local coordinates
    rr = 22.0
    ad = np.abs(lb) - (SR_HH - rr); sd_ = np.abs(la) - (SR_L - rr)
    dist = (np.sqrt(np.maximum(ad, 0) ** 2 + np.maximum(sd_, 0) ** 2) + np.minimum(np.maximum(ad, sd_), 0) - rr) * sc
    inside = np.clip(0.5 - dist, 0, 1)
    # what's behind: his face, the features filled where the slide has left, soft as the slide comes near
    base = A if j < 0 else A
    if gone > 0:
        q = 4; sm_ = cv2.resize(scr, (W // q, H // q), interpolation=cv2.INTER_AREA); keep = 1 - np.clip(sm_ * 1.5, 0, 1)
        bq_ = cv2.resize(base, (W // q, H // q), interpolation=cv2.INTER_AREA)                   # normalized convolution: the
        num = cv2.GaussianBlur(bq_ * keep[..., None], (0, 0), 14); den = cv2.GaussianBlur(keep, (0, 0), 14)[..., None]   # surroundings, smoothly
        Af = cv2.resize(num / np.maximum(den, 1e-3), (W, H), interpolation=cv2.INTER_CUBIC)
        base = base * (1 - scr[..., None] * gone) + Af * scr[..., None] * gone
    outside = _blur(base, dof)
    if inside.max() <= 0: return outside if j < 0 else B
    bev = 20.0 * max(1.0, sc ** 0.5)
    edge = np.clip(1 + dist / bev, 0, 1) * (dist <= 0)
    pull = edge ** 2 * 40.0
    nxb = np.where(ad > sd_, np.sign(lb), 0.0)
    gx_ = nxb * nax[0] + (1 - np.abs(nxb)) * np.sign(la) * uax[0]
    gy_ = nxb * nax[1] + (1 - np.abs(nxb)) * np.sign(la) * uax[1]
    mx = lp[0] + (_GX - lp[0]) / M + gx_ * pull; my = lp[1] + (_GY - lp[1]) / M + gy_ * pull
    glass = _remap(base, mx, my)
    if cin > 0:
        sa_n_for_b[sb["n"]] = sa["n"]; bx, by = sp_eye_b(sb); kk = smooth((j + 0.5) / post) if j >= 0 else 0.0
        ox = bx + (lp[0] - bx) * kk; oy = by + (lp[1] - by) * kk
        inb = cv2.remap(B, (ox + (_GX - lp[0]) + gx_ * pull).astype(np.float32), (oy + (_GY - lp[1]) + gy_ * pull).astype(np.float32),
                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        glass = glass * (1 - cin) + inb * cin
    tintc = np.array([0.94, 0.98, 0.93], np.float32)
    glass = glass * (1 - edge[..., None] * 0.40) + glass * tintc * edge[..., None] * 0.40
    hi = np.exp(-((dist + bev * 0.30) / (bev * 0.18)) ** 2) * (lb < 0) * 0.50 + np.exp(-((dist + bev * 0.55) / (bev * 0.25)) ** 2) * (lb > 0) * 0.16
    glass = glass + hi[..., None] * np.array([0.96, 0.98, 1.0], np.float32)
    # the slide's own smear and label ride on the glass (soft and fading as it comes to the lens)
    ft = cv2.remap(tex, (la + SR_L).astype(np.float32), (lb + SR_HH + 30).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fa = cv2.remap(alpha, (la + SR_L).astype(np.float32), (lb + SR_HH + 30).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fade = 1.0 if j < 0 else 1 - smooth((j + 0.5) / (post * 0.5))
    if sc > 1.6: ft = _blur(ft, (sc - 1.6) * 3.0)
    fa = fa * inside * fade
    glass = glass * (1 - fa[..., None]) + ft * fa[..., None]
    o = outside * (1 - inside[..., None]) + glass * inside[..., None]
    return np.clip(o, 0, 1)
TR2["specimen"] = (specimen, SP_PRE, SP_POST)

# ---- rev 1: new custom transitions (smooth, each its own idea) -------------------------------------------------------
_NZ = {}
def nz108(seed, sig, q=4):
    """a smooth, wrapping noise texture at 1/q resolution, normalised to 0..1 (deterministic)."""
    key = (seed, sig, q)
    if key not in _NZ:
        n = np.random.default_rng(seed).standard_normal((H // q, W // q)).astype(np.float32)
        n = cv2.GaussianBlur(np.tile(n, (3, 3)), (0, 0), sig)[H // q:2 * (H // q), W // q:2 * (W // q)]   # wraps
        _NZ[key] = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return _NZ[key]

def _up(m): return cv2.resize(m, (W, H), interpolation=cv2.INTER_CUBIC)

# HAZE: Miami heat. The picture shimmers in rising heat waves; the next shot condenses out of the shimmer.
def haze108(A, B, j, f, sa, sb, pre=10, post=12):
    q = (j + pre + 0.5) / (pre + post); amp = math.sin(math.pi * clamp(q, 0, 1)) ** 1.4; t = f / FPS
    dx = (np.sin(_GY * 0.040 - t * 9.0) * 0.6 + np.sin(_GY * 0.019 + _GX * 0.011 - t * 6.0)) * 42 * amp
    dy = (np.sin(_GX * 0.028 + _GY * 0.010 + t * 7.0) * 18 - 30) * amp
    w = smooth((q - 0.44) / 0.12)
    a = _remap(A, _GX + dx, _GY + dy) if w < 1 else None; b = _remap(B, _GX - dx * 0.8, _GY + dy) if w > 0 else None
    o = b if a is None else (a if b is None else a * (1 - w) + b * w)
    o = _blur(o, 3.0 * amp) * (1 + 0.07 * amp)
    return np.clip(o, 0, 1)
TR2["haze108"] = (haze108, 10, 12)

# DIFFUSION: "turn H2O to cognac". A cloud of cognac-red spreads through the frame like dye in water (turbulent, rising,
# fine wisps at its front); the next shot is inside the cloud.
DIFC = np.array([0.10, 0.30, 0.66], np.float32)          # BGR cognac / thinned blood
def diffusion108(A, B, j, f, sa, sb, pre=16, post=18):
    q = (j + pre + 0.5) / (pre + post); t = f / FPS
    h4, w4 = H // 4, W // 4
    yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
    n1, n2 = nz108(1101, 18), nz108(1102, 6)
    off = int(t * 60) % h4
    adv1 = np.roll(n1, -off // 2, axis=0); adv2 = np.roll(n2, -off, axis=0)                   # it rises as it spreads
    D = np.sqrt(((xx - w4 * 0.50) / w4) ** 2 + ((yy - h4 * 1.08) / h4 * 0.9) ** 2) * 1.20
    D = D + (adv1 - 0.5) * 0.55 + (adv2 - 0.5) * 0.16
    lvl = -0.05 + 1.85 * ein(q, 1.55)
    m = np.clip((lvl - D) / 0.22, 0, 1); m = m * m * (3 - 2 * m)
    band = np.exp(-((lvl - D - 0.06) / 0.16) ** 2) * (0.45 + 0.55 * adv2)
    dens = np.clip((lvl - D) / 0.45, 0, 1) * (0.6 + 0.4 * adv1)                                 # the dye's body
    gy, gx = np.gradient(cv2.GaussianBlur(D, (0, 0), 1.5))
    M_, BD = _up(m), _up(band); GX_, GY_ = _up(gx * band), _up(gy * band)
    a = _remap(A, _GX + GX_ * 260, _GY + GY_ * 260); b = _remap(B, _GX - GX_ * 160, _GY - GY_ * 160)
    DN = _up(dens) * (1 - smooth((j + 0.5) / post) if j >= 0 else 1.0)
    sharp = smooth((j + 0.5) / 10.0) if j >= 0 else 0.0                                         # inside the cloud it is soft until after the cut
    bs = cv2.resize(cv2.GaussianBlur(cv2.resize(b, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3.5), (W, H))
    b = bs * (1 - sharp) + b * sharp
    o = a * (1 - M_[..., None]) + b * M_[..., None]
    tint = np.clip(BD * 0.45 + DN * 0.40, 0, 0.7)[..., None]
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 5), (W, H))
    o = o * (1 - tint * 1.3) + soft * tint * 0.3 + (soft * 0.35 + DIFC * 0.75) * tint                 # a smooth wash of cognac
    return np.clip(o, 0, 1)
TR2["diffusion108"] = (diffusion108, 16, 18)

# DOUBLE VISION: the M99 takes hold. The picture doubles and sways apart, soft; the next shot arrives doubled and pulls
# back into focus.
def double108(A, B, j, f, sa, sb, pre=12, post=14):
    k = smooth((j + pre + 0.5) / (pre * 0.7)) if j < 0 else 1 - smooth((j + 0.5) / post)
    w = smooth((j + 3.5) / 7.0)
    def dbl(img):
        d = 78 * k; r = 1.6 * k * math.sin(f * 0.21)
        M1 = cv2.getRotationMatrix2D((W / 2, H * 0.42), r, 1 + 0.03 * k); M1[0, 2] += d
        M2 = cv2.getRotationMatrix2D((W / 2, H * 0.42), -r, 1 + 0.03 * k); M2[0, 2] -= d
        a = cv2.warpAffine(img, M1, (W, H), borderMode=cv2.BORDER_REFLECT); b = cv2.warpAffine(img, M2, (W, H), borderMode=cv2.BORDER_REFLECT)
        return _blur(a * 0.5 + b * 0.5, 3.5 * k)
    o = dbl(A) if w <= 0 else (dbl(B) if w >= 1 else dbl(A) * (1 - w) + dbl(B) * w)
    return np.clip(o * (1 - 0.10 * k), 0, 1)
TR2["double108"] = (double108, 12, 14)

# DEVELOPER: the darkroom. Red safelight falls over the frame and the tray's liquid ripples; the next shot develops out
# of a pale print, gaining contrast, and the safelight lifts.
SAFE = np.array([0.10, 0.16, 0.95], np.float32)
def developer108(A, B, j, f, sa, sb, pre=8, post=18):
    t = f / FPS; r = np.sqrt((_GX - W * 0.5) ** 2 + (_GY - H * 0.45) ** 2)
    if j < 0:
        u = (j + pre + 0.5) / pre; red = smooth(u); rip = smooth(u) * 8; img = A; dev = 1.0
    else:
        v = (j + 0.5) / post; red = 1 - smooth((v - 0.45) / 0.55); rip = 8 * (1 - smooth(v / 0.8)); img = B; dev = ein(clamp(v / 0.80, 0, 1), 1.3)
    wave = (np.sin(r * 0.045 - t * 14) + 0.5 * np.sin(r * 0.11 - t * 22)) * rip * 1.8
    img = _remap(img, _GX + wave * (_GX - W * 0.5) / (r + 1), _GY + wave * (_GY - H * 0.45) / (r + 1))
    if j >= 0:
        paper = np.float32(0.80)
        img = paper + (np.clip((img - 0.5) * (0.55 + 0.45 * dev) + 0.5 - 0.06 * (1 - dev), 0, 1) - paper) * (0.50 + 0.50 * dev)
    L = lum(img)[..., None]
    o = img * (1 - 0.55 * red) + L * SAFE * 0.85 * red
    sheen = np.clip(np.sin(r * 0.045 - t * 14) * np.sin(r * 0.11 - t * 22), 0, 1) ** 6 * (rip / 8.0) * 0.12
    o = o + sheen[..., None] * SAFE
    return np.clip(o, 0, 1)
TR2["developer108"] = (developer108, 8, 18)

# LUMINOL: the forensic spray. The light drops (not to black), the blue-white glow of luminol blooms in splatter where the
# blood was, and the next shot is in the glow; the glow spreads over the frame and fades to the picture.
LUMC = np.array([1.00, 0.62, 0.22], np.float32)
_LU = {}
def lu_field():
    """a wide luminol spray: hundreds of drops and smears across the frame (dense in clusters, thin between)."""
    if "g" not in _LU:
        rng = np.random.default_rng(1103); h4, w4 = H // 4, W // 4; g = np.zeros((h4, w4), np.float32)
        cl = [(rng.uniform(0.05, 0.95) * w4, rng.uniform(0.05, 0.95) * h4) for _ in range(9)]
        for k in range(420):
            cx, cy = cl[k % 9]; sp = rng.uniform(10, 70)
            x, y = int(cx + rng.normal(0, sp)), int(cy + rng.normal(0, sp * 1.3)); r_ = max(1, int(rng.exponential(2.2)))
            cv2.circle(g, (x, y), r_, float(rng.uniform(0.5, 1.0)), -1, cv2.LINE_AA)
            if rng.random() < 0.12: cv2.line(g, (x, y), (x + int(rng.normal(0, 4)), y + int(rng.uniform(8, 30))), 0.7, 1, cv2.LINE_AA)   # drips
        g = cv2.GaussianBlur(g, (0, 0), 1.8) + cv2.GaussianBlur(g, (0, 0), 7) * 1.1
        _LU["g"] = np.clip(g / np.percentile(g[g > 0.01], 95), 0, 1.3)
    return _LU["g"]

def luminol108(A, B, j, f, sa, sb, pre=10, post=18):
    g = lu_field(); n = nz108(1104, 10)
    if j < 0:
        u = (j + pre + 0.5) / pre; dim = 0.45 * smooth(u); lvl = -0.1 + 0.55 * smooth((u - 0.3) / 0.7); img = A
    else:
        v = (j + 0.5) / post; dim = 0.45 * (1 - smooth((v - 0.35) / 0.65)); lvl = 0.40 + 0.9 * ein(v, 1.2); img = B
    field = g * 0.85 + n * 0.30
    fs = face_scr(sb, sb["f0"]); h4, w4 = H // 4, W // 4
    if fs is not None:                                                                        # keep the glow off his face
        yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
        fm = np.clip((np.sqrt((xx - fs[0] / 4) ** 2 + ((yy - fs[1] / 4) * 0.8) ** 2) - fs[2] / 4 * 0.55) / (fs[2] / 4 * 0.25), 0, 1)
        below = np.clip((yy - (fs[1] + fs[2] * 0.75) / 4) / 12.0, 0, 1)                           # below the collar only
        field = field * fm * (0.15 + 0.85 * below)
    m = np.clip((field - (1.0 - lvl)) / 0.18, 0, 1); M_ = _up(m)
    glow = _up(np.clip(m * (0.6 + 0.4 * g), 0, 1)) * (1 - smooth((j + 0.5) / post) if j >= 0 else 1.0)
    L = lum(img)[..., None]
    dark = img * (1 - dim) * (1 - 0.4 * dim) + L * np.array([0.30, 0.22, 0.18], np.float32) * dim * 0.4
    lit = (B if j >= 0 else A) * (0.55 + 0.45 * (1 - glow[..., None])) + LUMC * L * glow[..., None] * 0.55
    if j < 0: lit = dark + LUMC * glow[..., None] * 0.42
    o = dark * (1 - M_[..., None]) + lit * M_[..., None]
    o = o + glow[..., None] * LUMC * 0.40 * (1 - M_[..., None] * 0.4)                             # the glow itself, blue
    return np.clip(o + cv2.GaussianBlur(glow, (0, 0), 18)[..., None] * LUMC * 0.14, 0, 1)
TR2["luminol108"] = (luminol108, 10, 18)

# FACE MATCH: one face becomes the next. The outgoing frame slides and scales so his face lands where the next shot's
# face is, they dissolve through each other, and the next shot settles to its own framing.
def facematch108(A, B, j, f, sa, sb, pre=8, post=10):
    fa = face_scr(sa, sa["f1"] - 1); fb = face_scr(sb, sb["f0"])
    if fa is None or fb is None: fa = fb = (W / 2, H * 0.42, 500.0)
    s_ = clamp(fb[2] / max(fa[2], 1.0), 0.6, 1.7)
    def warp(img, cx, cy, sc, tx, ty):
        M = np.float32([[sc, 0, tx - cx * sc], [0, sc, ty - cy * sc]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if j < 0:
        u = smooth((j + pre + 0.5) / pre)
        a = warp(A, fa[0], fa[1], 1 + (s_ - 1) * u, fa[0] + (fb[0] - fa[0]) * u, fa[1] + (fb[1] - fa[1]) * u)
        w = smooth((j + 3.5) / 7.0); o = a if w <= 0 else a * (1 - w) + B * w
        return np.clip(_blur(o, 1.5 * math.sin(math.pi * u)), 0, 1)
    v = smooth((j + 0.5) / post)
    a = warp(A, fa[0], fa[1], s_, fb[0], fb[1])
    w = smooth((j + 3.5) / 7.0); b = B
    return np.clip(a * (1 - w) + b * w if w < 1 else b, 0, 1)
TR2["facematch108"] = (facematch108, 8, 10)

# SINK: "go get bagged and checked in". The water rises over the lens (a meniscus, refraction, caustic light); under the
# surface the next shot comes up, and the water drains off it.
WATC = np.array([0.62, 0.70, 0.52], np.float32)
def sink108(A, B, j, f, sa, sb, pre=14, post=18):
    t = f / FPS
    if j < 0: yw = H * (1.05 - 1.15 * ein((j + pre + 0.5) / pre, 1.4)); img = A
    else: yw = H * (-0.10 + 1.20 * ein((j + 0.5) / post, 1.6)); img = B
    surf = yw + 22 * np.sin(_GX * 0.011 + t * 5.0) + 9 * np.sin(_GX * 0.031 - t * 7.0)
    under = (_GY > surf) if j < 0 else (_GY < surf)                                              # rising / draining
    d = (_GY - surf) if j < 0 else (surf - _GY)
    m = np.clip(d / 6.0 + 0.5, 0, 1)
    wob = np.sin(_GY * 0.02 + t * 6) * 10 + np.sin(_GX * 0.017 - t * 4) * 6
    uw = _remap(img, _GX + wob, _GY + wob * 0.5)
    ca = (np.abs(np.sin(_GX * 0.013 + np.sin(_GY * 0.011 + t * 3) * 2.0)) * np.abs(np.sin(_GY * 0.012 - t * 2.4))) ** 6
    uw = uw * WATC + ca[..., None] * 0.10 + 0.02
    men = np.exp(-(d / 5.0) ** 2) * 0.35
    o = img * (1 - m[..., None]) + uw * m[..., None] + men[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
    return np.clip(o, 0, 1)
TR2["sink108"] = (sink108, 14, 18)

def facematch108(A, B, j, f, sa, sb, pre=8, post=10):
    """rev 1b: registered on the eyes (scale, rotation and position), so one face becomes the other."""
    fa = face_scr(sa, sa["f1"] - 1); fb = face_scr(sb, sb["f0"])
    if fa is None or fb is None: return haze108(A, B, j, f, sa, sb, pre, post)
    ea = sorted((fa[3], fa[4])); eb = sorted((fb[3], fb[4]))
    va = np.subtract(ea[1], ea[0]); vb = np.subtract(eb[1], eb[0])
    sc = clamp(np.hypot(*vb) / max(np.hypot(*va), 1.0), 0.5, 2.0); rot = math.atan2(vb[1], vb[0]) - math.atan2(va[1], va[0])
    ca_ = np.mean(ea, axis=0); cb_ = np.mean(eb, axis=0)
    def M_of(k):                                                                            # identity -> A's eyes onto B's (k 0..1)
        s_ = 1 + (sc - 1) * k; r_ = rot * k; c, sn = math.cos(r_) * s_, math.sin(r_) * s_
        tx, ty = ca_ + (cb_ - ca_) * k
        return np.float32([[c, -sn, tx - (c * ca_[0] - sn * ca_[1])], [sn, c, ty - (sn * ca_[0] + c * ca_[1])]])
    if j < 0:
        k = smooth((j + pre + 0.5) / pre)
        a = cv2.warpAffine(A, M_of(k), (W, H), borderMode=cv2.BORDER_REFLECT)
        w = smooth((j + 2.5) / 5.0)
        if w <= 0: return np.clip(_blur(a, 1.2 * math.sin(math.pi * k)), 0, 1)
        bi = cv2.warpAffine(B, cv2.invertAffineTransform(M_of(1.0)) @ np.vstack([M_of(1.0), [0, 0, 1]])[:2] if False else np.float32([[1, 0, 0], [0, 1, 0]]), (W, H))
        return np.clip(a * (1 - w) + B * w, 0, 1)
    a = cv2.warpAffine(A, M_of(1.0), (W, H), borderMode=cv2.BORDER_REFLECT)
    w = smooth((j + 2.5) / 5.0)
    return np.clip(a * (1 - w) + B * w if w < 1 else B, 0, 1)
TR2["facematch108"] = (facematch108, 8, 10)

_sink_r1 = sink108
def sink108(A, B, j, f, sa, sb, pre=14, post=18):
    o = _sink_r1(A, B, j, f, sa, sb, pre, post)
    rng = np.random.default_rng(1108); t = f / FPS
    for k in range(26):                                                                      # bubbles rising under the surface
        x0 = rng.uniform(0.05, 0.95) * W; sp_ = rng.uniform(260, 520); r_ = rng.uniform(4, 13); ph = rng.uniform(0, 3)
        y = H * 1.05 - ((t * sp_ + ph * 400) % (H * 1.2)); x = x0 + 14 * math.sin(t * 6 + ph * 3)
        if 0 < y < H:
            q = (j + pre) / (pre + post); vis = math.sin(math.pi * clamp(q, 0, 1))
            if vis > 0.05:
                cv2.circle(o, (int(x), int(y)), int(r_), (0.85, 0.90, 0.95), 1, cv2.LINE_AA)
    return np.clip(o, 0, 1)
TR2["sink108"] = (sink108, 14, 18)

def wiper108(A, B, j, f, sa, sb):
    return wiper(A, B, j, f, sa, sb, pre=12, post=16)
TR2["wiper108"] = (wiper108, 12, 16)

# ============================================================================ v108 rev 2 (owner notes)
# The heat haze ("the squiggle, swirl, weird animation") is replaced by FRONDS: sunlit palm fronds sweep across the lens in
# the foreground (we pass under the palms he stands beneath), three depths with parallax and motion blur; the cut is
# behind the nearest frond. The rain-on-the-lens transition at 14 s is gone (a smooth push instead).
_FD = {}
def fd_frond(seed, length, lw, curve):
    """one palm frond as an rgba sprite (its own pixel space): a curved rachis with tapered leaflets on both sides, lit by
    the sun behind it (translucent yellow-green edges, darker veins)."""
    key = (seed, length, lw, curve)
    if key not in _FD:
        rng = np.random.default_rng(seed); Wd, Hd = int(length * 1.15), int(length * 0.75)
        a = np.zeros((Hd, Wd), np.float32); shade = np.zeros((Hd, Wd), np.float32)
        n = 34; pts = []
        for i in range(n + 1):
            u = i / n; x = Wd * 0.05 + u * length; y = Hd * 0.5 + curve * length * (u - 0.5) ** 2 - curve * length * 0.25
            pts.append((x, y))
        for i in range(1, n):
            (x, y), (x2, y2) = pts[i], pts[i + 1]; ang = math.atan2(y2 - y, x2 - x)
            for side in (-1, 1):
                L = lw * (0.55 + 0.45 * math.sin(math.pi * i / n)) * rng.uniform(0.85, 1.1)
                la = ang + side * math.radians(rng.uniform(48, 62)) + side * 0.25 * i / n
                ex, ey = x + math.cos(la) * L, y + math.sin(la) * L
                mx, my = (x + ex) / 2, (y + ey) / 2; ln = L / 2; wd = max(3, L * 0.075)
                cv2.ellipse(a, (int(mx), int(my)), (int(ln), int(wd)), math.degrees(la), 0, 360, 1.0, -1, cv2.LINE_AA)
                cv2.line(shade, (int(x), int(y)), (int(ex), int(ey)), 1.0, max(1, int(wd * 0.25)), cv2.LINE_AA)
        cv2.polylines(a, [np.int32(pts)], False, 1.0, max(3, int(lw * 0.05)), cv2.LINE_AA)
        a = cv2.GaussianBlur(a, (0, 0), 0.8)
        rim = np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)                        # backlit edges
        col = np.empty((Hd, Wd, 3), np.float32)
        base = np.array([0.05, 0.16, 0.10], np.float32); lit = np.array([0.20, 0.62, 0.55], np.float32)   # backlit: dark leaves, glowing edges
        g = np.linspace(0, 1, Wd, dtype=np.float32)[None, :] * 0.6 + 0.2
        for c in range(3): col[..., c] = base[c] + (lit[c] - base[c]) * (g * 0.35 + rim * 0.9) - shade * 0.03
        _FD[key] = (np.clip(col, 0, 1), np.clip(a, 0, 1))
    return _FD[key]

def fronds108(A, B, j, f, sa, sb, pre=14, post=14):
    q = (j + pre + 0.5) / (pre + post)
    w = smooth((j + 3.5) / 7.0)                                                               # the shots dissolve behind the leaves
    o = A * (1 - w) + B * w if 0 < w < 1 else (A if j < 0 else B).copy()
    for k, (seed, length, lw, curve, depth, y0, rot) in enumerate(((1201, 1500, 300, 0.25, 0.55, 0.30, -14),
                                                                  (1202, 2300, 470, 0.18, 0.80, 0.62, 10),
                                                                  (1203, 3200, 680, 0.12, 1.00, 0.48, -6))):
        col, a = fd_frond(seed, length, lw, curve)
        sc = 0.55 + 0.45 * depth; sw = int(col.shape[1] * sc)
        x = W * 0.5 + (0.5 - q) * (W + sw) * (0.9 + 0.5 * depth)                                   # each frond is centred on the cut; near ones faster
        M = cv2.getRotationMatrix2D((col.shape[1] / 2, col.shape[0] / 2), rot, sc)
        M[0, 2] += x - col.shape[1] / 2 + sw / 2 * 0; M[1, 2] += H * y0 - col.shape[0] / 2
        cw = cv2.warpAffine(col, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        aw = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        blur = int(6 + 40 * depth)                                                                    # motion blur along the sweep
        kx = np.ones((1, blur), np.float32) / blur
        cw = cv2.filter2D(cw, -1, kx); aw = cv2.filter2D(aw, -1, kx)
        dof = 1.5 + 11.0 * depth ** 2; cw = _blur(cw, dof); aw = _blur(aw, dof)                       # the near frond is far out of focus
        o = o * (1 - aw[..., None]) + cw * aw[..., None]
    return np.clip(o, 0, 1)
TR2["fronds108"] = (fronds108, 14, 14)
