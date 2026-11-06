// What Opus reads: the studio's capabilities and data formats. The owner's house style lives in
// knowledge.ts and the presets, and is added by the Director when a preset uses it.
import { AudioAnalysis, FONTS, MediaInfo, Project, REVEALS_IN, REVEALS_OUT, SFX, TEXT_ANIMS_IN, TEXT_ANIMS_OUT, TRANSITIONS } from '../state/types';
import { projectDuration } from '../state/util';
import { fxCatalogText } from '../engine/fxlib';
import { sourceNotes } from './sources';

export function reference(p: Project): string {
  return `HOW THE STUDIO WORKS
- Times are in seconds. The project is ${p.width}x${p.height} at ${p.fps} fps.
- Tracks are listed top to bottom; higher tracks draw on top. The video track marked "main" is magnetic: its clips always play back to back with no gaps, in order of their start times. Clips on other tracks sit exactly at their start time and may leave gaps. Text clips go on text tracks; sound-only clips go on audio tracks (a video file placed on an audio track contributes only its sound).
- A media clip plays source seconds [in, in + dur*speed) of its file, starting at timeline time start, for dur seconds of timeline. Video clips also play their own sound unless muted.
- A clip may not run past the end of its file: in + dur*speed must not exceed the media length.
- Clips on the same non-magnetic track must not overlap; an overlapping clip is moved to another track.

REPLY FORMAT
Reply with only one JSON object: {"message": string, "ops": [operation, ...]}
"message" is a few sentences for the user about what you did. The studio applies "ops" in order, as one undoable step, and reports any operation it had to reject or adjust.

OPERATIONS
{"op":"clear"}  remove every clip and reset the tracks (use it first when rebuilding from scratch)
{"op":"project","name":"..","width":1080,"height":1920,"fps":30,"background":"#000000"}
{"op":"track","id":"V3","kind":"video|audio|text","name":".."}  add a track; on an existing id it can set "name", "muted", "hidden"
{"op":"add","id":"c1","media":"m1","track":"V1","start":0,"in":12.5,"dur":2.0, ...clip fields}
{"op":"text","id":"t1","track":"T1","start":0.5,"dur":2.0,"text":"..", ...text fields}
{"op":"set","id":"c1", ...fields to change}  (start, dur, in, track and any clip or text field). Objects merge: transform, color, style, anim and an effect's params change only the keys you give; kf replaces only the properties you give ("kf":{"scale":null} removes one); "preset" swaps a library effect for another, keeping its timing and params that still apply
{"op":"remove","id":"c1"}  or  {"op":"remove","ids":["c1","c2"]}
{"op":"split","id":"c1","at":3.2,"newId":"c1b"}  split at timeline time "at"
{"op":"sfx","id":"s1","sound":"whoosh","start":2.1,"volume":0.35}  a generated sound effect on an SFX track; start may be before the cut so the sound peaks on it. Sounds: ${SFX.join(', ')} (lengths: whoosh 0.9 s peaking at 0.56 s, swish 0.35 s, impact 1.4 s, hit 0.45 s, boom 2.6 s, riser 2.0 s ending on its peak, subdrop 1.3 s, reverse 1.2 s ending on its peak, glitch 0.5 s, shutter 0.25 s, tick 0.08 s, tapestop 0.9 s, zap 0.75 s, glass 1.2 s (the crack is at its start, the shards ring after), rip 0.55 s peaking at 0.12 s). Materials: glass for a shatter or a lens breaking, rip for a tear, plastic or a zipper, shutter for apertures and blinds, zap for lightning
{"op":"sounds","volume":0.3}  matched sounds for the designed transitions only (soft joins such as crossfades, dips, slides, pushes and wipes stay silent; at most one every ~0.9 s; replaces earlier automatic sounds). Prefer placing the few sounds that matter yourself.
{"op":"lyrics","lines":[4,5,6],"text":{"5":"YOU WANTED ME\\nTO *BE*"},"style":{"emphColor":"#ff2b3a"},"transform":{"y":0.25}}  captions for TIMED LYRICS lines (numbered L1, L2… in the lyrics list), each placed on its sung time through the music clip: it maps song time to timeline time, shows the line until the next one (at most ~3.6 s), eases every word in on its own time, uses the house caption style (override with style/anim/transform) and splits the line over two lines (override per line with "text", same words, *emphasis* allowed). Also "from":4,"to":9 instead of "lines"; "music": the music clip id if there are several; "shift": seconds to nudge every line. Running it again for a line replaces that caption. Only available when the owner supplied timed lyrics.
{"op":"project","camera":{"on":true,"every":"beat","punch":0.055,"kick":1,"decay":0.16,"sections":[{"from":9,"to":16.8},{"from":18.6,"to":22.8,"punch":0.04,"kick":0.7,"every":"half"}]}}  the beat camera: zoom punch and rotation kick on the music's beats ("beat", "half" = every other beat, "downbeat"); video layers only, text stays clean. "sections" runs it only in those stretches, each with its own punch, kick and every (it rests in holds, freezes and the loop landing between them); or "from"/"to" for one stretch (with sections, from/to bound them all)
{"op":"loop","dur":0.4}  lands the loop in picture: a twin of the first shot (same file, framing, colour and exposure) dissolves in over the last "dur" seconds and ends on exactly the source frame frame 0 opens on. Run it after the shots are final; build the loop's set piece before it and keep the layers over the last frames the same as over frame 0.
{"op":"project","exposure":{"auto":true,"target":0.34}}  auto exposure: every shot whose picture is dimmer than the target mean brightness is lifted toward it (shadows and mids raised, highlights kept), so dark sources read on a phone; on by default for house-style edits. "exposure": false turns it off; "autoExposure": false on a clip keeps that shot's own darkness (a designed dark moment). Grade with clip color and the look on top of it.
Ids you give must be new and unique (letters, digits, - or _).
After your operations the studio runs two finishing passes and reports them back: every main-track cut within 90 ms of a music beat is moved exactly onto the beat (the text, effects and sounds over it move with it; lyric captions stay on the song), and sound effects are thinned (no two moments within 0.3 s, at most two layers per moment and two moments per second, about three every four seconds overall; automatic sounds go first).

CLIP FIELDS (all optional)
speed 0.1-10 (default 1); keepPitch true|false (default true)
ramp {"fast":2.2,"slow":0.45,"burst":0.18}: a velocity ramp synced to the music: a speed burst on every beat inside the clip, slow motion between (needs a music clip under it; the studio fits it to the source length). Or keyframe "speed" yourself. "ramp": null removes it
volume 0-4 (1 = as recorded); fadeIn, fadeOut (seconds); muted true|false
fit "cover" (fills the frame, crops; default) | "contain" (whole picture, may leave bars)
focus {"x":0.62,"y":0.34}: the subject's point in the SOURCE picture (0..1 from its top-left: read it off the cyan ruler on the contact sheets, x ticks .1-.9 across, y ticks .25/.5/.75 down). With cover fit the studio crops around it so the face sits centred in the 9:16 window (at about 44% of the height) at any scale, clamped to the picture's edges; transform x/y add to it. Set it on every shot from a landscape source, otherwise the crop takes the middle of the source. "focus": null removes it.
transform {x, y, scale, rotation, opacity}: x and y offset the centre in frame widths and heights (0,0 = centred); scale 1 = fitted size; rotation in degrees clockwise; opacity 0-1
kf {"scale": [[t, value, ease], ...], ...}: keyframes for x, y, scale, rotation, opacity, volume, speed; t is seconds from the clip's start; ease is linear|in|out|inOut|hold (default inOut) and shapes the move to the next key
color {brightness, contrast, saturation, temperature, tint: -1..1; hue: -180..180; vignette, blur: 0..1}
transition {"type": .., "dur": seconds, "at": {"x":0.5,"y":0.42}, "to": {"x":0.5,"y":0.42}} ("transition": null removes it): transition from the previous clip on the same track into this clip, centred on the cut; the previous clip must end exactly where this one starts; the outgoing clip keeps playing past its end during the first half (make sure its file has room). "at" is where the move happens on the outgoing picture and "to" where the next picture emerges, in frame coordinates (0..1 from the top-left; with "focus" set, a face's eyes sit near (0.5, 0.42)); dive, shatter, shutter, iris, ripple and swirl use them; tear takes both: its jagged edge sweeps across the frame in the direction from "at" to "to". Types: ${TRANSITIONS.join(', ')}.
  Signature types: logo (the voidfx logo slams in and the camera flies through its "o" into the next shot; allowed once per edit; ~1.2 s), dive (the camera dives into "at" (his eye, a blood drop, a muzzle, a photo, a screen) through a closing aperture with radial blur and a beat of black, and the next shot opens out of "to"; ~0.8 s; whoosh + subdrop), shatter (the frame cracks from "at" into radial glass shards that fall away onto the next shot; never on a face; ~0.7 s; impact + glass), tear (the frame tears open behind a ragged edge that sweeps across it, in the direction from "at" to "to" when given; rip), blink (eyelids close with blur and blink open), ink (a blood-red stain blooms open into the next shot), burn (film-burn holes with an ember rim), slash (a blade cuts the frame and the halves fly apart), punch (impact frame: one-frame negative and a zoom punch), shutter (a camera aperture closes on "at" and opens on "to"; shutter sound), wash (an exposure wash: the picture blows out and the next shot recovers from it; put its peak on the hit), light_sweep (a streetlight bar sweeps across and the cut happens under it), heat (heat-haze shimmer across the cut), light_leak (warm leak sweeps across), roll (the world rolls 90 degrees), shadow (darkness swallows the frame, the next shot emerges brightest-first), warp (radial pull through the centre), bolt (a forked lightning bolt strikes down the frame and the next shot opens out from its channel, with its light on both shots; ~0.55 s; pair it with the zap sound). flash is a flare that keeps the picture.
  Physical 3D types: cube_left/right/up/down (the world turns like a cube in perspective; ~0.6 s; whoosh + hit), flip_h/flip_v (a card flip; the edge-on moment is the cut), slices (the frame splits into bands that slide apart), blinds (venetian slats turn to reveal the next shot; shutter), wiper (a windscreen-wiper sweep).
  Distortions (generic filler, at most one in four joins, never two in a row): ripple, swirl, kaleido, pixelate, datamosh, glitch.
  Time-freeze: speed keyframes down to 0.05 hold a moment almost still (a 1 s hold plays 0.05 s of source); ramp back up to burst out of it.

TEXT FIELDS
text: the words (use \\n for a line break; wrap a word in *asterisks* to emphasise it)
words [t1, t2, ...]: when each word starts, in seconds from the clip's start (with anim.in "words", each word eases in on its own time)
style {font, weight 100-900, italic, size (fraction of frame height), lineScales [per-line size multipliers], color, emphColor, emphGlow 0-1, stroke (outline width as a fraction of size), strokeColor, shadow 0-1, scrim 0-1 (soft dark band behind the block), bg (box behind each line), bgColor, align left|center|right, uppercase, tracking (em), lineHeight, maxWidth (fraction of frame width), fit true (shrinks a line that would overflow the safe width), knockout true (footage-in-letters: the words become windows onto a brightened copy of the picture while the rest of the frame darkens by knockDark 0-1, default 0.82; for one big designed title, the one text allowed mid-frame), motif blood|ash|glass|sparks|petals (what the letters throw off when they blow away)}; colours are hex. Fonts: ${FONTS.join(', ')}
anim {in: ${TEXT_ANIMS_IN.join('|')}; out: ${TEXT_ANIMS_OUT.join('|')}; inDur; outDur}
  in: words (the v9 caption standard: each word fades in, rises and sharpens on its own time from "words"), bloom (the hero title: letters bloom open from a point on their word's onset, twist and flare; the last line, or an *emphasised* one-liner, floods with emphColor), slam (each word slams in from 1.5x, white-hot, on its onset: drops and hits), fly (words fly in from the camera), stamp (a rubber-stamp slam with a small bounce), sweep (a light bar sweeps across and writes the letters on), mask (each word rises out of its own box), track (letters close in from wide tracking), flicker (neon tubes flicker on, then hum), letters (letter by letter), typewriter (eased, never popping), rise, drop, pop, blur, fade, slide_left, slide_right.
  out: cap (the v9 caption exit: fade, rise and blur), blowaway (letters loosen one by one, lift, twist and blow away throwing style.motif particles: the hero title destroyed by the hit), streak (letters snatched off sideways at speed), zoom (the title flies past the camera), scatter (letters burst apart), fall (letters tumble and drop), sink, lift, shrink, blur, words, fade, slide_left, slide_right.
transform and kf work as for media clips; x and y move the text block's centre

LOOKS AND THE EFFECT LIBRARY (tested GPU presets: a line each, use them by name)
{"op":"look","preset":"noir_red","params":{"keep":"#c70f14"}}  one grade over the whole edit: it sits on the look track above all the footage, graphics and effects, under the text and the logo, so every shot shares it. Without "dur" it covers the whole edit and follows its length. Give "start" and "dur" for a section only (a flashback in film16, a night-vision stretch, a black-and-white freeze); a new look replaces the looks it overlaps. A bold look is the fastest way to give an edit its own identity: black-and-white noir with one colour kept, a duotone in the edit's colours, a film stock, CCTV, thermal.
{"op":"fx","id":"f1","preset":"exposure_wash","start":7.8,"dur":0.45,"params":{"amount":0.9},"at":{"x":0.5,"y":0.42}}  a library effect at a moment, on an overlay track (under the look, so it takes the edit's grade). "over": true puts it above the look instead (a light, a neon colour or blood that must keep its colour in a black-and-white edit). "at" anchors effects marked [anchor] in frame coordinates (the light's source, the impact point, the eye); kf x/y move the anchor to follow the action. Effects marked [beat] react to the music's beats on their own. Their transform and kf x/y are offsets from the frame centre (an anchor at frame x 0.62 is x 0.12), as for every clip. A preset's params are fixed for the clip: to animate its strength keyframe its opacity, its size its scale, or split it into two clips. Effects marked (add) or (screen) are light laid over the picture. Params take the defaults below when left out; colours are hex.
{"op":"set","id":"f1","params":{"amount":0.6}}  change a look's or effect's parameters; "preset" swaps it for another.
${fxCatalogText()}

CUSTOM GRAPHICS AND EFFECTS (design your own for this edit: set pieces, character-specific transitions, graphics no library has)
They go on overlay video tracks (never the main track) above the footage, and render the same in the preview, the export and the frames you review. Use them for the signature moments no preset covers; the library presets above are the quicker choice for everything else.
{"op":"graphic","id":"g1","start":3.1,"dur":1.2,"svg":"<svg viewBox='0 0 1000 1000'>…</svg>","gw":0.5,"blend":"normal|add|screen","glow":0.6,"reveal":{"in":"pop","out":"flicker","inDur":0.3,"outDur":0.25},"transform":{"x":0,"y":-0.12},"kf":{"rotation":[[0,-8],[1.2,0]]}}
  svg: vector art you draw (emblems, a lightning bolt, marks, frames, speed lines, shards). Drawing elements only: svg, g, path, circle, ellipse, rect, line, polyline, polygon, defs, linearGradient, radialGradient, stop, clipPath, mask, filter with feGaussianBlur/feOffset/feMerge/feColorMatrix/feBlend/feComposite/feFlood, use. No text (use text clips), no images, no scripts, no outside links; it needs a viewBox; up to 40,000 characters. gw = width as a fraction of the frame width (height follows the viewBox). glow 0-1 adds a soft light around it. reveal.in: ${REVEALS_IN.join('|')}; reveal.out: ${REVEALS_OUT.join('|')}. transform, kf (x, y, scale, rotation, opacity) and color work as for media clips, and graphics ride with the beat camera.
{"op":"shader","id":"e1","start":2.9,"dur":0.6,"blend":"normal|add|screen","code":"vec4 effect(vec2 uv, float t, float p) { … }","transform":{"x":0.1,"y":-0.05},"kf":{"x":[[0,0.1],[0.6,-0.1]]}}
  code: a GLSL ES 3.0 function the studio runs over the whole frame for every frame of the clip. It returns straight (not premultiplied) RGBA laid over the picture with "blend": normal (alpha over), add (light: lightning, glows, sparks), screen.
  uv: frame position, 0..1, (0,0) top-left. t: seconds since the clip started; p: 0..1 through the clip.
  Uniforms: uRes (pixels), uAspect (width/height), uDur, uTime (timeline seconds), uBeat (1.0 on each music beat, decaying over ~0.14 s), uBeatAge (seconds since the last beat), uEnergy (music loudness 0..1 now), uPos (anchor in uv from transform/kf x,y: 0.5+x, 0.5+y), uScale, uRot (radians), uOpacity (applied for you), uSeed, PI.
  Helpers: frame(uv) the picture under this layer (rgb) for distortions, ghosts, chromatic splits and relighting (return vec4(colour, 1.0) to replace the picture); aspectUv(uv) square coordinates centred on the frame (x in -0.28..0.28 for 9:16, y in -0.5..0.5); toLocal(uv) square coordinates around uPos with uScale/uRot applied; hash11, hash21, noise, fbm, rot2(angle), sdCircle, sdBox, sdSegment, glow(dist, width) = soft falloff, boltDist(p, a, b, seed, jag) = distance to a jagged lightning path from a to b (jag ~0.2-0.4; change seed every few frames, e.g. floor(t*12.0), to make it flicker), luma(rgb); for looks and finishes: rgb2hsv, hsv2rgb, saturate3(rgb, s), sCurve(rgb, k) (contrast), splitTone(rgb, shadowTint, highlightTint), screen3(a, b), overlay3(a, b), filmGrain(uv, t) (-1..1), vignette(uv, k) (a multiplier), blurFrame(uv, r) and glowFrame(uv, r, threshold) (r in uv units, ~0.004-0.03), sharpenFrame(uv, k), sobel(uv, w) (edge strength, w in pixels), voronoi(p, seed) (vec4: offset to the nearest cell point xy, the cell id, the distance to the cell edge: shards, cells, cracks), lookFinish(rgb, uv, t, grain, vignette, halo, haloTint) (grain + vignette + highlight halo in one call).
  Rules: smoothstep needs its first edge below the second (write 1.0 - smoothstep(a, b, x) for a falling edge); no #directives, uniform/in/out declarations, texture() (use frame), main(), while or do loops; for loops only as "for (int i = 0; i < N; i++)" with a literal N up to 64, at most 4 loops; up to 8000 characters. An effect that fails to compile is skipped and reported back to you with the compiler's message, so keep the code plain.
  Use effects for what the footage and the beat call for: a lightning arc from the hand that throws it (anchor uPos on it from the contact sheet and keyframe x/y to follow its movement), speed streaks along the running direction, a Speed Force tunnel that warps the picture on the drop, an energy ring on a beat, a freeze-frame glow, a custom transition across a cut (place the effect over the cut, often over a plain cut or a short crossfade). Keep them attached to the action, lit like the scene and brief; vary them.
  Example, a beat-pulsed lightning arc between two points (blend add):
  vec4 effect(vec2 uv, float t, float p) { vec2 q = aspectUv(uv); float d = boltDist(q, vec2(-0.18, -0.42), vec2(0.12, 0.35), floor(t * 14.0), 0.3); float core = glow(d - 0.002, 0.003), halo = glow(d, 0.035) * 0.55; float a = (core + halo) * (0.55 + 0.45 * uBeat) * smoothstep(0.0, 0.08, p) * (1.0 - smoothstep(0.75, 1.0, p)); return vec4(mix(vec3(1.0, 0.72, 0.18), vec3(1.0), core), a); }
  Example, a Speed Force pull that warps the picture toward the anchor (blend normal, reads the frame):
  vec4 effect(vec2 uv, float t, float p) { vec2 d = uv - uPos; float r = length(d * vec2(uAspect, 1.0)); float k = 0.5 * sin(p * PI); vec3 col = vec3(0.0); for (int i = 0; i < 12; i++) { float f = float(i) / 11.0; col += frame(uPos + d * (1.0 - k * f * 0.35)); } col /= 12.0; float streak = fbm(vec2(atan(d.y, d.x) * 4.0, r * 6.0 - t * 9.0)); col += vec3(1.0, 0.78, 0.3) * smoothstep(0.55, 0.9, streak) * k * 0.8; return vec4(col, 1.0); }
  Example, Dexter's plastic sheeting wiping across a cut (blend normal, reads the frame; centre a ~0.7 s effect on the cut: the sheet slides in over the outgoing shot, the cut happens under it, it slides off the new one):
  vec4 effect(vec2 uv, float t, float p) { vec2 q = aspectUv(uv); float w = (fbm(vec2(q.y * 7.0, t * 0.7)) - 0.5) * 0.06; float x = q.x + w; float front = mix(-0.36, 0.36, smoothstep(0.0, 0.5, p)); float back = mix(-0.36, 0.36, smoothstep(0.5, 1.0, p)); float cover = (1.0 - smoothstep(front - 0.012, front + 0.012, x)) * smoothstep(back - 0.012, back + 0.012, x); vec2 g = vec2(fbm(q * 8.0 + 1.7), fbm(q * 8.0 + 5.3)) - 0.5; vec3 pic = frame(uv + g * 0.05 * cover); float crease = smoothstep(0.62, 0.9, fbm(q * vec2(4.0, 13.0) + 2.0)); vec3 col = mix(pic, pic * 0.7 + vec3(0.2, 0.23, 0.24), 0.5 * cover) + vec3(0.9, 0.95, 1.0) * crease * cover * 0.55; return vec4(col, 1.0); }
  Example, speed streaks along the running direction (blend add): vec4 effect(vec2 uv, float t, float p) { vec2 q = rot2(-0.35) * aspectUv(uv); float lane = floor(q.y * 70.0); float s = fract(q.x * 1.5 - t * (3.0 + hash11(lane) * 4.0) + hash11(lane + 3.0)); float line = smoothstep(0.0, 0.02, s) * (1.0 - smoothstep(0.0, 0.35, s)) * step(0.82, hash11(lane + 7.0)); return vec4(vec3(1.0, 0.85, 0.5), line * 0.7 * sin(p * PI)); }`;
}

