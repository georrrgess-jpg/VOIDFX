# ============================================================================ v14 — KEEPSAKES (The Flash × C418 "Mice on Venus")
# Nostalgia as a box of instant photos. The hero object is the PRINT (a lit instant photo: cream card, thick bottom
# border, paper grain, a gloss sheen, a soft shadow) that develops like real instant film (the image rises out of the
# milky reagent, cool and flat first, then warm and full). It appears three times: the signature (a print develops
# beside him and we fall into it), THE ALBUM (the focal set piece in the song's pause: the memory freezes into a print
# and three more land on it, one per soft piano note; we fall into the last), and the loop (the last memory becomes a
# print and slides away to reveal frame 0). Every other transition is a different idea: DOUBLE EXPOSURE, SUN FLARE,
# FILM BURN, RIPPLE, FOCUS RACK, EMBLEM GLINT (the emblem transition), SPEED WHIP, LIGHT LEAK, dolly, MEMORY ECHO.
# Look SUNFADE (golden hour on faded film) under a faint SUPER 8 HAZE (grain, sub-pixel gate weave, slow edge light
# leaks, halation, a few dust specks), kept low so the clips stay clear.
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

# ---- the album's memories are loaded with the shots (they appear only inside prints) -----------------------------
_load_pre14 = load
def load():
    global SHOTS
    real = SHOTS
    extra = [dict(n=f"albumsrc{i}", src=pk, tmap=[(0, max(0.0, a - 0.1)), (1, b + 0.1)]) for i, (_, pk, a, b, *_r) in enumerate(E.ALBUM)]
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

# ---- the camera: gentle; it breathes on the strong notes and rests in the album and the loop ----------------------
def beat_bounce(f):
    e = f / FPS / E.HB
    if E.E_ALBUM <= e < E.HDROP or e >= E.E_LOOP: return 1.0
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
    z = smooth(clamp((u - 0.82) / 0.18, 0, 1))                                                 # the sharp frame takes over at the end
    return mixm(o, full, np.full((H, W), z, F32)) if z > 0 else o

def settle(B, j, post, z0=1.0):
    return B

# ---- the signature: a print develops beside him in the golden window light; we fall into it --------------------------
SIG = dict(k0=46, wcx=790.0, wcy=1230.0, sc=400.0 / CW, ang=7.0, dive=34, crop=760)
def sig_print(out, s, f, person):
    k = f - s["f0"]; n = s["f1"] - s["f0"]
    if k < SIG["k0"]: return out
    nxt = nxt_of(s); full = edge14(nxt, "first"); content = crop_portrait(full, SIG["crop"])
    u_in = clamp((k - SIG["k0"]) / 22, 0, 1)                                                 # it rises into place from below the frame
    wcx = SIG["wcx"] + 60 * (1 - eout(u_in, 2.5)); wcy = SIG["wcy"] + 900 * (1 - eout(u_in, 2.5))
    sway = 1.6 * math.sin((k - SIG["k0"]) * 0.07)
    ang = SIG["ang"] + sway
    dev = clamp((k - SIG["k0"] - 10) / 60, 0, 1)
    kd = n - SIG["dive"]
    if k < kd:
        return print_w(out, content, wcx, wcy, SIG["sc"], ang, dev=dev, gloss=clamp((k - SIG["k0"]) / 80, 0, 1))
    sway_d = 1.6 * math.sin((kd - SIG["k0"]) * 0.07)
    return dive(out, full, SIG["crop"], wcx, wcy, SIG["sc"], SIG["ang"] + sway_d, (k - kd) / SIG["dive"], 1.0)

def print_dive(A, B, j, f, sa, sb, pre=SIG["dive"], post=12):
    """PRINT DIVE (signature, part 2): the dive is drawn in the shot (sig_print); here the next shot settles."""
    if j < 0: return A
    return settle(B, j, post)

