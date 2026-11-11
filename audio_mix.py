#!/usr/bin/env python3
"""shortforge audio: original music (by mood) + synthesized SFX library + narration, with a sidechain that keeps
the narrator at least 15 dB above everything else while speaking.

usage: python audio_mix.py PLAN.json OUT.wav
Prints a clarity report (voice vs background, in dB). See references/plan-schema.md ("audio").
"""
import os, sys, json, subprocess
import numpy as np

SR = 44100
rng = np.random.default_rng(3)

def tt(d): return np.arange(int(round(d * SR))) / SR
def lp(x, a):
    y = np.empty_like(x); acc = 0.0; a = np.broadcast_to(np.asarray(a, dtype=float), x.shape)
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def hp(x, a): return x - lp(x, a)
def noise(d): return rng.uniform(-1, 1, int(round(d * SR)))
def norm(x, p=1.0): m = np.max(np.abs(x)) if len(x) else 1; return x / (m or 1) * p

# ---------------------------------------------------------------- SFX library
def whoosh(d=0.45, up=True):
    t = tt(d); env = np.sin(np.pi * t / d) ** 2; a = np.linspace(0.02, 0.35, len(t)) if up else np.linspace(0.35, 0.02, len(t))
    return norm(lp(noise(d), a) * env, 0.8)
def boom(d=1.0, f0=70, f1=32):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t * 5); ph = 2 * np.pi * np.cumsum(f) / SR
    return norm(np.sin(ph) * np.exp(-t * 3.2) + 0.25 * lp(noise(d), 0.05) * np.exp(-t * 6), 1.0)
def impact():
    b = boom(0.7, 110, 40); c = hp(noise(0.05), 0.3) * np.linspace(1, 0, int(round(0.05 * SR))); b[:len(c)] += 0.5 * c; return norm(b, 1.0)
def stamp():
    b = boom(0.5, 90, 45); return norm(b + 0.4 * lp(noise(len(b) / SR), 0.2) * np.exp(-np.arange(len(b)) / SR * 18), 1.0)
def pop():
    t = tt(0.09); f = np.linspace(380, 950, len(t)); return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30), 0.6)
def ding():
    t = tt(0.8); return norm((np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 5), 0.5)
def tick(hi=True):
    t = tt(0.04); return norm(np.sin(2 * np.pi * (2200 if hi else 1500) * t) * np.exp(-t * 150), 0.5)
def scribble(d=0.45):
    t = tt(d); env = (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)) * np.sin(np.pi * t / d); return norm(hp(lp(noise(d), 0.45), 0.15) * env, 0.35)
def siren(d=3.0):
    t = tt(d); f = 780 + 170 * np.sin(2 * np.pi * 1.6 * t); ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.6); return norm((np.sign(np.sin(ph)) * 0.3 + np.sin(ph) * 0.7) * env, 0.35)
def engine(d=3.0):
    t = tt(d); f = 60 + 25 * t / d; ph = 2 * np.pi * np.cumsum(f) / SR; saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    return norm(lp(saw * (0.7 + 0.3 * np.sin(2 * np.pi * 18 * t)), 0.12) * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.5), 0.5)
def crack():
    d = 0.45; out = np.zeros(int(d * SR))
    for k in range(7):
        st = int(rng.uniform(0, 0.25) * SR); L = int(0.03 * SR)
        out[st:st + L] += hp(noise(L / SR), 0.6)[:L] * np.exp(-np.arange(L) / SR * 120) * rng.uniform(0.5, 1)
    b = boom(d, 120, 60); L = min(len(b), len(out)); out[:L] += 0.4 * b[:L]; return norm(out, 0.9)
def riser(d=1.6):
    t = tt(d); a = np.linspace(0.01, 0.5, len(t)); f = 200 + 900 * (t / d) ** 2
    return norm(lp(noise(d), a) * (t / d) ** 2 + 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2, 0.7)