const r2 = (v: number) => Math.round(v * 100) / 100;
const list = (a: number[], max = 9999) => a.slice(0, max).map(r2).join(', ') + (a.length > max ? ` … (${a.length} total)` : '');

function soundLine(a: AudioAnalysis): string {
  const parts: string[] = [];
  if (a.bpm) {
    parts.push(`tempo ${a.bpm} BPM (pulse strength ${a.pulse})`);
    parts.push(`beats: ${list(a.beats, 600)}`);
    parts.push(`downbeats: ${list(a.downbeats, 200)}`);
  } else {
    parts.push('no steady beat');
  }
  if (a.rises.length) parts.push(`sharp rises in level at: ${list(a.rises)}`);
  if (a.hits.length) parts.push(`strongest hits (strongest first): ${list(a.hits, 32)}`);
  if (a.quiet.length) parts.push(`quiet stretches: ${a.quiet.slice(0, 80).map(([s, e]) => `${r2(s)}-${r2(e)}`).join(', ')}`);
  // loudness as digits 0-9, one per half second
  const step = Math.max(1, Math.round(a.energyRate / 2));
  const digits: string[] = [];
  for (let i = 0; i < a.energy.length; i += step) {
    let s = 0, n = 0;
    for (let k = i; k < Math.min(a.energy.length, i + step); k++) { s += a.energy[k]; n++; }
    digits.push(String(Math.min(9, Math.round((s / Math.max(1, n)) * 9))));
  }
  if (digits.length) parts.push(`loudness 0-9 per half second from 0s: ${digits.join('').slice(0, 2400)}`);
  parts.push(`average level ${a.rmsDb} dBFS`);
  return parts.join('\n    ');
}

