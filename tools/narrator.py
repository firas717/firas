#!/usr/bin/env python3
"""Narrator mastering chain for a restored voice: tone-match, tame the low end, de-ess, level, gate the pauses.

usage: narrator.py in.wav out.wav [--key raw.wav] [--eq-amount 0..1] [--presence <dB at 2.5-5 kHz>]
1. static zero-phase EQ from 250 Hz up toward the ANSI S3.5 speech curve plus a documentary-narrator tilt (measured on
   the input, smoothed across bands, clamped to -6..+3 dB, scaled by --eq-amount); 70 Hz 24 dB/oct high-pass;
2. dynamic low band (110-260 Hz): turned down only on loud syllables, where restoration adds fundamental (boom),
   so soft, calm syllables keep their chest;
3. level-aware split-band de-esser (4.5-10 kHz): only loud sibilants, never the weak fricatives (th, f, h);
4. 2:1 RMS compressor (~2-3 dB on word peaks);
5. fixed gain to -16 LUFS + look-ahead true-peak limiter at +1 dBTP (float output; the mix bus sets the final peak);
6. with --key (the raw, sample-aligned recording): downward gate in the pauses where the raw take was silent,
   so restoration hiss, rumble and lifted breath noise do not fill the silences.
Length is preserved sample for sample. Output: 48 kHz mono 32-bit float.
"""
import os, subprocess, sys, tempfile
import numpy as np, soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from ltass import REF, spectrum

args = sys.argv[3:]
opt = lambda k, d: float(args[args.index(k) + 1]) if k in args else d
KEY = args[args.index('--key') + 1] if '--key' in args else None
PRESENCE, AMOUNT = opt('--presence', 1.0), opt('--eq-amount', 0.7)
# narrator tilt relative to ANSI average speech: slightly darker top, a touch of presence
TILT = {2500: PRESENCE, 3150: PRESENCE, 4000: PRESENCE, 5000: PRESENCE * .5, 6300: -1, 8000: -2, 10000: -3, 12500: -5}
EDGE = {100: 30.0, 125: 31.5, 10000: -1.0, 12500: -3.5}


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stderr


def smooth_gr(gr, sr, attack, release):
    """One-pole attack/release smoothing of a gain-reduction curve (dB)."""
    a_att, a_rel = np.exp(-1 / (attack * sr)), np.exp(-1 / (release * sr))
    sm, st = np.empty_like(gr), 0.0
    for i, v in enumerate(gr):
        st = a_att * st + (1 - a_att) * v if v > st else a_rel * st + (1 - a_rel) * v
        sm[i] = st
    return sm


def correction(path):
    s = spectrum(path)
    bands = sorted(s)
    off = np.mean([s[f] - REF[f] for f in (250, 315, 400, 500, 630, 800, 1000)])
    dev = np.array([s[f] - off - REF.get(f, EDGE.get(f)) - TILT.get(f, 0) for f in bands])
    sm = np.convolve(np.pad(dev, 1, mode='edge'), [.25, .5, .25], 'valid')     # follow the trend, not each formant
    g = np.clip(-sm, -6, 3) * AMOUNT                                              # how far toward the target
    g[np.array(bands) < 250] = 0.0       # below 250 Hz the excess is level-dependent: handled by dynlow(), not here
    return bands, g


def dynlow(x, sr, rng=6.0, lo=110, hi=260, ratio=3.0, pct=60):
    """Dynamic low band: turn 110-260 Hz down only where that band is louder than its 60th percentile on active
    speech (Sidon adds ~6 dB of fundamental on loud syllables, ~0 on soft ones); ratio 3, at most 6 dB, 5/80 ms."""
    from scipy.signal import butter, sosfiltfilt
    band = sosfiltfilt(butter(3, [lo, hi], 'bandpass', fs=sr, output='sos'), x)
    win = int(0.010 * sr)
    eb = 10 * np.log10(np.convolve(band ** 2, np.ones(win) / win, 'same') + 1e-12)
    ef = 10 * np.log10(np.convolve(x ** 2, np.ones(win) / win, 'same') + 1e-12)
    thr = np.percentile(eb[ef > ef.max() - 40], pct)
    sm = smooth_gr(np.minimum(np.clip(eb - thr, 0, None) * (1 - 1 / ratio), rng), sr, 0.005, 0.080)
    print(f'  low band: active {np.mean(sm > 0.5) * len(x) / sr:.1f}s, mean {sm[sm > 0.5].mean():.1f} dB, max {sm.max():.1f} dB')
    return x - band * (1 - 10 ** (-sm / 20))


