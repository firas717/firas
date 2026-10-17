#!/usr/bin/env python3
"""Long-term speech spectrum vs the ANSI S3.5-1997 standard speech spectrum (normal effort), per 1/3 octave.

usage: ltass.py a.wav [b.wav ...]
Prints, for each band, how many dB the voice sits above (+) or below (-) the reference shape after
aligning both at 250-1000 Hz. Positive at 125-200 Hz = boomy; positive at 300-600 Hz = boxy;
negative at 2-5 kHz = dull/muffled; positive at 5-9 kHz = harsh/sibilant.
"""
import sys, numpy as np, soundfile as sf

# ANSI S3.5-1997 Table 3, standard speech spectrum level (dB/Hz), normal vocal effort
REF = {160: 32.41, 200: 34.48, 250: 34.75, 315: 33.98, 400: 34.59, 500: 34.27, 630: 32.06, 800: 28.30,
       1000: 25.01, 1250: 23.00, 1600: 20.15, 2000: 17.32, 2500: 13.18, 3150: 11.55, 4000: 9.33,
       5000: 5.31, 6300: 2.59, 8000: 1.13}
BANDS = [100, 125] + list(REF) + [10000, 12500]

def spectrum(p):
    x, sr = sf.read(p); x = x.mean(1) if x.ndim > 1 else x
    fr = int(0.02 * sr); n = len(x) // fr
    F = x[:n * fr].reshape(n, fr); db = 20 * np.log10(np.sqrt((F ** 2).mean(1)) + 1e-9)
    sp = F[db > db.max() - 35].ravel()                       # speech frames only
    seg = 8192; w = np.hanning(seg); acc = 0; k = 0
    for s in range(0, len(sp) - seg, seg // 2):
        acc = acc + np.abs(np.fft.rfft(sp[s:s + seg] * w)) ** 2; k += 1
    f = np.fft.rfftfreq(seg, 1 / sr)
    return {fc: 10 * np.log10(acc[(f >= fc / 2 ** (1 / 6)) & (f < fc * 2 ** (1 / 6))].mean() / k + 1e-30) for fc in BANDS}

if __name__ == '__main__':
    for p in sys.argv[1:]:
        s = spectrum(p)
        off = np.mean([s[fc] - REF[fc] for fc in (250, 315, 400, 500, 630, 800, 1000)])
        row = []
        for fc in BANDS:
            ref = REF.get(fc, {100: 30.0, 125: 31.5, 10000: -1.0, 12500: -3.5}.get(fc))  # edges extrapolated
            row.append(f"{fc if fc < 1000 else str(fc / 1000).rstrip('0').rstrip('.') + 'k'}:{s[fc] - off - ref:+.0f}")
        print(f"{p.split('/')[-1][:22]:<22}", ' '.join(row))