/**
 * The strongest stretches of a song for a ~23 s edit: a sharp rise (the drop) about 40% in, entered on
 * a downbeat, scored by how much the level jumps and how full the mix stays after it.
 */
export function songWindows(a: AudioAnalysis, dur: number, len = 23): { in: number; out: number; drop: number; score: number }[] {
  const E = a.energy, R = a.energyRate || 1;
  if (!E.length || dur < len + 2) return [];
  const mean = (s: number, e: number) => {
    let t = 0, n = 0;
    for (let i = Math.max(0, Math.floor(s * R)); i < Math.min(E.length, Math.ceil(e * R)); i++) { t += E[i]; n++; }
    return n ? t / n : 0;
  };
  const near = (list: number[], t: number, before: boolean) => {
    let best = t, bd = Infinity;
    for (const d of list) { if (before && d > t + 0.3) break; const k = Math.abs(d - t); if (k < bd) { bd = k; best = d; } }
    return bd < 2.5 ? best : t;
  };
  const cands = [...new Set([...a.rises, ...a.hits.slice(0, 10)].map(x => +x.toFixed(2)))];
  const all: { in: number; out: number; drop: number; score: number }[] = [];
  for (const r of cands) {
    let s = Math.max(0, r - 0.4 * len);
    if (a.downbeats.length) s = Math.max(0, near(a.downbeats, s, true));
    let e = s + len;
    if (a.downbeats.length) e = near(a.downbeats, e, false);
    if (e > dur - 0.05 || e - s < len - 3) continue;
    const after = mean(r, r + len * 0.45), before = mean(Math.max(0, r - 3), r);
    all.push({ in: s, out: e, drop: r, score: after * 0.7 + Math.max(0, after - before) * 0.9 + mean(s, e) * 0.3 });
  }
  all.sort((x, y) => y.score - x.score);
  const out: typeof all = [];
  for (const w of all) if (!out.some(o => Math.abs(o.drop - w.drop) < 6)) out.push(w);
  return out.slice(0, 3);
}