def deess(x, sr, thresh=-12.0, level=-24.0, ratio=3.0, rng=5.0):
    """Zero-phase split-band de-esser: when 4.5-10 kHz energy comes within `thresh` dB of the full-band energy AND is
    loud in absolute terms (above `level` dB re the median 50 ms speech peak), turn only that band down (ratio 3,
    at most `rng` dB, attack 1 ms, release 60 ms). The level term spares weak fricatives such as th/f/h."""
    from scipy.signal import butter, sosfiltfilt
    band = sosfiltfilt(butter(4, [4500, min(10000, sr / 2 - 100)], 'bandpass', fs=sr, output='sos'), x)
    win = int(0.005 * sr)
    env = lambda s: 10 * np.log10(np.convolve(s ** 2, np.ones(win) / win, 'same') + 1e-12)
    eb, ef = env(band), env(x)
    blk = int(0.05 * sr); nb = len(ef) // blk
    bm = ef[:nb * blk].reshape(nb, blk).max(1)
    ref = np.median(bm[bm > bm.max() - 40])
    over = np.clip(np.minimum((eb - ef) - thresh, eb - (ref + level)), 0, None)
    sm = smooth_gr(np.minimum(over * (1 - 1 / ratio), rng), sr, 0.001, 0.060)
    act = sm[sm > 0.5]
    print(f'  de-ess: active {len(act) / sr:.1f}s, mean {act.mean() if len(act) else 0:.1f} dB, max {sm.max():.1f} dB')
    return x - band * (1 - 10 ** (-sm / 20))


def zero_phase_eq(x, sr, bands, g):
    """Apply a smooth gain curve (dB at 1/3-octave centres, interpolated on log-frequency) with no phase shift
    and no change in length; plus a 70 Hz 24 dB/oct high-pass magnitude."""
    n = 1 << int(np.ceil(np.log2(len(x) + sr)))
    f = np.fft.rfftfreq(n, 1 / sr)
    lf = np.log2(np.maximum(f, 10))
    gdb = np.interp(lf, np.log2(bands), g, left=g[0], right=g[-1])
    hp = 1 / np.sqrt(1 + (70 / np.maximum(f, 1e-3)) ** 8)          # 4th-order Butterworth magnitude
    return np.fft.irfft(np.fft.rfft(x, n) * 10 ** (gdb / 20) * hp, n)[:len(x)]


