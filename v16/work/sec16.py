# ============================================================================ v16 — GOING HOME (The Flash × Drake "Hold On, We're Going Home")
# The fastest man alive can run anywhere, but every run ends at the same place. The Flash alone on a rooftop over the
# night city (somewhere in those lit windows is home); "Oh, just hold on, we're going home": HOLD ON draws the shot back
# like a slingshot and releases on "home" as the drums slam back; the run home through the night; LONG EXPOSURE (his
# lightning paints light trails that become the city's lights); alone; the real Flash signal (THE SIGNAL: its bolt is
# the doorway home); the loft, Iris; the loop (HOME LIGHT: the loft pulls back into one lit window of frame 0's city).
# Look AFTER HOURS: teal-ink night, sodium-amber lights, the suit's red kept rich; home in warm tungsten; a soft
# pro-mist halation, a faint anamorphic streak on the brightest lights, fine grain.
GOLDL = np.array([0.50, 0.80, 1.00], F32)                  # BGR gold light (lightning)
AMBR = np.array([0.28, 0.58, 1.00], F32)                   # BGR sodium amber
HOT = np.array([0.92, 0.96, 1.00], F32)                    # BGR white-hot
TEAL = np.array([0.62, 0.46, 0.18], F32)                   # BGR teal ink
CYAN = np.array([1.00, 0.82, 0.55], F32)                   # BGR cold streak
TUNG = np.array([0.40, 0.66, 1.00], F32)                   # BGR warm tungsten
HALO = np.array([0.32, 0.44, 1.00], F32)                   # BGR halation (warm red)
CRIM = np.array([0.16, 0.12, 0.78], F32)
AMB = AMBR
GOLDW, GOLD2, GOLD, EMBER2 = HOT.copy(), AMBR.copy(), GOLDL.copy(), AMBR.copy()
JASW, JASG, JASY = HOT.copy(), AMBR.copy(), AMBR.copy()
if E.VER == "v16":
    for _s in E.SHOTS:
        _s.setdefault("target", 0.42 if _s.get("look", "night") == "night" else 0.46)

_keys_at_pre16 = keys_at
def keys_at(keys, u):
    """LinZ keys (EDL) read as a straight line, valid outside 0..1: the roof's push keeps one speed across the wrap."""
    if getattr(keys, "linear", False):
        (u0, v0), (u1, v1) = keys[0], keys[-1]; return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return _keys_at_pre16(keys, u)

_tmap_pre16 = tmap
def tmap(s, u):
    """tneg shots (the roof) read their source before u = 0 too (the tmap's first key sits at negative u): the loop's
    virtual frames show the real rooftop footage running on into frame 0, not a held frame."""
    if u < 0 and s.get("tneg"):
        ks = s["tmap"]; return float(np.interp(u, [k[0] for k in ks], [k[1] for k in ks]))
    return _tmap_pre16(s, u)

_src_time_pre16 = src_time
def src_time(s, f):
    """tneg shots: the speed estimate at negative u without the 0..1 clamp (it divided by ~0 there and the sampler
    smeared frames of another shot into the loop's virtual frames)."""
    if s.get("tneg") and f < s["f0"] + 2:
        n = max(1, s["f1"] - s["f0"]); u = (f - s["f0"]) / n; du = 1.0 / n
        return tmap(s, u), u, abs(tmap(s, u + du) - tmap(s, u - du)) / (2 * du * n / FPS)
    return _src_time_pre16(s, f)

def shift_img(img, dx, dy=0.0):
    M = np.float32([[1, 0, dx], [0, 1, dy]]); return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_DK = {}
