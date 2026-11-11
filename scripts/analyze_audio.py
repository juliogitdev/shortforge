#!/usr/bin/env python3
"""Find speech segments in a narration file (silence detection) so subtitles and cuts can be timed to the voice.

usage: python analyze_audio.py narration.mp3 [--min-silence 0.18] [--noise -32]
prints JSON: {"duration": s, "segments": [[start, end], ...]}
Match each segment to the script sentences in order (long sentences may span 2 segments, short words may be their own).
"""
import sys, json, re, subprocess
path = sys.argv[1]
ms = float(sys.argv[sys.argv.index('--min-silence') + 1]) if '--min-silence' in sys.argv else 0.18
nz = sys.argv[sys.argv.index('--noise') + 1] if '--noise' in sys.argv else '-32'
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout)
log = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', f'silencedetect=noise={nz}dB:d={ms}', '-f', 'null', '-'], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', log)]; ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', log)]
segs, cur = [], 0.0
for s, e in zip(starts, ends + [dur] * (len(starts) - len(ends))):
    if s - cur > 0.08: segs.append([round(cur, 2), round(s, 2)])
    cur = e
if dur - cur > 0.08: segs.append([round(cur, 2), round(dur, 2)])
print(json.dumps({'duration': round(dur, 2), 'segments': segs}))