def heartbeat(d=4.6):
    n = int(d * SR); out = np.zeros(n); beat = boom(0.22, 75, 40); t = 0.0
    while t < d:
        per = 0.9 - 0.55 * (t / d)
        for off, g in ((0, 1.0), (0.18, 0.7)):
            i = int((t + off) * SR); L = min(len(beat), n - i)
            if L > 0: out[i:i + L] += beat[:L] * g * (0.5 + 0.5 * t / d)
        t += per
    return norm(out, 1.0)
def ringback(d=1.4): t = tt(d); return norm(np.sin(2 * np.pi * 425 * t) * ((t % 1.0) < 0.6) * 0.5, 0.35)
def voicemail(): t = tt(0.5); return norm(np.sin(2 * np.pi * 1000 * t) * (t < 0.45), 0.4)
def tape(d=0.6):
    t = tt(d); return norm(hp(noise(d), 0.3) * np.minimum(1, t / 0.05) * np.exp(-t * 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 40 * t)), 0.7)
def cash():
    t = tt(0.9); bell = (np.sin(2 * np.pi * 2093 * t) + 0.6 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 5)
    ch = np.zeros_like(t); L = int(0.12 * SR); ch[:L] = hp(noise(0.12), 0.4)[:L] * np.linspace(1, 0, L); return norm(bell + ch, 0.8)
def vibrate(d=3.0): t = tt(d); return norm(lp(np.sign(np.sin(2 * np.pi * 150 * t)) * ((t % 0.8) < 0.5), 0.2), 0.5)
def ringtone(d=3.0):
    t = tt(d); notes = [1318.5, 1568, 1975.5, 1568]; out = np.zeros_like(t)
    for i in range(int(d / 0.15)):
        if (i // 8) % 2 == 1: continue
        a = int(i * 0.15 * SR); L = int(0.13 * SR); seg = np.sin(2 * np.pi * notes[i % 4] * np.arange(L) / SR) * np.exp(-np.arange(L) / SR * 18)
        out[a:a + L] += seg[:max(0, min(L, len(out) - a))]
    return norm(out, 0.45)
def crickets(d=3.0): t = tt(d); return norm(np.sin(2 * np.pi * 4300 * t) * ((np.sin(2 * np.pi * 18 * t) > 0.3) * ((t % 0.9) < 0.35)), 0.2)
def rewind(d=2.0):
    t = tt(d); f = 900 * np.exp(-t * 1.2) + 120; ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)); return norm(lp(s, 0.25) * np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.3), 0.5)
def drumroll(d=2.0):
    n = int(d * SR); out = np.zeros(n); sn = hp(noise(0.06), 0.25) * np.exp(-tt(0.06) * 60); k = 0.0
    while k < d:
        i = int(k * SR); L = min(len(sn), n - i); out[i:i + L] += sn[:L] * (0.4 + 0.6 * k / d); k += 0.06 - 0.03 * k / d
    return norm(out, 0.8)
def thunder(d=1.6):
    t = tt(d); env = np.exp(-t * 2.2) * (0.6 + 0.4 * np.sin(t * 23) ** 2); x = lp(noise(d), 0.04)[:len(env)] * env
    b = boom(d, 60, 30); L = min(len(x), len(b)); x[:L] += 0.6 * b[:L]; return norm(x, 1.0)
def clank():
    t = tt(0.6); s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in [(523, 7), (1187, 9), (1720, 12), (2390, 15), (3100, 20)])
    s[:300] += hp(noise(300 / SR), 0.5)[:300]; return norm(s, 0.8)
def rain(d): return norm(hp(lp(noise(d), 0.5), 0.05) * 0.4 + lp(noise(d), 0.02) * 0.6, 0.5)

