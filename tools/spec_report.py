#!/usr/bin/env python3
"""Band energy of speech frames relative to 200-500 Hz (dB)."""
import sys, numpy as np, soundfile as sf
for p in sys.argv[1:]:
    x, sr = sf.read(p); x = x.mean(1) if x.ndim > 1 else x
    fr = int(0.02 * sr); n = len(x) // fr
    F = x[:n * fr].reshape(n, fr); db = 20 * np.log10(np.sqrt((F ** 2).mean(1)) + 1e-9)
    sp = F[db > np.percentile(db, 55)].ravel()
    S = np.abs(np.fft.rfft(sp * np.hanning(len(sp)))) ** 2; f = np.fft.rfftfreq(len(sp), 1 / sr)
    band = lambda lo, hi: 10 * np.log10(S[(f >= lo) & (f < hi)].mean() + 1e-20)
    ref = band(200, 500)
    out = [f"{lo}-{hi}:{band(lo,hi)-ref:+.1f}" for lo, hi in [(60,120),(120,200),(500,1000),(1000,2000),(2000,4000),(4000,6000),(6000,9000),(9000,14000)]]
    print(p, "|", " ".join(out))
