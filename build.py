#!/usr/bin/env python3
"""shortforge build: plan.json -> final MP4 + descricoes.md + QA contact sheet.

usage:
  python build.py PLAN.json                 # full build
  python build.py PLAN.json --preview t1,t2 # 3D+2D stills only (fast check before the full render)
  python build.py PLAN.json --skip-3d       # reuse existing 3D frames (e.g. after editing only overlays/audio)
Outputs go to <plan dir>/<output_dir> (default "out"): video.mp4, descricoes.md, contact_sheet.jpg, clarity.json
"""
import os, sys, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30

def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-4000:]); raise SystemExit(f'failed: {" ".join(cmd[:3])}')
    return r.stdout

def chunks(total, k):
    return [(total * i // k, total * (i + 1) // k) for i in range(k)]

def captions_md(plan):
    c = plan.get('captions', {}); title = plan.get('title', 'Vídeo')
    order = [('tiktok', 'TikTok'), ('instagram', 'Instagram (Reels)'), ('youtube', 'YouTube Shorts'), ('kwai', 'Kwai'), ('facebook', 'Facebook (Reels)')]
    out = [f'# Descrições: {title}', '']
    for key, label in order:
        v = c.get(key)
        if not v: continue
        out.append(f'## {label}')
        if isinstance(v, dict):
            if v.get('title'): out += ['**Título:**', '```', v['title'], '```']
            if v.get('description'): out += ['**Descrição:**', '```', v['description'], '```']
        else:
            out += ['```', v, '```']
        out.append('')
    if c.get('pinned_comment'): out += ['## Comentário fixado (todas as plataformas)', '```', c['pinned_comment'], '```', '']
    if c.get('tips'): out += ['## Dicas de postagem'] + [f'- {x}' for x in c['tips']] + ['']
    return '\n'.join(out)

def main():
    plan_path = os.path.abspath(sys.argv[1]); base = os.path.dirname(plan_path); plan = json.load(open(plan_path))
    outdir = os.path.join(base, plan.get('output_dir', 'out')); os.makedirs(outdir, exist_ok=True)
    frames_dir = os.path.join(base, plan.get('frames_dir', 'build/f3d')); os.makedirs(frames_dir, exist_ok=True)
    total = int(round(plan['duration'] * FPS)); workers = max(1, min(6, os.cpu_count() or 2))
    r3d = os.path.join(HERE, 'world3d', 'render3d.js'); comp = os.path.join(HERE, 'compose.py')
    has3d = bool(plan.get('shots'))

    if '--preview' in sys.argv:
        ts = sys.argv[sys.argv.index('--preview') + 1]
        if has3d:
            run(['node', r3d, plan_path, frames_dir + '_preview', '--still', ts])
            # map stills to frame names so compose can use them
            for t in ts.split(','):
                n = int(round(float(t) * FPS)); src = os.path.join(frames_dir + '_preview', f's_{float(t):.2f}.jpg')
                os.replace(src, os.path.join(frames_dir, f'f_{n:05d}.jpg'))
        prev = os.path.join(outdir, 'preview'); run([sys.executable, comp, plan_path, 'still', prev] + ts.split(','))
        sheet(prev, os.path.join(outdir, 'preview_sheet.jpg')); print('preview:', os.path.join(outdir, 'preview_sheet.jpg')); return

    t0 = time.time()
    if has3d and '--skip-3d' not in sys.argv:
        print(f'[1/4] 3D: {total} frames, {workers} workers ...', flush=True)
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda ab: run(['node', r3d, plan_path, frames_dir, str(ab[0]), str(ab[1])]), chunks(total, workers)))
    print(f'[2/4] compose 2D layer ...', flush=True)
    segs = [os.path.join(outdir, f'_seg{i}.mp4') for i in range(workers)]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda i_ab: run([sys.executable, comp, plan_path, 'range', str(i_ab[1][0]), str(i_ab[1][1]), segs[i_ab[0]]]), enumerate(chunks(total, workers))))
    print('[3/4] audio mix ...', flush=True)
    wav = os.path.join(outdir, '_mix.wav')
    rep = json.loads(run([sys.executable, os.path.join(HERE, 'audio_mix.py'), plan_path, wav]).strip().splitlines()[-1])
    json.dump(rep, open(os.path.join(outdir, 'clarity.json'), 'w'), indent=1)
    print('[4/4] mux + descriptions + QA ...', flush=True)
    lst = os.path.join(outdir, '_list.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
    final = os.path.join(outdir, plan.get('output_name', 'video') + '.mp4')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-movflags', '+faststart', '-shortest', final])
    open(os.path.join(outdir, 'descricoes.md'), 'w').write(captions_md(plan))
    qa_times = [round(sc['start'] + 0.6, 2) for sc in plan['scenes']]
    qa = os.path.join(outdir, '_qa'); os.makedirs(qa, exist_ok=True)
    for t in qa_times:
        run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(t), '-i', final, '-frames:v', '1', '-vf', 'scale=270:480', os.path.join(qa, f'q_{t:06.2f}.jpg')])
    sheet(qa, os.path.join(outdir, 'contact_sheet.jpg'))
    import shutil; shutil.rmtree(qa, ignore_errors=True)
    for s in segs + [lst, wav]:
        try: os.remove(s)
        except OSError: pass
    print(json.dumps({'video': final, 'descriptions': os.path.join(outdir, 'descricoes.md'), 'contact_sheet': os.path.join(outdir, 'contact_sheet.jpg'),
                      'clarity': rep, 'seconds': round(time.time() - t0)}))

def sheet(folder, out):
    from PIL import Image
    fs = sorted(f for f in os.listdir(folder) if f.endswith('.jpg'))
    if not fs: return
    ims = [Image.open(os.path.join(folder, f)).resize((270, 480)) for f in fs]; cols = min(8, len(ims)); rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (270 * cols, 480 * rows))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sh.save(out, quality=85)

if __name__ == '__main__':
    main()
