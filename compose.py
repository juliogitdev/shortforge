#!/usr/bin/env python3
"""Compose final frames: background (3D frame / neon / dark / image) + 2D overlays + subtitles + shakes/flashes.

usage:
  python compose.py PLAN.json still OUTDIR t1 t2 ...      # preview stills
  python compose.py PLAN.json range START END OUT.mp4     # render frame range (frame numbers)
See references/plan-schema.md for the overlay vocabulary.
"""
import os, sys, json, math, subprocess
from PIL import Image, ImageDraw, ImageFilter
import engine2d as E
from engine2d import W, H, FPS, put, txt, badge, pop, slam, lerp, clamp, eo, back, col, tint

PLAN = None; BASE = '.'; SUBS = None

def P(path):  # resolve plan-relative paths
    return path if os.path.isabs(path) else os.path.join(BASE, path)

# ------------------------------------------------------------------ backgrounds
def background(scene, T, t):
    bg = scene.get('bg', '3d')
    if bg == '3d':
        n = min(int(round(T * FPS)), PLAN['_frames'] - 1)
        fr = Image.open(os.path.join(P(PLAN.get('frames_dir', 'build/f3d')), f'f_{n:05d}.jpg')).convert('RGBA')
        if scene.get('blur'): fr = fr.filter(ImageFilter.GaussianBlur(scene['blur']))
        return fr
    if bg == 'neon':
        s = 1 + 0.012 * T; im = E.neon_bg(); cw, ch = W / s, H / s
        return im.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BILINEAR)
    if bg.startswith('dark'):
        return E.dark_bg(bg.split(':')[1] if ':' in bg else 'purple').copy()
    if bg.startswith('image:') or bg.startswith('blur:'):
        kind, path = bg.split(':', 1)
        im = E.image_bg(P(path), blur=8 if kind == 'blur' else 0, dark=150 if kind == 'blur' else 100, focus=tuple(scene.get('focus', (0.5, 0.4))))
        if kind == 'image':
            s = 1 + 0.02 * t; cw, ch = W / s, H / s
            return im.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BILINEAR)
        return im.copy()
    raise ValueError('unknown bg ' + bg)

# ------------------------------------------------------------------ overlays
def scale_in(o, t):
    at = o.get('at', 0.0)
    if t < at: return 0
    if o.get('until') is not None and t > o['until']: return 0
    return slam(t, at) if o.get('slam') else pop(t, at)

def ov_text(fr, o, t, T):
    s = scale_in(o, t)
    put(fr, txt(o['text'], o.get('size', 120), col(o.get('color'), E.WHITE), o.get('stroke', 12), col(o.get('stroke_color'), E.BLACK)),
        o.get('x', W / 2), o.get('y', 300) + o.get('bob', 0) * math.sin(t * 5), s, rot=o.get('rot', 0))

def ov_badge(fr, o, t, T):
    put(fr, badge(o['text'], o.get('size', 70), col(o.get('bg'), E.YEL), col(o.get('fg'), E.BLACK)), o.get('x', W / 2), o.get('y', 250),
        scale_in(o, t), rot=o.get('rot', 0))

def ov_counter(fr, o, t, T):
    at = o.get('at', 0)
    if t < at: return
    v = o.get('from', 0) + (o['to'] - o.get('from', 0)) * eo(clamp((t - at) / o.get('dur', 1.2)))
    s = f"{int(v):,}".replace(',', o.get('sep', '.'))
    put(fr, txt(o.get('prefix', '') + s + o.get('suffix', ''), o.get('size', 170), col(o.get('color'), (120, 255, 150)), 16, (10, 40, 20)),
        o.get('x', W / 2), o.get('y', 400), pop(t, at), rot=o.get('rot', -3))

def ov_card(fr, o, t, T):
    if t < o.get('at', 0): return
    c = E.card(P(o['image']), o.get('w', 820), o.get('h', 1000), col(o.get('border'), E.WHITE), z=1 + o.get('zoom', 0.03) * t,
               gray=o.get('gray', False), focus=tuple(o.get('focus', (0.5, 0.3))))
    put(fr, c, o.get('x', W / 2), o.get('y', 820), lerp(0.85, 1.0, back((t - o.get('at', 0)) / 0.3)), rot=o.get('rot', 0))
    if o.get('credit'):
        put(fr, txt(o['credit'], 30, (220, 220, 230), 4, E.BLACK, w='bold'), W / 2, o.get('y', 820) + o.get('h', 1000) / 2 + 50)

