#!/usr/bin/env python3
"""Mix voice + music + SFX for an episode from build/audio_plan.json (numpy, 48 kHz stereo).

usage: mix.py <episode_dir> <out.wav>
Brand (CLAUDE.md §6): voice -16 LUFS / -1.5 dBTP; music under voice -24..-26 LUFS with 8-10 dB ducking
(attack 150 ms, release 400 ms); SFX peaks -18 dB (transitions) / -14 dB (impacts); silences respected.
"""
import json, os, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt

EP, OUT = sys.argv[1], sys.argv[2]
SR = 48000
plan = json.load(open(f'{EP}/build/audio_plan.json'))
N = int(plan['duration'] * SR)
UP = '/root/.claude/uploads/77444345-a615-5688-a3fa-bc71d6bb52c1'
DRIVE2 = '/tmp/claude-0/-home-user-firas/77444345-a615-5688-a3fa-bc71d6bb52c1/scratchpad/downloads/drive-folder-2/majed-video-ad-editor/studio/sfx_prev'
man = {m['id']: m['path'] for m in json.load(open(f'{EP}/build/sfx/manifest.json'))}
COM = f'{EP}/build/sfx/commons'

def load(path, mono=False):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1' if mono else '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return x if mono else x.reshape(-1, 2)

def lufs(x):
    p = '/tmp/_lufs.wav'
    import soundfile as sf
    sf.write(p, x, SR, subtype='FLOAT')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    import re
    v = re.findall(r'I:\s+(-?[\d.]+) LUFS', r)
    return float(v[-1]) if v else -70.0

def lowpass(x, hz):
    sos = butter(4, hz, 'low', fs=SR, output='sos'); return sosfilt(sos, x, axis=0).astype(np.float32)

def fade(x, fin, fout):
    n = len(x)
    if fin > 0:
        k = min(n, int(fin * SR)); x[:k] *= np.linspace(0, 1, k, dtype=np.float32)[:, None]
    if fout > 0:
        k = min(n, int(fout * SR)); x[n - k:] *= np.linspace(1, 0, k, dtype=np.float32)[:, None]
    return x

def peak_norm(x, db):
    pk = np.abs(x).max() + 1e-9
    return x * (10 ** (db / 20) / pk)

# ---- SFX library: name -> (source, offset, duration, options)
LIB = {
    'impact_low':  (man['A-2'], 0.0, 3.0, {'lp': 3000}),
    'impact_mid':  (man['K-72'], 0.0, 2.0, {}),
    'impact_big':  (man['A-1'], 0.0, 3.5, {}),
    'gravel':      (man['F-3'], 1.0, 2.6, {'lp': 900}),
    'rumble':      (man['F-1'], 0.0, 2.4, {'lp': 500}),
    'collapse':    (man['F-1'], 0.0, 2.6, {'lp': 900, 'layer': (man['A-11'], 0.0, 2.6)}),
    'whoosh_soft': (man['C-16'], 0.0, 1.6, {}),
    'whoosh_down': (man['C-12'], 0.0, 1.6, {}),
    'whoosh_up':   (man['C-16'], 0.0, 1.6, {}),
    'wind':        (f'{COM}/Howling_wind.ogg', 2.0, 6.0, {'lp': 2500}),
    'riser':       (man['M-18'], None, None, {'align_end': True}),
    'pop':         (man['D-2'], 0.0, 0.8, {}),
    'hit':         (man['K-35'], 0.0, 0.6, {}),
    'thud':        (man['K-39'], 0.0, 0.5, {}),
    'shutter':     (man['J-16'], 0.0, 0.3, {}),
    'tick':        (man['unnamed3'], 0.0, 2.4, {}),
    'paper':       (f'{COM}/Food_wrapper_crumpling.ogg', 0.4, 1.2, {}),
    'clang':       (man['K-11'], 0.0, 2.6, {}),
    'cheer':       (f'{COM}/Slow_starting_applause.ogg', 0.0, 12.0, {'layer': (f'{COM}/Applause_i.ogg', 0.0, 12.0)}),
    'crowd_murmur': (f'{COM}/Applause_i.ogg', 4.0, 4.0, {'lp': 1800}),
    'drill':       (man['A-3'], 1.0, 6.0, {'lp': 400}),          # low machinery hum (owner library)
    'winch':       (man['A-4'], 0.5, 9.0, {'lp': 500}),          # low mechanical rumble under the winch shots
}