export function mediaCatalog(media: Record<string, MediaInfo>, order: string[]): string {
  const rows: string[] = [];
  for (const id of order) {
    const m: MediaInfo | undefined = media[id];
    if (!m || m.status !== 'ready') continue;
    const dims = m.kind !== 'audio' ? ` ${m.width}x${m.height}` : '';
    const len = m.kind === 'image' ? 'still image' : `${m.duration.toFixed(2)}s`;
    const fps = m.kind === 'video' ? ` ${m.fps}fps` : '';
    const snd = m.kind === 'image' ? '' : m.hasAudio ? ' with sound' : ' no sound';
    rows.push(`${m.id} ${m.kind} "${m.name}" ${len}${dims}${fps}${snd}`);
    const known = sourceNotes(m);
    if (known) rows.push(`    ${known}`);
    if (m.shots && m.shots.length > 1) rows.push(`    shots (${m.shots.length}): ${m.shots.slice(0, 220).map(([a, b], i) => `#${i + 1} ${r2(a)}-${r2(b)}`).join(', ')}${m.shots.length > 220 ? ' …' : ''}`);
    if (m.tags?.length) rows.push(`    tags: ${m.tags.join(', ')}`);
    if (m.analysis && m.hasAudio) {
      rows.push(`    ${soundLine(m.analysis)}`);
      const wins = m.analysis.bpm ? songWindows(m.analysis, m.duration) : [];
      if (wins.length) rows.push(`    best windows for a ~23 s edit (song in -> out, the drop; strongest first): ${wins.map(w => `${r2(w.in)} -> ${r2(w.out)} (drop at ${r2(w.drop)}, ${Math.round(((w.drop - w.in) / (w.out - w.in)) * 100)}% in)`).join('; ')}`);
      // the same windows on the timeline, so the plan needs no beat arithmetic: place the music clip with
      // in = the window's start at timeline 0 and these are where the bars and the drop fall
      const a = m.analysis;
      for (const [k, w] of wins.slice(0, 2).entries()) {
        const bars = a.downbeats.filter(d => d >= w.in - 0.01 && d <= w.out + 0.01).map(d => r2(d - w.in));
        const beat = a.bpm ? 60 / a.bpm : 0;
        rows.push(`    window ${k + 1} on the timeline (music clip in=${r2(w.in)} at start 0, dur ${r2(w.out - w.in)}): the drop at ${r2(w.drop - w.in)}; bars (downbeats) at ${bars.join(', ')}${beat ? `; a beat every ${beat.toFixed(3)} s, a half-beat every ${(beat / 2).toFixed(3)} s` : ''}`);
      }
    }
    else if (m.hasAudio && m.analysisState !== 'done') rows.push('    (sound not analysed)');
  }
  return rows.length ? rows.join('\n') : '(the library is empty)';
}

export function timelineJson(p: Project): string {
  const tracks = p.tracks.map(t => ({ id: t.id, kind: t.kind, name: t.name, ...(t.main ? { main: true } : {}), ...(t.muted ? { muted: true } : {}), ...(t.hidden ? { hidden: true } : {}) }));
  const clips = [...p.clips].sort((a, b) => a.start - b.start).map(c => {
    const { track, ...rest } = c;
    return { ...rest, track };
  });
  return JSON.stringify({ name: p.name, width: p.width, height: p.height, fps: p.fps, background: p.background, camera: p.camera, duration: +projectDuration(p).toFixed(3), tracks, clips });
}

/** What the owner's notes may ask for that the studio cannot do, with the nearest thing it can. */
export const STUDIO_LIMITS = `WHAT THE STUDIO CANNOT DO (the owner's notes may ask for these: do the nearest thing below, say so in one line of "message", and do not spend thinking on the rest)
- You cannot watch video or hear audio, or review an exported file: you see contact sheets, rendered frames and the sound analysis. Judge the song section from the analysis (beats, rises, quiet parts, loudness).
- No subject isolation, masks or rotoscoping: no cut-out afterimages or subject-only speed trails. Nearest: speed ramps, whips, warp, the beat camera, the bolt transition, and your own effects (ghost echoes of the whole frame with frame(), streaks, glows anchored near the subject).
- No automatic motion tracking: you place text, graphics and effects yourself. To follow movement, keyframe x/y (and scale) from where the subject is in the contact sheets.
- No footage beyond this project's media and the database items attached to it. If the notes name material that is not in MEDIA, say it is missing.
- One output: the timeline. Export, delivery and saving are the owner's step.`;

export interface ContextExtras {
  houseRules: string;
  benchmarks: string;
  /** The craft recipes, the set-piece playbook and how to work fast (with the house rules). */
  craft?: string;
  /** Worked examples of the approved edits, beat by beat (for the calls that direct or judge an edit). */
  exemplars?: string;
  /** How the critic will judge the edit (for the calls that direct it). */
  canon?: string;
  /** What the critic kept finding on recent edits. */
  lessons?: string;
  presetName: string;
  presetPrompt: string;
  standards: string;
  knowledge: string;
  checks?: string;
}

export function contextBlock(ctx: { project: Project; media: Record<string, MediaInfo>; order: string[] }, imageCaptions: string[], imageNote: string | undefined, x: ContextExtras): string {
  const p = ctx.project;
  return [
    'You are the editor inside VOIDFX Studio, a video editing app. You build and change the owner\'s edit by replying with operations that the studio applies to its timeline. You cannot watch or hear the media: the images and the sound analysis below are how you perceive it.',
    x.houseRules ? x.houseRules : '',
    x.benchmarks ? `THE OWNER'S STANDARDS (approved edits; match or exceed them, never copy their look)\n${x.benchmarks}` : '',
    x.exemplars || '',
    x.craft || '',
    x.canon ? `HOW THE EDIT WILL BE JUDGED (the critic scores every round against this; plan to score 8 or more in every area)\n${x.canon}` : '',
    x.lessons ? `LESSONS FROM THE CRITIC ON RECENT EDITS (its critical and major findings; make sure this edit does not repeat them)\n${x.lessons}` : '',
    x.standards ? `REFERENCE EDITS THE OWNER ADDED AS STANDARDS\n${x.standards}` : '',
    x.knowledge.trim() ? `STUDIO KNOWLEDGE (from the owner; follow it)\n${x.knowledge.trim()}` : '',
    x.presetPrompt.trim() ? `PRESET "${x.presetName}" (the standing brief for this edit)\n${x.presetPrompt.trim()}` : '',
    reference(p),
    STUDIO_LIMITS,
    `MEDIA\n${mediaCatalog(ctx.media, ctx.order)}`,
    imageNote ? `IMAGES\n${imageNote}` : imageCaptions.length ? `IMAGES (attached, in this order)\n${imageCaptions.map((c, i) => `${i + 1}. ${c}`).join('\n')}` : 'IMAGES: none attached.',
    `CURRENT TIMELINE\n${timelineJson(p)}`,
    x.checks ? `AUTOMATED CHECKPOINT (the studio's measurable gates on the current timeline)\n${x.checks}` : '',
  ].filter(Boolean).join('\n\n');
}

/** Parse one JSON value from a reply (whole text, a code fence, or the outermost braces). */
export function parseJson(text: string): any {
  const tryParse = (s: string) => { try { return JSON.parse(s); } catch { return undefined; } };
  let v = tryParse(text.trim());
  if (v === undefined) {
    const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fence) v = tryParse(fence[1]);
  }
  if (v === undefined) {
    const a = text.indexOf('{'), b = text.lastIndexOf('}');
    if (a >= 0 && b > a) v = tryParse(text.slice(a, b + 1));
  }
  return v;
}