def defocus(img, r):
    if r < 0.6: return img
    if r < 6: return cv2.GaussianBlur(img, (0, 0), r / 2)
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    sm = sm + np.clip(sm - 0.58, 0, 1) * 2.2
    rr = int(math.ceil(r / q))
    if rr not in _DK:
        k = np.zeros((2 * rr + 1, 2 * rr + 1), F32); cv2.circle(k, (rr, rr), rr, 1.0, -1, cv2.LINE_AA); _DK[rr] = k / k.sum()
    return np.clip(cv2.resize(cv2.filter2D(sm, -1, _DK[rr]), (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

def defocus16(img, r):
    """defocus with no jump where the gaussian hands over to the bokeh disc."""
    if r < 0.6: return img
    g = cv2.GaussianBlur(img, (0, 0), r / 2)
    if r < 3: return g
    w = clamp((r - 3) / 6, 0, 1); return g * (1 - w) + defocus(img, max(r, 6.01)) * w

def shot_by(name):
    return next(s for s in SHOTS if s["n"] == name)

def e_of(f): return f / FPS / E.HB

def lumf(img): return img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299

# ---- grade: AFTER HOURS -------------------------------------------------------------------------------------------------
LOOKS16 = {"night": dict(sh=(0.052, 0.022, -0.012), hi=(-0.034, 0.012, 0.044), sat=0.90),
           "dusk": dict(sh=(0.034, 0.012, -0.004), hi=(-0.046, 0.006, 0.052), sat=0.92),
           "home": dict(sh=(-0.008, 0.010, 0.030), hi=(-0.052, 0.012, 0.052), sat=0.96)}
E_EV16 = {"iris": -0.30, "signal": -0.10, "thinks": -0.45, "lrun": -0.30, "lrun2": -0.35}
_LUTS = {}
def lut16():
    if "n" not in _LUTS:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTS["n"] = (x, PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.028, 0.050, 0.185, 0.500, 0.815, 0.940, 0.975])(x).astype(np.float32))
    return _LUTS["n"]

_grade_pre16 = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in LOOKS16: return _grade_pre16(img, s, f)
    P_ = LOOKS16[lk]; g, gains = corr9(s); ev = (s.get("ev") or 0) + E_EV16.get(s["n"], 0.0)
    lx, ly = lut16()
    if in_unit(img): x = apply_lut3(img, tone_lut(("ah16", s["n"], round(ev, 3), float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.clip(img * gains, 0, 1) ** g
        if ev: x = np.clip(x * 2 ** ev, 0, 1)
        x = np.interp(x, lx, ly).astype(F32)
    B, G, R = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = B * 0.114 + G * 0.587 + R * 0.299
    hue = (R - G) / (R + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((R - B) * 6, 0, 1) * np.clip(L * 3, 0, 1)
    red = np.clip((R - np.maximum(G, B)) * 3.0 - 0.3, 0, 1) * (1 - skin)                      # the suit keeps its red
    sat = (P_["sat"] + 0.08 * skin + 0.20 * red) * s.get("satk", 1.0)
    sh = (1 - L) ** 2.2 * (1 - 0.6 * skin); hi = np.clip((L - 0.55) / 0.45, 0, 1) ** 1.3
    o = np.empty(x.shape, F32)
    for c, Pc in enumerate((B, G, R)):
        o[..., c] = L + (Pc - L) * sat + sh * P_["sh"][c] + hi * P_["hi"][c]
    return np.clip(o, 0, 1, out=o)

# ---- the finish: a pro-mist halation, a faint anamorphic streak on the brightest lights, fine grain ---------------------
_FIN = {}
def finish16(out, f, s, mix=None):
    if "v" not in _FIN:
        grain(0, 0.012); _FIN["v"] = np.repeat(0.80 + 0.20 * VIG, 3, axis=2)
    k = ("g", f % 6)
    if k not in _FIN: _FIN[k] = np.repeat(grain(f, 0.010), 3, axis=2)
    o = out
    small = cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    mx = small.max(2)
    hi_ = np.clip(mx - 0.62, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 4) * 0.55 + cv2.GaussianBlur(hi_, (0, 0), 16) * 0.45, (W, H))
    addc(o, bl, HALO, 0.36)                                                                     # the halation round every light
    pt = np.clip(mx - 0.80, 0, 1) * 3.0
    st = cv2.resize(cv2.GaussianBlur(pt, (0, 0), sigmaX=30, sigmaY=0.5), (W, H))
    m_ = mix if mix is not None else (0.0 if s.get("look") == "home" else 1.0)
    addc(o, st, TUNG * (1 - m_) + CYAN * m_, 0.30)                                              # the night-drive streak
    o *= _FIN["v"]; o += _FIN[k]
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: a punch on every beat from the drop (stronger on the half bar), resting in the verse and the loop
def beat_e(e): return 2 * math.floor(e / 2 + 1e-9)
def cam_live(e): return E.HDROP <= e < E.E_LOOP

def beat_bounce(f):
    e = e_of(f)
    if not cam_live(e): return 1.0
    eb = beat_e(e); dt = (e - eb) * E.HB
    amp = 0.034 if eb % 4 == 0 else 0.016
    return 1 + amp * math.exp(-dt / 0.085)

def beat_fx(out, f):
    e = e_of(f)
    if not cam_live(e): return out
    eb = beat_e(e); dt = (e - eb) * E.HB
    if eb % 4 != 0 or dt > 0.05: return out
    k = math.exp(-dt / 0.022)
    o = radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.030 * k, 4)
    return np.clip(rgb_split(o, 5 * k) if eb % 8 == 0 else o, 0, 1)

def init_hits():
    HITS.clear()

# ---- smoothness: flow on the 24p/30p shots, a per-shot limit for the fast ones ------------------------------------------
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

# ---- faces: everything is kept off them ---------------------------------------------------------------------------------
def face_soft(s, f, pad=1.0, q=4):
    """a soft ellipse over the face (1 on the face), for keeping graphics off it."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs and s.get("face_hint"): fs = s["face_hint"]
    if not fs: return None
    m = np.zeros((H // q, W // q), F32)
    cv2.ellipse(m, (int(fs[0] / q), int(fs[1] / q)), (int(fs[2] * 0.95 * pad / q), int(fs[2] * 1.3 * pad / q)), 0, 0, 360, 1.0, -1)
    return cv2.resize(cv2.GaussianBlur(m, (0, 0), 12 / q), (W, H))[..., None]

def off_face(new, old, s, f, pad=1.0):
    m = face_soft(s, f, pad)
    return new if m is None else new * (1 - m) + old * m

def face_keep(s, f, pad=1.2):
    m = face_soft(s, f, pad)
    return 1.0 if m is None else (1 - m)

def body_only(person, s, f):
    """his matte below the chin (lightning is born on his shoulders and arms, never round his head)."""
    if person is None: return None
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return person
    y0 = int(clamp(fs[1] + fs[2] * 1.05, 0, H)); p_ = person.copy(); p_[:y0] = 0; return p_

def hi_point(img, s=None, f=None, thr=0.70):
    """the centroid of the brightest light in a frame (off the face)."""
    q = 8; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA); L = sm.max(2)
    m = np.clip((L - thr) / 0.2, 0, 1)
    if s is not None:
        fm = face_soft(s, f, 1.6, q)
        if fm is not None: m = m * (1 - cv2.resize(fm[..., 0], (W // q, H // q)))
    if m.sum() < 0.5: return W / 2, H * 0.45
    ys, xs = np.nonzero(m > 0.05); w_ = m[ys, xs]
    return float((xs * w_).sum() / w_.sum() * q + q / 2), float((ys * w_).sum() / w_.sum() * q + q / 2)

# ---- in-shot animations (each motivated by its shot, kept off faces) ---------------------------------------------------
_TW = {}
def tw_phase(q=4):
    if "p" not in _TW:
        rng = np.random.default_rng(1616); _TW["p"] = (rng.random((H // q, W // q)) * 2 * math.pi).astype(F32)
        _TW["r"] = (0.35 + 0.9 * rng.random((H // q, W // q))).astype(F32)
    return _TW["p"], _TW["r"]

def a_twinkle(img, person, s, f, warm=False):
    """THE CITY: every lit window breathes on its own slow phase, with a soft halo (behind him, never on him)."""
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA); L = lumf(sm)
    pts = np.clip((L - 0.30) / 0.30, 0, 1)
    ph, rate = tw_phase(q); t = f / FPS
    mod = np.sin(2 * math.pi * 0.55 * rate * t + ph)
    lay = cv2.GaussianBlur(pts * (0.55 + 0.45 * mod), (0, 0), 2.2)
    lay = cv2.resize(lay, (W, H))[..., None]
    keep = 1.0 if person is None else (1 - np.clip(person * 1.3, 0, 1))[..., None]
    col = TUNG if warm else AMBR * 0.7 + HOT * 0.3
    o = img * (1 + 0.20 * cv2.resize(pts * mod, (W, H))[..., None] * keep) + lay * col * 0.30 * keep
    return np.clip(o, 0, 1)

def a_windows(img, person, s, f):
    return a_twinkle(img, person, s, f, warm=True)

def a_flares(img, person, s, f):
    """STREETLIGHTS: the lights behind him throw long anamorphic streaks across the lens."""
    q = 8; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    hi = np.clip(sm.max(2) - 0.58, 0, 1) * 3.0
    st = cv2.resize(cv2.GaussianBlur(hi, (0, 0), sigmaX=34, sigmaY=0.7) * 6.0, (W, H))[..., None]
    core = cv2.resize(cv2.GaussianBlur(hi, (0, 0), sigmaX=10, sigmaY=0.5) * 3.0, (W, H))[..., None]
    o = img + st * CYAN * 0.45 + core * np.array([1.0, 0.9, 0.85], F32) * 0.30
    return off_face(np.clip(o, 0, 1), img, s, f, 1.25)

def a_motes(img, person, s, f):
    """HOME: warm dust drifting slowly through the lamplight (smooth paths, never in front of a face)."""
    rng = np.random.default_rng(1661); t = f / FPS; lay = np.zeros((H // 2, W // 2), F32)
    for i in range(46):
        x0, y0, sp, ph, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(12, 34), rng.uniform(0, 6.28), rng.uniform(1.2, 3.4)
        x = x0 + 26 * math.sin(t * 0.45 + ph); y = (y0 - sp * t) % (H + 80) - 40
        a = 0.45 + 0.35 * math.sin(t * 1.3 + ph * 2)
        cv2.circle(lay, (int(x / 2 * 4), int(y / 2 * 4)), int(r / 2 * 4), a, -1, cv2.LINE_AA, shift=2)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.6), (W, H))[..., None]
    lit = np.clip(lumf(cv2.GaussianBlur(img, (0, 0), 20)) * 1.6, 0.25, 1.0)[..., None]            # brighter where the lamp is
    return off_face(np.clip(img + lay * lit * TUNG * 0.55, 0, 1), img, s, f, 1.3)

ANIMS = {"twinkle": a_twinkle, "windows": a_windows, "flares": a_flares, "motes": a_motes}

# ---- BOKEH DRIFT (the rooftop -> over his shoulder): the city's lights swell into discs that drift, and settle again ---
def drop_whip(A, B, j, f, sa, sb, pre=6, post=8):
    """DROP WHIP: the camera drops off his face to the wet street where he is already running (a strip tilt down)."""
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    strip = np.concatenate([A, B], axis=0); y0 = int(round(p * H))
    return np.clip(hblur(np.ascontiguousarray(strip[y0:y0 + H]), 2 + 170 * sp, vertical=True), 0, 1)

def flare_sweep(A, B, j, f, sa, sb, pre=8, post=10):
    """FLARE SWEEP: a warm streetlight flare sweeps low across the lens; under its glare he becomes Barry looking at her."""
    x = (j + pre) / (pre + post - 1); cx = -0.3 * W + 1.6 * W * smooth(x); cy = H * 0.78
    pk = math.exp(-((x - 0.5) / 0.14) ** 2)
    w = smooth(clamp((x - 0.44) / 0.12, 0, 1)); o = A * (1 - w) + B * w
    d2 = (_GX - cx) ** 2 + ((_GY - cy) * 1.6) ** 2
    bloom = np.exp(-d2 / (2 * 260.0 ** 2)).astype(F32)
    streak = (np.exp(-((_GY - cy) / 9.0) ** 2) * np.exp(-np.abs(_GX - cx) / 700.0)).astype(F32)
    addc(o, bloom, TUNG, 0.9 * math.sin(math.pi * clamp(x, 0, 1))); addc(o, streak, HOT * 0.4 + TUNG * 0.6, 0.8)
    return np.clip(o * (1 - 0.3 * pk) + TUNG * 0.30 * pk, 0, 1)

def bokeh_drift(A, B, j, f, sa, sb, pre=10, post=14):
    x = (j + pre) / (pre + post - 1); r = 30 * math.sin(math.pi * clamp(x, 0, 1)) ** 1.2
    a = defocus16(shift_img(A, 80 * smooth(x)), r); b = defocus16(shift_img(B, -80 * (1 - smooth(x))), r)
    w = smooth(clamp((x - 0.28) / 0.44, 0, 1))
    return np.clip(a * (1 - w) + b * w, 0, 1)

# ---- REFLECTION ("who you could be"): her face rises in the night glass over the city lights ---------------------------
def reflection(A, B, j, f, sa, sb, pre=16, post=12):
    x = (j + pre) / (pre + post - 1)
    ka = 1 - smooth(clamp((x - 0.35) / 0.65, 0, 1))                                             # the city fades out of the glass
    kb = 0.55 * smooth(clamp(x / 0.5, 0, 1)) + 0.45 * smooth(clamp((x - 0.5) / 0.5, 0, 1))     # her reflection comes up, then she is there
    Bs = defocus16(zoom_about(B, W / 2, H * 0.42, 1.0 + 0.06 * (1 - smooth(x))), 5 * (1 - smooth(x)))
    fk = face_keep(sb, sb["f0"], 1.3)
    Aa = A * (ka * (1 - 0.70 * smooth(clamp(x / 0.45, 0, 1))))
    if not isinstance(fk, float): Aa = Aa * (1 - (1 - fk) * smooth(clamp((x - 0.3) / 0.3, 0, 1)))
    o = 1 - (1 - Aa) * (1 - Bs * kb)                                                            # a screen: light adds like glass
    band = np.exp(-(((_GX * 0.55 + _GY * 0.83) - (-400 + 2600 * x)) / 160.0) ** 2).astype(F32) * math.sin(math.pi * x)
    if not isinstance(fk, float): band = band * fk[..., 0]
    addc(o, band, HOT, 0.07)                                                                    # the sheen of the glass
    return np.clip(o, 0, 1)

# ---- HEADLIGHTS (her -> him, masked, at night): a car's lights sweep across the lens and the night is behind them ----
def headlight_pass(A, B, j, f, sa, sb, pre=10, post=10):
    x = (j + pre) / (pre + post - 1); env = math.sin(math.pi * clamp(x, 0, 1)) ** 0.8
    cx = -0.35 * W + 1.7 * W * smooth(x); cy = H * 0.72
    lay = np.zeros((H, W), F32)
    for dx_ in (0.0, 190.0):
        d2 = (_GX - (cx + dx_)) ** 2 + (_GY - cy) ** 2
        lay += np.exp(-d2 / (2 * 30.0 ** 2)) * 1.4 + np.exp(-d2 / (2 * 140.0 ** 2)) * 0.5
    streak = np.exp(-((_GY - cy) / 7.0) ** 2) * np.exp(-np.abs(_GX - cx - 95) / 520.0)
    w = smooth(clamp((x - 0.45) / 0.10, 0, 1))
    o = A * (1 - w) + B * w
    keep = face_keep(sa if w < 0.5 else sb, sa["f1"] - 1 if w < 0.5 else sb["f0"], 1.2)
    lay = lay * (keep[..., 0] if not isinstance(keep, float) else 1.0)
    pk = math.exp(-((x - 0.5) / 0.10) ** 2)
    addc(o, lay.astype(F32), HOT * 0.5 + AMBR * 0.5, 0.75 * env + 0.6 * pk); addc(o, streak.astype(F32), CYAN, 0.6 * env + 0.4 * pk)
    o = o * (1 - 0.35 * pk) + (HOT * 0.3 + AMBR * 0.7) * 0.32 * pk                               # the glare covers the switch
    return np.clip(o, 0, 1)

# ---- LIGHT WARP (his eyes spark -> the run at us): the night's lights stretch into speed lines -------------------------
def light_warp(A, B, j, f, sa, sb, pre=8, post=10):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.47) / 0.06, 0, 1)); base = A * (1 - w) + B * w
    cx, cy = W / 2, H * 0.44
    hi = base * np.clip((lumf(base) - 0.50) * 2.2, 0, 1)[..., None]
    st = radial_blur(hi, cx, cy, 1.0, 1.0 + 0.38 * k, 10)
    keep = face_keep(sa if w < 0.5 else sb, sa["f1"] - 1 if w < 0.5 else sb["f0"], 1.3)
    o = zoom_about(base, cx, cy, 1 + 0.06 * k)
    o = o + st * 1.5 * k * (keep if not isinstance(keep, float) else 1.0)
    return np.clip(o, 0, 1)

# ---- HOLD ON (e20 -> e24, "hold on, we're going home"): the shot drawn back like a slingshot --------------------------
_HO = {}
def hold_on(img, person, s, f):
    e = e_of(f); u = clamp((e - E.E_HOLD) / (E.HDROP - E.E_HOLD), 0, 1)
    if u <= 0: return img
    t = ein(u, 1.5); cx, cy = W / 2, H * 0.45
    if "dn" not in _HO:
        d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); _HO["dn"] = (d / (0.5 * math.hypot(W, H))).astype(F32)
    dn = _HO["dn"]; k = 0.26 * t
    sc = 1 + k * (dn - 0.25)                                                                    # the picture pulled back toward the far point
    mx = (cx + (_GX - cx) * sc).astype(F32); my = (cy + (_GY - cy) * sc).astype(F32)
    o = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = radial_blur(o, cx, cy, 1.0, 1.0 - 0.14 * t, 10)                                        # streaks drawn in toward it
    tt = f / FPS; tr = 2.4 * t
    o = shift_img(o, tr * math.sin(2 * math.pi * 11 * tt), 0.6 * tr * math.sin(2 * math.pi * 13 * tt + 1.0))   # it strains
    o = o * (1 - 0.32 * t * np.clip(dn, 0, 1)[..., None] ** 1.5)                               # tension at the edges
    bo = body_only(person, s, f)
    o2 = edge_arcs(o, f, bo, 0.5 + 1.4 * t, 1601); o2 = edge_arcs(o2, f + 1, bo, 0.3 + 1.2 * t, 1611)
    return off_face(np.clip(o2, 0, 1), o, s, f, 1.45)

def release(A, B, j, f, sa, sb, pre=4, post=12):
    """RELEASE (on "home", the drums back): the drawn-back shot lets go: the run blasts out at us and settles."""
    cx, cy = W / 2, H * 0.45
    if j < 0:
        u = (j + pre) / pre
        return np.clip(zoom_about(A, cx, cy, 1 - 0.04 * ein(u, 2)) * (1 + 0.15 * u), 0, 1)
    v = (j + 1) / post
    zb = 1 + 0.32 * (1 - eout(v, 3.0)); kb = 0.24 * (1 - eout(v, 2.2))
    o = zoom_about(B, cx, cy, zb)
    if kb > 0.004: o = radial_blur(o, cx, cy, 1.0, 1.0 + kb, 10)
    return np.clip(o + AMBR * 0.20 * (1 - v) ** 2, 0, 1)

# ---- STREAK PASS (ported, v15): he streaks past the lens, low; the cut behind him ----------------------------------------
def streak_pass(A, B, j, f, sa, sb, pre=5, post=7):
    q = (j + pre) / (pre + post - 1); x = -0.45 * W + 1.9 * W * ein(clamp(q, 0, 1), 1.3)
    cy = H * 0.80; hh = H * 0.15                                                                # low, past the lens (never at face height)
    yy = (_GY - cy) / hh; body = np.exp(-yy ** 4) * np.clip((_GX - (x - W * 0.55)) / (W * 0.55), 0, 1) * np.clip((x + 60 - _GX) / 60, 0, 1)
    body = body.astype(F32)
    w = smooth(clamp((q - 0.12) / 0.76, 0, 1)); under = A * (1 - w) + B * w                  # the switch under the blur
    kb = math.sin(math.pi * clamp(q, 0, 1)) ** 1.5
    sm = hblur(under, 120)
    o = mixm(under, sm, np.clip(np.maximum(body * 1.4, kb * 0.85), 0, 1).astype(F32))
    col = CRIM * 0.55 + AMBR * 0.45
    fk = face_keep(sb, sb["f0"], 1.4); body = body * (fk[..., 0] if not isinstance(fk, float) else 1.0)
    o = o * (1 - 0.55 * body[..., None]) + body[..., None] * col * 0.75
    cv = bolt_canvas()
    for k_ in range(3):
        yk = cy + (k_ - 1) * hh * 0.45
        put_bolt(cv, (x - W * 0.6, yk + 20 * math.sin(f * 0.6 + k_)), (x, yk), 8800 + k_ + 5 * (f // 2), 1, 0.25, 4, 0)
    lt = light_rgb(cv, 0.8 * math.sin(math.pi * clamp(q, 0, 1)), HOT, AMB)
    return np.clip(o + lt * (fk if not isinstance(fk, float) else 1.0), 0, 1)

# ---- LIGHT FLARE (masked close -> past S.T.A.R. Labs): the light behind him flares across the lens -------------------
def light_flare(A, B, j, f, sa, sb, pre=6, post=8):
    x = (j + pre) / (pre + post - 1); env = math.sin(math.pi * clamp(x, 0, 1)) ** 0.9
    if "lf" not in _HO or _HO["lf"][0] != sa["n"]: _HO["lf"] = (sa["n"], hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.62))
    px, py = _HO["lf"][1]
    w = smooth(clamp((x - 0.42) / 0.16, 0, 1)); o = A * (1 - w) + B * w
    d2 = (_GX - px) ** 2 + (_GY - py) ** 2
    bloom = np.exp(-d2 / (2 * (60 + 260 * env) ** 2)).astype(F32)
    streak = (np.exp(-((_GY - py) / (6 + 8 * env)) ** 2) * np.exp(-np.abs(_GX - px) / (200 + 900 * env))).astype(F32)
    keep = face_keep(sa if w < 0.5 else sb, sa["f1"] - 1 if w < 0.5 else sb["f0"], 1.2)
    if not isinstance(keep, float): bloom = bloom * keep[..., 0]; streak = streak * keep[..., 0]
    addc(o, bloom, HOT * 0.4 + AMBR * 0.6, 0.55 * env); addc(o, streak, CYAN * 0.7 + 0.3, 0.75 * env)
    return np.clip(o, 0, 1)

# ---- WHIP UP (ported, v15): a tilt-whip up over the rooftops ---------------------------------------------------------------
def whip_up15(A, B, j, f, sa, sb, pre=6, post=8):
    """WHIP UP: the camera tilts up hard: the frame and the next one as one strip, with vertical motion blur (no mirrored
    edges)."""
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    strip = np.concatenate([B, A], axis=0); y0 = int(round((1 - p) * H))
    return np.clip(hblur(np.ascontiguousarray(strip[y0:y0 + H]), 2 + 170 * sp, vertical=True), 0, 1)

# ---- CITY DIVE (the city from above -> his run): we dive into one of his light trails over the city --------------------
def city_dive(A, B, j, f, sa, sb, pre=8, post=10):
    if "cd" not in _HO:
        _HO["cd"] = (hi_point(edge15(sa, "last"), None, None, 0.55), hi_point(edge15(sb, "first"), None, None, 0.6))
    (ax, ay), (bx, by) = _HO["cd"]
    if j < 0:
        u = (j + pre) / pre; z = 1 + 1.3 * ein(u, 2.2)
        o = zoom_about(A, ax, ay, z); o = radial_blur(o, ax, ay, 1.0, 1.0 + 0.20 * ein(u, 2.0), 8)
        w = smooth(clamp((u - 0.7) / 0.3, 0, 1))
        if w > 0: o = o * (1 - w) + zoom_about(B, bx, by, 1.8) * w
        return np.clip(o * (1 + 0.25 * ein(u, 2)), 0, 1)
    v = (j + 1) / post; z = 1 + 0.8 * (1 - eout(v, 2.6))
    o = zoom_about(B, bx, by, z); k = 0.18 * (1 - eout(v, 2))
    if k > 0.004: o = radial_blur(o, bx, by, 1.0, 1.0 + k, 8)
    return np.clip(o * (1 + 0.25 * (1 - v) ** 2), 0, 1)

# ---- LONG EXPOSURE (the focal piece, e42 -> e48 and into "alone"): the shutter stays open on his run ------------------
E_LEX0 = 42.5
E_LEX1 = 48.0
_LEX = {}
def lex_hi(s, k, q=4):
    """the lights of frame k of the run (his lightning), at quarter resolution."""
    if k not in _LEX:
        if len(_LEX) > 160: _LEX.clear()
        img, _ = base11(s, k)
        sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
        L = lumf(sm); hi = np.clip((L - 0.62) / 0.30, 0, 1)
        core = np.clip(hi - 0.85 * cv2.GaussianBlur(hi, (0, 0), 3), 0, 1)                    # the filaments, not the glow
        tint = (sm * 0.35 + AMBR * 0.65)
        _LEX[k] = (tint * core[..., None]).astype(F32)
    return _LEX[k]

def lex_z(s, k):
    """the lens creeps in while the shutter is open, so even the still lights draw trails (a zoom burst); one creep over
    both runs (the shutter stays open across the cut)."""
    f0 = fh(E_LEX0); return 1.0 + 0.40 * clamp((k - f0) / max(1, fh(E_LEX1) - f0), 0, 1)

_LEXC = {}
def lex_layer(s, f, q=4, win=40, d=0.93):
    f0 = fh(E_LEX0); acc = np.zeros((H // q, W // q, 3), F32)
    if f < f0: return acc
    zf = lex_z(s, f); cx, cy = W / q / 2, H / q * 0.45
    for k in range(max(f0, s["f0"], f - win), f + 1):
        h = lex_hi(s, k, q); sc = lex_z(s, k) / zf
        if abs(sc - 1) > 1e-4: h = cv2.warpAffine(h, cv2.getRotationMatrix2D((cx, cy), 0, sc), (W // q, H // q), flags=cv2.INTER_LINEAR, borderValue=0)
        np.maximum(acc, h * (d ** (f - k)), out=acc)
    if s["n"] == "lrun2":                                                                       # EXPOSURE CUT: the first run's trails stay on
        s1 = shot_by("lrun"); k1 = s1["f1"] - 1
        if q not in _LEXC: _LEXC[q] = lex_layer(s1, k1, q, win, d)
        sc = lex_z(s1, k1) / zf
        c = cv2.warpAffine(_LEXC[q], cv2.getRotationMatrix2D((cx, cy), 0, sc), (W // q, H // q), flags=cv2.INTER_LINEAR, borderValue=0)
        np.maximum(acc, c * (0.965 ** (f - k1)), out=acc)
    return acc

def long_exposure_fx(img, person, s, f):
    e = e_of(f)
    if e < E_LEX0: return img
    g = smooth(clamp((e - E_LEX0) / 1.2, 0, 1)); sw = smooth(clamp((e - 46.0) / 2.0, 0, 1)) * s.get("lexk", 1.0)
    lay = cv2.resize(lex_layer(s, f), (W, H), interpolation=cv2.INTER_LINEAR)
    glow = cv2.GaussianBlur(lay, (0, 0), 6)
    pm = 0.0 if person is None else np.clip(person * 1.2, 0, 1)[..., None]
    o = img * (1 - 0.42 * g - 0.10 * sw) + (lay * 1.6 + glow * 0.9) * (g + 0.35 * sw) * (1 - 0.92 * pm) * s.get("lexg", 1.0)   # light passes behind him
    return np.clip(o, 0, 1)

def long_exposure(A, B, j, f, sa, sb, pre=12, post=18):
    """the shutter closes: the trails linger over the next shot and settle into its own lights (the city's windows)."""
    x = (j + pre) / (pre + post - 1)
    if j < 0: return A
    v = (j + 1) / post
    lay = cv2.resize(lex_layer(sa, sa["f1"] - 1), (W, H), interpolation=cv2.INTER_LINEAR) * (0.90 ** (j + 1))
    lay = zoom_about(lay, W / 2, H * 0.40, 1 - 0.85 * ein(v, 1.6))                               # drawn back into points of light
    w = smooth(clamp(v / 0.45, 0, 1))
    hiB = B * np.clip((lumf(B) - 0.45) / 0.3, 0, 1)[..., None]
    bump = math.sin(math.pi * clamp(v, 0, 1))
    keep = face_keep(sb, sb["f0"], 1.3); pmB = PERSON.get(f)
    if pmB is not None: keep = keep * (1 - np.clip(cv2.GaussianBlur(pmB, (0, 0), 3) * 1.2, 0, 1))[..., None]   # the trails go behind him
    o = A * (1 - w) + B * w + (lay * 1.2 + cv2.GaussianBlur(hiB, (0, 0), 10) * 0.9 * bump) * (keep if not isinstance(keep, float) else 1.0)
    return np.clip(o, 0, 1)

# ---- FACE MATCH (alone, wide -> alone, close): the push in lands on the close-up's eye line --------------------------
def face_match(A, B, j, f, sa, sb, pre=10, post=12):
    fa = face_scr(sa, sa["f1"] - 1) if sa.get("face") is not None else None
    fb = face_scr(sb, sb["f0"]) if sb.get("face") is not None else None
    if not fa or not fb: return A if j < 0 else B
    s_ab = fb[2] / max(1.0, fa[2])
    def M_(img, fx, fy, sc, tx, ty):
        return cv2.warpAffine(img, np.float32([[sc, 0, tx - sc * fx], [0, sc, ty - sc * fy]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    x = (j + pre) / (pre + post - 1); p = smooth(x)
    sA = s_ab ** p; tA = (fa[0] + (fb[0] - fa[0]) * p, fa[1] + (fb[1] - fa[1]) * p)              # A carried onto B's face
    sB = s_ab ** (p - 1); tB = tA
    a = M_(A, fa[0], fa[1], sA, *tA); b = M_(B, fb[0], fb[1], sB, *tB)
    w = smooth(clamp((x - 0.44) / 0.12, 0, 1)); o = a * (1 - w) + b * w
    k = 0.03 * math.sin(math.pi * x)
    return np.clip(radial_blur(o, tA[0], tA[1], 1.0, 1.0 + k, 8) if k > 0.004 else o, 0, 1)

# ---- BEAM CALL (alone -> the signal): a searchlight beam crosses the sky behind him and turns to us ----------------------
def beam_call(A, B, j, f, sa, sb, pre=20, post=8):
    x = (j + pre) / (pre + post - 1)
    sx, sy = 1.3 * W, H * 0.12
    th = math.radians(186 - 34 * smooth(clamp(x / 0.8, 0, 1)))                                   # the beam swings down across the sky behind him
    hw = math.radians(7 + 12 * ein(clamp((x - 0.55) / 0.45, 0, 1), 2))                           # and widens as it turns to us
    ang = np.arctan2(_GY - sy, _GX - sx); da = np.abs(((ang - th) + math.pi) % (2 * math.pi) - math.pi)
    cone = np.clip(1 - da / hw, 0, 1) ** 1.6
    dist = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2) / H
    beam = (cone * np.exp(-dist * 0.55)).astype(F32) * smooth(clamp(x / 0.25, 0, 1))
    pm = PERSON.get(f) if j < 0 else _HO.get("bc_pm")
    if j < 0 and pm is not None: _HO["bc_pm"] = pm
    behind = 1.0 if pm is None else (1 - np.clip(cv2.dilate(pm, np.ones((9, 9), np.uint8)) * 1.3, 0, 1))
    fsm = face_soft(sa, sa["f1"] - 1, 0.95)
    if fsm is not None: behind = behind * (1 - fsm[..., 0])
    w = smooth(clamp((x - 0.68) / 0.12, 0, 1))
    if "lens0" not in _HO: _HO["lens0"] = sig_lens(sb, sb["f0"])
    lx, ly, lr = _HO["lens0"]
    hot = np.exp(-(((_GX - lx) ** 2 + (_GY - ly) ** 2) / (2 * (lr * 1.4) ** 2))).astype(F32) * ein(clamp((x - 0.5) / 0.5, 0, 1), 2)
    o = A * (1 - w) + B * w
    lay = beam * behind * (1 - w)                                                                # behind his matte: light behind the subject
    addc(o, lay, TUNG * 0.6 + HOT * 0.4, 1.5); addc(o, cv2.GaussianBlur(lay, (0, 0), 30), TUNG, 0.8)
    addc(o, hot * (1 - 0.6 * w), HOT * 0.5 + TUNG * 0.5, 0.45)
    return np.clip(o, 0, 1)

# ---- THE SIGNAL (the emblem transition): the real Flash signal; its bolt is the doorway home ---------------------------
def sig_lens(s, f):
    t, _, _ = src_time(s, f); T = E.SIG_TRACK; ts = [a[0] for a in T]
    x, y, r = (float(np.interp(t, ts, [a[i] for a in T])) for i in (1, 2, 3))
    X, Y, sc = to_screen(s, f, x, y); return X, Y, r * sc

def bolt_poly(X, Y, R):
    return np.float32([(X + u * R, Y + v * R) for u, v in E.SIG_BOLT])

def poly_mask(P, soft=1.2):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.int32(np.round(P * 4))], 255, cv2.LINE_AA, shift=2)
    m = m.astype(F32) / 255
    return cv2.GaussianBlur(m, (0, 0), soft) if soft > 0 else m

def lens_rays(img, X, Y, R, bolt_m, amt, q=4):
    """god rays from the lamp's lens through the dark; the bolt's shadow streams out in them."""
    disc = np.zeros((H // q, W // q), F32); cv2.circle(disc, (int(X / q * 4), int(Y / q * 4)), int(R * 0.92 / q * 4), 1.0, -1, cv2.LINE_AA, shift=2)
    src = disc * (1 - cv2.resize(bolt_m, (W // q, H // q)))
    acc = np.zeros_like(src); ws = 0.0
    for i in range(16):
        sc = 1.0 + 0.07 * i; d_ = 0.86 ** i
        acc += cv2.warpAffine(src, cv2.getRotationMatrix2D((X / q, Y / q), 0, sc), (W // q, H // q), flags=cv2.INTER_LINEAR, borderValue=0) * d_; ws += d_
    rays = cv2.resize(cv2.GaussianBlur(acc / ws, (0, 0), 1.2), (W, H))[..., None]
    return img + rays * (TUNG * 0.55 + HOT * 0.45) * amt

def signal_fx(img, s, f):
    """the lamp warms up: the lens glows brighter (the bolt stays dark) and throws rays (e57 -> e64)."""
    e = e_of(f); g = smooth(clamp((e - 58.3) / 3.4, 0, 1))
    if g <= 0: return img
    X, Y, R = sig_lens(s, f); bm = poly_mask(bolt_poly(X, Y, R), 1.0)
    disc = disc_mask16(X, Y, R * 0.95, 3)
    o = img * (1 + 0.10 * g * (disc * (1 - bm))[..., None])
    return np.clip(lens_rays(o, X, Y, R, bm, 0.55 * g), 0, 1)

def disc_mask16(cx, cy, r, soft=2.0):
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    return np.clip((r - d) / soft + 0.5, 0, 1).astype(F32)

SIG_PRE, SIG_POST = 48, 24
def emblem_signal(A, B, j, f, sa, sb, pre=SIG_PRE, post=SIG_POST):
    """THE SIGNAL: we push into the lamp; through the bolt in its lens the light is home (the loft's warm lamp); the bolt
    opens past the frame and we are there. Stages: the push in (the rays, the bolt dark), home appears inside the bolt
    with a warm rim on its edge, the bolt doorway grows past the frame."""
    ff = f if j < 0 else sa["f1"] - 1
    X, Y, R = sig_lens(sa, ff); P0 = bolt_poly(X, Y, R); bc = P0.mean(0)
    u = (j + pre) / pre if j < 0 else 1.0
    z = 1 + 1.7 * ein(u, 2.2)
    tx, ty = bc[0] + (W / 2 - bc[0]) * smooth(u), bc[1] + (H * 0.47 - bc[1]) * smooth(u)
    if j >= 0:
        v = (j + 1) / post; z = z * math.exp(3.4 * ein(v, 1.8))
    M = np.float32([[z, 0, tx - z * bc[0]], [0, z, ty - z * bc[1]]])
    Ac = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Pz = np.float32([(M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]) for x, y in P0])
    bm = poly_mask(Pz, 1.0 + 0.6 * z)
    Xz, Yz, Rz = M[0, 0] * X + M[0, 2], M[1, 1] * Y + M[1, 2], R * z
    Ac = lens_rays(Ac, Xz, Yz, Rz, bm, 0.40 * ein(u, 1.5))                                      # on top of the shot's own rays: from zero
    bw = smooth(clamp((u - 0.30) / 0.45, 0, 1))
    fb = face_scr(sb, sb["f0"]) if sb.get("face") is not None else None                      # his face sits inside the bolt's middle blade
    if fb:
        pin = (M[0, 0] * (X - 0.02 * R) + M[0, 2], M[1, 1] * (Y - 0.02 * R) + M[1, 2])
        rel = 1.0 if j < 0 else 1 - smooth(clamp(((j + 1) / post - 0.20) / 0.80, 0, 1))
        bsc = clamp(0.20 * R * z / max(1.0, fb[2]), 0.12, 1.0)                                  # his face fits the bolt's middle blade
        sc_ = 1 + (bsc - 1) * rel; tx_, ty_ = fb[0] + (pin[0] - fb[0]) * rel, fb[1] + (pin[1] - fb[1]) * rel
        Bz = cv2.warpAffine(B, np.float32([[sc_, 0, tx_ - sc_ * fb[0]], [0, sc_, ty_ - sc_ * fb[1]]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    else:
        Bz = zoom_about(B, W / 2, H * 0.47, 1.10 if j < 0 else 1.10 - 0.10 * eout((j + 1) / post, 2.0))
    m = bm * bw
    if j >= 0: m = np.maximum(m, smooth(clamp(((j + 1) / post - 0.35) / 0.65, 0, 1)))   # exactly home by the end
    o = Ac * (1 - m[..., None]) + Bz * m[..., None]
    rim = np.clip(cv2.GaussianBlur(bm, (0, 0), 3 + 2 * z) - bm, 0, 1) * bw * (1 - (smooth((j + 1) / post) if j >= 0 else 0))
    addc(o, rim, TUNG, 3.0); addc(o, cv2.GaussianBlur(rim, (0, 0), 8), AMBR, 1.2)                   # the bolt's edge glows
    o = o * (1 - (1 - m[..., None]) * np.array([0.26, 0.10, 0.0], F32) * smooth(u)) + (1 - m[..., None]) * TUNG * 0.04 * smooth(u)   # the glare is warm light
    return np.clip(o, 0, 1)

# ---- LAMPLIGHT (the loft -> Iris in the kitchen): the lamp's warm glow swells and carries us across the room ----------
def lamplight(A, B, j, f, sa, sb, pre=8, post=12):
    x = (j + pre) / (pre + post - 1); env = math.sin(math.pi * clamp(x, 0, 1))
    if "ll" not in _HO: _HO["ll"] = hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.55)
    px, py = _HO["ll"]
    w = smooth(clamp((x - 0.45) / 0.1, 0, 1)); o = A * (1 - w) + B * w
    d2 = (_GX - px) ** 2 + (_GY - py) ** 2
    bloom = np.exp(-d2 / (2 * (120 + 700 * env) ** 2)).astype(F32)
    pk = math.exp(-((x - 0.5) / 0.12) ** 2)
    addc(o, bloom, TUNG, 0.36 * env + 0.30 * pk)                                                # warm lamplight washes the room, brightest on the switch
    return np.clip(o, 0, 1)

# ---- TURN PAN (Iris -> him): the camera turns from her to him, a whip across the room ----------------------------------
def turn_pan(A, B, j, f, sa, sb, pre=5, post=7):
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1))
    strip = np.concatenate([A, B], axis=1); x0 = int(round(p * W))
    o = np.ascontiguousarray(strip[:, x0:x0 + W]); sp = math.sin(math.pi * clamp(q, 0, 1))
    return np.clip(hblur(o, 2 + 150 * sp), 0, 1)

# ---- HOME LIGHT (the loop, e76 -> e80): the loft pulls back into one lit window of frame 0's city ---------------------
def frame_virtual(fv, with_person=False):
    s0 = SHOTS[0]; out, person = base16(s0, fv)
    return (out, person) if with_person else out

def home_cam(t):
    t = clamp(t, 0, 1); return t * t * t * (t * (6 * t - 15) + 10)

_HLS = {}
def home_win(fv):
    """frame 0's lit window (HOME_WIN, measured on frame 0) on screen at the roof's virtual frame fv: fixed on the
    source, so it rides the roof's own push."""
    s0 = SHOTS[0]
    if "src" not in _HLS:
        t, u, _ = src_time(s0, 0); cx_, cy_, ch_ = frame_geom(s0, 0, t, u)[:3]; sc0 = W / (ch_ * 9 / 16)
        wx, wy, ww, wh = E.HOME_WIN; _HLS["src"] = ((wx - W / 2) / sc0 + cx_, (wy - H / 2) / sc0 + cy_, ww / sc0, wh / sc0)
    x, y, ww, wh = _HLS["src"]; X, Y, sc = to_screen(s0, fv, x, y); return X, Y, ww * sc, wh * sc

def home_light(img, f, s):
    """THE HOME LIGHT (the loop, e74 -> frame 0, on "going home"): the camera pulls back out of the loft through its
    window. The loft is the window: the night city of frame 0 opens round it (the real rooftop footage at frame 0's
    virtual frames, its push-in running on), the window shrinks into one lit window of the city, he comes in solid in
    front of it, and its light is all that is left: frame 0. The reverse of WINDOW HOP. The pull starts and lands at rest
    (a smootherstep in log zoom), so the roof's own slow push carries the camera across the wrap."""
    f0 = fh(E.E_LOOP); N = E.DUR_F - f0
    if f < f0: return img
    t = (f - f0) / N; e = home_cam(t)                                                           # t = 1 is frame 0
    fv = f - E.DUR_F; world, pm0 = frame_virtual(fv, True)
    wx, wy, ww, wh = home_win(fv)
    fade = 1 - smooth(clamp((t - 0.80) / 0.20, 0, 1))                                           # the light is all that is left
    bm = soft_rect(wx, wy, ww / 2 - 4, wh / 2 - 4, 6.0)
    world = world * (1 - 0.72 * bm * fade)[..., None]                                          # the window's light is in the card now
    Z0 = H / wh; lz = math.log(Z0) * (1 - e); Z = math.exp(lz); pr = lz / math.log(Z0)
    cx, cy = wx + (W / 2 - wx) * pr, wy + (H / 2 - wy) * pr                                     # where the window is on screen
    if Z > 1.0005:
        M = np.float32([[Z, 0, cx - Z * wx], [0, Z, cy - Z * wy]])
        wz = cv2.warpAffine(world, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        pz = cv2.warpAffine(pm0, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) if pm0 is not None else None
    else:
        wz, pz = world, pm0
    r = 9 * smooth(clamp((lz - 0.7) / 1.6, 0, 1))
    if r > 0.6: wz = defocus16(wz, r)                                                           # up close, the city is soft
    kh = 0.40 * smooth(clamp((lz - 0.8) / 1.5, 0, 1))
    if kh > 0.003: wz = wz * (1 - kh * np.clip((lumf(wz) - 0.45) / 0.40, 0, 1))[..., None]    # a giant bokeh disc would glare
    asp = W / H + (ww / wh - W / H) * smooth(clamp((e - 0.04) / 0.50, 0, 1))                   # the frame's shape -> the window's
    hh = wh / 2 * Z; hw = hh * asp; cs = max(2 * hw / W, 2 * hh / H)                            # the loft fills the window
    card = cv2.warpAffine(img, np.float32([[cs, 0, cx - cs * W / 2], [0, cs, cy - cs * H / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) if abs(cs - 1) > 1e-3 else img
    fe = (1.5 + 0.05 * min(hw, hh)) * smooth(clamp(t / 0.12, 0, 1)) + 1e-3
    m = soft_rect(cx, cy, hw - fe, hh - fe, fe)                                                 # the edge feathers inward (nothing outside the loft)
    if pz is not None and t > 0: m = m * (1 - np.clip(pz * 1.15, 0, 1))                       # he stands in front of the window
    mf = (m * fade)[..., None]
    o = wz * (1 - mf) + card * mf
    glow = cv2.GaussianBlur(m, (0, 0), 4 + 0.16 * min(hw, hh)) * (1 - m)
    addc(o, glow, TUNG, 0.70 * fade * smooth(clamp(t / 0.10, 0, 1)))                            # the window's warm light round it
    spd = 30 * t * t * (1 - t) * (1 - t) / 1.875
    if spd > 0.05: o = radial_blur(o, cx, cy, 1.0, 1.0 - 0.035 * spd, 8)                       # the pull's motion
    return np.clip(o, 0, 1)

def loop_in16(out, f, k):
    return out

# ---- FOCUS PULL (the two of them -> his eyes): the lens racks off her and finds him ------------------------------------
def focus_pull(A, B, j, f, sa, sb, pre=8, post=10):
    x = (j + pre) / (pre + post - 1); r = 34 * math.sin(math.pi * clamp(x, 0, 1)) ** 1.3
    w = smooth(clamp((x - 0.40) / 0.2, 0, 1))
    return np.clip(defocus16(A, r) * (1 - w) + defocus16(B, r) * w, 0, 1)

# ---- BOLT TRAIL (the run -> down the street): his lightning stretches ahead into the street's speed trails -------------
def bolt_trail(A, B, j, f, sa, sb, pre=6, post=10):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.32) / 0.36, 0, 1)); base = A * (1 - w) + B * w
    hi = base * np.clip((lumf(base) - 0.50) * 2.5, 0, 1)[..., None]
    L = int(2 + 420 * k); st = hblur(shift_img(hi, 120 * k), L)
    o = hblur(base, 2 + 60 * k) * (1 - 0.45 * k) + st * 0.6 * k
    return np.clip(o, 0, 1)

# ---- WINDOW HOP (the falling city -> him by the van, ~1 s): one lit window of the tower holds the next shot ------------
WH_PRE, WH_POST = 36, 24
def wh_point(s, f):
    """the tracked window (WH_TRACK, source px) on screen for shot s at frame f, with its half size."""
    t, _, _ = src_time(s, f); T = E.WH_TRACK; ts = [a_[0] for a_ in T]
    x = float(np.interp(t, ts, [a_[1] for a_ in T])); y = float(np.interp(t, ts, [a_[2] for a_ in T]))
    X, Y, sc = to_screen(s, f, x, y); return X, Y, E.WH_SIZE[0] * sc, E.WH_SIZE[1] * sc

def soft_rect(cx, cy, hw, hh, fe):
    """1 inside the rect, a soft edge of width fe outside it (outward feather)."""
    dx = np.abs(_GX - cx) - hw; dy = np.abs(_GY - cy) - hh
    return (np.clip(1 - dx / fe, 0, 1) * np.clip(1 - dy / fe, 0, 1)).astype(F32)

def window_hop(A, B, j, f, sa, sb, pre=WH_PRE, post=WH_POST):
    """WINDOW HOP: the camera glides into one lit window of the falling city (a log-zoom with an eased start and landing),
    the window drifting to the centre and opening to the frame's shape; inside it the next shot is waiting in warm light
    behind the glass, the city rushes softly away round it, and we are inside. A is live until the cut (the window is
    tracked on the source), B is live after it; B lands exactly at scale 1."""
    N = pre + post - 1; x = clamp((j + pre) / N, 0, 1)
    ff = f if j < 0 else sa["f1"] - 1
    px, py, hw0, hh0 = wh_point(sa, ff)
    e = home_cam(x)                                                                             # zero speed at both ends
    Zend = (H / 2) / hh0; lz = math.log(Zend) * e; z = math.exp(lz)
    dr = smooth(clamp(e * 1.12, 0, 1)); tx, ty = px + (W / 2 - px) * dr, py + (H / 2 - py) * dr  # the window drifts to the centre
    asp = hw0 / hh0 + (W / H - hw0 / hh0) * smooth(clamp((e - 0.30) / 0.50, 0, 1))             # and opens to the frame's shape
    hh = hh0 * z; hw = hh * asp
    kw = smooth(clamp(e / 0.30, 0, 1))
    if kw > 0.002:                                                                              # its cold glass warms to a lamp-lit home window
        wm = soft_rect(px, py, hw0 + 1, hh0 + 1, 2.5)[..., None] * kw
        A = A * (1 - 0.75 * wm) + (TUNG * 0.55 + AMBR * 0.10) * wm
    M = np.float32([[z, 0, tx - z * px], [0, z, ty - z * py]])
    Az = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    spd = 30 * x * x * (1 - x) * (1 - x) / 1.875                                                # the zoom's speed, 0..1
    if spd > 0.05: Az = radial_blur(Az, tx, ty, 1.0, 1.0 + 0.045 * spd, 8)                     # the city rushes away round it
    Az = Az * (1 - 0.50 * e)
    bs = max(2 * hw / W, 2 * hh / H)                                                           # B fills the window (exactly 1 at the end)
    Bz = cv2.warpAffine(B, np.float32([[bs, 0, tx - bs * W / 2], [0, bs, ty - bs * H / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) if bs < 0.999 else B
    gl = 1 - smooth(clamp((x - 0.25) / 0.60, 0, 1))                                             # behind the glass, in warm light
    if gl > 0.002:
        band = np.exp(-((((_GX - tx) * 0.55 + (_GY - ty) * 0.83) / max(hw, 1.0) - (-1.6 + 3.2 * x)) / 0.35) ** 2).astype(F32)
        Bz = Bz * (1 - 0.22 * gl) + TUNG * 0.10 * gl
        addc(Bz, band, HOT * 0.5 + TUNG * 0.5, 0.16 * gl)                                       # the glass catches the light
    fe = (1.5 + 0.10 * min(hw, hh)) * (1 - smooth(clamp((x - 0.80) / 0.20, 0, 1))) + 1e-3
    m = soft_rect(tx, ty, hw - fe, hh - fe, fe)                                                 # the edge feathers inward
    o = Az * (1 - m[..., None]) + Bz * m[..., None]
    sp_ = 1 - smooth(clamp((x - 0.55) / 0.40, 0, 1))                                            # the warm light spills out round it
    if sp_ > 0.002:
        glow = cv2.GaussianBlur(m, (0, 0), 3 + 0.20 * min(hw, hh)) * (1 - m)
        addc(o, glow, AMBR * 0.5 + TUNG * 0.5, 0.75 * sp_)
    return np.clip(o, 0, 1)

# ---- ARC JUMP (the run -> him, the lightning crackling round him): a bolt leaps from his run to his lightning ----------
def arc_jump(A, B, j, f, sa, sb, pre=6, post=10):
    x = (j + pre) / (pre + post - 1)
    if _HO.get("aj_n") != sb["n"]:
        _HO["aj_n"] = sb["n"]; _HO["aj"] = (hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.62), hi_point(edge15(sb, "first"), sb, sb["f0"], 0.62))
    (ax, ay), (bx, by) = _HO["aj"]
    grow = eout(clamp(x / 0.42, 0, 1), 2.2); ex, ey = ax + (bx - ax) * grow, ay + (by - ay) * grow
    w = smooth(clamp((x - 0.40) / 0.14, 0, 1)); o = A * (1 - w) + B * w
    cv = bolt_canvas()
    for k_ in range(2):
        put_bolt(cv, (ax, ay), (ex + 12 * k_, ey - 9 * k_), 4400 + 7 * k_ + 3 * (f // 2), 3 - k_, 0.30, 6, 1)
    fade = 1 - smooth(clamp((x - 0.55) / 0.45, 0, 1))
    keep = face_keep(sa if w < 0.5 else sb, sa["f1"] - 1 if w < 0.5 else sb["f0"], 1.35)
    o = o + light_rgb(cv, 0.95 * fade, HOT, AMBR) * (keep if not isinstance(keep, float) else 1.0)
    pk = math.exp(-((x - 0.47) / 0.11) ** 2)
    return np.clip(o * (1 - 0.22 * pk) + AMBR * 0.20 * pk, 0, 1)                               # its flash covers the switch

# ---- EXPOSURE CUT (run -> run, the shutter still open): the frame drags sideways, the trails stay on ----------------------
def exposure_cut(A, B, j, f, sa, sb, pre=4, post=8):
    q = (j + pre) / (pre + post - 1); sp = math.sin(math.pi * clamp(q, 0, 1))
    w = smooth(clamp((q - 0.25) / 0.45, 0, 1)); o = A * (1 - w) + B * w                      # a double exposure, the way film does it
    o = zoom_about(o, W / 2, H * 0.45, 1 + 0.05 * sp)
    return np.clip(hblur(o, 2 + 150 * sp), 0, 1)

# ---- TIME LAPSE ("hard to do these things alone"): the night streams past him while he stands still ------------------
def time_lapse(A, B, j, f, sa, sb, pre=12, post=12):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1)) ** 1.2
    live, s_ = (A, sa) if j < 0 else (B, sb)
    pm = PERSON.get(f)
    if pm is None:
        fk = face_keep(s_, f, 1.6); pm = (1 - fk[..., 0]) if not isinstance(fk, float) else np.zeros((H, W), F32)
    pm = cv2.GaussianBlur(np.clip(pm * 1.15, 0, 1), (0, 0), 2)[..., None]
    bg = hblur(live, int(2 + 220 * k))
    hi = live * np.clip((lumf(live) - 0.42) * 2.6, 0, 1)[..., None]
    trails = hblur(hi, int(2 + 640 * k)) * 2.6 * k
    o = (bg + trails * (TUNG * 0.5 + 0.5)) * (1 - pm) + live * pm                               # he stays sharp, the world streams
    pk = math.exp(-((x - 0.5) / 0.10) ** 2)
    return np.clip(o * (1 + 0.10 * pk), 0, 1)

# ---- SKY STRIKE (alone -> the lightning in his eyes): a bolt cracks down behind him, and in its light he is charged -----
def sky_strike(A, B, j, f, sa, sb, pre=10, post=8):
    if j >= 0:
        v = (j + 1) / post; return np.clip(B * (1 + 0.28 * (1 - v) ** 2) + AMBR * 0.10 * (1 - v) ** 2, 0, 1)
    u = (j + pre) / pre
    fs = face_scr(sa, f) if sa.get("face") is not None else None
    fx_, fw_ = (fs[0], fs[2]) if fs else (W / 2, 160)
    side = 1 if fx_ < W / 2 else -1
    bx = clamp(fx_ + side * 2.3 * fw_, 90, W - 90); p0 = (bx - side * 120, -30); p1 = (bx + side * 40, H * 0.66)
    grow = eout(clamp(u / 0.45, 0, 1), 2.0); pe = (p0[0] + (p1[0] - p0[0]) * grow, p0[1] + (p1[1] - p0[1]) * grow)
    cv = bolt_canvas(); put_bolt(cv, p0, pe, 5150 + (f // 2), 4, 0.32, 7, 2)
    fl = 0.75 + 0.25 * math.sin(f * 2.1)
    pm = PERSON.get(f); behind = 1.0 if pm is None else (1 - np.clip(cv2.dilate(pm, np.ones((7, 7), np.uint8)) * 1.3, 0, 1))[..., None]
    lt = light_rgb(cv, 1.1 * fl, HOT, AMBR)
    lift = 0.45 * ein(u, 1.6)                                                                    # the night lights up behind him
    o = A + (lt + A * lift * fl) * behind
    if pm is not None:
        rim = np.clip(cv2.GaussianBlur(pm, (0, 0), 3) - pm * 0.8, 0, 1)[..., None]              # his edge catches it
        o = o + rim * AMBR * 0.5 * ein(u, 1.5)
    return np.clip(o, 0, 1)

# ---- MOTE DRIFT (the loft -> Barry home): the lamplit dust thickens into a warm drift across the lens --------------------
def mote_drift(A, B, j, f, sa, sb, pre=10, post=12):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.40) / 0.20, 0, 1)); base = defocus16(A * (1 - w) + B * w, 20 * k ** 1.3)
    rng = np.random.default_rng(6616); lay = np.zeros((H // 4, W // 4), F32); cx = -0.5 * W + 2.0 * W * smooth(x)
    for i in range(80):
        dx, yy, rr, a_ = rng.normal(0, 240), rng.uniform(-200, H + 200), rng.uniform(12, 50), rng.uniform(0.35, 1.0)
        px_ = cx + dx + 0.35 * (yy - H / 2); py_ = yy - 160 * x
        cv2.circle(lay, (int(px_ / 4 * 4), int(py_ / 4 * 4)), max(1, int(rr / 4 * 4)), a_, -1, cv2.LINE_AA, shift=2)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 2.5), (W, H))[..., None]
    keep = face_keep(sa if w < 0.5 else sb, sa["f1"] - 1 if w < 0.5 else sb["f0"], 1.3)
    return np.clip(base + lay * TUNG * 0.60 * k * keep, 0, 1)

# ---- in-shot: SUIT CURRENT (the masked close-up) and SPARKS (lightning shedding sparks off his shoulders) ----------------
def a_current(img, person, s, f):
    return off_face(edge_arcs(img, f, body_only(person, s, f), 0.8, 1701), img, s, f, 1.2)

def a_sparks(img, person, s, f):
    """SPARKS: his lightning sheds sparks off his shoulders that arc out and fall (analytic paths, off the face)."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return img
    fx_, fy_, fw_ = fs[:3]; t = (f - s["f0"]) / FPS; T = (s["f1"] - s["f0"]) / FPS
    rng = np.random.default_rng(2626); cv = np.zeros((H // 2, W // 2), F32)
    for i in range(54):
        side = -1 if i % 2 else 1; tb = rng.uniform(-0.6, T); life = rng.uniform(0.45, 0.85); age = t - tb
        ox, oy = fx_ + side * fw_ * rng.uniform(0.75, 1.25), fy_ + fw_ * rng.uniform(1.05, 1.7)
        vx, vy = side * rng.uniform(260, 700), -rng.uniform(150, 520)
        if not (0 <= age <= life): continue
        def pos(a_): return ox + vx * a_, oy + vy * a_ + 0.5 * 1100 * a_ * a_
        x1, y1 = pos(age); x0, y0 = pos(max(0.0, age - 0.035))
        cv2.line(cv, (int(x0 / 2 * 4), int(y0 / 2 * 4)), (int(x1 / 2 * 4), int(y1 / 2 * 4)), float(1 - age / life) ** 0.7, 2, cv2.LINE_AA, shift=2)
    cv = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 0.6), (W, H))[..., None]
    o = img + cv * HOT * 1.6 + cv2.GaussianBlur(cv[..., 0], (0, 0), 5)[..., None] * AMBR * 2.2
    return off_face(np.clip(o, 0, 1), img, s, f, 1.05)

ANIMS.update({"current": a_current, "sparks": a_sparks})

# ---- AFTERGLOW (the lightning in his eyes -> him alone at night): the cut lands on the beat and the lightning stays burnt
# on the eye a moment, spreading and fading (off his face)
def afterglow(A, B, j, f, sa, sb, pre=2, post=16):
    if j < 0: return np.clip(A * (1 + 0.10 * (j + pre + 1) / pre), 0, 1)
    v = (j + 1) / post
    if _HO.get("ag_n") != sa["n"]:
        L = lumf(edge15(sa, "last")); _HO["ag_n"] = sa["n"]; _HO["ag"] = cv2.GaussianBlur(np.clip((L - 0.70) / 0.25, 0, 1), (0, 0), 2.0)
    lay = cv2.GaussianBlur(_HO["ag"], (0, 0), 1 + 9 * v) * (1 - v) ** 1.8
    keep = face_keep(sb, f, 0.95)
    if not isinstance(keep, float): lay = lay * keep[..., 0]
    o = B.copy(); addc(o, lay.astype(F32), AMBR * 0.8 + HOT * 0.2, 0.85)
    return np.clip(o, 0, 1)

TR2.update({"arc_jump": (arc_jump, 6, 10), "exposure_cut": (exposure_cut, 4, 8), "time_lapse": (time_lapse, 12, 12),
            "sky_strike": (sky_strike, 10, 8), "mote_drift": (mote_drift, 10, 12), "afterglow": (afterglow, 2, 16)})

TR2.update({"drop_whip": (drop_whip, 6, 8), "flare_sweep": (flare_sweep, 8, 10), "focus_pull": (focus_pull, 8, 10), "bolt_trail": (bolt_trail, 6, 10), "window_hop": (window_hop, WH_PRE, WH_POST)})

TR2.update({"bokeh_drift": (bokeh_drift, 10, 14), "reflection": (reflection, 16, 12), "headlight_pass": (headlight_pass, 10, 10),
            "light_warp": (light_warp, 8, 10), "release": (release, 4, 12), "streak_pass": (streak_pass, 5, 7),
            "light_flare": (light_flare, 6, 8), "whip_up15": (whip_up15, 6, 8), "city_dive": (city_dive, 8, 10),
            "long_exposure": (long_exposure, 12, 18), "face_match": (face_match, 10, 12), "beam_call": (beam_call, 20, 8),
            "emblem_signal": (emblem_signal, SIG_PRE, SIG_POST), "lamplight": (lamplight, 8, 12), "turn_pan": (turn_pan, 5, 7),
            "loop_in16": ((lambda A, B, j, f, sa, sb: B), 0, 1)})

# ---- the frame ----------------------------------------------------------------------------------------------------------
def base16(s, f):
    img, person = base11(s, f)
    if s.get("anim") in ANIMS: img = ANIMS[s["anim"]](img, person, s, f)
    n = s["n"]
    if n == "charge": img = hold_on(img, person, s, f)
    elif n in ("lrun", "lrun2"): img = long_exposure_fx(img, person, s, f)
    elif n == "signal": img = signal_fx(img, s, f)
    elif n == "home": img = home_light(img, f, s)
    return img, person

_B16 = {}
def edge15(S_, which):
    key = (S_["n"], which)
    if key not in _B16:
        if len(_B16) > 8: _B16.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        _B16[key] = base16(S_, fr)
    return _B16[key][0]

def edge_person(S_, which):
    edge15(S_, which); return _B16[(S_["n"], which)][1]

PERSON = {}
def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base16(s, f)
    PERSON.clear(); PERSON[f] = person
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge15(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge15(n_, "first"), kn, f, s, n_)
    return np.clip(out, 0, 1)

def render(f):
    s = shot_at(f); out = flash_governor(beat_fx(prefinish(f), f))
    f0 = fh(E.E_LOOP); mix = home_cam((f - f0) / (E.DUR_F - f0)) if (s["n"] == "home" and f >= f0) else None
    return (np.clip(finish16(out, f, s, mix), 0, 1) * 255 + 0.5).astype(np.uint8)