sfx_bus = np.zeros((N, 2), np.float32)
missing = []
for ev in plan['sfx']:
    name = ev['name']
    if name not in LIB:
        missing.append(name); continue
    src, off, dur, opt = LIB[name]
    if not os.path.exists(src):
        missing.append(f'{name} ({os.path.basename(src)})'); continue
    x = load(src)
    want = ev.get('dur', dur)
    if opt.get('align_end'):              # risers: take the last `want` seconds so the peak lands at at+want
        want = ev.get('dur', 2.0); x = x[-int(want * SR):]
    else:
        x = x[int((off or 0) * SR):int(((off or 0) + want) * SR)]
    if 'layer' in opt:
        s2, o2, d2 = opt['layer']
        y = load(s2)[int(o2 * SR):int((o2 + want) * SR)]
        m = min(len(x), len(y)); x = x[:m] * 0.8 + y[:m] * 0.6
    if opt.get('lp'): x = lowpass(x, opt['lp'])
    x = fade(x.copy(), 0.01, ev.get('fade', min(0.25, len(x) / SR / 3)))
    x = peak_norm(x, ev['gain'])
    if 'ramp' in ev:                       # level ramp in dB across the clip
        r = np.linspace(ev['ramp'][0] - ev['gain'], ev['ramp'][1] - ev['gain'], len(x), dtype=np.float32)
        x *= (10 ** (r / 20))[:, None]
    i0 = int(ev['at'] * SR); i1 = min(N, i0 + len(x))
    if i0 < N: sfx_bus[i0:i1] += x[:i1 - i0]

# ---- music
music_bus = np.zeros((N, 2), np.float32)
for seg in plan['music']:
    x = load(f"{EP}/{seg['file']}")
    L = seg['end'] - seg['start']
    y = x[int(seg['offset'] * SR):int((seg['offset'] + L) * SR)].copy()
    y = fade(y, seg['fade_in'], seg['fade_out'])
    target = -14.5 + seg.get('gain', 0)
    cur = lufs(x[int(seg['offset'] * SR):int((seg['offset'] + max(L, 8)) * SR)])
    y *= 10 ** ((target - cur) / 20)
    i0 = int(seg['start'] * SR); i1 = min(N, i0 + len(y))
    music_bus[i0:i1] += y[:i1 - i0]
# silences
g = np.ones(N, np.float32)
for a, b in plan['music_dips']:
    ia, ib = int(a * SR), int(b * SR); r = int(0.12 * SR)
    g[ia:ib] = 0.0
    g[max(0, ia - r):ia] = np.minimum(g[max(0, ia - r):ia], np.linspace(1, 0, ia - max(0, ia - r)))
    g[ib:ib + r] = np.minimum(g[ib:ib + r], np.linspace(0, 1, len(g[ib:ib + r])))
music_bus *= g[:, None]

# ---- voice and ducking (attack 150 ms, release 400 ms, 9 dB)
voice = load(f"{EP}/{plan['voice']}", mono=True)
v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(v ** 2, np.ones(hop * 3) / (hop * 3), 'same') + 1e-12)
active = (20 * np.log10(env) > -38).astype(np.float32)
red = np.zeros(N, np.float32)
a_att, a_rel = np.exp(-1 / (0.150 * SR)), np.exp(-1 / (0.400 * SR))
# one-pole smoothing at control rate for speed
ctrl = active[::hop]; out = np.zeros_like(ctrl); st = 0.0
aa, ar = np.exp(-1 / (0.150 * 100)), np.exp(-1 / (0.400 * 100))
for i, c in enumerate(ctrl):
    tgt = 9.0 * c
    st = aa * st + (1 - aa) * tgt if tgt > st else ar * st + (1 - ar) * tgt
    out[i] = st
red = np.repeat(out, hop)[:N]
music_bus *= (10 ** (-red / 20))[:, None]

mix = music_bus + sfx_bus + np.stack([v, v], 1)
import soundfile as sf
sf.write('/tmp/_premix.wav', mix, SR, subtype='FLOAT')
sf.write(OUT.replace('.wav', '.music.wav'), music_bus, SR, subtype='FLOAT')
sf.write(OUT.replace('.wav', '.sfx.wav'), sfx_bus, SR, subtype='FLOAT')
# two-pass loudnorm to -16 LUFS / -1.5 dBTP
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', '/tmp/_premix.wav', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
js = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
      f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,alimiter=limit=0.84:level=false,aresample=48000")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', '/tmp/_premix.wav', '-af', af, '-c:a', 'pcm_s24le', OUT], check=True)
print('missing sfx:', missing)
print('premix', js['input_i'], 'LUFS, TP', js['input_tp'])