# ---- THE ALBUM (focal set piece, the song's pause e30-e46) -------------------------------------------------------------
_ALB = {}
def album_content(i, f):
    """print i's picture: the frozen laugh (0), the two memories that live only here (1, 2), the sea run (3)."""
    note, pk, a, b, *_r = E.ALBUM[i]
    if i == 0: return crop_portrait(edge14(prev_shot(shot_by("album")), "last"), 760)
    if i == 3: return crop_portrait(edge14(shot_by("searun"), "first"), 820)
    ps = _ALB.get(("ps", i))
    if ps is None:
        ps = dict(n=f"albumsrc{i}", src=pk, tmap=[(0, a), (1, b)], look="sunfade", face=None, target=0.42); _ALB[("ps", i)] = ps
    t0 = E.th(note); tt = a + (b - a) * clamp((f / FPS - t0) / max(0.01, E.th(46) - t0), 0, 1)
    src = sample(pk, tt, "flow")
    h, w = src.shape[:2]; ch = h; cw = int(ch * 0.742); cxs = {1: 610, 2: 690}.get(i, w // 2)
    x0 = int(clamp(cxs - cw / 2, 0, w - cw))
    im = cv2.resize(np.ascontiguousarray(src[:, x0:x0 + cw]), (WW, WH), interpolation=cv2.INTER_AREA).astype(F32) / 255
    return grade(im, ps, f)

def shot_by(name):
    return next(s for s in SHOTS if s["n"] == name)

_ORB = {}
def orbs(f, n=14, seed=33):
    """slow warm bokeh lights drifting in the album's space (quarter res)."""
    if "p" not in _ORB:
        rng = np.random.default_rng(seed); _ORB["p"] = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(20, 70), rng.uniform(0.25, 0.7), rng.uniform(0, 6.28)) for _ in range(n)]
    q = np.zeros((H // 4, W // 4), F32); t = f / FPS
    for x, y, r, a, ph in _ORB["p"]:
        cx = (x + 0.02 * math.sin(t * 0.6 + ph)) * W / 4; cy = ((y - 0.012 * t) % 1.0) * H / 4
        cv2.circle(q, (int(cx), int(cy)), int(r / 4), float(a * (0.75 + 0.25 * math.sin(t * 1.3 + ph))), -1, cv2.LINE_AA)
    return cv2.resize(cv2.GaussianBlur(q, (0, 0), 2.5), (W, H))

ALB_SC = 700.0 / CW
def album_fx(s, f):
    k = f - s["f0"]; n = s["f1"] - s["f0"]
    lastL = edge14(prev_shot(s), "last")
    if "bg" not in _ALB: _ALB["bg"] = np.clip(defocus(lastL, 30) * np.array([0.78, 0.90, 1.05], F32) * 0.92, 0, 1)
    if k == 0: return lastL
    u0 = clamp(k / 18, 0, 1)
    z = 1 + 0.05 * (k / n)                                                                   # a slow push through the pause
    bg = zoom_about(_ALB["bg"], W / 2, H * 0.46, z)
    lay = np.zeros((H, W, 3), F32); addc(lay, orbs(f), AMBR, 0.28); bg = np.clip(bg + lay * smooth(u0), 0, 1)
    _, _, _, _, x0, y0, a0 = E.ALBUM[0]
    tx, ty = crop_centre(760)
    if u0 < 1:                                                                              # the laugh freezes into a print
        e_ = smooth(u0); sc = S_ID + (ALB_SC - S_ID) * e_
        o = mixm(lastL, bg, np.full((H, W), smooth(clamp(u0 / 0.6, 0, 1)), F32))
        o = print_w(o, album_content(0, f), tx + (x0 - tx) * e_, ty + (y0 - ty) * e_, sc, a0 * e_, gloss=0.2, shadow=0.45 * e_, border=smooth(clamp(u0 / 0.5, 0, 1)))
        w0 = 1 - smooth(clamp(u0 / 0.14, 0, 1))                                               # sharp first frames (no softness pop)
        return mixm(o, lastL, np.full((H, W), w0, F32)) if w0 > 0 else o
    o = print_w(bg, album_content(0, f), x0, y0 - 6 * (k / n), ALB_SC, a0, gloss=0.15)
    dv = n - 32                                                                              # the dive into the last print starts (e44)
    for i in (1, 2, 3):
        note, pk, a, b, xi, yi, ai = E.ALBUM[i]
        kl = E.fh(note) - s["f0"]                                                             # landing frame (on the note)
        if k < kl - 16: continue
        uu = clamp((k - (kl - 16)) / 16, 0, 1); e_ = eout(uu, 2.6)
        bounce = 1 + 0.03 * math.sin(math.pi * clamp((k - kl) / 8, 0, 1)) * (k >= kl)
        dirx, diry = (-1, -1) if i == 1 else (1, -1) if i == 2 else (-0.4, 1)
        cx = xi + dirx * 900 * (1 - e_); cy = yi + diry * 1300 * (1 - e_)
        ang = ai + 25 * dirx * (1 - e_)
        dev = clamp((k - kl + 6) / 26, 0, 1)                                                     # it develops as it lands (readable within ~0.35 s)
        if i == 3 and k >= dv:
            return dive(o, edge14(nxt_of(s), "first"), 820, xi, yi, ALB_SC, ai, (k - dv) / 32, 1.0)
        o = print_w(o, album_content(i, f), cx, cy, ALB_SC * bounce, ang, dev=dev, gloss=clamp((k - kl) / 50, 0, 1), lift=1 + 0.8 * (1 - e_))
    return o

def shutter_freeze(A, B, j, f, sa, sb, pre=3, post=6):
    """SHUTTER FREEZE: a soft camera flash on the pause's first note; the frame freezes into a print (album_fx)."""
    if j < 0: k = (j + pre + 1) / (pre + 1); return np.clip(A * (1 + 0.20 * k) + 0.06 * k, 0, 1)
    k = math.exp(-j / 2.0); return np.clip(B * (1 + 0.20 * k) + 0.06 * k, 0, 1)

def album_out(A, B, j, f, sa, sb, pre=32, post=12):
    """ALBUM OUT: the dive into the last print is drawn in album_fx; the sea run settles."""
    if j < 0: return A
    return settle(B, j, post)

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
        if j >= -4: o = mixm(o, defocus(B, 50), np.full((H, W), 0.2 * (j + 5), F32))           # found in the blur over 4 frames
        return o
    v = (j + 1) / post; return defocus(B, 50 * (1 - eout(v, 2.0)))

# ---- EMBLEM GLINT (the emblem transition) ----------------------------------------------------------------------------
ZIG = np.array([(0.24, -0.5), (-0.05, -0.03), (0.10, 0.03), (-0.24, 0.5)], np.float32)     # the bolt (top-right -> bottom-left)
def bolt_path(ex, ey, er, n=60):
    p = ZIG * (er * 1.35) + np.array([ex, ey], np.float32)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); s_ = np.linspace(0, cum[-1], n)
    return np.stack([np.interp(s_, cum, p[:, 0]), np.interp(s_, cum, p[:, 1])], 1), p

def glint_star(cv, x, y, L, a):
    q = np.zeros((H // 2, W // 2), F32); xx, yy = int(x / 2), int(y / 2)
    cv2.line(q, (xx - int(L / 2), yy), (xx + int(L / 2), yy), a, 1, cv2.LINE_AA); cv2.line(q, (xx, yy - int(L / 2)), (xx, yy + int(L / 2)), a, 1, cv2.LINE_AA)
    cv2.circle(q, (xx, yy), 3, a, -1, cv2.LINE_AA)
    return np.maximum(cv, cv2.resize(cv2.GaussianBlur(q, (0, 0), 1.0), (W, H)))

def real_bolt(img, ex, ey, er):
    """the emblem's gold bolt as a mask (the gold pixels inside the emblem's circle) and its two ends along its axis."""
    x0, y0 = int(max(0, ex - er * 1.1)), int(max(0, ey - er * 1.1)); x1, y1 = int(min(W, ex + er * 1.1)), int(min(H, ey + er * 1.1))
    sub = img[y0:y1, x0:x1]; Bc, Gc, Rc = sub[..., 0], sub[..., 1], sub[..., 2]
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
    inside = (np.sqrt((xx - ex) ** 2 + (yy - ey) ** 2) < er * 0.92)
    gold = inside & (Rc > 0.42) & (Gc > 0.28) & ((Rc - Bc) > 0.16) & (Gc > Bc)
    m = np.zeros((H, W), F32); m[y0:y1, x0:x1] = gold.astype(F32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    ys, xs = np.nonzero(gold)
    if len(xs) < 20: return m, (ex + er * 0.3, ey - er * 0.6), (ex - er * 0.3, ey + er * 0.6)
    X = np.stack([xs + x0, ys + y0], 1).astype(F32); c = X.mean(0); _, _, vt = np.linalg.svd(X - c, full_matrices=False)
    d = vt[0] if vt[0][1] < 0 else -vt[0]                                                       # point up (top end first)
    pr = (X - c) @ d; return m, tuple(c + d * pr.max()), tuple(c + d * pr.min())

def glint_B(B, sb, ex, ey, k):
    """the next shot, shifted so the emblem's opening shows his lit face (k = 1), easing back to its own framing (k = 0)."""
    fs = face_scr(sb, sb["f0"]) if sb.get("face") is not None else None
    if not fs or k <= 0: return B
    return shift_img(B, (ex - fs[0]) * k, (ey - fs[1]) * k)

def glint_cam(sa, f, e_):
    """the camera finds the emblem: it rises toward the frame's lower third and the shot pushes in (affine, scale s).
    One detection per shot (the shot's last frame), so a stray circle on one frame can't move it."""
    ex, ey, er = emblem_at(sa, sa["f1"] - 1); s_ = 1 + 0.30 * e_
    tx_, ty_ = ex + (W / 2 - ex) * 0.6 * e_, ey + (H * 0.70 - ey) * e_
    M = np.float32([[s_, 0, tx_ - s_ * ex], [0, s_, ty_ - s_ * ey]])
    return M, tx_, ty_, er * s_

def emblem_glint(A, B, j, f, sa, sb, pre=16, post=14):
    """EMBLEM GLINT: the camera finds the S1 emblem, the sun catches it, a glint runs down its bolt, the bolt lights up
    gold, and the emblem's light blooms out softly with the next memory growing out of it."""
    if j < 0:
        u = (j + pre) / pre; M, ex, ey, er = glint_cam(sa, f, ein(clamp(u / 0.7, 0, 1), 1.6))
        A2 = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        bm, p0, p1 = real_bolt(A2, ex, ey, er)
        cv = np.zeros((H, W), F32)
        gp = clamp((u - 0.2) / 0.5, 0, 1); gx, gy = p0[0] + (p1[0] - p0[0]) * gp, p0[1] + (p1[1] - p0[1]) * gp
        lit = smooth(clamp((u - 0.30) / 0.45, 0, 1))
        o = A2.copy()
        if lit > 0:                                                                          # the emblem's own gold bolt lights up
            addc(o, bm, GOLDL, 0.55 * lit); addc(o, cv2.GaussianBlur(bm, (0, 0), 6), GOLDL, 0.9 * lit); addc(o, cv2.GaussianBlur(bm, (0, 0), 22), AMBR, 0.6 * lit)
        if 0.2 <= u < 0.8:
            cv = glint_star(cv, gx, gy, 60 + 60 * math.sin(math.pi * (u - 0.2) / 0.6), 1.0)
            addc(o, cv, HOT, 1.2); addc(o, cv2.GaussianBlur(cv, (0, 0), 8), GOLDL, 1.0)
        bloom = smooth(clamp((u - 0.62) / 0.38, 0, 1))
        if bloom > 0:
            o = add_glow(o, ex, ey, 140 + 380 * bloom, 0.75 * bloom, GOLDL)                       # the gold fills the emblem first
            m = np.clip((240 * bloom - np.sqrt((_GX - ex) ** 2 + (_GY - ey) ** 2)) / 220 + 0.5, 0, 1) * clamp((bloom - 0.35) / 0.65, 0, 1)
            o = mixm(o, glint_B(B, sb, ex, ey, 1.0), m)
        return np.clip(o, 0, 1)
    v = (j + 1) / post; M, ex, ey, er = glint_cam(sa, sa["f1"] - 1, 1.0)
    A2 = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if v >= 1: return B
    Rm = 240 + 2600 * ein(v, 1.5)
    m = np.clip((Rm - np.sqrt((_GX - ex) ** 2 + (_GY - ey) ** 2)) / 360 + 0.5, 0, 1)
    o = mixm(A2, glint_B(B, sb, ex, ey, 1 - smooth(clamp(v / 0.6, 0, 1))), m)
    o = add_glow(o, ex, ey, 520 + 300 * v, 0.55 * (1 - v) ** 1.5, GOLDL)
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

TR2.update({"print_dive": (print_dive, SIG["dive"], 12), "double_exp": (double_exp, 12, 14), "sun_flare": (sun_flare, 10, 12),
            "film_burn": (film_burn, 8, 12), "shutter_freeze": (shutter_freeze, 3, 6), "album_out": (album_out, 32, 12),
            "ripple": (ripple, 10, 14), "focus_rack14": (focus_rack14, 10, 12), "emblem_glint": (emblem_glint, 16, 14),
            "speed_whip14": (speed_whip14, 5, 7), "light_leak14": (light_leak14, 10, 12), "afterimage14": (memory_echo, 12, 12)})

# ---- the loop: the last memory becomes a print and slides away; frame 0 is underneath ---------------------------------
LOOP_N = 46
def frame_virtual(fv):
    s0 = SHOTS[0]; out, _ = base14(s0, fv)
    return out

def tall_card(img, bw):
    """the whole frame as a tall print: a cream border bw px wide (4 bw at the bottom) round it (BGR + alpha)."""
    h, w = img.shape[:2]; c = np.empty((h + 5 * bw, w + 2 * bw, 3), F32); c[:] = CREAM
    c[bw:bw + h, bw:bw + w] = img
    a = np.ones(c.shape[:2], F32)
    return c, a

def loop_print(out, f, s):
    """THE LOOP: the last memory becomes a print (its cream border grows in round the picture as it shrinks), tips, and
    drops away below the faces like a photo let go; frame 0 is underneath and is all that is left at the wrap."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]
    if k < n - LOOP_N: return out
    u = (k - (n - LOOP_N)) / (LOOP_N - 1)                                                    # 0..1, 1 = the last frame
    under = frame_virtual(f - E.DUR_F)
    if u >= 1: return under
    if u <= 0: return out
    a = clamp(u / 0.42, 0, 1); e_ = smooth(a)
    sc = 1 - 0.40 * e_                                                                       # the picture's scale on screen
    bw = int(round(46 * e_))                                                                 # the border grows in
    q = 2; small = cv2.resize(out, (W // q, H // q), interpolation=cv2.INTER_AREA)
    card, alpha = tall_card(small, max(0, bw // q))
    ch, cw = card.shape[:2]
    b = clamp((u - 0.42) / 0.58, 0, 1); eb = ein(b, 2.2)
    ang = -3.0 * e_ - 14.0 * eb                                                              # it tips as it falls
    ox, oy = bw / q, bw / q                                                                  # picture origin inside the card
    cx = W / 2 - 60 * eb; cy = H / 2 + 120 * e_ + 2300 * eb                                  # it falls straight down, under the faces
    M = cv2.getRotationMatrix2D((ox + W / q / 2, oy + H / q / 2), ang, sc * q)
    M[0, 2] += cx - (ox + W / q / 2); M[1, 2] += cy - (oy + H / q / 2)
    img = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    Ms = M.copy(); Ms[0, 2] += 22 * (1 + eb); Ms[1, 2] += 34 * (1 + eb)
    sh = cv2.warpAffine(alpha, Ms, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    sh = cv2.resize(cv2.GaussianBlur(cv2.resize(sh, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))
    base = under * (1 - 0.45 * sh * e_)[..., None]
    o = mixm(base, img, m)
    w0 = 1 - smooth(clamp(u / 0.06, 0, 1))                                                   # the first frames are the frame itself
    return mixm(o, out, np.full((H, W), w0, F32)) if w0 > 0 else o

def loop_in14(out, f, k):
    return out

# ---- the frame ------------------------------------------------------------------------------------------------------
def base14(s, f):
    if s["n"] == "album": return album_fx(s, f), None
    img, person = base11(s, f)
    if s["n"] == "now" and f >= 0: img = sig_print(img, s, f, person)
    if s["n"] == "today": img = loop_print(img, f, s)
    return img, person

_B14 = {}
def edge14(S_, which):
    key = (S_["n"], which)
    if key not in _B14:
        if len(_B14) > 8: _B14.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        if S_["n"] == "album": _B14[key] = album_fx(S_, fr)
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
    return (np.clip(finish14(out, f, fin_s), 0, 1) * 255 + 0.5).astype(np.uint8)
