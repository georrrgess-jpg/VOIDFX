# ============================================================================ v14 — KEEPSAKES (The Flash × C418 "Mice on Venus"), rev 2
# Nostalgia for where it all began. THE WAKE opens the edit (the focal set piece at the start): the dark medical bay at
# S.T.A.R. Labs, the lights flicker on, Barry gasps awake, and the owner's achievement toast pops up ("Achievement
# Made! The Beginning?", drawn with our own pixel font and crate icon). The hero object is THE LENSBALL: a glass ball
# lens that holds his memories upside down (a real ball lens inverts what is behind it); in the song's pause the laugh
# is drawn into it, it turns to a new memory on each soft note, and on the pickup we fall in and the picture flips
# upright as the theme returns. EMBLEM GLINT is slow and pronounced, on the real S1 emblem with its bolt redrawn to the
# shape traced on the source. The print is used once, fast (PRINT DIVE). The loop: the last memory's lights flicker,
# the dark medical bay flashes through, the lights go out on frame 0, and they flicker back on as he wakes.
# Look SUNFADE (golden hour on faded film) under a faint SUPER 8 HAZE, kept low so the clips stay clear.
GOLDL = np.array([0.55, 0.82, 1.00], F32)                  # BGR warm gold light
AMBR = np.array([0.30, 0.58, 1.00], F32)                   # BGR amber
EMBR = np.array([0.18, 0.36, 0.95], F32)                   # BGR red-orange (film leak, halation)
CREAM = np.array([0.86, 0.93, 0.97], F32)                  # BGR print card
MILK = np.array([0.80, 0.80, 0.74], F32)                   # BGR undeveloped reagent (milky blue-grey)
SHAD = np.array([0.020, 0.030, 0.050], F32)                # BGR shadow lift (warm brown)
HOT = np.array([0.88, 0.96, 1.00], F32)
# restyle the library's gold / red light in the v14 palette
GOLDW, GOLD2, GOLD, EMBER2 = HOT.copy(), AMBR.copy(), GOLDL.copy(), EMBR.copy()
JASW, JASG, JASY = HOT.copy(), AMBR.copy(), AMBR.copy()
if E.VER == "v14":
    for _s in E.SHOTS:
        _s.setdefault("target", 0.42)

def shift_img(img, dx, dy=0.0):
    M = np.float32([[1, 0, dx], [0, 1, dy]]); return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_DK = {}
