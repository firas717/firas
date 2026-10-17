#!/usr/bin/env python3
"""Replace short spans of a restored voice with the same spans from another, sample-aligned rendering of the take
(e.g. the raw recording run through the same narrator chain) — for the rare word the restoration model changed.

usage: patch_voice.py base.wav donor.wav out.wav <t0-t1> [<t0-t1> ...]
Each span is level-matched to the base over the surrounding word (span +/- 150 ms) and blended in with 10 ms
equal-power crossfades (the two renderings are not phase-coherent). Sample positions are unchanged, so sync holds.
"""
import sys
import numpy as np, soundfile as sf

base, sr = sf.read(sys.argv[1], dtype='float64')
donor, sr2 = sf.read(sys.argv[2], dtype='float64')
assert sr == sr2 and len(base) == len(donor), 'base and donor must be sample-aligned renderings of the same take'
y, xf, ctx = base.copy(), int(0.010 * sr), int(0.150 * sr)
for span in sys.argv[4:]:
    t0, t1 = (float(v) for v in span.split('-'))
    a, b = int(t0 * sr), int(t1 * sr)
    ca, cb = max(0, a - ctx), min(len(y), b + ctx)
    g = np.sqrt(np.mean(base[ca:cb] ** 2) / (np.mean(donor[ca:cb] ** 2) + 1e-20))
    w = np.zeros(len(y)); w[a:b] = 1.0
    ramp = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    w[a - xf:a] = ramp; w[b:b + xf] = ramp[::-1]
    sel = slice(a - xf, b + xf)
    # equal-power blend: base * cos, donor * sin (w is sin^2)
    y[sel] = base[sel] * np.sqrt(1 - w[sel]) + g * donor[sel] * np.sqrt(w[sel])
    print(f'  patched {t0:.3f}-{t1:.3f}s from donor (gain {20 * np.log10(g):+.1f} dB)')
sf.write(sys.argv[3], y.astype(np.float32), sr, subtype='FLOAT')
