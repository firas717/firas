#!/usr/bin/env python3
"""How loud is the music under the voice? Measures a mix's stems written by mix.py.

usage: mix_report.py <voice.wav> <mix.wav> [...]
For each mix, uses <mix>.music.wav and reports the music's loudness while the voice speaks and in the pauses,
and the gap to the voice (LU). Torcoli et al. 2019: >= 10 LU is the minimum; this channel's owner wants ~25+.
"""
import re, subprocess, sys, tempfile
import numpy as np, soundfile as sf

SR = 48000


def lufs(x):
    p = tempfile.mktemp(suffix='.wav'); sf.write(p, x, SR, subtype='FLOAT')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    v = re.findall(r'I:\s+(-?[\d.]+) LUFS', r)
    return float(v[-1]) if v else -70.0


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


v = load(sys.argv[1])[:, 0]
hop = SR // 100
env = 20 * np.log10(np.sqrt(np.convolve(v ** 2, np.ones(hop * 3) / (hop * 3), 'same')) + 1e-9)
for mix in sys.argv[2:]:
    m = load(mix.replace('.wav', '.music.wav'))
    n = min(len(m), len(env)); act = env[:n] > -38
    vl = lufs(np.stack([v[:n][act]] * 2, 1))
    ms, mp = lufs(m[:n][act]), lufs(m[:n][~act])
    print(f'{mix.split("/")[-1]:<24} voice {vl:6.1f} | music under speech {ms:6.1f} ({vl - ms:4.1f} LU below) | in pauses {mp:6.1f}')