def defocus(img, r):
    if r < 0.6: return img
    if r < 6: return cv2.GaussianBlur(img, (0, 0), r / 2)
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    sm = sm + np.clip(sm - 0.58, 0, 1) * 2.2                                                  # highlights bloom into bokeh discs
    rr = int(math.ceil(r / q))
    if rr not in _DK:
        k = np.zeros((2 * rr + 1, 2 * rr + 1), F32); cv2.circle(k, (rr, rr), rr, 1.0, -1, cv2.LINE_AA); _DK[rr] = k / k.sum()
    return np.clip(cv2.resize(cv2.filter2D(sm, -1, _DK[rr]), (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

# ---- the lensball's memories are loaded with the shots (they appear only inside the glass) ------------------------
_load_pre14 = load
def load():
    global SHOTS
    real = SHOTS
    extra = [dict(n=f"ballsrc{i}", src=pk, tmap=[(0, max(0.0, a - 0.1)), (1, b + 0.1)]) for i, (_, pk, a, b, _x) in enumerate(E.BALL) if i > 0]
    SHOTS = real + extra
    try: _load_pre14()
    finally: SHOTS = real

# ---- grade: SUNFADE ------------------------------------------------------------------------------------------------
_LUTS = {}
def lutS():
    if "s" not in _LUTS:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTS["s"] = (x, PchipInterpolator([0, .04, .18, .50, .78, .93, 1], [0.050, 0.070, 0.190, 0.500, 0.775, 0.895, 0.930])(x).astype(np.float32))
    return _LUTS["s"]

E_BRIGHT14 = {"now": -0.05, "wake": 0.10, "lab": 0.05, "searun": 0.10, "shore": 0.08}
_grade_pre14 = grade
def grade(img, s, f):
    if s.get("look") != "sunfade": return _grade_pre14(img, s, f)
    g, gains = corr9(s); ev = (s.get("ev") or 0) - 0.45 * E_BRIGHT14.get(s["n"], 0.0)
    lx, ly = lutS()
    if in_unit(img): x = apply_lut3(img, tone_lut(("sun", s["n"], round(ev, 3), float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.clip(img * gains, 0, 1) ** g
        if ev: x = np.clip(x * 2 ** ev, 0, 1)
        x = np.interp(x, lx, ly).astype(F32)
    B, G, R = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = B * 0.114 + G * 0.587 + R * 0.299
    hue = (R - G) / (R + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((R - B) * 6, 0, 1) * np.clip(L * 3, 0, 1)
    blue = np.clip((B - R) * 4.0, 0, 1)                                                       # blues and cyans fade most (old prints)
    sat = (0.64 + 0.16 * skin) * (1 - 0.35 * blue) * s.get("satk", 1.0)
    sh = (1 - L) ** 2.4; hi = np.clip((L - 0.55) / 0.45, 0, 1) ** 1.5; mid = 4 * L * (1 - L)
    hiw = (-0.035, 0.012, 0.040)                                                              # highlights to cream-gold (BGR)
    midw = (-0.022, 0.004, 0.022)                                                             # a warm cast through the mids
    o = np.empty(x.shape, F32)
    for c, P in enumerate((B, G, R)):
        o[..., c] = L + (P - L) * sat + sh * SHAD[c] * 0.9 + hi * hiw[c] + mid * midw[c]
    o[..., 1] = o[..., 1] * 0.985 + o[..., 2] * 0.015                                         # greens lean olive
    return np.clip(o, 0, 1, out=o)

# ---- SUPER 8 HAZE (the overlay) + the finish ---------------------------------------------------------------------
_FIN14 = {}
def _periodic(f, cyc, ph=0.0):
    return math.sin(2 * math.pi * cyc * (f % E.DUR_F) / E.DUR_F + ph)

def gate_weave(img, f):
    """sub-pixel film weave: smooth sines with whole cycles over the edit (the loop wraps without a step)."""
    dx = 0.42 * _periodic(f, 3, 0.4) + 0.22 * _periodic(f, 7, 1.9)
    dy = 0.55 * _periodic(f, 5, 2.2) + 0.25 * _periodic(f, 11, 0.7)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def edge_leaks(f):
    """two slow warm light leaks breathing at the left and right edges (quarter-res), periodic over the edit."""
    q = np.zeros((H // 4, W // 4), F32)
    y1 = (0.30 + 0.18 * _periodic(f, 2, 0.3)) * H / 4; y2 = (0.68 + 0.16 * _periodic(f, 3, 2.0)) * H / 4
    a1 = 0.55 + 0.45 * _periodic(f, 4, 1.1); a2 = 0.55 + 0.45 * _periodic(f, 5, 2.6)
    cv2.ellipse(q, (int(-W / 4 * 0.06), int(y1)), (int(W / 4 * 0.20), int(H / 4 * 0.22)), 0, 0, 360, float(a1), -1)
    cv2.ellipse(q, (int(W / 4 * 1.05), int(y2)), (int(W / 4 * 0.18), int(H / 4 * 0.20)), 0, 0, 360, float(a2), -1)
    return cv2.resize(cv2.GaussianBlur(q, (0, 0), 26), (W, H))

def dust(out, f, s):
    """film dust specks (one or two frames each, big enough to read on a phone) and a hair about once a second; kept
    off the face."""
    rng = np.random.default_rng(1400 + (f % E.DUR_F)); n = int(rng.choice([0, 1, 1, 2, 3]))
    fb = face_box(s, f) if s.get("face") is not None else None
    for _ in range(n):
        x, y = float(rng.uniform(60, W - 60)), float(rng.uniform(80, H - 80))
        if fb and fb[0] - 40 < x < fb[1] + 40 and y < fb[2] + 60: continue
        r = float(rng.uniform(2.2, 4.8)); dark = rng.random() < 0.7; a = float(rng.uniform(0.35, 0.55))
        x0, y0, x1, y1 = int(x - 8), int(y - 8), int(x + 9), int(y + 9)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
        m = np.clip(r + 0.5 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2), 0, 1) * a
        sub = out[y0:y1, x0:x1]
        sub[:] = sub * (1 - m[..., None]) + (0.05 if dark else 0.92) * m[..., None]
    if f % 61 == 23 or f % 61 == 24:                                                         # a hair, about once a second, 2 frames
        x0 = float(rng.uniform(80, 260)) if rng.random() < 0.5 else float(rng.uniform(W - 260, W - 80))
        y0 = float(rng.uniform(H * 0.55, H * 0.85)); t_ = np.linspace(0, 1, 40)
        pts = np.stack([x0 + 70 * t_ + 18 * np.sin(t_ * 5), y0 + 110 * t_ ** 1.3], 1)
        cv = np.zeros((H, W), F32); cv2.polylines(cv, [(pts * 4).astype(np.int32)], False, 1.0, 2, cv2.LINE_AA, shift=2)
        out *= (1 - 0.45 * cv2.GaussianBlur(cv, (0, 0), 0.8))[..., None]
    return out

STRONG = [46, 50, 54, 58, 60, 62, 66, 70, 76, 78, 82, 84, 86, 90]                           # the piano's strong notes after the return
def breath(f):
    """the light breathes on the piano's strong notes (a designed beat inside the holds, no sound)."""
    t = f / FPS; b = 0.0
    for e in STRONG:
        d = t - E.th(e)
        if 0 <= d < 0.6: b = max(b, math.exp(-d / 0.20))
    return b

def gate_mask():
    """the Super 8 gate: soft rounded corners, darker toward each corner (not bars: the picture runs to every edge)."""
    if "gate" not in _FIN14:
        q = np.zeros((H // 4, W // 4), F32); r = 34
        cv2.rectangle(q, (r, 0), (W // 4 - r, H // 4), 1.0, -1); cv2.rectangle(q, (0, r), (W // 4, H // 4 - r), 1.0, -1)
        for (x, y) in ((r, r), (W // 4 - r, r), (r, H // 4 - r), (W // 4 - r, H // 4 - r)): cv2.circle(q, (x, y), r, 1.0, -1, cv2.LINE_AA)
        g = cv2.resize(cv2.GaussianBlur(q, (0, 0), 7), (W, H))
        _FIN14["gate"] = (0.30 + 0.70 * g)[..., None].astype(F32)
    return _FIN14["gate"]

def coarse_grain(f):
    """film grain clumps (~4 px) that survive a phone's downscale; 6 frames that cycle like the engine's grain."""
    k = ("cg", f % 6)
    if k not in _FIN14:
        rng = np.random.default_rng(1440 + f % 6)
        n = cv2.resize(rng.standard_normal((H // 4, W // 4)).astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)
        _FIN14[k] = np.repeat((n * 0.016)[..., None], 3, axis=2)
    return _FIN14[k]

def finish14(out, f, s):
    if "v" not in _FIN14:
        grain(0, 0.012); _FIN14["v"] = np.repeat(0.74 + 0.26 * VIG, 3, axis=2)
    k = ("g", f % 6)
    if k not in _FIN14: _FIN14[k] = np.repeat(grain(f, 0.012), 3, axis=2)
    o = gate_weave(out, f)
    small = cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.66, 0, 1)
    hal = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 5) * 0.45 + cv2.GaussianBlur(hi_, (0, 0), 20) * 0.55, (W, H))
    addc(o, hal, EMBR, 0.42)                                                                   # halation: warm red round the highlights
    lk = edge_leaks(f); room = np.clip(1 - lum8(o), 0.2, 1); bt = breath(f)
    addc(o, lk * room, AMBR, 0.24 + 0.14 * bt); addc(o, (lk ** 2) * room, EMBR, 0.14 + 0.10 * bt)
    flick = 1 + 0.016 * _periodic(f, 13, 0.5) + 0.009 * _periodic(f, 29, 1.7) + 0.035 * bt
    o *= flick
    o *= _FIN14["v"]; o *= gate_mask(); o += _FIN14[k]; o += coarse_grain(f)
    o = dust(np.clip(o, 0, 1), f, s)
    return np.clip(o, 0, 1, out=o)

# ---- the camera: gentle; it breathes on the strong notes and rests in the lensball and the loop ----------------------
def beat_bounce(f):
    e = f / FPS / E.HB
    if E.E_BALL <= e < E.HDROP or e >= E.E_LOOP: return 1.0
    return 1 + 0.006 * breath(f)

def beat_fx(out, f):
    return out

def init_hits():
    HITS.clear()

# ---- smoothness: flow on the slow 24p/30p shots, a per-shot limit for the fast ones (v13) ----------------------------
def src_weights(s, f):
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f); thr = s.get("flowmax", 14)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > thr:
            if s.get("flowfall") == "blend": return [(i0, 1 - a), (i1, a)]
            return [(i0 if a < 0.5 else i1, 1.0)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

# ---- THE PRINT (hero object) ------------------------------------------------------------------------------------------
CW, CH = 540, 860                                                                            # the card (Instax-like 54 x 86)
WX0, WY0, WW, WH = 40, 40, 460, 620                                                          # the image window (0.742)
_PC = {}
def card_base():
    """cream card with paper grain, a soft light falloff and rounded corners (BGRA float, CH x CW)."""
    if "c" not in _PC:
        rng = np.random.default_rng(140)
        n = cv2.GaussianBlur(rng.standard_normal((CH, CW)).astype(F32), (0, 0), 1.2) * 0.012
        n += cv2.GaussianBlur(rng.standard_normal((CH, CW)).astype(F32), (0, 0), 9) * 0.010
        yy, xx = np.mgrid[0:CH, 0:CW].astype(F32)
        fall = 1.0 - 0.05 * (xx / CW) - 0.06 * (yy / CH)
        c = (CREAM[None, None, :] * fall[..., None] + n[..., None]).astype(F32)
        a = np.zeros((CH, CW), F32); r = 14
        cv2.rectangle(a, (r, 0), (CW - r, CH), 1.0, -1); cv2.rectangle(a, (0, r), (CW, CH - r), 1.0, -1)
        for (x, y) in ((r, r), (CW - r - 1, r), (r, CH - r - 1), (CW - r - 1, CH - r - 1)): cv2.circle(a, (x, y), r, 1.0, -1, cv2.LINE_AA)
        inset = np.zeros((CH, CW), F32); cv2.rectangle(inset, (WX0 - 1, WY0 - 1), (WX0 + WW, WY0 + WH), 1.0, 1)
        c -= cv2.GaussianBlur(inset, (0, 0), 1.5)[..., None] * 0.10                             # the window's pressed edge
        _PC["c"], _PC["a"] = np.clip(c, 0, 1), a
    return _PC["c"], _PC["a"]

def crop_portrait(img, cy=None):
    """the 0.742 portrait crop of a 1080x1920 frame (or any frame), centred on cy, resized to the print window."""
    h, w = img.shape[:2]; ch = int(min(h, w / 0.742)); cw = int(ch * 0.742)
    cy = h / 2 if cy is None else cy; y0 = int(clamp(cy - ch / 2, 0, h - ch)); x0 = (w - cw) // 2
    return cv2.resize(np.ascontiguousarray(img[y0:y0 + ch, x0:x0 + cw]), (WW, WH), interpolation=cv2.INTER_AREA)

def develop(img, dev):
    """instant-film development: the image rises out of the milky reagent, cool and flat first, then warm and full."""
    if dev >= 1: return img
    a = smooth(clamp(dev / 0.55, 0, 1)); b = smooth(clamp((dev - 0.35) / 0.65, 0, 1))
    L = lum8(img)[..., None]
    flat = MILK * 0.55 + (L * 0.75 + 0.15) * np.array([1.04, 1.0, 0.92], F32) * 0.45      # cool, low contrast
    o = MILK * (1 - a) + flat * a
    return np.clip(o * (1 - b) + img * b, 0, 1)

def print_card(content, dev=1.0, gloss=0.0, border=1.0):
    """the card with its developed image and a gloss sheen across the window (BGR + alpha); border < 1 fades the card
    round the window (a print that starts or ends as the plain frame)."""
    c, a = card_base(); o = c.copy()
    if border < 1:
        a = a * border; a[WY0:WY0 + WH, WX0:WX0 + WW] = 1.0
    im = develop(content, dev)
    if gloss > 0:
        yy, xx = np.mgrid[0:WH, 0:WW].astype(F32)
        band = np.exp(-(((xx * 0.8 + yy * 0.6) - (gloss * 1300 - 300)) / 70.0) ** 2) * 0.16
        im = np.clip(im + band[..., None] * HOT, 0, 1)
    o[WY0:WY0 + WH, WX0:WX0 + WW] = im
    return o, a

S_ID = W / WW                                                                                # card scale at which the window spans the frame width
WOFF = (WX0 + WW / 2 - CW / 2, WY0 + WH / 2 - CH / 2)                                         # window centre relative to the card centre
def card_centre(wcx, wcy, sc, ang):
    r = math.radians(-ang); ox, oy = WOFF[0] * sc, WOFF[1] * sc
    return wcx - (ox * math.cos(r) - oy * math.sin(r)), wcy - (ox * math.sin(r) + oy * math.cos(r))

def crop_centre(cy):
    ch = int(min(H, W / 0.742)); y0 = int(clamp(cy - ch / 2, 0, H - ch)); return W / 2, y0 + ch / 2

def print_draw(out, content, cx, cy, wpx, ang, dev=1.0, gloss=0.0, alpha=1.0, shadow=0.45, lift=1.0, person=None, border=1.0):
    """composite a print centred at (cx, cy), wpx wide on screen, rotated ang degrees, with a soft offset shadow;
    person: drawn behind his matte when given."""
    card, a = print_card(content, dev, gloss, border)
    sc = wpx / CW
    M = cv2.getRotationMatrix2D((CW / 2, CH / 2), ang, sc); M[0, 2] += cx - CW / 2; M[1, 2] += cy - CH / 2
    img = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * alpha
    if person is not None: m = m * (1 - np.clip(person * 1.2, 0, 1))
    o = out
    if shadow > 0:
        Ms = M.copy(); Ms[0, 2] += 14 * lift * sc * 2; Ms[1, 2] += 22 * lift * sc * 2
        sh = cv2.warpAffine(a, Ms, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        sh = cv2.resize(cv2.GaussianBlur(cv2.resize(sh, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 4 + 4 * lift), (W, H)) * alpha
        if person is not None: sh = sh * (1 - np.clip(person * 1.2, 0, 1))
        o = o * (1 - shadow * sh * border)[..., None]
    return mixm(o, img, m)

def print_w(out, content, wcx, wcy, sc, ang, **kw):
    """a print placed by its window centre (wcx, wcy) and card scale sc."""
    cx, cy = card_centre(wcx, wcy, sc, ang); return print_draw(out, content, cx, cy, CW * sc, ang, **kw)

def window_rect(cx, cy, wpx, ang):
    """the print window's screen transform (for diving into it): centre, size and angle of the window."""
    sc = wpx / CW; ox, oy = (WX0 + WW / 2 - CW / 2) * sc, (WY0 + WH / 2 - CH / 2) * sc
    r = math.radians(-ang)
    return cx + ox * math.cos(r) - oy * math.sin(r), cy + ox * math.sin(r) + oy * math.cos(r), WW * sc, WH * sc

def dive(out, full, crop_cy, wcx, wcy, sc0, ang0, u, dev=1.0):
    """fall into a resting print (window centre wcx, wcy, card scale sc0, angle ang0): it straightens and grows until its
    window is the frame; the frame round it turns into the next shot as the card's border falls away, so the last
    frame is exactly `full` (the next shot at scale 1.0)."""
    if u >= 1: return full
    e_ = ein(u, 2.0); sc = sc0 + (S_ID - sc0) * e_; ang = ang0 * (1 - smooth(u))
    tx, ty = crop_centre(crop_cy); wcx2 = wcx + (tx - wcx) * smooth(u); wcy2 = wcy + (ty - wcy) * smooth(u)
    o = defocus(out, 16 * e_) * (1 - 0.30 * e_) if u > 0.12 else out
    w_out = smooth(clamp((u - 0.55) / 0.45, 0, 1))
    o = mixm(o, full, np.full((H, W), w_out, F32)) if w_out > 0 else o
    o = print_w(o, crop_portrait(full, crop_cy), wcx2, wcy2, sc, ang, dev=dev, gloss=0.3 + 0.6 * u, shadow=0.45 * (1 - e_), lift=1 + u, border=1 - w_out)
    z = smooth(clamp((u - 0.72) / 0.28, 0, 1))                                                 # the sharp frame takes over at the end
    return mixm(o, full, np.full((H, W), z, F32)) if z > 0 else o

def settle(B, j, post, z0=1.0):
    return B

# ---- PRINT DIVE (the print, once and fast): a developed print of the next memory flicks in, and we fall into it --------
PD = dict(fly=11, dive=12, wcx=770.0, wcy=1430.0, sc=430.0 / CW, ang=6.0, crop=760)
def back_out(u, s_=1.6):
    u = clamp(u, 0.0, 1.0) - 1; return 1 + u * u * ((s_ + 1) * u + s_)

def print_dive(A, B, j, f, sa, sb, pre=23, post=6):
    """PRINT DIVE: in the lab's last 0.4 s a print of the next memory flicks in from the lower right with a spin (its
    milky veil clearing as it lands), and we fall straight into it: the first suit is behind its window."""
    if j >= 0: return B
    k = j + pre; content = crop_portrait(B, PD["crop"])
    if k < PD["fly"]:
        u = (k + 1) / PD["fly"]; e_ = back_out(u, 1.3)
        wcx = PD["wcx"] + 520 * (1 - e_); wcy = PD["wcy"] + 900 * (1 - e_); ang = PD["ang"] + 34 * (1 - e_)
        return print_w(A, content, wcx, wcy, PD["sc"], ang, dev=0.55 + 0.45 * smooth(u), gloss=0.2 + 0.5 * u, lift=1.6 - 0.6 * u)
    u = (k - PD["fly"] + 1) / PD["dive"]
    return dive(A, B, PD["crop"], PD["wcx"], PD["wcy"], PD["sc"], PD["ang"], u, 1.0)

def shot_by(name):
    return next(s for s in SHOTS if s["n"] == name)

_ORB = {}
def orbs(f, n=14, seed=33):
    """slow warm bokeh lights drifting behind the lensball (quarter res)."""
    if "p" not in _ORB:
        rng = np.random.default_rng(seed); _ORB["p"] = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(20, 70), rng.uniform(0.25, 0.7), rng.uniform(0, 6.28)) for _ in range(n)]
    q = np.zeros((H // 4, W // 4), F32); t = f / FPS
    for x, y, r, a, ph in _ORB["p"]:
        cx = (x + 0.02 * math.sin(t * 0.6 + ph)) * W / 4; cy = ((y - 0.012 * t) % 1.0) * H / 4
        cv2.circle(q, (int(cx), int(cy)), int(r / 4), float(a * (0.75 + 0.25 * math.sin(t * 1.3 + ph))), -1, cv2.LINE_AA)
    return cv2.resize(cv2.GaussianBlur(q, (0, 0), 2.5), (W, H))

# ---- THE LENSBALL (the hero object; the song's pause e30-e46) ---------------------------------------------------------
BALL_C = (540.0, 1275.0); BALL_R = 330.0; BALL_RC = 820.0; BALL_K = 1.15; R_FULL = 1400.0; CCY = 760.0
LB_IN = (6, 24); LB_DIVE = 32; LB_TURN = 14
_BC = {}

def lens_ball(bg, content, cx, cy, R, phi, k, rc, ccx, ccy, hi=1.0, sweep=None):
    """a glass ball lens of radius R at (cx, cy) in front of bg. Inside it the content, turned by phi (180 = the ball's
    own inversion) and squeezed toward the rim (barrel k: the rim maps to rc content px), with rim dispersion, a dark
    Fresnel edge that mirrors the room, a soft window highlight, a sharp specular and a back-lit rim. hi scales the
    glass (0 = the plain content: the first frames of the transition are exactly the shot)."""
    x0, y0 = max(0, int(cx - R - 2)), max(0, int(cy - R - 2)); x1, y1 = min(W, int(cx + R + 3)), min(H, int(cy + R + 3))
    if x1 <= x0 or y1 <= y0: return bg
    gx, gy = _GX[y0:y1, x0:x1] - cx, _GY[y0:y1, x0:x1] - cy
    rr = np.sqrt(gx * gx + gy * gy) / R
    c_, s_ = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    ux, uy = gx * c_ - gy * s_, gx * s_ + gy * c_
    g = (1 + k * rr * rr) / (1 + k) * (rc / R)
    ch = []
    for ci, ca in enumerate((-0.018, 0.0, 0.018)):                                             # rim dispersion (B in, R out)
        gg = g * (1 + ca * hi * rr ** 4) if hi > 0 else g
        mx = (ccx + ux * gg).astype(F32); my = (ccy + uy * gg).astype(F32)
        ch.append(cv2.remap(np.ascontiguousarray(content[..., ci]), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    inner = np.stack(ch, -1)
    if hi > 0:
        ed = np.clip((rr - 0.76) / 0.24, 0, 1) ** 2
        inner = inner * (1 - 0.45 * hi * ed)[..., None]                                       # the Fresnel edge darkens ...
        rf = cv2.resize(bg[y0:y1, x0:x1], ((x1 - x0) // 4 + 1, (y1 - y0) // 4 + 1), interpolation=cv2.INTER_AREA)
        rf = cv2.resize(cv2.GaussianBlur(cv2.flip(rf, -1), (0, 0), 2.5), (x1 - x0, y1 - y0))
        inner = inner + rf * (0.32 * hi * ed)[..., None]                                      # ... and mirrors the room
        inner = inner * (1 + hi * np.array([-0.025, 0.004, 0.030], F32))                     # the glass is a touch warm
        hx, hy = gx + 0.40 * R, gy + 0.46 * R; ca_, sa_ = math.cos(math.radians(-35)), math.sin(math.radians(-35))
        a_ = (hx * ca_ + hy * sa_) / (0.22 * R); b_ = (-hx * sa_ + hy * ca_) / (0.12 * R)
        spec = np.exp(-(a_ * a_ + b_ * b_) ** 1.5) * 0.26                                       # the window, reflected
        spec += np.exp(-((gx + 0.33 * R) ** 2 + (gy + 0.40 * R) ** 2) / (0.034 * R) ** 2) * 0.85   # the sharp specular
        th_ = np.arctan2(gy, gx)
        spec += np.clip((rr - 0.93) / 0.07, 0, 1) * (rr < 1) * np.clip(np.cos(th_ - math.radians(50)), 0, 1) ** 2 * 0.42   # back-lit rim
        if sweep is not None and 0 < sweep < 1:                                               # a glint crosses the glass as it turns
            spec += np.exp(-(((gx * 0.8 + gy * 0.6) / R - (-1.3 + 2.6 * smooth(sweep))) / 0.16) ** 2) * (rr < 1) * 0.20 * math.sin(math.pi * sweep)
        inner = inner + (spec * hi)[..., None] * HOT
    a = np.clip((1 - rr) * R + 0.5, 0, 1)[..., None]
    out = bg.copy(); sub = out[y0:y1, x0:x1]
    if hi > 0:
        sub += (np.exp(-np.clip(rr - 1, 0, None) * R / 60) * (rr >= 1) * 0.10 * hi)[..., None] * GOLDL     # warm light round the glass
    out[y0:y1, x0:x1] = sub * (1 - a) + inner * a
    return np.clip(out, 0, 1)

def ball_content(i, f):
    """memory i inside the ball as a full 9:16 graded frame: the laugh carried in (0), Iris by the water (1), the loft
    (2), the sea run's lead-in (3: graded as the sea run shot, so the dive lands on it)."""
    note, pk, a, b, xc = E.BALL[i]
    if i == 0:
        L = edge14(shot_by("laugh"), "last"); f0 = shot_by("ball")["f0"] + LB_IN[1]
        z = 1 + 0.05 * clamp((f - f0) / max(1, E.fh(34) - LB_TURN // 2 - f0), 0, 1)
        return zoom_about(L, W / 2, H * 0.42, z) if z > 1 else L
    nb = E.BALL[i + 1][0] if i + 1 < len(E.BALL) else 46
    t0, t1 = E.th(note) - LB_TURN / 2 / FPS, E.th(nb) + LB_TURN / 2 / FPS
    tt = a + (b - a) * clamp((f / FPS - t0) / (t1 - t0), 0, 1)
    key = ("c", i, round(tt, 4))
    if key not in _BC:
        if len(_BC) > 12: _BC.clear()
        src = sample(pk, tt, "flow"); h, w = src.shape[:2]; cw = int(round(h * 9 / 16))
        x0 = int(clamp(xc * w / E.SRC[pk][2] - cw / 2, 0, w - cw))
        im = cv2.resize(np.ascontiguousarray(src[:, x0:x0 + cw]), (W, H), interpolation=cv2.INTER_LINEAR).astype(F32) / 255
        ps = shot_by("searun") if i == 3 else dict(n=f"ballsrc{i}", src=pk, tmap=[(0, a), (1, b)], look="sunfade", face=None, target=0.42)
        _BC[key] = grade(im, ps, f)
    return _BC[key]

def ball_rest(f):
    """the resting ball at frame f: centre, radius and turn (a slow bob, a breath on each note it turns on)."""
    t = f / FPS; pulse = 0.0
    for e_ in E.BALL_NOTES[1:]:
        d = t - E.th(e_)
        if d >= 0: pulse = max(pulse, math.exp(-d / 0.25) * min(1.0, d / 0.05))
    cx = BALL_C[0] + 4 * math.sin(2 * math.pi * t / 3.1 + 1.0); cy = BALL_C[1] + 7 * math.sin(2 * math.pi * t / 2.4)
    return cx, cy, BALL_R * (1 + 0.025 * pulse), 180.0 + 2.5 * math.sin(2 * math.pi * t / 2.8)

def lens_entry(bg, L, q, f):
    """the laugh is drawn into the glass: from the plain frame (q = 0) to the resting ball (q = 1), the ball shrinks out
    of the frame's edges, the picture turns upside down inside it and the glass comes up."""
    cx, cy, R, phi = ball_rest(f); e_ = smooth(q)
    R_ = math.exp(math.log(R_FULL) + (math.log(R) - math.log(R_FULL)) * e_)
    return lens_ball(bg, L, W / 2 + (cx - W / 2) * e_, H / 2 + (cy - H / 2) * e_, R_, phi * smooth(clamp((q - 0.08) / 0.84, 0, 1)),
                     BALL_K * e_, R_ + (BALL_RC - R_) * e_, W / 2, H / 2 + (CCY - H / 2) * e_, smooth(clamp(q / 0.7, 0, 1)))

def lens_ball_bg(s, f):
    bgs, _ = base11(s, f)
    bg = defocus(bgs, 14) * 0.84
    ob = orbs(f); fs = face_scr(s, f) if s.get("face") is not None else None
    if fs:                                                                                   # the bokeh drifts round his face, not over it
        fm = np.zeros((H // 4, W // 4), F32); cv2.ellipse(fm, (int(fs[0] / 4), int(fs[1] / 4)), (int(fs[2] * 0.75 / 4), int(fs[2] * 1.0 / 4)), 0, 0, 360, 1.0, -1)
        ob = ob * (1 - cv2.resize(cv2.GaussianBlur(fm, (0, 0), 6), (W, H)))
    lay = np.zeros((H, W, 3), F32); addc(lay, ob, AMBR, 0.22)
    return np.clip(bg + lay, 0, 1)

def ball_fx(s, f):
    """THE LENSBALL: Barry now stands out of focus behind a glass ball that holds his memories upside down. The laugh is
    drawn into it on the pause's first note; it turns to a new memory on each soft note (e34, e38, e42); on the pickup
    (e44) we fall into it and the picture flips upright as the theme returns on the sea run."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]; pre, post = LB_IN
    bg = lens_ball_bg(s, f)
    if k < post:
        return lens_entry(bg, edge14(prev_shot(s), "last"), (k + pre) / (pre + post - 1), f)
    cx, cy, R, phi = ball_rest(f)
    i, tq = 0, None
    for m, e_ in enumerate(E.BALL_NOTES[1:], 1):
        a_ = E.fh(e_) - LB_TURN // 2
        if f >= a_ + LB_TURN: i = m
        elif f >= a_: i, tq = m, (f - a_ + 1) / LB_TURN; break
    if tq is None: content, ccx = ball_content(i, f), W / 2
    else:                                                                                       # the ball turns: the next memory comes round
        content = np.concatenate([ball_content(i - 1, f), ball_content(i, f)], axis=1); ccx = W / 2 + W * smooth(tq)
        phi += 8 * math.sin(math.pi * tq)
    kd = n - LB_DIVE
    if k < kd: return lens_ball(bg, content, cx, cy, R, phi, BALL_K, BALL_RC, ccx, CCY, 1.0, tq)
    q = (k - kd + 1) / (LB_DIVE + 1); e_ = smooth(q) ** 1.15                                 # the dive: we fall into the ball
    full = edge14(nxt_of(s), "first")
    w_ = smooth(clamp((q - 0.70) / 0.30, 0, 1))
    content = content * (1 - w_) + full * w_ if w_ > 0 else content
    R_ = math.exp(math.log(R) + (math.log(R_FULL) - math.log(R)) * e_)
    bgz = zoom_about(bg, cx, cy, 1 + 0.6 * ein(q, 2.0))
    return lens_ball(bgz, content, cx + (W / 2 - cx) * e_, cy + (H / 2 - cy) * e_, R_, phi + (360 - phi) * smooth(clamp((q - 0.08) / 0.84, 0, 1)),
                     BALL_K * (1 - e_), BALL_RC + (R_ - BALL_RC) * e_, W / 2, CCY + (H / 2 - CCY) * e_, 1 - smooth(clamp((q - 0.45) / 0.55, 0, 1)), None)

def lens_in(A, B, j, f, sa, sb, pre=LB_IN[0], post=LB_IN[1]):
    """LENS IN: the laugh starts to bend into the glass just before the note (j < 0); the ball's own frames draw the rest."""
    if j >= 0: return B
    return lens_entry(B, A, (j + pre) / (pre + post - 1), f)

def lens_dive(A, B, j, f, sa, sb, pre=LB_DIVE, post=6):
    """LENS DIVE (the signature): drawn in ball_fx; the sea run is exactly the frame we land on."""
    return A if j < 0 else B

# ---- DOUBLE EXPOSURE ------------------------------------------------------------------------------------------------
def double_exp(A, B, j, f, sa, sb, pre=12, post=14):
    """DOUBLE EXPOSURE: the next memory exposes into this one's shadows first (a film double exposure), the two hold
    together for a moment, then the old one fades out of the highlights."""
    q = (j + pre) / (pre + post); b = smooth(clamp(q / 0.65, 0, 1)); a = 1 - smooth(clamp((q - 0.40) / 0.60, 0, 1))
    A2 = zoom_about(A, W / 2, H * 0.45, 1 + 0.04 * q); B2 = zoom_about(B, W / 2, H * 0.45, 1.05 - 0.05 * q)
    o = 1 - (1 - A2 * a) * (1 - B2 * b * 0.92)
    return np.clip(o / (1 + 0.30 * math.sin(math.pi * q)), 0, 1)

# ---- SUN FLARE ------------------------------------------------------------------------------------------------------
_FLR = {}
def flare_origin(img, sa, f):
    key = (sa["n"],)
    if key not in _FLR:
        q = cv2.GaussianBlur(cv2.resize(lum8(img), (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3)
        fb = face_box(sa, f) if sa.get("face") is not None else None
        if fb: q[:int(fb[2] / 8) + 8, max(0, int(fb[0] / 8) - 4):int(fb[1] / 8) + 4] *= 0.4    # not on his face
        y, x = np.unravel_index(int(np.argmax(q[:int(H / 8 * 0.6)])), q[:int(H / 8 * 0.6)].shape)
        top = H
        for sh_, ff in ((sa, sa["f1"] - 1), (nxt_of(sa), nxt_of(sa)["f0"] if nxt_of(sa) else 0)):
            fs = face_scr(sh_, ff) if sh_ is not None and sh_.get("face") is not None else None
            if fs: top = min(top, fs[1] - 0.95 * fs[2])                                       # above the hairline of both faces
        py = y * 8.0 + 4
        if py > top - 90: py = max(30.0, top - 90)
        _FLR[key] = (x * 8.0 + 4, py)
    return _FLR[key]

def sun_flare(A, B, j, f, sa, sb, pre=10, post=12):
    """SUN FLARE: the brightest light in the shot (the lab's window) blooms across the lens: a soft core, a long warm
    anamorphic streak and a line of ghosts through the centre; the next shot appears as the flare fades."""
    q = (j + pre) / (pre + post); pk = math.sin(math.pi * clamp(q, 0, 1)) ** 1.4
    px, py = flare_origin(A, sa, sa["f1"] - 1)
    mix = smooth(clamp((q - 0.30) / 0.40, 0, 1)); o = A * (1 - mix) + B * mix               # crossed under the flare, not cut
    q4 = np.zeros((H // 4, W // 4), F32)
    cv2.circle(q4, (int(px / 4), int(py / 4)), int(30 + 30 * pk), 1.0, -1)
    core = cv2.GaussianBlur(q4, (0, 0), 14)
    streak = np.exp(-((_GY[::4, ::4] - py) / (10 + 6 * pk)) ** 2) * np.exp(-((_GX[::4, ::4] - px) / (900 + 400 * pk)) ** 2)
    gh = np.zeros((H // 4, W // 4), F32)
    for k_, (t_, r_) in enumerate(((0.55, 34), (1.25, 22), (1.65, 46))):
        gx, gy = px + (W / 2 - px) * 2 * t_, py + (H * 0.5 - py) * 2 * t_
        cv2.circle(gh, (int(gx / 4), int(gy / 4)), r_, 0.35 - 0.08 * k_, -1, cv2.LINE_AA)
    gh = cv2.GaussianBlur(gh, (0, 0), 3)
    lay = np.zeros((H, W, 3), F32)
    addc(lay, cv2.resize(core, (W, H)), HOT, 1.1 * pk); addc(lay, cv2.resize(streak.astype(F32), (W, H)), AMBR, 0.70 * pk)
    addc(lay, cv2.resize(gh, (W, H)), GOLDL, 0.60 * pk)
    room = np.clip(1.1 - lum8(o), 0.15, 1)[..., None]
    return np.clip(o * (1 + 0.10 * pk) + lay * room, 0, 1)

# ---- FILM BURN ------------------------------------------------------------------------------------------------------
_NZ = {}
def burn_noise():
    if "n" not in _NZ:
        rng = np.random.default_rng(1414)
        n = sum(cv2.resize(cv2.GaussianBlur(rng.standard_normal((H // s_, W // s_)).astype(F32), (0, 0), 2), (W, H)) * w_
                for s_, w_ in ((32, 1.0), (12, 0.5), (5, 0.25)))
        _NZ["n"] = (n / n.std()).astype(F32)
    return _NZ["n"]

def film_burn(A, B, j, f, sa, sb, pre=8, post=12):
    """FILM BURN: the frame stops in the gate and the projector lamp burns through it: a bubbling hole opens at the
    corner with a white-hot rim and a scorched brown edge, and the next memory is behind it."""
    q = (j + pre) / (pre + post - 1); nz = burn_noise()
    cx, cy = W * 0.92, H * 0.94                                                               # the bottom-right corner, away from him
    fm = np.zeros((H, W), F32)                                                                # his face: the front is smooth and soft there
    for sh_, ff in ((sa, sa["f1"] - 1), (sb, sb["f0"])):
        fs = face_scr(sh_, ff) if sh_.get("face") is not None else None
        if fs: cv2.ellipse(fm, (int(fs[0]), int(fs[1])), (int(fs[2] * 0.85), int(fs[2] * 1.15)), 0, 0, 360, 1.0, -1)
    fm = cv2.GaussianBlur(fm, (0, 0), 50)
    R = 40 + 2400 * ein(q, 1.9)
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) - 120 * nz * (1 - 0.9 * fm)
    m = np.clip((R - d) / (18 + 160 * fm) + 0.5, 0, 1)
    if q >= 1: return B
    rim = np.exp(-((R - d) / (26 + 20 * q)) ** 2) * (1 - q ** 3) * (1 - 0.9 * fm)
    scorch = np.clip(1 - (d - R) / 160, 0, 1) * (d > R) * (1 - q ** 2) * (1 - 0.9 * fm)
    brown = np.array([0.05, 0.12, 0.30], F32)
    Af = A * (1 - 0.70 * scorch)[..., None] + (0.55 * scorch)[..., None] * brown
    o = mixm(Af, B, m)
    lay = np.zeros((H, W, 3), F32); addc(lay, rim, GOLDL, 0.75); addc(lay, cv2.GaussianBlur(rim, (0, 0), 14), EMBR, 1.0)
    return np.clip(o + lay, 0, 1)

# ---- RIPPLE (water to water) -------------------------------------------------------------------------------------------
def ripple(A, B, j, f, sa, sb, pre=10, post=14):
    """RIPPLE: a drop falls on the sea; its rings refract the picture and the next shot surfaces from the centre outward
    behind the leading ring."""
    q = (j + pre) / (pre + post - 1)
    if q >= 1: return B
    cx, cy = W * 0.50, H * 0.80
    r = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); front = 60 + 2300 * ein(q, 1.6)
    env = np.exp(-((r - front * 0.85) / 260) ** 2) * (1 - q) + 0.35 * np.exp(-r / 700) * (1 - q)
    disp = 46 * env * np.sin(r / 46 - q * 16)
    dx = (disp * (_GX - cx) / (r + 1)).astype(F32); dy = (disp * (_GY - cy) / (r + 1)).astype(F32)
    mx, my = (_GX + dx).astype(F32), (_GY + dy).astype(F32)
    Aw = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = np.clip((front * 0.85 - r) / 260 + 0.5, 0, 1)
    o = mixm(Aw, Bw, m)
    spec = np.clip(np.sin(r / 46 - q * 16 + 0.6) * env, 0, 1) ** 2.5 * 0.55
    lay = np.zeros((H, W, 3), F32); addc(lay, spec, HOT, 1.0)
    return np.clip(o + lay, 0, 1)

# ---- FOCUS RACK ------------------------------------------------------------------------------------------------------
def focus_rack14(A, B, j, f, sa, sb, pre=10, post=12):
    """FOCUS RACK: the lens racks out until the sunset is all warm bokeh, the next shot is found in the blur, and the lens
    racks back in on it."""
    if j < 0:
        u = (j + pre) / pre; o = defocus(A, 50 * ein(u, 1.8))
        if j >= -8: o = mixm(o, defocus(B, 50), np.full((H, W), smooth((j + 9) / 9), F32))       # found in the blur over 8 frames
        return o
    v = (j + 1) / post; return defocus(B, 50 * (1 - eout(v, 2.0)))

# ---- EMBLEM GLINT (the emblem transition): the real S1 emblem, its bolt redrawn to the shape traced on the source ------
# The S1 emblem runs off the bottom of every S1 frame (the lower third of the disc is below the source's last row), so
# the camera can't rise onto it from the footage alone. The emblem is drawn (EMB_BOLT, traced on the real bolt: a
# point-symmetric zigzag whose tips pass the ring) and laid exactly over the real one as the push begins; the suit
# below the frame is the bottom band with the emblem inpainted out, mirrored down.
GL_PRE, GL_POST, EXT = 97, 30, 520
_EMC = {}
def emb_src(t):
    T = E.EMB_TRACK; ts = [a_[0] for a_ in T]
    return float(np.interp(t, ts, [a_[1] for a_ in T])), float(np.interp(t, ts, [a_[2] for a_ in T]))

def emb_screen(s, f):
    """the real emblem's centre and radius on screen (the measured source track through the shot's camera)."""
    t, _, _ = src_time(s, f); x, y = emb_src(t); X, Y, sc = to_screen(s, f, x, y); return X, Y, E.EMB_R * sc

def emb_colors(sa):
    """the disc's red and the ring's gold as graded in this shot (sampled on the real emblem at the push's first frame,
    so every frame gets the same colours whatever order they render in)."""
    if sa["n"] not in _EMC:
        f = sa["f1"] - GL_PRE; A = base11(sa, f)[0]; ex, ey, er = emb_screen(sa, f)
        px, py = int(ex - 0.45 * er), int(ey - 0.30 * er)
        disc = np.median(A[py - 6:py + 7, px - 6:px + 7].reshape(-1, 3), axis=0)
        ring = A[int(ey - er * 1.03):int(ey - er * 0.90), int(ex - 0.35 * er):int(ex + 0.35 * er)].reshape(-1, 3)
        gold = ring[np.argsort(lum8(ring[None])[0])[-max(6, len(ring) // 8):]].mean(0)
        _EMC[sa["n"]] = (disc.astype(F32), gold.astype(F32))
    return _EMC[sa["n"]]

def emb_canvas(A, ex, ey, er):
    """A with EXT px of suit below the frame: the emblem inpainted out of the bottom band, mirrored down."""
    band = A[H - EXT:]; q = 4
    sm = cv2.resize(band, (W // q, EXT // q), interpolation=cv2.INTER_AREA)
    mk = np.zeros(sm.shape[:2], np.uint8); oy = ey - (H - EXT)
    cv2.circle(mk, (int(ex / q), int(oy / q)), int(er * 1.16 / q), 255, -1)
    pts = (np.array(E.EMB_BOLT, F32) * er * 1.10 + np.array([ex, oy], F32)) / q
    cv2.fillPoly(mk, [np.round(pts).astype(np.int32)], 255); mk = cv2.dilate(mk, np.ones((5, 5), np.uint8))
    inp = cv2.inpaint((np.clip(sm, 0, 1) * 255).astype(np.uint8), mk, 7, cv2.INPAINT_TELEA).astype(F32) / 255
    m = cv2.resize(cv2.GaussianBlur(mk.astype(F32) / 255, (0, 0), 1.5), (W, EXT))[..., None]
    band2 = band * (1 - m) + cv2.resize(inp, (W, EXT), interpolation=cv2.INTER_LINEAR) * m
    return np.concatenate([A, band2[::-1]], axis=0)

def emblem_draw(out, cx, cy, R, disc, gold, alpha=1.0, lit_p=0.0, lit=0.0, ring_p=None, ring=0.0, flare=0.0, portal=None, pr=0.0, bolt_a=1.0):
    """the S1 emblem drawn at (cx, cy), radius R px, lit from the upper left: a dark red disc (the shot's own red), a
    bevelled gold ring and the bolt (bevelled, with a soft contact shadow on the disc and the suit). lit lights the bolt
    from its top tip down to lit_p (0 = top tip, 1 = bottom tip); ring lights the ring (a light at angle ring_p runs
    round it); flare makes it glow; portal (an image) opens inside the disc to radius pr px behind the bolt."""
    m_ = 1.62 * R
    x0, y0, x1, y1 = max(0, int(cx - m_)), max(0, int(cy - m_)), min(W, int(cx + m_) + 1), min(H, int(cy + m_) + 1)
    if x1 <= x0 or y1 <= y0 or alpha <= 0: return out
    w_, h_ = x1 - x0, y1 - y0; gx, gy = _GX[y0:y1, x0:x1] - cx, _GY[y0:y1, x0:x1] - cy
    rho = np.sqrt(gx * gx + gy * gy) / R
    P = np.array(E.EMB_BOLT, F32) * R + np.array([cx - x0, cy - y0], F32)
    ss = 2; bm = np.zeros((h_ * ss, w_ * ss), np.uint8)
    cv2.fillPoly(bm, [np.round(P * ss * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    bm = cv2.resize(bm, (w_, h_), interpolation=cv2.INTER_AREA).astype(F32) / 255
    aa = 1.0 / max(R, 1.0)
    rm = np.clip((rho - 0.935) / aa + 0.5, 0, 1) * np.clip((1.0 - rho) / aa + 0.5, 0, 1)        # the ring
    dm = np.clip((0.95 - rho) / aa + 0.5, 0, 1)                                               # the disc (under the ring's inner half)
    bm = bm * bolt_a; gm = np.maximum(bm, rm)                                                 # gold (the bolt can fade into its own light)
    # bevel: a rounded height field on the bolt and the ring, lit from the upper left
    hb = np.clip(cv2.distanceTransform((bm > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / max(1.0, 0.055 * R), 0, 1)
    hb = hb * hb * (3 - 2 * hb)
    hr = np.sin(math.pi * np.clip((rho - 0.935) / 0.065, 0, 1)) * (rm > 0)
    hh = cv2.GaussianBlur(np.maximum(hb * bm, hr), (0, 0), max(0.6, 0.006 * R))
    sx = cv2.Sobel(hh, cv2.CV_32F, 1, 0, ksize=3); sy = cv2.Sobel(hh, cv2.CV_32F, 0, 1, ksize=3)
    kk = 0.06 * R; nx, ny, nz = -sx * kk / 8, -sy * kk / 8, np.ones_like(sx)
    nn = np.sqrt(nx * nx + ny * ny + nz * nz); L_ = np.array([-0.50, -0.68, 0.75], F32); L_ /= np.linalg.norm(L_)
    dif = np.clip((nx * L_[0] + ny * L_[1] + nz * L_[2]) / nn, 0, 1)
    gs = np.clip(0.18 + 0.70 * dif ** 1.4 + 0.55 * dif ** 24, 0, 1.3)
    hi_g = gold * 0.45 + np.array([0.62, 0.92, 1.00], F32) * 0.55; dk_g = gold * 0.30
    gcol = np.where((gs < 0.55)[..., None], dk_g + (gold - dk_g) * (gs / 0.55)[..., None], gold + (hi_g - gold) * np.clip((gs - 0.55) / 0.6, 0, 1.3)[..., None])
    # the bolt lit from its top tip down to lit_p, the ring lit round from ring_p
    T_, B_ = np.array(E.EMB_BOLT[0], F32), np.array(E.EMB_BOLT[3], F32); ax = B_ - T_
    pos = ((gx / R - T_[0]) * ax[0] + (gy / R - T_[1]) * ax[1]) / float(ax @ ax)
    lt = bm * np.clip((lit_p - pos) / 0.12 + 1, 0, 1) * lit
    if ring_p is not None:
        dth = np.angle(np.exp(1j * (np.arctan2(gy, gx) - ring_p))).astype(F32)
        rl = rm * (np.exp(-(dth / 0.35) ** 2) + ring * 0.6)
    else: rl = rm * ring * 0.6
    gcol = gcol * (1 + 0.32 * lt + 0.40 * rl + 0.25 * flare * gm)[..., None] + (lt * 0.12 + rl * 0.20)[..., None] * HOT
    # the disc: the shot's red, lighter to the upper left, the bolt's shadow on it
    shb = cv2.GaussianBlur(np.roll(np.roll(bm, int(0.05 * R), 0), int(0.035 * R), 1), (0, 0), max(1.0, 0.03 * R))
    dcol = disc * (0.90 + 0.16 * np.clip(-(gx + gy) / (2.8 * R), -1, 1))[..., None] * (1 - 0.55 * shb)[..., None]
    dcol = dcol * (1 + 0.6 * flare) + flare * 0.10 * GOLDL
    sub = out[y0:y1, x0:x1].copy()
    if portal is not None and pr > 0:
        pm = np.clip((pr - rho * R) / max(6.0, 0.08 * R) + 0.5, 0, 1) * np.clip((0.94 - rho) / aa + 0.5, 0, 1)
        dcol = dcol * (1 - pm[..., None]) + portal[y0:y1, x0:x1] * pm[..., None]
        edge_ = np.exp(-((rho * R - pr) / max(4.0, 0.05 * R)) ** 2) * (rho < 0.95) * (pr < 0.94 * R)
        dcol = dcol + edge_[..., None] * GOLDL * 0.55
    sub = sub * (1 - 0.50 * shb * (rho > 1.0) * alpha)[..., None]                             # the tips' shadow on the suit
    emb = dcol * (dm * (1 - gm))[..., None] + gcol * gm[..., None]
    am = np.maximum(dm, gm) * alpha
    out[y0:y1, x0:x1] = sub * (1 - am[..., None]) + emb * am[..., None]
    if lit > 0 or flare > 0 or ring > 0:                                                      # the light it gives off
        q4 = cv2.resize(lt + 0.6 * rl + flare * gm, (w_ // 4 + 1, h_ // 4 + 1), interpolation=cv2.INTER_AREA)
        g1 = cv2.resize(cv2.GaussianBlur(q4, (0, 0), max(1.0, 0.02 * R)), (w_, h_)); g2 = cv2.resize(cv2.GaussianBlur(q4, (0, 0), max(2.0, 0.07 * R)), (w_, h_))
        o_ = out[y0:y1, x0:x1]; o_ += (g1 * (0.55 + 0.4 * flare) * alpha)[..., None] * GOLDL + (g2 * (0.45 + 0.5 * flare) * alpha)[..., None] * AMBR
    return out

def bolt_edge_pts(cx, cy, R):
    return np.array(E.EMB_BOLT, F32) * R + np.array([cx, cy], F32)

def glint_path(cx, cy, R, p):
    """a point on the bolt's lit upper-left edge (top tip -> the step -> bottom tip), p in 0..1 by arc length."""
    P = bolt_edge_pts(cx, cy, R)[[0, 1, 2, 3]]
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); s_ = clamp(p, 0, 1) * cum[-1]
    i = min(int(np.searchsorted(cum, s_, side="right")) - 1, len(seg) - 1); u = (s_ - cum[i]) / max(seg[i], 1e-6)
    return P[i] + (P[i + 1] - P[i]) * u

def glint_star(o, x, y, L, a):
    """a four-point specular star with a hot core (half res, blurred)."""
    q = np.zeros((H // 2, W // 2), F32); xx, yy = x / 2, y / 2
    for ang, ln in ((0.26, L), (0.26 + math.pi / 2, L * 0.75)):
        dx, dy = math.cos(ang) * ln / 4, math.sin(ang) * ln / 4
        cv2.line(q, (int((xx - dx) * 4), int((yy - dy) * 4)), (int((xx + dx) * 4), int((yy + dy) * 4)), a, 1, cv2.LINE_AA, shift=2)
    cv2.circle(q, (int(xx * 4), int(yy * 4)), int(max(2.0, L / 30) * 4), a, -1, cv2.LINE_AA, shift=2)
    st = cv2.resize(cv2.GaussianBlur(q, (0, 0), 0.9), (W, H)); addc(o, st, HOT, 1.3); addc(o, cv2.resize(cv2.GaussianBlur(q, (0, 0), 6), (W, H)), GOLDL, 1.2)
    return o

def emb_arcs(o, cx, cy, R, n, f, amp):
    """small gold lightning arcs crawling off the bolt's edges (re-struck every 2 frames), half res."""
    if n <= 0 or amp <= 0: return o
    P = bolt_edge_pts(cx, cy, R); rng = np.random.default_rng(6400 + f // 2)
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    q = np.zeros((H // 2, W // 2), F32)
    for _ in range(n):
        s_ = rng.uniform(0, cum[-1]); i = min(int(np.searchsorted(cum, s_, side="right")) - 1, len(P) - 1)
        a_, b_ = P[i], P[(i + 1) % len(P)]; u = (s_ - cum[i]) / max(seg[i], 1e-6); p = a_ + (b_ - a_) * u
        d = (b_ - a_) / max(seg[i], 1e-6); nrm = np.array([d[1], -d[0]], F32)
        if cv2.pointPolygonTest(P.reshape(-1, 1, 2), (float(p[0] + nrm[0] * 3), float(p[1] + nrm[1] * 3)), False) > 0: nrm = -nrm
        hd = math.atan2(nrm[1], nrm[0]) + rng.uniform(-0.8, 0.8); L = R * rng.uniform(0.16, 0.36); st = 8
        pts = [p.copy()]
        for k_ in range(st):
            hd += rng.normal(0, 0.55); pts.append(pts[-1] + np.array([math.cos(hd), math.sin(hd)], F32) * L / st)
            if k_ == 3 and rng.random() < 0.7:
                bh = hd + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1); bp = [pts[-1].copy()]
                for _k in range(3): bh += rng.normal(0, 0.5); bp.append(bp[-1] + np.array([math.cos(bh), math.sin(bh)], F32) * L / st)
                cv2.polylines(q, [np.round(np.array(bp) / 2 * 4).astype(np.int32)], False, 0.7 * amp, 1, cv2.LINE_AA, shift=2)
        cv2.polylines(q, [np.round(np.array(pts) / 2 * 4).astype(np.int32)], False, amp, 1, cv2.LINE_AA, shift=2)
    core = cv2.resize(cv2.GaussianBlur(q, (0, 0), 0.6), (W, H))
    addc(o, core, HOT, 1.6); addc(o, cv2.resize(cv2.GaussianBlur(q, (0, 0), 3), (W, H)), GOLDL, 1.4); addc(o, cv2.resize(cv2.GaussianBlur(q, (0, 0), 10), (W, H)), AMBR, 0.8)
    return o

def glint_B(B, sb, ex, ey, k):
    """the next shot, shifted so his lit face is in the emblem's opening (k = 1), easing back to its framing (k = 0)."""
    fs = face_scr(sb, sb["f0"]) if sb.get("face") is not None else None
    if not fs or k <= 0: return B
    return shift_img(B, (ex - fs[0]) * k, (ey - fs[1]) * k)

GL_TGT = (540.0, 1150.0)
def glint_cam(A, sa, f, u):
    """the camera finds the emblem: a slow push (to 1.45x) that tilts down onto it (the emblem rises to GL_TGT)."""
    ex, ey, er = emb_screen(sa, f); P_ = smooth(clamp(u / 0.78, 0, 1)); s_ = 1 + 0.40 * P_ + 0.05 * u
    tx, ty = ex + (GL_TGT[0] - ex) * P_, ey + (GL_TGT[1] - ey) * P_
    M = np.float32([[s_, 0, tx - s_ * ex], [0, s_, ty - s_ * ey]])
    C = emb_canvas(A, ex, ey, er)
    o = cv2.warpAffine(C, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if P_ > 0.02:                                                                             # depth: the lens holds focus on the emblem
        d = np.sqrt((_GX - tx) ** 2 + (_GY - ty) ** 2); m = np.clip((d - 1.7 * er * s_) / (0.8 * er * s_), 0, 1)
        o = mixm(o, defocus(o, 5 * P_), m)
    return o, tx, ty, er * s_, s_

def emblem_glint(A, B, j, f, sa, sb, pre=GL_PRE, post=GL_POST):
    """EMBLEM GLINT, slow and pronounced (2.1 s): the camera pushes down onto the S1 emblem, which sharpens into the
    drawn emblem (the bolt traced on the real one); a glint runs down the bolt's zigzag and lights it from the top tip
    to the bottom tip; a light runs round the ring; gold lightning crawls off the bolt's edges; the emblem glows and its
    disc opens on his lit face, and we fly through the ring into the next memory."""
    disc, gold = emb_colors(sa)
    if j < 0:
        u = (j + pre) / pre
        o, tx, ty, R, _ = glint_cam(A, sa, f, u)
        gp = clamp((u - 0.34) / 0.26, 0, 1); rq = clamp((u - 0.56) / 0.26, 0, 1); au = clamp((u - 0.58) / 0.42, 0, 1)
        fl = smooth(clamp((u - 0.80) / 0.20, 0, 1)); pu = clamp((u - 0.84) / 0.16, 0, 1)
        portal = glint_B(B, sb, tx, ty, 1.0) if pu > 0 else None
        o = emblem_draw(o, tx, ty, R, disc, gold, alpha=smooth(clamp(u / 0.09, 0, 1)), lit_p=gp * 1.15, lit=1.0 if gp > 0 else 0.0,
                        ring_p=(-math.pi / 2 + 2 * math.pi * rq) if 0 < rq < 1 else None, ring=smooth(rq), flare=0.8 * fl,
                        portal=portal, pr=0.94 * R * ein(pu, 1.4), bolt_a=1 - 0.85 * smooth(pu))
        if 0 < gp < 1:
            x, y = glint_path(tx, ty, R, gp); o = glint_star(o, x, y, R * (0.55 + 0.35 * math.sin(math.pi * gp)), 1.0)
        o = emb_arcs(o, tx, ty, R, int(round(1 + 6 * au)) if au > 0 else 0, f, 0.55 + 0.45 * au)
        return np.clip(o, 0, 1)
    v = (j + 1) / post
    if v >= 1: return B
    o, tx, ty, R, s0 = glint_cam(A, sa, sa["f1"] - 1, 1.0)
    sf = 1 + 3.2 * ein(v, 1.7)                                                                # we fly through the ring
    o = zoom_about(o, tx, ty, sf); R2 = R * sf
    cx_, cy_ = tx + (W / 2 - tx) * smooth(v), ty + (H * 0.5 - ty) * smooth(v)
    o = shift_img(o, cx_ - tx, cy_ - ty)
    Bp = glint_B(B, sb, cx_, cy_, 1 - smooth(clamp(v / 0.75, 0, 1)))
    o = emblem_draw(o, cx_, cy_, R2, disc, gold, alpha=1 - smooth(clamp(v / 0.8, 0, 1)), lit_p=1.2, lit=1.0, ring=1.0, flare=0.8 * (1 - v), portal=Bp, pr=0.94 * R2,
                    bolt_a=0.15 * (1 - smooth(clamp(v / 0.4, 0, 1))))
    m = np.clip((0.94 * R2 - np.sqrt((_GX - cx_) ** 2 + (_GY - cy_) ** 2)) / 30 + 0.5, 0, 1)
    o = mixm(o, Bp, m * smooth(clamp(v / 0.5, 0, 1)))
    o = mixm(o, B, np.full((H, W), smooth(clamp((v - 0.7) / 0.3, 0, 1)), F32))
    return np.clip(o, 0, 1)

# ---- SPEED WHIP / LIGHT LEAK / MEMORY ECHO ------------------------------------------------------------------------------
def speed_whip14(A, B, j, f, sa, sb, pre=5, post=7):
    """SPEED WHIP: a real whip pan across the two shots laid side by side (the camera swings from one memory to the
    next; no mirrored edges), with motion blur and a soft streak of his gold light at chest height."""
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1))
    strip = np.concatenate([A, B], axis=1); x0 = int(round(p * W))
    o = np.ascontiguousarray(strip[:, x0:x0 + W]); sp = math.sin(math.pi * clamp(q, 0, 1))
    o = hblur(o, 2 + 150 * sp)
    xs = np.exp(-((_GX[:1, :] - W * 0.5) / 360.0) ** 2)                                        # fades toward both edges
    band = np.exp(-((_GY[:, :1] - H * 0.80) / 12.0) ** 2) * xs * sp
    lay = np.zeros((H, W, 3), F32); addc(lay, band, HOT, 0.30); addc(lay, np.exp(-((_GY[:, :1] - H * 0.80) / 50.0) ** 2) * xs * sp, AMBR, 0.16)
    return np.clip(o + lay, 0, 1)

def light_leak14(A, B, j, f, sa, sb, pre=10, post=12):
    """LIGHT LEAK: a warm red-orange leak floods in from the edge of the film, and the shots cross under its peak."""
    q = (j + pre) / (pre + post); pk = math.sin(math.pi * q)
    mix = smooth((q - 0.35) / 0.30); o = A * (1 - mix) + B * mix
    q4 = np.zeros((H // 4, W // 4), F32)
    for (x0, y0, x1, y1, r, a) in ((1.25, 0.10, 0.55, 0.30, 0.48, 1.0), (-0.25, 0.85, 0.40, 0.62, 0.36, 0.7)):
        x = (x0 + (x1 - x0) * q) * W / 4; y = (y0 + (y1 - y0) * q) * H / 4
        cv2.circle(q4, (int(x), int(y)), int(r * W / 4), a, -1)
    lk = cv2.resize(cv2.GaussianBlur(q4, (0, 0), 40), (W, H))
    lay = np.zeros((H, W, 3), F32); addc(lay, lk, EMBR, 0.75 * pk); addc(lay, lk ** 2, GOLDL, 0.55 * pk)
    return np.clip(o * (1 + 0.12 * pk) + lay * np.clip(1.1 - lum8(o), 0.2, 1)[..., None], 0, 1)

def memory_echo(A, B, j, f, sa, sb, pre=12, post=12):
    """MEMORY ECHO: the memory lets go: faint gold copies of him drift up, the picture washes into a warm haze like an
    over-exposed print, and the present comes up out of it (the two shots cross only inside the haze)."""
    m = PERSON.get(f)
    q = (j + pre) / (pre + post); hz = math.sin(math.pi * q) ** 1.6
    mix = smooth(clamp((q - 0.42) / 0.16, 0, 1)); o = A * (1 - mix) + B * mix
    if j < 0 and m is not None:
        u = (j + pre) / pre; fig = A * np.clip(m * 1.3, 0, 1)[..., None]
        for k in range(1, 3):
            c = shift_img(fig, 0, -80 * k * ein(u, 1.3)); o = o + lum8(c)[..., None] * GOLDL * (0.14 * u * (1 - k / 3))
    warm = np.array([0.62, 0.78, 0.92], F32)
    o = o * (1 - 0.55 * hz) + warm * (0.55 * hz) * np.clip(0.6 + lum8(o), 0, 1)[..., None]
    return np.clip(o, 0, 1)

TR2.update({"print_dive": (print_dive, 23, 6), "double_exp": (double_exp, 12, 14), "sun_flare": (sun_flare, 10, 12),
            "film_burn": (film_burn, 8, 12), "lens_in14": (lens_in, LB_IN[0], LB_IN[1]), "lens_dive14": (lens_dive, LB_DIVE, 6),
            "ripple": (ripple, 10, 14), "focus_rack14": (focus_rack14, 10, 12), "emblem_glint": (emblem_glint, GL_PRE, GL_POST),
            "speed_whip14": (speed_whip14, 5, 7), "light_leak14": (light_leak14, 10, 12), "afterimage14": (memory_echo, 12, 12),
            "lights_on14": ((lambda A, B, j, f, sa, sb: B), 0, 24)})

# ---- the medical bay's lights: dim before he wakes, flickering on (frame 0) and flickering out (the loop) ---------------
LIGHTS_ON = [0.30] * 8 + [0.82, 0.86, 0.40, 0.36, 0.42, 1.0, 0.97, 0.60, 0.66, 0.92, 0.95, 0.90, 0.94, 0.97, 0.99, 1.0]
def lights_on(f):
    return LIGHTS_ON[0] if f < 0 else (LIGHTS_ON[f] if f < len(LIGHTS_ON) else 1.0)

def dim(img, L):
    """the room with its lights down to L: cooler and darker, but its screens and the IV bag still glow."""
    if L >= 1: return img
    keep = np.clip((lum8(img) - 0.40) / 0.30, 0, 1) * np.clip((img[..., 0] - img[..., 2]) * 4, 0, 1) * (1 - L) * 0.85   # only the cyan screens
    o = img * (L + keep)[..., None]
    return np.clip(o * (1 + (1 - L) * np.array([0.16, 0.02, -0.12], F32)), 0, 1)

def frame_virtual(fv):
    """frame 0's own picture at a virtual frame fv < 0 (the dark room, before the lights come on)."""
    s0 = SHOTS[0]; out, _ = base14(s0, fv)
    return out

# THE LOOP: the last memory's lights flicker twice on the strong notes (e92, e94) and the dark medical bay flashes through
# for a few frames each time; then the lights go out and it is the dark room of frame 0 that is left at the wrap.
def loop_lights(img, f, s):
    e92, e94, end = E.fh(92), E.fh(94), s["f1"]
    room = lambda: frame_virtual(f - E.DUR_F)                                                # frame 0's dark room (already dimmed)
    flashes = [(e92, 3), (e94, 4)]
    for a_, n_ in flashes:
        if a_ <= f < a_ + n_: return room()
        if a_ + n_ <= f < a_ + n_ + 3: return dim(img, (0.55, 0.82, 0.96)[f - a_ - n_])
    out0 = end - 20                                                                          # the lights go out
    if f < out0: return img
    k = f - out0
    seq = [0.80, 0.55, 0.40, 0.34, 0.75, 0.70, 0.36, 0.32]                                  # a last flicker, then down
    if k < len(seq): return dim(img, seq[k])
    w = smooth(clamp((k - len(seq) + 1) / 5, 0, 1))
    return dim(img, 0.32) * (1 - w) + room() * w

# ---- THE ACHIEVEMENT (the owner's toast; our own pixel font and crate icon, built from code) ---------------------------
TP = 6                                                                                       # screen px per toast pixel
GLY = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "c": [".....", ".....", ".####", "#....", "#....", "#....", ".####"],
    "d": ["....#", "....#", ".##.#", "#..##", "#...#", "#...#", ".####"],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".####"],
    "g": [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", "####."],
    "h": ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#"],
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#...#", "#...#"],
    "n": [".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "t": [".#..", ".#..", "####", ".#..", ".#..", ".#..", "..##"],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "!": ["#", "#", "#", "#", "#", ".", "#"],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}
TOAST_U = (128, 32); TOAST_TITLE, TOAST_DESC = "Achievement Made!", "The Beginning?"
TOAST_C = (540.0, 1364.0)
COL_T = np.array([0.32, 0.93, 0.90], F32); COL_D = np.array([1.0, 1.0, 1.0], F32)
_TS = {}

def crate_icon():
    """a 16 x 16 wooden crate with a lid, planks and a latch (our own pixels), BGRA."""
    if "icon" in _TS: return _TS["icon"]
    o_, li, wd, dk, mt, mk = (0.05, 0.10, 0.17), (0.25, 0.48, 0.72), (0.16, 0.34, 0.55), (0.10, 0.22, 0.38), (0.62, 0.66, 0.68), (0.22, 0.24, 0.26)
    ic = np.zeros((16, 16, 4), F32)
    for y in range(1, 15):
        for x in range(1, 15):
            if x in (1, 14) or y in (1, 14) or y == 6: c = o_
            elif y <= 5: c = li if (y == 2 or x == 2) else (dk if x == 13 else wd)                # the lid, lit from the upper left
            else: c = dk if (y in (9, 12) or x == 13) else (li if x == 2 else wd)              # the body's planks
            ic[y, x, :3] = c; ic[y, x, 3] = 1
    for y in range(5, 9):
        for x in range(7, 9): ic[y, x, :3] = mt if (5 < y < 8) else mk                       # the latch
    _TS["icon"] = ic; return ic

def put_glyph(spr, ch, x, y, col, a):
    g = GLY[ch]
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v != "#": continue
            ya, xa = y + r * TP, x + c * TP
            if ya < 0 or xa < 0 or ya + TP > spr.shape[0] or xa + TP > spr.shape[1]: continue
            blk = spr[ya:ya + TP, xa:xa + TP]
            blk[..., :3] = blk[..., :3] * (1 - a) + col * a; blk[..., 3] = np.maximum(blk[..., 3], a)

def put_text(spr, txt, ux, uy, col, k, k0, step):
    """a line of pixel text; each letter hops in on its own frame (k0 + n * step), with the font's drop shadow."""
    x = ux * TP
    for n, ch in enumerate(txt):
        a = clamp((k - (k0 + n * step)) / 2.5, 0, 1)
        if a > 0 and ch != " ":
            dy = int(round(-9 * math.sin(math.pi * a))) if a < 1 else 0
            put_glyph(spr, ch, x + TP, uy * TP + dy + TP, col * 0.26, a)                       # the shadow, one pixel down-right
            put_glyph(spr, ch, x, uy * TP + dy, col, a)
        x += (len(GLY[ch][0]) + 1) * TP

def toast_box():
    if "box" in _TS: return _TS["box"]
    uw, uh = TOAST_U; b = np.zeros((uh, uw, 4), F32)
    b[1:-1, 1:-1, :3] = 0.125; b[1:-1, 1:-1, 3] = 0.94
    b[0, 1:-1, :3] = b[-1, 1:-1, :3] = 0.40; b[1:-1, 0, :3] = b[1:-1, -1, :3] = 0.40
    b[0, 1:-1, 3] = b[-1, 1:-1, 3] = b[1:-1, 0, 3] = b[1:-1, -1, 3] = 1.0                       # a light grey border, notched corners
    b[1, 1:-1, :3] = 0.19; b[-2, 1:-1, :3] = 0.08                                             # a one-pixel bevel inside it
    _TS["box"] = cv2.resize(b, (uw * TP, uh * TP), interpolation=cv2.INTER_NEAREST); return _TS["box"]

def toast_sprite(k):
    spr = toast_box().copy()
    ki = k - 5                                                                               # the crate pops in with a bounce and a wobble
    if ki >= 0:
        si = 1 - math.exp(-ki / 2.6) * math.cos(0.8 * ki); rot = 10 * math.exp(-ki / 4) * math.sin(0.9 * ki)
        ic = cv2.resize(crate_icon(), (16 * TP, 16 * TP), interpolation=cv2.INTER_NEAREST)
        icx, icy = (8 + 8) * TP, (8 + 8) * TP
        if abs(si - 1) < 0.004 and abs(rot) < 0.05:
            sub = spr[8 * TP:24 * TP, 8 * TP:24 * TP]; al = ic[..., 3:4]
            sub[..., :3] = sub[..., :3] * (1 - al) + ic[..., :3] * al; sub[..., 3:4] = np.maximum(sub[..., 3:4], al)
        elif si > 0.02:
            M = cv2.getRotationMatrix2D((8 * TP, 8 * TP), rot, si); M[0, 2] += icx - 8 * TP; M[1, 2] += icy - 8 * TP
            w_ = cv2.warpAffine(ic, M, (spr.shape[1], spr.shape[0]), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
            al = w_[..., 3:4]; spr[..., :3] = spr[..., :3] * (1 - al) + w_[..., :3] * al; spr[..., 3:4] = np.maximum(spr[..., 3:4], al)
    put_text(spr, TOAST_TITLE, 30, 7, COL_T, k, 5, 0.45)
    put_text(spr, TOAST_DESC, 30, 18, COL_D, k, 11, 0.40)
    if 18 <= k < 34:                                                                         # a stepped shine crosses the box
        uw, uh = TOAST_U; yy, xx = np.mgrid[0:uh, 0:uw].astype(F32)
        band = (np.abs((xx + yy * 0.8) - (-30 + (k - 18) / 16 * (uw + 60))) < 5).astype(F32) * 0.16
        spr[..., :3] += cv2.resize(band, (uw * TP, uh * TP), interpolation=cv2.INTER_NEAREST)[..., None] * spr[..., 3:4]
    return spr

def toast_draw(out, f):
    """THE ACHIEVEMENT: the toast pops up on the gasp (a spring: it rises with an overshoot and settles), the crate
    bounces in, the title hops in letter by letter, the second line follows, a shine crosses it; it slides away on e13."""
    k0 = E.fh(E.E_TOAST) - 3; k = f - k0; ko = E.fh(E.E_TOAST_OUT) - k0
    if k < 0 or k > ko + 11: return out
    spr = toast_sprite(k)
    sc = 1 - 0.38 * math.exp(-k / 3.0) * math.cos(0.72 * k); dy = 70 * math.exp(-k / 3.4) * math.cos(0.6 * k); al = smooth(k / 4)
    if k > ko:
        e_ = clamp((k - ko) / 11, 0, 1); dy += 120 * ein(e_, 2.0); al *= 1 - smooth(e_); sc *= 1 - 0.05 * e_
    h_, w_ = spr.shape[:2]; cx, cy = TOAST_C[0], TOAST_C[1] + dy
    crisp = abs(sc - 1) < 0.002 and abs(dy - round(dy)) < 0.05
    if crisp:
        img = np.zeros((H, W, 4), F32); x0, y0 = int(round(cx - w_ / 2)), int(round(cy - h_ / 2))
        img[y0:y0 + h_, x0:x0 + w_] = spr
    else:
        M = np.float32([[sc, 0, cx - sc * w_ / 2], [0, sc, cy - sc * h_ / 2]])
        img = cv2.warpAffine(spr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = img[..., 3] * al
    sh = cv2.resize(cv2.GaussianBlur(cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3.5), (W, H))
    sh = np.roll(sh, 14, axis=0)
    o = out * (1 - 0.50 * sh)[..., None]
    if 2 <= k < 30:                                                                          # a warm glow as it lands
        gl = cv2.resize(cv2.GaussianBlur(cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 7), (W, H))
        addc(o, gl, GOLDL, 0.30 * math.exp(-(k - 3) / 7))
    o = o * (1 - a[..., None]) + img[..., :3] * a[..., None]
    return np.clip(o, 0, 1)

# ---- the frame ------------------------------------------------------------------------------------------------------
def base14(s, f):
    if s["n"] == "ball": return ball_fx(s, f), None
    img, person = base11(s, f)
    if s["n"] == "wake" and f < len(LIGHTS_ON): img = dim(img, lights_on(f))
    if s["n"] == "today": img = loop_lights(img, f, s)
    return img, person

_B14 = {}
def edge14(S_, which):
    key = (S_["n"], which)
    if key not in _B14:
        if len(_B14) > 8: _B14.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        if S_["n"] == "ball": _B14[key] = ball_fx(S_, fr)
        else: _B14[key] = base11(S_, fr)[0]
    return _B14[key]

PERSON = {}
def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base14(s, f)
    PERSON.clear(); PERSON[f] = person
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge14(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge14(n_, "first"), kn, f, s, n_)
    return np.clip(out, 0, 1)

def render(f):
    s = shot_at(f); out = flash_governor(prefinish(f))
    fin_s = SHOTS[0] if (s["n"] == "today" and f >= s["f1"] - 1) else s
    out = toast_draw(finish14(out, f, fin_s), f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