SFX = {'whoosh': lambda d=None: whoosh(d or 0.4), 'whoosh_down': lambda d=None: whoosh(d or 0.5, False), 'boom': lambda d=None: boom(d or 1.0),
       'boom_deep': lambda d=None: boom(d or 1.6, 55, 26), 'impact': lambda d=None: impact(), 'stamp': lambda d=None: stamp(), 'pop': lambda d=None: pop(),
       'ding': lambda d=None: ding(), 'tick': lambda d=None: tick(True), 'tock': lambda d=None: tick(False), 'scribble': lambda d=None: scribble(d or 0.45),
       'siren': lambda d=None: siren(d or 3.0), 'engine': lambda d=None: engine(d or 3.0), 'crack': lambda d=None: crack(), 'riser': lambda d=None: riser(d or 1.6),
       'heartbeat': lambda d=None: heartbeat(d or 4.6), 'ringback': lambda d=None: ringback(d or 1.4), 'voicemail': lambda d=None: voicemail(),
       'tape': lambda d=None: tape(d or 0.6), 'cash': lambda d=None: cash(), 'vibrate': lambda d=None: vibrate(d or 3.0), 'ringtone': lambda d=None: ringtone(d or 3.0),
       'crickets': lambda d=None: crickets(d or 3.0), 'rewind': lambda d=None: rewind(d or 2.0), 'drumroll': lambda d=None: drumroll(d or 2.0),
       'thunder': lambda d=None: thunder(d or 1.6), 'clank': lambda d=None: clank()}