def pause_gate(y, key, sr, below=35.0, rng=18.0, pre=0.030, post=0.100):
    """Downward gate keyed by the raw take: where the raw 10 ms level is more than `below` dB under its typical
    speech level (pauses the phone left near-silent), attenuate by `rng` dB; open 30 ms before and hold 100 ms after
    any sound, with raised-cosine ramps (5 ms opening, 25 ms closing) so onsets and word tails are untouched."""
    from scipy.ndimage import maximum_filter1d
    win = int(0.010 * sr)
    k = 10 * np.log10(np.convolve(key ** 2, np.ones(win) / win, 'same') + 1e-14)
    ref = np.median(k[k > k.max() - 30])
    op = (k > ref - below).astype(np.float64)
    a, b = int(pre * sr), int(post * sr)
    op = maximum_filter1d(op, size=a + b + 1, origin=(b - a) // 2)   # widen: a samples before, b after
    g = np.empty_like(op); st = op[0]
    up, down = 1 / (0.005 * sr), 1 / (0.025 * sr)
    for i, v in enumerate(op):                                        # linear ramps, then raised-cosine shape
        st = min(v, st + up) if v > st else max(v, st - down)
        g[i] = st
    g = 0.5 - 0.5 * np.cos(np.pi * g)
    gain = 10 ** (-rng * (1 - g) / 20)
    print(f'  pause gate: closed on {np.mean(g < 0.01) * 100:.1f}% of the file (raw speech ref {ref:.1f} dBFS)')
    return y * gain


def tp_limit(x, sr, ceiling_db, look=0.002, release=0.060):
    """Look-ahead peak limiter on the 4x-oversampled (true-peak) envelope: gain only ever goes down where a peak
    would cross the ceiling, reached over `look` seconds before it, recovering over `release`."""
    from scipy.signal import resample_poly
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    ceil = 10 ** (ceiling_db / 20) * 0.98
    tp = np.abs(resample_poly(x, 4, 1)).reshape(-1, 4).max(1)[:len(x)]
    need = np.minimum(1.0, ceil / np.maximum(tp, 1e-9))
    L = max(1, int(look * sr))
    g = 1 / maximum_filter1d(1 / need, size=2 * L + 1)                # hold the deepest cut across the look-ahead
    a = np.exp(-1 / (release * sr)); out = np.empty_like(g); st = 1.0
    for i, v in enumerate(g):                                          # instant attack (already pre-held), smooth release
        st = v if v < st else a * st + (1 - a) * v
        out[i] = st
    out = uniform_filter1d(out, L)            # round the attack edge; stays under the need since the hold spans +/-L
    gr = -20 * np.log10(out)
    print(f'  limiter: {np.mean(gr > 1) * 100:.2f}% of samples > 1 dB, max {gr.max():.1f} dB')
    return x * out


def lufs(x, sr, tmp):
    p = f'{tmp}/_l.wav'
    sf.write(p, x.astype(np.float32), sr, subtype='FLOAT')
    m = run(['ffmpeg', '-hide_banner', '-i', p, '-af', 'ebur128', '-f', 'null', '-'])
    return float(m[m.rindex('I:'):].split()[1])


def main(inp, out):
    sr = sf.info(inp).samplerate
    bands, g = correction(inp)
    tmp = tempfile.mkdtemp()
    stage1, pre = f'{tmp}/st1.wav', f'{tmp}/comp.wav'
    x, _ = sf.read(inp, dtype='float64')
    x = deess(dynlow(zero_phase_eq(x.mean(1) if x.ndim > 1 else x, sr, bands, g), sr), sr)
    # level to -20 LUFS after EQ/de-ess so the compressor threshold means the same thing for any input
    x = x * 10 ** ((-20 - lufs(x, sr, tmp)) / 20)
    sf.write(stage1, x, sr, subtype='FLOAT')
    run(['ffmpeg', '-v', 'error', '-y', '-i', stage1, '-af',
         'acompressor=threshold=-18dB:ratio=2:attack=15:release=180:knee=6:makeup=1:detection=rms', '-c:a', 'pcm_f32le', pre])
    y, _ = sf.read(pre, dtype='float64')
    if KEY:
        k, ksr = sf.read(KEY, dtype='float64')
        k = k.mean(1) if k.ndim > 1 else k
        assert ksr == sr and len(k) == len(y), f'key must be sample-aligned with the input ({ksr} Hz, {len(k)} samples)'
        y = pause_gate(y, k, sr)
    # fixed gain to -16 LUFS (ffmpeg loudnorm would silently switch to its gain-riding "dynamic" mode on speech),
    # then only the rare peaks above +1 dBTP are limited; the mix bus brings the final mix under -1 dBTP
    for _ in range(2):                                                 # second pass corrects for the limiter's loss
        y = y * 10 ** ((-16 - lufs(y, sr, tmp)) / 20)
        y = tp_limit(y, sr, 1.0)
    if sr != 48000:
        import soxr
        y = soxr.resample(y, sr, 48000, 'VHQ')
    sf.write(out, y.astype(np.float32), 48000, subtype='FLOAT')
    n_in, n_out = sf.info(inp).frames * 48000 / sr, sf.info(out).frames
    print(f'{os.path.basename(out)}: EQ ' + ' '.join(f'{f}:{v:+.1f}' for f, v in zip(bands, g)))
    print(f'  length in {n_in / 48000:.3f}s out {n_out / 48000:.3f}s, {lufs(y, 48000, tmp):.1f} LUFS')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
