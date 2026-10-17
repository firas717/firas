#!/usr/bin/env python3
"""Lower the speaking pitch slightly without changing timing or vowel colour (Praat PSOLA, formants untouched).

usage: PYTHONPATH=<parselmouth> voice_depth.py in.wav out.wav <semitones, e.g. -1.0>
"""
import sys
import numpy as np, soundfile as sf, parselmouth
from parselmouth.praat import call

inp, out, st = sys.argv[1], sys.argv[2], float(sys.argv[3])
x, sr = sf.read(inp, dtype='float64')
x = x.mean(1) if x.ndim > 1 else x
snd = parselmouth.Sound(x, sampling_frequency=sr)
pitch = call(snd, 'To Pitch', 0.0, 75, 400)
f0 = call(pitch, 'Get quantile', 0, 0, 0.5, 'Hertz')
# Change gender: pitch floor/ceiling, formant shift ratio 1 (keep vowels), new median, range factor 1, duration 1
y = call(snd, 'Change gender', 75, 400, 1.0, f0 * 2 ** (st / 12), 1.0, 1.0).values[0]
y = np.concatenate([y, np.zeros(max(0, len(x) - len(y)))])[:len(x)]
sf.write(out, y.astype(np.float32), sr, subtype='FLOAT')
print(f'{out}: median F0 {f0:.0f} -> {f0 * 2 ** (st / 12):.0f} Hz, {len(x) / sr:.3f}s -> {len(y) / sr:.3f}s')