def ov_phone(fr, o, t, T):
    if t < o.get('at', 0): return
    after = o.get('after')
    status, sc = (o['status_after'], E.RED) if after is not None and t >= after else (o.get('status', 'chamando...'), (180, 180, 200))
    im = E.phone(o.get('title', 'Cliente'), status, sc, ring=o.get('ring', True) and (after is None or t < after), t=t)
    put(fr, im, o.get('x', 820), o.get('y', 760), o.get('scale', 0.55) * lerp(0.7, 1.0, back((t - o.get('at', 0)) / 0.3)), rot=o.get('rot', 6))

def ov_timer(fr, o, t, T):
    total = o.get('seconds', 10); left = total - (T - o['start_abs']) * o.get('speed', 0.75)
    E.timer_ring(fr, o.get('x', W / 2), o.get('y', 1080), max(0, left), total, o.get('r', 170))

def ov_choice(fr, o, t, T):
    a = o['a'].split('|') + ['']; b = o['b'].split('|') + ['']
    put(fr, E.choice_card('A', a[0], a[1], col(o.get('a_color'), (220, 160, 0))), 285, o.get('y', 900), pop(t, o.get('at', 0)), rot=-3)
    if t > o.get('at_b', 1.8):
        put(fr, E.choice_card('B', b[0], b[1], col(o.get('b_color'), (30, 90, 220))), 795, o.get('y', 900), pop(t, o.get('at_b', 1.8)), rot=3)

def ov_bubbles(fr, o, t, T):
    for i, it in enumerate(o['items']):
        text, user, c, at = it[0], it[1], col(it[2]), it[3]
        b = E.bubble(text, user, c); x = 70 + b.width / 2 if i % 2 == 0 else W - 70 - b.width / 2
        put(fr, b, x, o.get('y0', 650) + i * 175, pop(t, at))

def ov_endcard(fr, o, t, T):
    at = o.get('at', 0)
    if t < at: return
    k = t - at; tint(fr, (10, 0, 30, int(220 * clamp(k / 0.3))))
    if o.get('mascot', True): put(fr, E.mascot(), W / 2, 1000, 0.8 * lerp(0.5, 1.0, back(k / 0.35)))
    for i, line in enumerate(o.get('lines', [])):
        put(fr, badge(line, 84 if i == 0 else 68, E.YEL if i == 0 else E.PINK, E.BLACK if i == 0 else E.WHITE), W / 2, 300 + i * 150, pop(k, 0.1 + 0.2 * i))

def ov_tint(fr, o, t, T):
    if t < o.get('at', 0) or (o.get('until') is not None and t > o['until']): return
    c = list(o.get('color', [255, 0, 30, 40]))
    if o.get('pulse'):
        p = (math.sin(t * 2 * math.pi * (1.2 + t * 0.35)) + 1) / 2; c[3] = int(c[3] * (0.4 + 0.6 * p))
    if o.get('blink'): c[3] = c[3] if int(t * 8) % 2 else c[3] // 3
    if o.get('flash'): c[3] = int(c[3] * clamp(1 - (t - o.get('at', 0)) / 0.15))
    tint(fr, c)

def ov_vignette(fr, o, t, T): E.vignette(fr, o.get('strength', 1.2))

def ov_progress(fr, o, t, T):
    if t < o.get('at', 0): return
    d = ImageDraw.Draw(fr); p = o.get('to', 0.6) * eo(clamp((t - o.get('at', 0)) / o.get('dur', 1.6))); y = o.get('y', 440)
    d.rounded_rectangle((120, y - 40, 960, y + 40), 40, fill=(30, 20, 60)); d.rounded_rectangle((120, y - 40, 120 + 840 * p, y + 40), 40, fill=col(o.get('color'), E.GREEN))
    put(fr, txt(o.get('label', '{p}%').replace('{p}', str(int(p * 100))), 50, E.WHITE, 6), W / 2, y)