# ---------------------------------------------------------------- music
def music(mood, dur, levels=None):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    def add(sig, t0, g=1.0):
        i = int(t0 * SR)
        if i < n: L = min(len(sig), n - i); out[i:i + L] += sig[:L] * g
    kick = boom(0.32, 150, 45); snare = norm(hp(noise(0.2), 0.25) * np.exp(-tt(0.2) * 18) + 0.4 * np.sin(2 * np.pi * 190 * tt(0.2)) * np.exp(-tt(0.2) * 25), 1)
    hat = norm(hp(noise(0.05), 0.7) * np.exp(-tt(0.05) * 90), 1)
    if mood in ('synthwave', 'upbeat'):
        beat = 0.6 if mood == 'synthwave' else 0.5; st = beat / 4
        chords = [(110.0, [220.0, 261.63, 329.63]), (87.31, [174.61, 220.0, 261.63]), (130.81, [261.63, 329.63, 392.0]), (98.0, [196.0, 246.94, 293.66])]
        bar, t0 = 0, 0.0
        while t0 < dur:
            root, tri = chords[bar % 4]
            for s in range(16):
                ts = t0 + s * st
                if s % 4 == 0: add(kick, ts, 0.9)
                if s in (4, 12): add(snare, ts, 0.45)
                if s % 2 == 0: add(hat, ts, 0.1)
                if s % 2 == 0:
                    tb = tt(st * 1.8); saw = 2 * ((root * tb) % 1) - 1; add(lp(saw, 0.12) * np.exp(-tb * 6), ts, 0.55)
                ta = tt(st * 0.9); add(np.sign(np.sin(2 * np.pi * tri[s % 3] * (2 if (s // 3) % 2 else 1) * ta)) * 0.5 * np.exp(-ta * 14), ts, 0.07)
            tp = tt(beat * 4); add(sum(np.sin(2 * np.pi * f * tp) for f in tri) * np.minimum(1, tp / 0.4) * np.minimum(1, (beat * 4 - tp) / 0.3), t0, 0.06)
            bar += 1; t0 += beat * 4
    elif mood in ('tension', 'heist'):
        drone = lp(sum(np.sin(2 * np.pi * f * t + np.sin(t * 0.3 + f)) for f in (55, 82.4, 110, 130.8)) / 4, 0.05); out += drone * 0.5
        for k in np.arange(0, dur, 0.3):
            L = int(0.25 * SR); add(np.sin(2 * np.pi * 55 * np.arange(L) / SR) * np.exp(-np.arange(L) / SR * 9), k, 0.6)
            if mood == 'heist' and int(round(k / 0.3)) % 2 == 0: add(kick, k, 0.5)
            add(hat, k, 0.08)
    elif mood == 'none':
        return out
    out = norm(lp(out, 0.35), 1.0)
    if levels:  # [[t, level], ...]
        out *= np.interp(t, [p[0] for p in levels], [p[1] for p in levels])
    return out

# ---------------------------------------------------------------- mix
def load_audio(path, n=None):
    b = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(b, dtype=np.float32).astype(float)
    if n is not None:
        y = np.zeros(n); y[:min(n, len(x))] = x[:n]; return y
    return x

def mix(plan, base, out):
    A = plan.get('audio', {}); dur = plan['duration']; n = int(dur * SR); t = np.arange(n) / SR
    v = load_audio(os.path.join(base, A['narration']), n)
    venv = lp(np.abs(v), 0.002); vpk = np.max(venv) or 1
    v = v * lp(np.clip((vpk * 0.55) / np.maximum(venv, vpk * 0.08), 0.8, 2.2), 0.0005)   # gentle leveling
    v = v + 0.35 * hp(v, 0.25)                                                             # presence
    mu = A.get('music', {'mood': 'tension'})
    m = music(mu.get('mood', 'tension'), dur, mu.get('levels'))
    for a, b in mu.get('silence', []): m[(t >= a) & (t < b)] *= 0.05
    if mu.get('file'): m = norm(load_audio(os.path.join(base, mu['file']), n), 1.0)
    amb = np.zeros(n)
    for a_ in A.get('ambience', []):
        if a_['type'] == 'rain':
            r = rain(a_['to'] - a_['from']); i = int(a_['from'] * SR); L = min(len(r), n - i); amb[i:i + L] += r[:L] * a_.get('gain', 1.0)
    fx = np.zeros(n)
    for e in A.get('sfx', []):
        tm, name, g = e[0], e[1], (e[2] if len(e) > 2 else 0.6); d = e[3] if len(e) > 3 else None
        s = SFX[name](d); i = int(tm * SR); L = min(len(s), n - i)
        if L > 0: fx[i:i + L] += s[:L] * g
    fade = np.minimum(1, t / 0.1) * np.minimum(1, (dur - t) / 1.2)
    bgd = m * mu.get('gain', 0.18) * fade + amb * 0.07 + fx * A.get('sfx_gain', 0.30)
    # sidechain: background >= 15 dB under the voice while talking (anticipates each phrase by 0.25 s)
    win = int(0.03 * SR); k = np.ones(win) / win
    ve = np.sqrt(np.convolve(v * v, k, mode='same') + 1e-12); be = np.sqrt(np.convolve(bgd * bgd, k, mode='same') + 1e-12)
    talking = lp((ve > np.max(ve) * 0.03).astype(float), 0.002)
    g = 1 - talking * (1 - np.minimum(1.0, (ve * 10 ** (-A.get('voice_margin_db', 15) / 20) + 1e-4) / be))
    step = int(0.01 * SR)
    g = np.minimum.reduce([np.roll(g, s) for s in range(-int(0.08 * SR), int(0.25 * SR), step)])
    g = lp(g, 0.002); bg_final = bgd * g
    res = v + bg_final; res = norm(np.tanh(res * 1.05) / np.tanh(1.05), 0.95)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-ac', '2', out], stdin=subprocess.PIPE)
    p.stdin.write(res.astype(np.float32).tobytes()); p.stdin.close(); p.wait()
    # clarity report
    w = SR // 4; rs = []; low = []
    for i in range(0, n - w, w):
        a = v[i:i + w]
        if np.sqrt(np.mean(a ** 2)) < 0.03: continue
        r = 20 * np.log10(np.sqrt(np.mean(a ** 2)) / max(1e-7, np.sqrt(np.mean(bg_final[i:i + w] ** 2)))); rs.append(r)
        if r < 10: low.append(round(i / SR, 2))
    rs = np.array(rs) if rs else np.array([99.0])
    rep = {'voice_over_background_db_mean': round(float(rs.mean()), 1), 'worst_db': round(float(rs.min()), 1), 'windows_below_10db': low}
    print(json.dumps(rep)); return rep

if __name__ == '__main__':
    plan_path = sys.argv[1]; plan = json.load(open(plan_path))
    mix(plan, os.path.dirname(os.path.abspath(plan_path)), sys.argv[2])
