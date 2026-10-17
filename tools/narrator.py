#!/usr/bin/env python3
"""Narrator mastering chain for a restored voice: tone-match to a reference speech curve, de-ess, gentle levelling.

usage: narrator.py in.wav out.wav [--depth <dB at 100-160 Hz>] [--presence <dB at 2.5-5 kHz>] [--report]
1. measures the voice's long-term 1/3-octave spectrum and builds a corrective EQ toward the ANSI S3.5 speech
   curve plus a documentary-narrator tilt (smoothed across bands, clamped to -6..+3 dB, applied with firequalizer);
2. high-pass 70 Hz (24 dB/oct), de-esser on 5-9 kHz, 2:1 RMS compressor (2-3 dB of gain reduction);
3. two-pass loudnorm to -16 LUFS / -1.5 dBTP, 48 kHz 24-bit. Length is preserved sample for sample.
"""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from ltass import REF, spectrum

args = sys.argv[3:]
opt = lambda k, d: float(args[args.index(k) + 1]) if k in args else d
DEPTH, PRESENCE = opt('--depth', 0.0), opt('--presence', 1.0)
# narrator tilt relative to ANSI average speech: slightly darker top, a touch of presence, no boom
TILT = {100: -4, 125: -1, 160: 0, 200: 0, 2500: PRESENCE, 3150: PRESENCE, 4000: PRESENCE, 5000: PRESENCE * .5,
        6300: -1, 8000: -2, 10000: -3, 12500: -5}
EDGE = {100: 30.0, 125: 31.5, 10000: -1.0, 12500: -3.5}


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stderr


def correction(path):
    s = spectrum(path)
    bands = sorted(s)
    off = np.mean([s[f] - REF[f] for f in (250, 315, 400, 500, 630, 800, 1000)])
    dev = np.array([s[f] - off - REF.get(f, EDGE.get(f)) - TILT.get(f, 0) for f in bands])
    sm = np.convolve(np.pad(dev, 1, mode='edge'), [.25, .5, .25], 'valid')     # follow the trend, not each formant
    g = np.clip(-sm, -6, 3)
    g[bands.index(100)] = min(g[bands.index(100)], 2)                            # never pump up phone rumble
    for f in (100, 125, 160):
        g[bands.index(f)] += DEPTH
    return bands, g


def deess(x, sr, thresh=-12.0, ratio=3.0, rng=6.0):
    """Zero-phase split-band de-esser: when 4.5-10 kHz energy comes within `thresh` dB of the full-band energy
    (an 's'/'sh'/'ص'), turn only that band down (ratio 3, at most `rng` dB, attack 1 ms, release 60 ms)."""
    from scipy.signal import butter, sosfiltfilt
    band = sosfiltfilt(butter(4, [4500, min(10000, sr / 2 - 100)], 'bandpass', fs=sr, output='sos'), x)
    win = int(0.005 * sr)
    env = lambda s: 10 * np.log10(np.convolve(s ** 2, np.ones(win) / win, 'same') + 1e-12)
    eb, ef = env(band), env(x)
    over = np.clip((eb - ef) - thresh, 0, None) * (eb > ef.max() - 50)
    gr = np.minimum(over * (1 - 1 / ratio), rng)
    a_att, a_rel = np.exp(-1 / (0.001 * sr)), np.exp(-1 / (0.060 * sr))
    sm, st = np.empty_like(gr), 0.0
    for i, v in enumerate(gr):                                   # peak-hold style smoothing
        st = a_att * st + (1 - a_att) * v if v > st else a_rel * st + (1 - a_rel) * v
        sm[i] = st
    y = x - band * (1 - 10 ** (-sm / 20))
    act = sm[sm > 0.5]
    print(f'  de-ess: active {len(act) / sr:.1f}s, mean {act.mean() if len(act) else 0:.1f} dB, max {sm.max():.1f} dB')
    return y.astype(np.float32)


def zero_phase_eq(x, sr, bands, g):
    """Apply a smooth gain curve (dB at 1/3-octave centres, interpolated on log-frequency) with no phase shift
    and no change in length; plus a 70 Hz 24 dB/oct high-pass magnitude."""
    n = 1 << int(np.ceil(np.log2(len(x) + sr)))
    f = np.fft.rfftfreq(n, 1 / sr)
    lf = np.log2(np.maximum(f, 10))
    gdb = np.interp(lf, np.log2(bands), g, left=g[0], right=g[-1])
    hp = 1 / np.sqrt(1 + (70 / np.maximum(f, 1e-3)) ** 8)          # 4th-order Butterworth magnitude
    y = np.fft.irfft(np.fft.rfft(x, n) * 10 ** (gdb / 20) * hp, n)[:len(x)]
    return y


def main(inp, out):
    sr = sf.info(inp).samplerate
    bands, g = correction(inp)
    tmp = tempfile.mkdtemp()
    stage1, pre = f'{tmp}/eq.wav', f'{tmp}/pre.wav'
    # pre-level to about -20 LUFS so the compressor threshold means the same thing for any input
    m = run(['ffmpeg', '-hide_banner', '-i', inp, '-af', 'ebur128', '-f', 'null', '-'])
    I = float(m[m.rindex('I:'):].split()[1])
    x, _ = sf.read(inp, dtype='float64')
    x = (x.mean(1) if x.ndim > 1 else x) * 10 ** ((-20 - I) / 20)
    sf.write(stage1, deess(zero_phase_eq(x, sr, bands, g), sr), sr, subtype='FLOAT')
    run(['ffmpeg', '-v', 'error', '-y', '-i', stage1, '-af',
         'acompressor=threshold=-24dB:ratio=2:attack=15:release=180:knee=6:makeup=1:detection=rms', '-c:a', 'pcm_f32le', pre])
    r = run(['ffmpeg', '-hide_banner', '-i', pre, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'])
    js = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    run(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af', f'{ln},alimiter=limit=0.84:level=false,aresample=48000:resampler=soxr',
         '-c:a', 'pcm_s24le', out])
    n_in, n_out = sf.info(inp).frames * 48000 / sr, sf.info(out).frames
    print(f'{os.path.basename(out)}: EQ ' + ' '.join(f'{f}:{v:+.1f}' for f, v in zip(bands, g)))
    print(f'  length in {n_in / 48000:.3f}s out {n_out / 48000:.3f}s')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