def ov_calendar(fr, o, t, T):
    if t < o.get('at', 0): return
    put(fr, E.calendar(o['month'], o['day'], o.get('year', '')), W / 2, o.get('y', 820), lerp(0.7, 1.0, back((t - o.get('at', 0)) / 0.3)))
    d = ImageDraw.Draw(fr); y = o.get('y', 820)
    if o.get('cross_at') is not None and t > o['cross_at']:
        p = clamp((t - o['cross_at']) / 0.35); d.line((300, y - 260, lerp(300, 780, p), lerp(y - 260, y + 260, p)), fill=E.RED, width=40)
        p2 = clamp((t - o['cross_at'] - 0.35) / 0.35)
        if p2 > 0: d.line((780, y - 260, lerp(780, 300, p2), lerp(y - 260, y + 260, p2)), fill=E.RED, width=40)
    if o.get('circle_at') is not None and t > o['circle_at']:
        p = clamp((t - o['circle_at']) / 0.8); d.arc((330, y - 200, 750, y + 260), -90, -90 + 360 * p, fill=E.YEL, width=22)

def ov_image(fr, o, t, T):  # free image (logo, sticker)
    if t < o.get('at', 0): return
    im = E.load_image(P(o['image'])); s = o.get('w', 400) / im.width
    put(fr, im, o.get('x', W / 2), o.get('y', 800), s * pop(t, o.get('at', 0)), rot=o.get('rot', 0))

def ov_mascot(fr, o, t, T):
    put(fr, E.mascot(), o.get('x', W / 2), o.get('y', 920) + 18 * math.sin(t * 7), o.get('scale', 0.9) * lerp(0.6, 1.0, back((t - o.get('at', 0)) / 0.3)))

OVERLAYS = {'text': ov_text, 'badge': ov_badge, 'counter': ov_counter, 'card': ov_card, 'phone': ov_phone, 'timer': ov_timer,
            'choice': ov_choice, 'bubbles': ov_bubbles, 'endcard': ov_endcard, 'tint': ov_tint, 'vignette': ov_vignette,
            'progress': ov_progress, 'calendar': ov_calendar, 'image': ov_image, 'mascot': ov_mascot}

# ------------------------------------------------------------------ frame
def frame(T):
    scenes = PLAN['scenes']
    for i, sc in enumerate(scenes):
        end = scenes[i + 1]['start'] if i + 1 < len(scenes) else PLAN['duration'] + 1
        if sc['start'] <= T < end: break
    t = T - sc['start']
    fr = background(sc, T, t)
    for o in sc.get('overlays', []):
        OVERLAYS[o['type']](fr, o, t, T)
    hud = PLAN.get('hud')
    if hud: put(fr, badge(hud, 34, E.YEL), 60 + badge(hud, 34, E.YEL).width / 2, 110)
    SUBS.draw(fr, T)
    dx = dy = 0
    for st, amp in PLAN.get('shakes', []):
        k = T - st
        if 0 <= k < 0.35:
            e = amp * (1 - k / 0.35); dx += e * math.sin(k * 90); dy += e * math.cos(k * 75)
    if dx or dy:
        f2 = Image.new('RGBA', (W, H), E.BLACK); f2.alpha_composite(fr.resize((int(W * 1.04), int(H * 1.04))), (int(-W * 0.02 + dx), int(-H * 0.02 + dy))); fr = f2
    for st in PLAN.get('flashes', [sc_['start'] for sc_ in scenes[1:] if sc_.get('flash', False)]):
        k = T - st
        if 0 <= k < 0.1: tint(fr, (255, 255, 255, int(200 * (1 - k / 0.1))))
    return fr.convert('RGB')

def load(path):
    global PLAN, BASE, SUBS
    PLAN = json.load(open(path)); BASE = os.path.dirname(os.path.abspath(path))
    PLAN['_frames'] = int(round(PLAN['duration'] * FPS))
    SUBS = E.Subtitles(PLAN.get('subs', []), PLAN.get('highlights', {}), PLAN.get('subs_y', 1470))

if __name__ == '__main__':
    load(sys.argv[1]); mode = sys.argv[2]
    if mode == 'still':
        os.makedirs(sys.argv[3], exist_ok=True)
        for tt in sys.argv[4:]: frame(float(tt)).save(os.path.join(sys.argv[3], f'c_{float(tt):06.2f}.jpg'), quality=85)
    else:
        a, b, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for n in range(a, b): p.stdin.write(frame(n / FPS).tobytes())
        p.stdin.close(); p.wait()