/** Parse the JSON object Opus replies with. */
export function parseReply(text: string): { message: string; ops: unknown[] } | null {
  const tryParse = (s: string) => { try { return JSON.parse(s); } catch { return undefined; } };
  let v = tryParse(text.trim());
  if (v === undefined) {
    const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fence) v = tryParse(fence[1]);
  }
  if (v === undefined) {
    const a = text.indexOf('{'), b = text.lastIndexOf('}');
    if (a >= 0 && b > a) v = tryParse(text.slice(a, b + 1));
  }
  if (!v || typeof v !== 'object') return salvageOps(text);
  if (Array.isArray(v)) return { message: '', ops: v };
  return { message: typeof v.message === 'string' ? v.message : '', ops: Array.isArray(v.ops) ? v.ops : [] };
}

/**
 * A reply cut short mid-JSON (time or length limit): keep the message and every operation that was
 * written out completely, so a long build is not thrown away for its last half-written line.
 */
export function salvageOps(text: string): { message: string; ops: unknown[]; salvaged: true } | null {
  const k = text.indexOf('"ops"');
  if (k < 0) return null;
  const a = text.indexOf('[', k);
  if (a < 0) return null;
  const ops: unknown[] = [];
  let depth = 0, start = -1, inStr = false, esc = false;
  for (let i = a + 1; i < text.length; i++) {
    const ch = text[i];
    if (inStr) { if (esc) esc = false; else if (ch === '\\') esc = true; else if (ch === '"') inStr = false; continue; }
    if (ch === '"') { inStr = true; continue; }
    if (ch === '{') { if (depth === 0) start = i; depth++; }
    else if (ch === '}') {
      depth--;
      if (depth === 0 && start >= 0) { try { ops.push(JSON.parse(text.slice(start, i + 1))); } catch { /* skip a broken one */ } start = -1; }
    } else if (ch === ']' && depth === 0) break;
  }
  if (!ops.length) return null;
  const m = text.slice(0, k).match(/"message"\s*:\s*"((?:[^"\\]|\\.)*)"/);
  let message = '';
  if (m) { try { message = JSON.parse(`"${m[1]}"`); } catch { message = m[1]; } }
  return { message, ops, salvaged: true };
}
